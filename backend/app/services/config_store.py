import json
import logging
from pathlib import Path

from app.services.prompts import EXPLANATION_SYSTEM, QUESTION_SYSTEM

logger = logging.getLogger(__name__)

_CONFIG_FILE = Path(__file__).parent.parent / "config_overrides.json"

_DEFAULTS: dict = {
    "question_prompt": QUESTION_SYSTEM,
    "explanation_prompt": EXPLANATION_SYSTEM,
    "model": "",
}


def _load() -> dict:
    if _CONFIG_FILE.exists():
        try:
            stored = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            return {**_DEFAULTS, **stored}
        except Exception:
            pass
    return dict(_DEFAULTS)


def get_all() -> dict:
    return _load()


def get_question_prompt() -> str:
    return _load()["question_prompt"]


def get_explanation_prompt() -> str:
    return _load()["explanation_prompt"]


def get_model_override() -> str:
    return _load()["model"]


def update(updates: dict) -> dict:
    data = _load()
    changed = {k: v for k, v in updates.items() if k in _DEFAULTS and v is not None}
    data.update(changed)
    _CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("config_store.update fields=%s", list(changed.keys()))
    return data
