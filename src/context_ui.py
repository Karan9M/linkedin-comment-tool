from __future__ import annotations

import streamlit as st

from src.founder_context import (
    get_founder_context,
    load_comment_bank,
    save_founder_context,
)


def render_founder_context_panel(
    founder: str,
) -> None:

    context = get_founder_context(
        founder
    )

    with st.expander(
        "🧠 Founder Context",
        expanded=False,
    ):

        st.caption(
            "Observed patterns are evidence. "
            "Candidate vocabulary can be edited by the founder."
        )

        observed_vocab = ", ".join(
            context.get(
                "observed_vocabulary",
                [],
            )
        )

        candidate_vocab = ", ".join(
            context.get(
                "candidate_vocabulary",
                [],
            )
        )

        preferred_moves = ", ".join(
            context.get(
                "preferred_moves",
                [],
            )
        )

        avoid_patterns = ", ".join(
            context.get(
                "avoid_patterns",
                [],
            )
        )

        st.text_area(
            "Observed vocabulary",
            value=observed_vocab,
            disabled=True,
        )

        editable_vocab = st.text_input(
            "Candidate / custom vocabulary",
            value=candidate_vocab,
            help=(
                "Add words or phrases the founder "
                "actually uses or wants to use."
            ),
        )

        editable_moves = st.text_input(
            "Preferred comment moves",
            value=preferred_moves,
        )

        editable_avoid = st.text_input(
            "Avoid phrases",
            value=avoid_patterns,
        )

        if st.button(
            "Save Founder Context",
            key=f"save_context_{founder}",
        ):

            save_founder_context(
                founder=founder,
                updates={
                    "candidate_vocabulary": [
                        item.strip()
                        for item in editable_vocab.split(",")
                        if item.strip()
                    ],
                    "preferred_moves": [
                        item.strip()
                        for item in editable_moves.split(",")
                        if item.strip()
                    ],
                    "avoid_patterns": [
                        item.strip()
                        for item in editable_avoid.split(",")
                        if item.strip()
                    ],
                },
            )

            st.success(
                "Founder context saved."
            )


def render_demo_post_selector(
    founder: str,
) -> str:

    posts = load_comment_bank(
        founder=founder
    )

    labels = [
        f"{item['topic']} · synthetic fixture"
        for item in posts
    ]

    options = [
        "Paste my own post"
    ] + labels

    selected = st.selectbox(
        "Demo post",
        options,
        key=f"demo_post_{founder}",
    )

    if selected == "Paste my own post":
        return ""

    index = (
        options.index(selected) - 1
    )

    item = posts[index]

    st.text_area(
        "Demo post",
        value=item["post"],
        height=180,
        disabled=True,
        key=f"demo_text_{founder}",
    )

    st.caption(
        "Synthetic calibration fixture"
    )

    return item["post"]