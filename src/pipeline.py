from dataclasses import dataclass
import json
from pathlib import Path

from src.claims import load_facts, validate_claims
from src.comment_mode import select_comment_mode
from src.engagement import decide_engagement
from src.generator import GeneratedComment, generate_comment
from src.models import (
    CommentMode,
    EngagementDecision,
    Post,
    VoiceExample,
)
from src.paths import FACTS_FILE, VOICE_PROFILE_FILE
from src.quality import check_comment_quality


@dataclass
class PipelineResult:
    post: Post
    founder: str

    engagement_decision: EngagementDecision
    engagement_reason: str
    engagement_confidence: float

    comment_mode: CommentMode | None

    voice_examples: list[VoiceExample]
    reference_examples: list[dict]

    generated_comment: GeneratedComment | None

    quality_warnings: list[str]
    claim_warnings: list[str]

    blocked: bool


def load_voice_profile(
    founder: str,
    path: str | Path = VOICE_PROFILE_FILE,
) -> dict:
    """
    Load founder-specific voice profile.

    Missing or invalid profile data should not crash the pipeline.
    """

    try:
        data = json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )

        return data.get(
            founder,
            {},
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def run_pipeline(
    post: Post,
    person: str,
    voice_examples: list[VoiceExample],
    provider: str | None = None,
    force_draft: bool = False,
) -> PipelineResult:

    # =====================================================
    # 1. Engagement decision
    # =====================================================

    engagement = decide_engagement(
        post
    )

    # ASK / SKIP normally stop drafting.
    # The human can override this using Draft Anyway.
    should_stop = (
        engagement.decision
        in {
            EngagementDecision.SKIP,
            EngagementDecision.ASK,
        }
        and not force_draft
    )

    if should_stop:

        return PipelineResult(
            post=post,
            founder=person,

            engagement_decision=(
                engagement.decision
            ),
            engagement_reason=(
                engagement.reason
            ),
            engagement_confidence=(
                engagement.confidence
            ),

            comment_mode=None,
            voice_examples=[],
            reference_examples=[],

            generated_comment=None,

            quality_warnings=[],
            claim_warnings=[],
            blocked=False,
        )

    # =====================================================
    # 2. Select comment mode
    # =====================================================

    mode = select_comment_mode(
        post=post,
        person=person,
        voice_examples=voice_examples,
    )

    # =====================================================
    # 3. Retrieve observed voice examples
    # =====================================================

    from src.voice import retrieve_voice_examples

    try:
        relevant_examples = retrieve_voice_examples(
            post=post,
            person=person,
            examples=voice_examples,
            top_k=5,
            desired_mode=mode,
        )

    except TypeError:
        # Backward compatibility if the retriever
        # does not yet support desired_mode.
        relevant_examples = retrieve_voice_examples(
            post=post,
            person=person,
            examples=voice_examples,
            top_k=5,
        )

    # =====================================================
    # 4. Load founder voice profile
    # =====================================================

    voice_profile = load_voice_profile(
        founder=person
    )

    # =====================================================
    # 5. Generate comment
    # =====================================================

    generated = generate_comment(
        post=post,
        mode=mode,
        voice_examples=relevant_examples,
        founder=person,
        voice_profile=voice_profile,
        provider=provider,
    )

    # =====================================================
    # 6. Quality checks
    # =====================================================

    quality_warnings = check_comment_quality(
        comment=generated.text,
        mode=mode,
        post_text=post.text,
    )

    # Add model/provider warnings.
    quality_warnings.extend(
        generated.warnings
    )

    # Remove duplicates while preserving order.
    quality_warnings = list(
        dict.fromkeys(
            quality_warnings
        )
    )

    # =====================================================
    # 7. Claims / hallucination check
    # =====================================================

    claim_warnings = validate_claims(
        generated.text,
        post.text,
        person,
        load_facts(
            FACTS_FILE
        ),
    )

    # =====================================================
    # 8. Retrieve calibration examples
    # =====================================================

    try:

        from src.founder_context import (
            retrieve_reference_pairs,
        )

        reference_examples = (
            retrieve_reference_pairs(
                post_text=post.text,
                founder=person,
                mode=mode.value,
                top_k=4,
            )
        )

    except Exception:

        reference_examples = []

    # =====================================================
    # 9. Final result
    # =====================================================

    return PipelineResult(
        post=post,
        founder=person,

        engagement_decision=(
            engagement.decision
        ),
        engagement_reason=(
            engagement.reason
        ),
        engagement_confidence=(
            engagement.confidence
        ),

        comment_mode=mode,

        voice_examples=relevant_examples,

        reference_examples=(
            reference_examples
        ),

        generated_comment=generated,

        quality_warnings=(
            quality_warnings
        ),

        claim_warnings=(
            claim_warnings
        ),

        blocked=bool(
            claim_warnings
        ),
    )