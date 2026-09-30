import json
import logging
import random
import time

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
import app.services.config_store as config_store
from app.services.prompt_guard import sanitize_user_input

# module_content is admin-authored long-form text; keep the existing 4000-char
# prompt budget instead of the default short-message cap (which would halve it).
_MODULE_CONTENT_BUDGET = 4000

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

# Retry only on transient OpenAI transport errors. Deterministic failures
# (empty content, schema/JSON errors) are NOT retried — retrying them just
# burns quota and latency for a guaranteed-identical failure.
_TRANSIENT_ERRORS = (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

_llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(_TRANSIENT_ERRORS),
)

QUESTION_CATEGORIES = [
    "scenario",
    "definition",
    "best_practice",
    "threat_recognition",
    "consequence",
    "policy",
    "technical",
    "decision",
]


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=get_settings().OPENAI_API_KEY)
    return _client


class QuestionSchema(BaseModel):
    text: str
    options: list[str]
    correct_index: int
    explanation: str

    def model_post_init(self, __context):
        if len(self.options) != 4:
            raise ValueError("options must have exactly 4 items")
        if not (0 <= self.correct_index <= 3):
            raise ValueError("correct_index must be 0-3")


def _effective_model() -> str:
    override = config_store.get_model_override()
    return override if override else get_settings().OPENAI_MODEL


@_llm_retry
async def chat_completion(messages: list[dict], temperature: float = 0.5) -> str:
    t0 = time.monotonic()
    response = await get_client().chat.completions.create(
        model=_effective_model(),
        messages=messages,
        temperature=temperature,
    )
    latency_ms = int((time.monotonic() - t0) * 1000)
    tokens = response.usage.total_tokens if response.usage else 0
    logger.info("llm.chat_completion latency_ms=%d tokens=%d", latency_ms, tokens)
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("LLM returned empty content")
    return content.strip()


@_llm_retry
async def generate_question(
    module_title: str,
    module_content: str,
    recent_questions: list[str] | None = None,
    category: str | None = None,
) -> QuestionSchema:
    cat = category or random.choice(QUESTION_CATEGORIES)

    # generate_question builds its own prompt, so it sanitizes its own untrusted
    # parts (mirrors mentor/incident/social_eng). All three inputs are
    # admin/DB-sourced text that lands verbatim in the LLM prompt: a poisoned
    # module or a prior poisoned question could otherwise backdoor generation.
    safe_title = sanitize_user_input(module_title)
    safe_content = sanitize_user_input(module_content, max_len=_MODULE_CONTENT_BUDGET)

    user_parts = [
        f"CATEGORY: {cat}",
        f"Module: {safe_title}",
        "",
        safe_content,
    ]
    if recent_questions:
        safe_recent = [sanitize_user_input(q) for q in recent_questions[-8:]]
        user_parts.append(
            "\nrecent_topics (DO NOT repeat these):\n"
            + "\n".join(f"- {q}" for q in safe_recent)
        )

    t0 = time.monotonic()
    response = await get_client().chat.completions.create(
        model=_effective_model(),
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": config_store.get_question_prompt()},
            {"role": "user", "content": "\n".join(user_parts)},
        ],
        temperature=0.9,
    )
    latency_ms = int((time.monotonic() - t0) * 1000)
    tokens = response.usage.total_tokens if response.usage else 0
    logger.info(
        "llm.generate_question category=%s latency_ms=%d tokens=%d",
        cat,
        latency_ms,
        tokens,
    )

    raw = response.choices[0].message.content
    if raw is None:
        raise ValueError("LLM returned empty content")
    return QuestionSchema.model_validate(json.loads(raw))


# No @retry here: this fully delegates to chat_completion, which already
# carries the transient-error retry policy. A second decorator would chain
# retries (up to 3x3 API calls).
async def generate_explanation(
    question_text: str,
    correct_answer: str,
    user_answer: str,
    context_chunks: list[str],
) -> str:
    # All four inputs land verbatim in the LLM prompt and are untrusted:
    # question_text/correct_answer/user_answer are LLM-generated or DB-stored,
    # context_chunks is admin-uploaded RAG document text. Sanitize at the
    # prompt-construction boundary (mirrors generate_question, vkr-f2l/vkr-s3v).
    safe_question = sanitize_user_input(question_text)
    safe_correct = sanitize_user_input(correct_answer)
    safe_user = sanitize_user_input(user_answer)
    context = "\n".join(f"- {sanitize_user_input(c)}" for c in context_chunks[:5])
    user_msg = (
        f"Question: {safe_question}\n"
        f"Correct answer: {safe_correct}\n"
        f"Student answered: {safe_user}\n"
        + (f"\nKnowledge base context:\n{context}" if context else "")
    )
    return await chat_completion(
        messages=[
            {"role": "system", "content": config_store.get_explanation_prompt()},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.5,
    )
