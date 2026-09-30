import logging
import re

logger = logging.getLogger(__name__)

MAX_USER_INPUT = 2000

_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+\w+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an|if)\s+\w+", re.IGNORECASE),
    re.compile(r"new\s+(role|persona|instruction)\s*:", re.IGNORECASE),
]

_TAG_PATTERN = re.compile(
    r"<\s*(system|prompt|inst|s|\/s)\s*>.*?<\s*/\s*(system|prompt|inst|s)\s*>|"
    r"<\s*(system|prompt|inst)\s*>|\[INST\]|\[\/INST\]|\[\[|\]\]",
    re.IGNORECASE | re.DOTALL,
)

_DELIMITER_PATTERN = re.compile(r"#{3,}|-{3,}|={3,}|```+\s*system", re.IGNORECASE)


def sanitize_user_input(text: str, max_len: int = MAX_USER_INPUT) -> str:
    if len(text) > max_len:
        logger.warning("prompt_guard.truncated original_len=%d", len(text))
        text = text[:max_len]

    cleaned = _TAG_PATTERN.sub("", text)
    cleaned = _DELIMITER_PATTERN.sub("", cleaned)

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            logger.warning(
                "prompt_guard.injection_detected pattern=%s", pattern.pattern[:40]
            )
            cleaned = pattern.sub("[filtered]", cleaned)

    return cleaned.strip()
