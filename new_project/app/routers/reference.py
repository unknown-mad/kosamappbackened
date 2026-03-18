"""Reference API for React Native - save/list references by customer."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import Profile, Reference
from ..schemas import ReferenceCreate
from ..services.journey_service import mark_step_complete
from .auth import get_mobile_from_token

router = APIRouter(prefix="/reference", tags=["Reference"])
security = HTTPBearer(auto_error=False)


@router.get("")
async def list_references(
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
    result = await db.execute(select(Reference).where(Reference.customer_id == profile.id))
    refs = result.scalars().all()
    return [
        {
            "id": r.id,
            "customerId": r.customer_id,
            "name": r.name,
            "relation": r.relation,
            "mobile": r.mobile,
        }
        for r in refs
    ]


@router.post("")
async def save_reference(
    payload: ReferenceCreate,
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
    ref = Reference(
        customer_id=profile.id,
        user_mobile=mobile,
        name=payload.name,
        relation=payload.relation,
        mobile=payload.mobile,
    )
    db.add(ref)
    await db.commit()
    await db.refresh(ref)
    await mark_step_complete(db, mobile, "reference")
    return {
        "success": True,
        "id": ref.id,
        "customerId": ref.customer_id,
        "name": ref.name,
        "relation": ref.relation,
        "mobile": ref.mobile,
    }
