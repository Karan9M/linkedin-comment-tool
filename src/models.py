from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EngagementDecision(str, Enum):
    ENGAGE = "engage"
    SKIP = "skip"
    ASK = "ask"


class CommentMode(str, Enum):
    QUICK_REACTION = "quick_reaction"
    HUMOROUS_PERSONAL = "humorous_personal"
    ADD_INSIGHT = "add_insight"
    THOUGHTFUL_QUESTION = "thoughtful_question"


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"


@dataclass
class Post:
    id: str
    text: str
    author: str = ""
    url: Optional[str] = None
    already_commented: bool = False


@dataclass
class VoiceExample:
    id: str
    person: str
    source_type: str  # post | comment
    text: str
    topic: str = ""
    source_url: Optional[str] = None
    comment_mode: Optional[CommentMode] = None
    target_post_excerpt: str = ""
    evidence_role: str = ""


@dataclass
class EngagementResult:
    decision: EngagementDecision
    reason: str
    confidence: float


@dataclass
class Review:
    candidate_text: str
    decision: ReviewDecision
    edited_text: Optional[str] = None
    rejection_reason: Optional[str] = None
    founder: str = ""
    post_text: str = ""
    comment_mode: Optional[CommentMode] = None
    quality_warnings: list[str] = field(default_factory=list)


@dataclass
class GeneratedComment:
    text: str
    mode: CommentMode
    provider: str
    warnings: list[str] = field(default_factory=list)
