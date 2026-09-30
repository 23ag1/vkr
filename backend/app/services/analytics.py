import logging
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import UserModuleProgress
from app.models.phishing import PhishingRecipient
from app.models.test import UserAnswer
from app.models.user import User

logger = logging.getLogger(__name__)


async def get_overview(db: AsyncSession) -> dict:
    row = (await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM users)                                                AS total_users,
            (SELECT COUNT(*) FROM user_module_progress WHERE status = 'completed')      AS completed,
            (SELECT COUNT(*) FROM user_module_progress)                                 AS total_progress,
            (SELECT AVG(is_correct::int) FROM user_answers)                             AS avg_score,
            (SELECT COUNT(*) FROM phishing_recipients)                                  AS total_recipients,
            (SELECT COUNT(*) FROM phishing_recipients WHERE opened_at IS NOT NULL)      AS opened,
            (SELECT COUNT(*) FROM phishing_recipients WHERE clicked_at IS NOT NULL)     AS clicked,
            (SELECT COUNT(*) FROM phishing_recipients WHERE submitted_at IS NOT NULL)   AS submitted,
            (SELECT COUNT(*) FROM phishing_recipients WHERE reported_at IS NOT NULL)    AS reported
    """))).one()

    completion_rate = round(row.completed / row.total_progress, 4) if row.total_progress else 0.0
    avg_score = round(float(row.avg_score or 0), 4)
    n = row.total_recipients or 1
    phishing_open_rate = round(row.opened / n, 4)
    phishing_click_rate = round(row.clicked / n, 4)
    phishing_submit_rate = round(row.submitted / n, 4)
    phishing_report_rate = round(row.reported / n, 4)

    result = {
        "total_users": row.total_users,
        "completion_rate": completion_rate,
        "avg_score": avg_score,
        "phishing_open_rate": phishing_open_rate,
        "phishing_click_rate": phishing_click_rate,
        "phishing_submit_rate": phishing_submit_rate,
        "phishing_report_rate": phishing_report_rate,
    }
    logger.info(
        "analytics.overview users=%d completion=%.2f avg_score=%.2f phishing_click=%.2f",
        row.total_users, completion_rate, avg_score, phishing_click_rate,
    )
    return result


async def get_departments_analytics(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(text("""
        SELECT
            d.id                                                                          AS dept_id,
            d.name                                                                        AS dept_name,
            COUNT(DISTINCT u.id)                                                          AS total_users,
            COUNT(DISTINCT ump.id) FILTER (WHERE ump.status = 'completed')                AS completed,
            COUNT(DISTINCT ump.id)                                                        AS total_progress,
            AVG(ua.is_correct::int)                                                       AS avg_score,
            COUNT(DISTINCT pr.id) FILTER (WHERE pr.clicked_at IS NOT NULL)                AS clicked,
            COUNT(DISTINCT pr.id)                                                         AS total_recipients
        FROM departments d
        LEFT JOIN users u ON u.department_id = d.id
        LEFT JOIN user_module_progress ump ON ump.user_id = u.id
        LEFT JOIN user_answers ua ON ua.user_id = u.id
        LEFT JOIN phishing_recipients pr ON pr.user_id = u.id
        GROUP BY d.id, d.name
        ORDER BY d.name
    """))).mappings().all()

    result = []
    for row in rows:
        n_prog = row["total_progress"] or 0
        n_recip = row["total_recipients"] or 0
        result.append({
            "id": str(row["dept_id"]),
            "name": row["dept_name"],
            "total_users": row["total_users"],
            "completion_rate": round(row["completed"] / n_prog, 4) if n_prog else 0.0,
            "avg_score": round(float(row["avg_score"]), 4) if row["avg_score"] else 0.0,
            "phishing_click_rate": round(row["clicked"] / n_recip, 4) if n_recip else 0.0,
        })
    logger.info("analytics.departments count=%d", len(result))
    return result


async def get_briefing_stats(db: AsyncSession) -> list[dict]:
    rows = (await db.execute(text("""
        SELECT
            m.briefing_type,
            COUNT(ump.id) FILTER (WHERE ump.status = 'completed') AS completed,
            COUNT(ump.id) AS total
        FROM modules m
        LEFT JOIN user_module_progress ump ON ump.module_id = m.id
        WHERE m.briefing_type != 'none'
        GROUP BY m.briefing_type
        ORDER BY m.briefing_type
    """))).mappings().all()

    result = []
    for row in rows:
        total = row["total"] or 0
        result.append({
            "briefing_type": row["briefing_type"],
            "completed": row["completed"],
            "total": total,
            "completion_rate": round(row["completed"] / total, 4) if total else 0.0,
        })
    return result


async def get_user_profile(db: AsyncSession, user_id: uuid.UUID) -> dict:
    modules_completed = (await db.execute(
        select(func.count()).select_from(UserModuleProgress)
        .where(UserModuleProgress.user_id == user_id,
               UserModuleProgress.status == "completed")
    )).scalar_one()

    correct = (await db.execute(
        select(func.count()).select_from(UserAnswer)
        .where(UserAnswer.user_id == user_id, UserAnswer.is_correct.is_(True))
    )).scalar_one()
    total_answers = (await db.execute(
        select(func.count()).select_from(UserAnswer).where(UserAnswer.user_id == user_id)
    )).scalar_one()
    avg_score = round(correct / total_answers, 4) if total_answers else 0.0

    phishing_clicks = (await db.execute(
        select(func.count()).select_from(PhishingRecipient)
        .where(PhishingRecipient.user_id == user_id,
               PhishingRecipient.clicked_at.isnot(None))
    )).scalar_one()

    logger.info(
        "analytics.user_profile user_id=%s modules_completed=%d answers=%d avg_score=%.2f",
        user_id, modules_completed, total_answers, avg_score,
    )
    return {
        "user_id": str(user_id),
        "modules_completed": modules_completed,
        "avg_score": avg_score,
        "phishing_clicks": phishing_clicks,
    }
