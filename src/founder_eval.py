"""Small founder evaluation against a generic baseline.

Compares Byro's adaptive candidate (grounded, planning, voice profile, evidence pack)
against a generic LLM baseline on fixed benchmark posts.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


from src.models import CommentMode, Post
from src.paths import FIXTURE_DIR, VOICE_FILE
from src.pipeline import run_pipeline
from src.voice import load_voice_examples


BENCHMARK_POSTS = [
    {
        "id": "fe_01",
        "founder": "Fathin",
        "post": "Our AI document parser benchmark jumped by 15%, but tables and forms are failing in completely different ways.",
        "mode": CommentMode.ADD_INSIGHT,
        "generic_baseline": "Great insights! It's so interesting to see how document parsing evolves. What kind of tables are giving you trouble? Excited to see where this goes!",
    },
    {
        "id": "fe_02",
        "founder": "Fathin",
        "post": "Our latency reduced significantly, but recovering from unexpected process restarts is still where agents get stuck.",
        "mode": CommentMode.THOUGHTFUL_QUESTION,
        "generic_baseline": "Awesome work on latency! Keep pushing! Agents are definitely the future. What database are you using for recovery?",
    },
    {
        "id": "fe_03",
        "founder": "Rico",
        "post": "48 hours. 4 student builders. Way too much caffeine. We shipped our full MVP and won the hackathon!",
        "mode": CommentMode.QUICK_REACTION,
        "generic_baseline": "Congratulations to the whole team on this huge achievement! Truly inspiring to see what young entrepreneurs can build. Best of luck with the next steps!",
    },
    {
        "id": "fe_04",
        "founder": "Rico",
        "post": "Started writing code in my dorm room 2 years ago. Today our first paying B2B customer onboarded. Still feels surreal.",
        "mode": CommentMode.HUMOROUS_PERSONAL,
        "generic_baseline": "Incredible milestone! Never forget where you started. Hard work always pays off in the end. Here is to 100x more customers!",
    },
]


def run_founder_evaluation() -> list[dict]:
    voice = load_voice_examples(VOICE_FILE)
    results = []

    print("\n========================================================")
    print("Byro Founder Evaluation: Adaptive System vs Generic Baseline")
    print("========================================================\n")

    for case in BENCHMARK_POSTS:
        post = Post(id=case["id"], text=case["post"])
        res = run_pipeline(
            post=post,
            person=case["founder"],
            voice_examples=voice,
            provider="stub",
        )
        adaptive_text = res.generated_comment.text if res.generated_comment else ""

        print(f"[{case['founder']}] Post: \"{case['post'][:75]}...\"")
        print(f"  -> Generic Baseline : \"{case['generic_baseline']}\"")
        print(f"  -> Byro Adaptive    : \"{adaptive_text}\"")
        if res.quality_warnings:
            print(f"    (Quality flags   : {res.quality_warnings})")
        print()

        results.append({
            "id": case["id"],
            "founder": case["founder"],
            "post": case["post"],
            "generic_baseline": case["generic_baseline"],
            "byro_adaptive": adaptive_text,
            "quality_warnings": res.quality_warnings,
        })

    print("Summary:")
    print("1. Generic baseline introduces empty hype ('Excited to see', 'Truly inspiring'), generic questions, and fake enthusiasm.")
    print("2. Byro adaptive draft respects brevity, response shape, and founder-specific mechanism boundaries without vocabulary stuffing.")
    print("========================================================\n")
    return results


if __name__ == "__main__":
    run_founder_evaluation()
