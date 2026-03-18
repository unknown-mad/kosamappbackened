"""Selfie API for React Native - save/get selfie by customer."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import Profile, Selfie
from ..schemas import SelfieCreate
from ..services.journey_service import mark_step_complete
from .auth import get_mobile_from_token

router = APIRouter(prefix="/selfie", tags=["Selfie"])
security = HTTPBearer(auto_error=False)


@router.get("")
async def get_selfie(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    result = await db.execute(select(Selfie).where(Selfie.customer_id == profile.id))
    selfie = result.scalar_one_or_none()
    if not selfie:
        raise HTTPException(status_code=404, detail="Selfie not found")
    return {
        "id": selfie.id,
        "customerId": selfie.customer_id,
        "selfieUrl": selfie.selfie_url,
        "verified": selfie.verified,
    }


@router.post("")
async def save_selfie(
    payload: SelfieCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found")
    result = await db.execute(select(Selfie).where(Selfie.customer_id == profile.id))
    existing = result.scalar_one_or_none()
    data = {
        "customer_id": profile.id,
        "user_mobile": mobile,
        "selfie_url": payload.selfieUrl,
    }
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        row = existing
    else:
        selfie = Selfie(**data)
        db.add(selfie)
        await db.commit()
        await db.refresh(selfie)
        row = selfie
    await mark_step_complete(db, mobile, "selfie")
    return {
        "success": True,
        "id": row.id,
        "customerId": row.customer_id,
        "selfieUrl": row.selfie_url,
        "verified": row.verified,
    }
