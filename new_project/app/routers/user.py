"""User journey and step-complete API."""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.journey_service import mark_step_complete, upsert_user_journey_status
from .auth import get_mobile_from_token

router = APIRouter(prefix="/user", tags=["User"])
security = HTTPBearer(auto_error=False)


@router.get("/journey")
async def get_journey_status(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Return current journey step and completion flags. Keyed by customer_id when profile exists."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    status = await upsert_user_journey_status(db, mobile)
    # Service already returns the correctly shaped response for the frontend.
    return status


@router.post("/journey/step")
@router.post("/step-complete")
async def step_complete(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Accepts JSON with 'step' or 'stepName'. Example: {"step": "banking"} or {"stepName": "banking"}."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    body: dict = {}
    try:
        raw = await request.body()
        if raw:
            body = json.loads(raw) if isinstance(raw, bytes) else raw
    except Exception as e:
        logging.warning("step-complete: body parse failed: %s", e)
    step = ""
    if isinstance(body, dict):
        step = (body.get("step") or body.get("stepName") or body.get("step_name") or "").strip()
    elif isinstance(body, str):
        step = body.strip()
    if not step:
        raise HTTPException(
            status_code=422,
            detail="Body must contain 'step' or 'stepName'. Example: {\"step\": \"banking\"}",
        )
    result = await mark_step_complete(db, mobile, step)
    return {"success": True, "step": result["step"]}