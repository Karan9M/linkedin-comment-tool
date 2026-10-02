import json
from collections import Counter
from pathlib import Path

from src.models import Post
from src.paths import EVAL_FILE, HELD_OUT_EVAL_FILE, VOICE_FILE
from src.pipeline import run_pipeline
from src.voice import load_voice_examples


def run_eval_suite(cases: list[dict], suite_name: str, voice: list) -> dict:
    correct = 0
    expected_counts = Counter()
    actual_counts = Counter()
    mode_counts = Counter()
    quality_flagged = 0
    claims_blocked = 0
    mismatches = []

    for case in cases:
        expected = case["expected_decision"]
        expected_counts[expected] += 1
        result = run_pipeline(
            post=Post(case["id"], case["text"]),
            person=case["founder"],
            voice_examples=voice,
            provider="stub",
        )
        actual = result.engagement_decision.value
        actual_counts[actual] += 1
        if result.comment_mode:
            mode_counts[result.comment_mode.value] += 1
        if actual == expected:
            correct += 1
        else:
            mismatches.append((case["id"], expected, actual, case.get("notes", "")))
        if result.quality_warnings:
            quality_flagged += 1
        if result.blocked:
            claims_blocked += 1

    total = len(cases)
    skip_expected = expected_counts["skip"]
    skip_correct = sum(
        1 for case in cases
        if case["expected_decision"] == "skip" and run_pipeline(
            Post(case["id"], case["text"]), case["founder"], voice, provider="stub"
        ).engagement_decision.value == "skip"
    )

    print(f"\n========================================================")
    print(f"Byro Evaluation: {suite_name} (deterministic stub)")
    print(f"========================================================")
    print(f"Cases evaluated: {total}")
    print(f"Decision accuracy: {correct}/{total} = {correct/total:.0%}")
    print(f"Skip accuracy: {skip_correct}/{skip_expected} = {skip_correct/skip_expected:.0%}" if skip_expected else "Skip accuracy: n/a")
    print(f"Drafts flagged by quality checks: {quality_flagged}")
    print(f"Drafts blocked by claims guard: {claims_blocked}")

    print("\nExpected decisions:")
    for key in ("engage", "ask", "skip"):
        print(f"  {key:>6}: {expected_counts[key]}")
    print("\nActual decisions:")
    for key in ("engage", "ask", "skip"):
        print(f"  {key:>6}: {actual_counts[key]}")
    print("\nMode distribution:")
    for key, count in sorted(mode_counts.items()):
        print(f"  {key:>20}: {count}")

    if mismatches:
        print("\nMismatches:")
        for item in mismatches:
            print(f"  [{item[0]}] expected={item[1]} actual={item[2]} ({item[3]})")

    return {
        "suite": suite_name,
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "mismatches": mismatches,
    }


def main() -> None:
    voice = load_voice_examples(VOICE_FILE)

    # 1. Primary regression suite
    if EVAL_FILE.exists():
        cases = json.loads(EVAL_FILE.read_text(encoding="utf-8"))
        run_eval_suite(cases, "Primary Regression Suite", voice)

    # 2. Held-out independent evaluation suite
    if HELD_OUT_EVAL_FILE.exists():
        held_out_cases = json.loads(HELD_OUT_EVAL_FILE.read_text(encoding="utf-8"))
        run_eval_suite(held_out_cases, "Held-Out Independent Suite", voice)


if __name__ == "__main__":
    main()
