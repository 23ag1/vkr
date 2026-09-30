"""Audit log service — central writer + querier for compliance records.

All significant security-relevant events should go through write().
Failures here MUST NOT break the main flow (audit is best-effort).
"""

import csv
import io
import logging
import uuid
from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


async def write(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    action: str,
    details: dict | None = None,
    ip_address: str | None = None,
    *,
    commit: bool = True,
) -> None:
    """Persist a single audit record.

    commit=True (default): standalone, best-effort. The audit row is committed in
    its own transaction and failures are swallowed so a flaky audit never breaks
    the main flow. Use for events with no preceding DB mutation (login, settings).

    commit=False: shared transaction. The row is flushed but NOT committed — the
    CALLER owns the single commit so the audit row and its triggering action
    persist atomically (one transaction). Errors are NOT swallowed: they propagate
    and roll the whole transaction back, so a destructive/audited action can never
    commit without its audit row (ФСТЭК-21 compliance). Use for every action that
    mutates the DB and must be audited.
    """
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
    )
    if not commit:
        db.add(log)
        await db.flush()
        logger.info("audit.write action=%s user_id=%s shared_tx=1", action, user_id)
        return

    try:
        db.add(log)
        await db.commit()
        logger.info("audit.write action=%s user_id=%s", action, user_id)
    except Exception as exc:
        logger.warning("audit.write_failed action=%s error=%s", action, exc)


async def list_logs(
    db: AsyncSession,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    limit: int = 50,
) -> Iterable[AuditLog]:
    """Paginated audit-log query with optional filters."""
    stmt = select(AuditLog)
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if date_from is not None:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(AuditLog.created_at <= date_to)

    stmt = (
        stmt.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def export_csv(
    db: AsyncSession,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> str:
    """Export filtered audit log as CSV (used for ФСТЭК evidence)."""
    rows = await list_logs(
        db,
        user_id=user_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        page=1,
        limit=10000,
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "user_id", "action", "details", "ip_address", "created_at"])
    for r in rows:
        writer.writerow(
            [
                str(r.id),
                str(r.user_id) if r.user_id else "",
                r.action,
                str(r.details) if r.details else "",
                r.ip_address or "",
                r.created_at.isoformat() if r.created_at else "",
            ]
        )
    return buf.getvalue()
