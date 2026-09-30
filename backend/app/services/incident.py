import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import app.services.audit as audit_service
import app.services.llm as llm_service
from app.services.prompt_guard import sanitize_user_input

logger = logging.getLogger(__name__)

_INCIDENT_SYSTEM = (
    "You are an information security incident response advisor. "
    "An employee has reported a potential security incident. "
    "Provide clear, step-by-step immediate actions they should take RIGHT NOW. "
    "Be concise (5-7 steps max). Use plain language. "
    "Do not ask for credentials or PII. "
    "Always end with: 'Сообщите о произошедшем своему руководителю и в службу ИБ.'"
)


async def report_incident(
    db: AsyncSession, user_id: uuid.UUID, description: str
) -> dict:
    description = sanitize_user_input(description)
    incident_id = str(uuid.uuid4())

    messages = [
        {"role": "system", "content": _INCIDENT_SYSTEM},
        {"role": "user", "content": f"Описание инцидента: {description}"},
    ]

    guidance = await llm_service.chat_completion(messages, temperature=0.2)
    logger.info("incident.report user_id=%s incident_id=%s desc_len=%d", user_id, incident_id, len(description))

    await audit_service.write(
        db, user_id=user_id, action="incident_reported",
        details={"incident_id": incident_id, "description_preview": description[:100]},
    )

    return {"incident_id": incident_id, "guidance": guidance}
