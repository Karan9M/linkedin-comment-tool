"""Backward-compatible imports for the canonical founder-evidence module.

New code should import from :mod:`src.context`. This module remains only to
avoid breaking early callers while the prototype evolves.
"""

from src.context import (
    get_founder_context,
    load_comment_bank,
    retrieve_reference_pairs,
    save_founder_context,
)

__all__ = [
    "get_founder_context",
    "load_comment_bank",
    "retrieve_reference_pairs",
    "save_founder_context",
]
