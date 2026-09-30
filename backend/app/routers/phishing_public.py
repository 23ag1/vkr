"""Public phishing tracking routes — no auth required.

These URLs appear in simulated phishing emails so they must not require auth.
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.phishing_campaigns as campaign_service
from app.deps import get_db

router = APIRouter()

_TRACKING_PIXEL = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!"
    b"\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


@router.get("/track/{token}/open", include_in_schema=False)
async def track_open(token: str, db: AsyncSession = Depends(get_db)):
    await campaign_service.record_tracking_event(db, token, "opened_at")
    return Response(content=_TRACKING_PIXEL, media_type="image/gif")


@router.get("/track/{token}/click", include_in_schema=False)
async def track_click(token: str, db: AsyncSession = Depends(get_db)):
    await campaign_service.record_tracking_event(db, token, "clicked_at")
    return RedirectResponse(url=f"/phishing/landing/{token}")


@router.post("/track/{token}/submit", include_in_schema=False)
async def track_submit(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    await campaign_service.record_tracking_event(db, token, "submitted_at")
    return Response(status_code=200)


@router.get("/landing/{token}", response_class=HTMLResponse, include_in_schema=False)
async def phishing_landing(token: str):
    # clicked_at already recorded by track_click redirect; landing just shows the page
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><title>Вход в систему</title>
<style>
  body{{font-family:sans-serif;background:#f0f2f5;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
  .box{{background:#fff;border-radius:8px;padding:32px;width:320px;box-shadow:0 2px 8px rgba(0,0,0,.1)}}
  h2{{margin:0 0 20px;font-size:18px;color:#1c1e21}}
  input{{width:100%;padding:10px;border:1px solid #ccd0d5;border-radius:4px;font-size:14px;box-sizing:border-box;margin-bottom:12px}}
  button{{width:100%;padding:10px;background:#1877f2;color:#fff;border:none;border-radius:4px;font-size:15px;cursor:pointer}}
  button:hover{{background:#166fe5}}
</style></head>
<body>
  <div class="box">
    <h2>Вход в корпоративный портал</h2>
    <form method="POST" action="/phishing/track/{token}/submit">
      <input type="text" name="username" placeholder="Логин или email" required>
      <input type="password" name="password" placeholder="Пароль" required>
      <button type="submit">Войти</button>
    </form>
  </div>
</body></html>"""
    return HTMLResponse(content=html)
