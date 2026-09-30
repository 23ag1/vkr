import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.llm as llm_service
from app.core.exceptions import NotFoundException
from app.models.chat import ChatMessage, ChatSession
from app.services.prompt_guard import sanitize_user_input

logger = logging.getLogger(__name__)

# Per-message budget for re-fed history. Larger than MAX_USER_INPUT so a benign
# long attacker turn keeps context fidelity, while still capping each turn.
# Mirrors mentor._HISTORY_MSG_BUDGET (ADR vkr-33c).
_HISTORY_MSG_BUDGET = 4000

# Only these roles may be re-fed from stored history; a DB-sourced "system"
# role would otherwise become a privileged prompt frame (security: vkr-i3k).
_ALLOWED_HISTORY_ROLES = frozenset({"user", "assistant"})

_SCENARIOS: list[dict] = [
    {
        "id": "it_support",
        "title": "Звонок из IT-поддержки",
        "description": "Злоумышленник представляется сотрудником IT и запрашивает учётные данные.",
        "attacker_persona": (
            "You are a social engineer pretending to be from IT support. "
            "You call the employee and try to get their password or other sensitive info. "
            "Start the conversation naturally, build trust, then escalate your request."
        ),
        "opener": (
            "Добрый день! Это служба технической поддержки. "
            "У нас зафиксирована подозрительная активность с вашего аккаунта. "
            "Мне нужно верифицировать вашу личность, чтобы заблокировать угрозу. "
            "Не могли бы вы сообщить свой логин?"
        ),
    },
    {
        "id": "ceo_fraud",
        "title": "Письмо от CEO",
        "description": "Злоумышленник имитирует директора и просит срочно перевести деньги или раскрыть данные.",
        "attacker_persona": (
            "You are a social engineer impersonating the CEO via email/chat. "
            "You ask the employee to urgently transfer money or reveal financial data. "
            "Use urgency, authority, and pressure tactics."
        ),
        "opener": (
            "Срочно! Это Александр Петров, генеральный директор. "
            "Мне нужна ваша помощь с конфиденциальным вопросом. "
            "Я сейчас на переговорах и не могу говорить по телефону. "
            "Нужно срочно выполнить перевод на 500 000 руб. — это критически важно."
        ),
    },
    {
        "id": "vendor_link",
        "title": "Письмо от поставщика",
        "description": "Злоумышленник просит перейти по ссылке для 'обновления договора'.",
        "attacker_persona": (
            "You are a social engineer posing as a vendor/supplier. "
            "You send a message with a link to a 'document update' that is actually malware. "
            "Be professional, use urgency, and try to get the employee to click the link."
        ),
        "opener": (
            "Добрый день! Это ООО 'Техпоставка', ваш поставщик оборудования. "
            "Нам нужно срочно обновить условия договора. "
            "Пожалуйста, перейдите по ссылке для подписания нового соглашения: "
            "http://techpostavka-docs.ru/agreement-2024.pdf"
        ),
    },
]

_SCENARIO_BY_ID = {s["id"]: s for s in _SCENARIOS}

_EVAL_SYSTEM = (
    "You are a cybersecurity trainer evaluating an employee's response to a social engineering attack. "
    "You have two jobs:\n"
    "1. Continue the social engineering roleplay as the attacker (stay in character).\n"
    "2. Privately evaluate the employee's response.\n\n"
    "Respond ONLY with valid JSON in this exact format:\n"
    '{"reply": "<attacker\'s next message in Russian>", "score": <0-100>, '
    '"feedback": "<1 sentence evaluation in Russian>"}\n\n'
    "Score guide: 100 = perfect refusal with reporting intent; "
    "50 = partial resistance; 0 = gave away sensitive info or complied fully."
)


def get_scenarios() -> list[dict]:
    return [
        {"id": s["id"], "title": s["title"], "description": s["description"]}
        for s in _SCENARIOS
    ]


async def start_simulation(
    db: AsyncSession, user_id: uuid.UUID, scenario_id: str
) -> dict:
    scenario = _SCENARIO_BY_ID.get(scenario_id)
    if scenario is None:
        raise NotFoundException

    session = ChatSession(user_id=user_id, title=f"[sim] {scenario['title']}")
    db.add(session)
    await db.commit()
    await db.refresh(session)

    opener = scenario["opener"]
    first_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=opener,
        sources={"scenario_id": scenario_id, "turn": 0},
    )
    db.add(first_msg)
    await db.commit()

    logger.info(
        "social_eng.start user_id=%s scenario_id=%s session_id=%s",
        user_id,
        scenario_id,
        session.id,
    )
    return {
        "session_id": str(session.id),
        "content": opener,
        "scenario": scenario["title"],
    }


async def simulation_turn(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID, user_message: str
) -> dict:
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if session is None or session.user_id != user_id:
        raise NotFoundException

    user_message = sanitize_user_input(user_message)

    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    history = history_result.scalars().all()

    scenario_id = None
    for msg in history:
        if msg.sources and isinstance(msg.sources, dict):
            scenario_id = msg.sources.get("scenario_id")
            if scenario_id:
                break

    scenario = _SCENARIO_BY_ID.get(scenario_id or "it_support")

    user_msg = ChatMessage(session_id=session_id, role="user", content=user_message)
    db.add(user_msg)
    await db.commit()

    messages = [
        {"role": "system", "content": _EVAL_SYSTEM},
        {
            "role": "system",
            "content": f"Attacker persona: {scenario['attacker_persona']}",
        },
    ]
    # Re-fed chat history is untrusted at prompt-construction: role=assistant is
    # GPT-4o output stored verbatim (a poisoned attacker reply re-executes on
    # later turns) and role=user may predate sanitize-at-write. Sanitize each
    # before it reaches the LLM (indirect-injection backstop, ADR vkr-33c).
    # The DB role column is also untrusted: an arbitrary/stored "system" role
    # would promote a history row to a privileged frame, so allowlist roles.
    # Window is 8 (4 attacker/defender exchanges); mentor.py uses 10 for
    # open-ended Q&A — _HISTORY_MSG_BUDGET is the shared part (ADR vkr-33c).
    for msg in history[-8:]:
        if msg.role not in _ALLOWED_HISTORY_ROLES:
            continue
        clean = sanitize_user_input(msg.content, max_len=_HISTORY_MSG_BUDGET)
        messages.append({"role": msg.role, "content": clean})
    messages.append({"role": "user", "content": user_message})

    raw = await llm_service.chat_completion(messages, temperature=0.7)
    logger.info("social_eng.turn session_id=%s raw_len=%d", session_id, len(raw))

    try:
        parsed = json.loads(raw)
        reply = parsed.get("reply", "...")
        score = int(parsed.get("score", 50))
        score = max(0, min(100, score))
        feedback = parsed.get("feedback", "")
    except (json.JSONDecodeError, ValueError):
        reply = raw
        score = 50
        feedback = ""

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=reply,
        sources={"scenario_id": scenario_id, "score": score, "feedback": feedback},
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return {"content": reply, "score": score, "feedback": feedback}
