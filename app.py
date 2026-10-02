import streamlit as st

from src.claims import load_facts, validate_claims
from src.context_ui import (
    render_demo_post_selector,
    render_founder_context_panel,
)
from src.models import Post, Review, ReviewDecision
from src.outbox import save_handoff
from src.paths import FACTS_FILE, VOICE_FILE
from src.pipeline import run_pipeline
from src.quality import check_comment_quality
from src.review import (
    delete_review,
    list_reviews,
    save_review,
)
from src.voice import load_voice_examples


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Byro Comment Copilot",
    page_icon="💬",
    layout="wide",
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULT_STATE = {
    "analysis_result": None,
    "editing_comment": False,
    "edited_text": "",
    "draft_initialized": False,
    "post_source": "Synthetic demo post",
    "last_analyzed_post": "",
    "last_analyzed_source": "",
}


for key, default in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():
    return load_voice_examples(VOICE_FILE)


# =========================================================
# ANALYZE POST
# =========================================================

def analyze(
    post_text: str,
    person: str,
) -> None:

    result = run_pipeline(
        post=Post(
            id="live-input",
            text=post_text.strip(),
        ),
        person=person,
        voice_examples=load_data(),
    )

    st.session_state.analysis_result = result
    st.session_state.last_analyzed_post = post_text.strip()
    st.session_state.last_analyzed_source = st.session_state.post_source

    st.session_state.editing_comment = False

    if result.generated_comment:
        st.session_state.edited_text = (
            result.generated_comment.text
        )
        st.session_state.draft_initialized = True
    else:
        st.session_state.edited_text = ""
        st.session_state.draft_initialized = False


# =========================================================
# MAIN
# =========================================================

def main():

    # -----------------------------------------------------
    # Header
    # -----------------------------------------------------

    st.title("Byro Comment Copilot")

    st.caption(
        "Human-in-the-loop LinkedIn commenting assistant"
    )

    # -----------------------------------------------------
    # Load examples
    # -----------------------------------------------------

    examples = load_data()

    people = sorted(
        {
            example.person
            for example in examples
            if example.person.lower() != "byro/company"
        }
    )

    if not people:
        st.error(
            "No personal voice examples found."
        )
        return

    # =====================================================
    # FOUNDER
    # =====================================================

    person = st.selectbox(
        "Founder",
        people,
        key="founder",
    )

    # -----------------------------------------------------
    # Founder Context
    # -----------------------------------------------------

    render_founder_context_panel(
        person
    )

    st.divider()

    # =====================================================
    # POST SOURCE
    # =====================================================

    st.radio(
        "Post source",
        [
            "Synthetic demo post",
            "Paste a post",
        ],
        horizontal=True,
        key="post_source",
    )

    post_text = ""

    # -----------------------------------------------------
    # Synthetic demo
    # -----------------------------------------------------

    if (
        st.session_state.post_source
        == "Synthetic demo post"
    ):

        post_text = render_demo_post_selector(
            person
        )

    # -----------------------------------------------------
    # Manual input
    # -----------------------------------------------------

    else:

        post_text = st.text_area(
            "LinkedIn post",
            height=220,
            placeholder=(
                "Paste a LinkedIn post here..."
            ),
            key="post_input",
        )

    # =====================================================
    # ANALYZE
    # =====================================================

    if st.button(
        "Analyze Post",
        type="primary",
        use_container_width=True,
    ):

        if not post_text.strip():

            st.warning(
                "Please enter or select a LinkedIn post."
            )

        else:

            with st.spinner(
                "Analyzing founder fit, relevance and possible response..."
            ):

                analyze(
                    post_text,
                    person,
                )

    # =====================================================
    # NO RESULT YET
    # =====================================================

    result = st.session_state.analysis_result

    if result is None:

        st.info(
            "Choose a synthetic demo or paste a post, "
            "then click Analyze Post."
        )

        return

    # Prevent an old result from being shown for a newly changed input.
    current_post = (post_text or "").strip()
    analyzed_post = (result.post.text or "").strip()

    if current_post and current_post != analyzed_post:
        st.warning(
            "The post has changed since the last analysis. "
            "Click **Analyze Post** to refresh the decision."
        )

        with st.expander("Post currently shown in the previous analysis"):
            st.write(analyzed_post)

        return

    st.divider()

    # Show exactly what the pipeline analyzed. This makes it easy to
    # catch selector/state mismatches during the demo.
    with st.expander("Post analyzed by the pipeline", expanded=False):
        st.write(analyzed_post)
        st.caption(
            f"Source: {st.session_state.last_analyzed_source or 'Unknown'}"
        )

    # =====================================================
    # 1. ENGAGEMENT DECISION
    # =====================================================

    st.subheader(
        "1. Engagement Decision"
    )

    decision_value = (
        result.engagement_decision.value
    )

    if decision_value == "engage":

        st.success(
            "ENGAGE"
        )

    elif decision_value == "ask":

        st.warning(
            "ASK FOR HUMAN DECISION"
        )

    else:

        st.info(
            "SKIP"
        )

    st.write(
        result.engagement_reason
    )

    st.caption(
        f"Confidence: "
        f"{result.engagement_confidence:.0%}"
    )

    # =====================================================
    # NO AUTOMATIC DRAFT
    # =====================================================

    if result.generated_comment is None:

        st.info(
            "The system recommends not drafting automatically."
        )

        if st.button(
            "Draft Anyway",
            type="secondary",
            use_container_width=True,
        ):

            with st.spinner(
                "Drafting because the human chose to override "
                "the recommendation..."
            ):

                try:

                    override = run_pipeline(
                        post=result.post,
                        person=result.founder,
                        voice_examples=examples,
                        force_draft=True,
                    )

                except TypeError:

                    st.error(
                        "Your current pipeline does not support "
                        "`force_draft=True`. Update `src/pipeline.py` "
                        "before using Draft Anyway."
                    )

                    return

            st.session_state.analysis_result = override

            if override.generated_comment:

                st.session_state.edited_text = (
                    override.generated_comment.text
                )

                st.session_state.draft_initialized = True

            else:

                st.session_state.edited_text = ""
                st.session_state.draft_initialized = False

            st.session_state.editing_comment = False

            st.rerun()

        return

    # =====================================================
    # 2. COMMENT MODE
    # =====================================================

    st.subheader(
        "2. Comment Mode"
    )

    st.code(
        result.comment_mode.value,
        language="text",
    )

    # =====================================================
    # 3. VOICE EVIDENCE
    # =====================================================

    st.subheader(
        "3. Voice Evidence"
    )

    if result.voice_examples:

        for example in result.voice_examples:

            with st.expander(
                f"{example.source_type.title()} — "
                f"{example.id}"
            ):

                st.write(
                    example.text
                )

                if example.topic:

                    st.caption(
                        f"Topic: {example.topic}"
                    )

    else:

        st.info(
            "No matching voice evidence found."
        )

    # =====================================================
    # 4. CALIBRATION EVIDENCE
    # =====================================================

    reference_examples = getattr(
        result,
        "reference_examples",
        [],
    )

    if reference_examples:

        st.subheader(
            "4. Founder Calibration Evidence"
        )

        st.caption(
            "Synthetic calibration examples used to "
            "help match the founder's commenting behavior."
        )

        for index, example in enumerate(
            reference_examples,
            start=1,
        ):

            with st.expander(
                f"Calibration example {index}"
            ):

                st.write(
                    "**Reference post:**"
                )

                st.write(
                    example.get(
                        "post",
                        "",
                    )
                )

                st.write(
                    "**Reference comment:**"
                )

                st.code(
                    example.get(
                        "reference_comment",
                        "",
                    )
                )

                if example.get("style_note"):

                    st.caption(
                        example["style_note"]
                    )

    # =====================================================
    # 5. SUGGESTED COMMENT
    # =====================================================

    st.subheader(
        "5. Suggested Comment"
    )

    generated_text = (
        result.generated_comment.text
    )

    # -----------------------------------------------------
    # Generation failure
    # -----------------------------------------------------

    if not generated_text:

        st.error(
            "The model could not safely generate a comment."
        )

        warnings = (
            result.generated_comment.warnings
            if result.generated_comment
            else []
        )

        if warnings:

            st.write(
                "Generator details:"
            )

            for warning in warnings:

                st.warning(
                    warning
                )

        return

    # -----------------------------------------------------
    # Initialize draft
    # -----------------------------------------------------

    if not st.session_state.draft_initialized:

        st.session_state.edited_text = (
            generated_text
        )

        st.session_state.draft_initialized = True

    # =====================================================
    # NORMAL DISPLAY
    # =====================================================

    if not st.session_state.editing_comment:

        st.text_area(
            "AI draft",
            value=(
                st.session_state.edited_text
            ),
            height=140,
            disabled=True,
        )

        if st.button(
            "✏️ Edit Comment",
            use_container_width=False,
        ):

            st.session_state.editing_comment = True

            st.rerun()

    # =====================================================
    # EDIT MODE
    # =====================================================

    else:

        edited_value = st.text_area(
            "Edit the comment",
            value=(
                st.session_state.edited_text
            ),
            height=140,
            key="editing_box",
        )

        if st.button(
            "✅ Done Editing",
            use_container_width=False,
        ):

            st.session_state.edited_text = (
                edited_value.strip()
            )

            st.session_state.editing_comment = False

            st.rerun()

    # =====================================================
    # FINAL TEXT
    # =====================================================

    final_text = (
        st.session_state.edited_text.strip()
    )

    # =====================================================
    # 6. QUALITY & SAFETY
    # =====================================================

    st.subheader(
        "6. Quality & Safety Checks"
    )

    final_quality = check_comment_quality(
        final_text,
        result.comment_mode,
        result.post.text,
    )

    final_claims = validate_claims(
        final_text,
        result.post.text,
        result.founder,
        load_facts(FACTS_FILE),
    )

    # -----------------------------------------------------
    # Quality
    # -----------------------------------------------------

    if final_quality:

        for warning in final_quality:

            st.warning(
                warning
            )

    else:

        st.success(
            "No obvious quality problems detected."
        )

    # -----------------------------------------------------
    # Claims
    # -----------------------------------------------------

    if final_claims:

        for warning in final_claims:

            st.error(
                warning
            )

        st.error(
            "Approval is blocked until the final draft "
            "no longer contains unsupported claims."
        )

    else:

        st.success(
            "Claims check passed."
        )

    # =====================================================
    # 7. HUMAN REVIEW
    # =====================================================

    st.subheader(
        "7. Human Review"
    )

    approve_disabled = (
        not final_text
        or bool(final_claims)
    )

    edited_disabled = (
        final_text == generated_text
        or bool(final_claims)
        or not final_text
    )

    col1, col2, col3 = st.columns(3)

    # -----------------------------------------------------
    # APPROVE
    # -----------------------------------------------------

    with col1:

        if st.button(
            "✅ Approve",
            use_container_width=True,
            disabled=approve_disabled,
        ):

            review = Review(
                candidate_text=generated_text,
                decision=ReviewDecision.APPROVE,
                founder=result.founder,
                post_text=result.post.text,
                comment_mode=result.comment_mode,
                quality_warnings=final_quality,
                edited_text=None,
                rejection_reason=None,
            )

            save_review(
                review
            )

            handoff = save_handoff(
                result.founder,
                result.post.text,
                final_text,
                result.comment_mode.value,
            )

            st.success(
                f"APPROVED → MOCK HANDOFF COMPLETE "
                f"({handoff['id']})"
            )

    # -----------------------------------------------------
    # SAVE EDITED
    # -----------------------------------------------------

    with col2:

        if st.button(
            "💾 Save Edited",
            use_container_width=True,
            disabled=edited_disabled,
        ):

            review = Review(
                candidate_text=generated_text,
                decision=ReviewDecision.EDIT,
                edited_text=final_text,
                founder=result.founder,
                post_text=result.post.text,
                comment_mode=result.comment_mode,
                quality_warnings=final_quality,
                rejection_reason=None,
            )

            save_review(
                review
            )

            st.success(
                "Edited version saved as contextual feedback."
            )

    # -----------------------------------------------------
    # REJECT
    # -----------------------------------------------------

    with col3:

        rejection_reason = st.text_input(
            "Rejection reason",
            key="rejection_reason",
            placeholder="Optional reason...",
        )

        if st.button(
            "❌ Reject",
            use_container_width=True,
        ):

            review = Review(
                candidate_text=generated_text,
                decision=ReviewDecision.REJECT,
                edited_text=None,
                rejection_reason=(
                    rejection_reason.strip()
                    or "Human rejected draft."
                ),
                founder=result.founder,
                post_text=result.post.text,
                comment_mode=result.comment_mode,
                quality_warnings=final_quality,
            )

            save_review(
                review
            )

            st.success(
                "Rejection saved as negative feedback."
            )

    # =====================================================
    # 8. LEARNED MEMORY
    # =====================================================

    st.subheader(
        "8. Learned Memory"
    )

    learned = list_reviews(
        founder=result.founder
    )

    st.caption(
        f"Stored decisions for "
        f"{result.founder}: {len(learned)}"
    )

    if not learned:

        st.info(
            "No human feedback has been saved yet."
        )

    else:

        for item in learned[-8:][::-1]:

            decision_label = (
                item.get(
                    "decision",
                    "",
                )
                .upper()
            )

            mode_label = (
                item.get(
                    "comment_mode"
                )
                or "unknown mode"
            )

            item_id = item.get(
                "id",
                "unknown",
            )

            with st.expander(
                f"{decision_label} · "
                f"{mode_label}"
            ):

                st.caption(
                    f"Feedback ID: {item_id}"
                )

                st.write(
                    "**Post:**"
                )

                st.write(
                    item.get(
                        "post_text",
                        "",
                    )[:500]
                )

                st.write(
                    "**AI draft:**"
                )

                st.write(
                    item.get(
                        "ai_draft",
                        item.get(
                            "candidate_text",
                            "",
                        ),
                    )
                )

                st.write(
                    "**Final:**"
                )

                st.write(
                    item.get(
                        "final_text",
                        item.get(
                            "edited_text",
                            "",
                        ),
                    )
                )

                reason = item.get(
                    "reason"
                ) or item.get(
                    "rejection_reason"
                )

                if reason:

                    st.write(
                        "**Reason:**",
                        reason,
                    )

                if st.button(
                    "Delete learned entry",
                    key=f"delete_{item_id}",
                ):

                    delete_review(
                        item_id
                    )

                    st.success(
                        "Learned entry deleted."
                    )

                    st.rerun()

    # =====================================================
    # MOCK HANDOFF / PRIVACY NOTE
    # =====================================================

    st.divider()

    st.caption(
        "LinkedIn publishing is intentionally not connected. "
        "Approved comments are only handed off to the local "
        "mock outbox."
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()