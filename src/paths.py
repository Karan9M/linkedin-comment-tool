from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FIXTURE_DIR = BASE_DIR / "fixtures"
FEEDBACK_FILE = DATA_DIR / "feedback.json"
OUTBOX_FILE = DATA_DIR / "outbox.json"
VOICE_FILE = FIXTURE_DIR / "voice_examples.json"
VOICE_PROFILE_FILE = FIXTURE_DIR / "voice_profiles.json"
FACTS_FILE = FIXTURE_DIR / "facts.json"
DEMO_POSTS_FILE = FIXTURE_DIR / "demo_posts.json"
EVAL_FILE = FIXTURE_DIR / "eval_posts.json"
