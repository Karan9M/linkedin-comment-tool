import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.paths import OUTBOX_FILE


def save_handoff(founder: str, post_text: str, comment: str, mode: str, outbox_file: Path = OUTBOX_FILE) -> dict:
    outbox_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = json.loads(outbox_file.read_text(encoding="utf-8")) if outbox_file.exists() else []
    except json.JSONDecodeError:
        existing = []
    raw = "|".join([founder, post_text, comment])
    handoff_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    if any(item.get("id") == handoff_id for item in existing):
        return next(item for item in existing if item.get("id") == handoff_id)
    record = {
        "id": handoff_id,
        "status": "approved_handoff_mock",
        "founder": founder,
        "post_text": post_text,
        "comment": comment,
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    existing.append(record)
    outbox_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def load_handoffs(outbox_file: Path = OUTBOX_FILE) -> list[dict]:
    if not outbox_file.exists():
        return []
    try:
        data = json.loads(outbox_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []
