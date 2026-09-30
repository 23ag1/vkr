import logging

from sqlalchemy.ext.asyncio import AsyncSession

import app.services.analytics as analytics_service
import app.services.llm as llm_service
from app.services.prompt_guard import sanitize_user_input

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = (
    "You are an expert information security program advisor for an organization. "
    "You have access to the following current metrics:\n\n"
    "{metrics}\n\n"
    "Answer the administrator's question with concrete, actionable recommendations. "
    "Be concise and reference the metrics where relevant. Do not include PII."
)


async def admin_ask(db: AsyncSession, question: str) -> str:
    question = sanitize_user_input(question)

    overview = await analytics_service.get_overview(db)
    metrics_text = (
        f"- Total employees: {overview['total_users']}\n"
        f"- Module completion rate: {overview['completion_rate'] * 100:.1f}%\n"
        f"- Average test score: {overview['avg_score'] * 100:.1f}%\n"
        f"- Phishing open rate: {overview.get('phishing_open_rate', 0) * 100:.1f}%\n"
        f"- Phishing click rate: {overview['phishing_click_rate'] * 100:.1f}%\n"
        f"- Phishing submit rate: {overview.get('phishing_submit_rate', 0) * 100:.1f}%\n"
        f"- Phishing report rate: {overview.get('phishing_report_rate', 0) * 100:.1f}%"
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT_TEMPLATE.format(metrics=metrics_text)},
        {"role": "user", "content": question},
    ]

    reply = await llm_service.chat_completion(messages, temperature=0.3)
    logger.info("admin_llm.ask question_len=%d reply_len=%d", len(question), len(reply))
    return reply
