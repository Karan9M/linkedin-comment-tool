from dataclasses import dataclass, field
import json
from pathlib import Path

from src.claims import load_facts, validate_claims
from src.comment_mode import select_comment_mode
from src.context import build_founder_evidence_pack
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

    positive_factors: list[str] = field(default_factory=list)
    negative_factors: list[str] = field(default_factory=list)
    founder_fit_score: float = 0.0




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
        post,
        founder=person,
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
            positive_factors=engagement.positive_factors,
            negative_factors=engagement.negative_factors,
            founder_fit_score=engagement.fit_score,

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
    # 3. Build one evidence pack for both UI and generation
    # =====================================================

    evidence_pack = build_founder_evidence_pack(
        founder=person,
        post_text=post.text,
        mode=mode,
        voice_examples=voice_examples,
    )
    relevant_examples = (
        evidence_pack["matched_observed_examples"]
        + evidence_pack["style_only_observed_comments"]
    )

    # =====================================================
    # 4. Generate comment
    # =====================================================

    generated = generate_comment(
        post=post,
        mode=mode,
        voice_examples=voice_examples,
        founder=person,
        provider=provider,
        evidence_pack=evidence_pack,
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
    # 8. Surface the same calibration used by generation
    # =====================================================

    reference_examples = evidence_pack["candidate_calibration"]

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
        positive_factors=engagement.positive_factors,
        negative_factors=engagement.negative_factors,
        founder_fit_score=engagement.fit_score,

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
