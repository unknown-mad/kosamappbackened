"""Permission API - save user's granted permissions in journey."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import Permission
from ..schemas import PermissionCreate
from ..services.journey_service import upsert_user_journey_status
from .auth import get_mobile_from_token

router = APIRouter(tags=["Permission"])
security = HTTPBearer(auto_error=False)


@router.post("")
async def save_permissions(
    payload: PermissionCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(select(Permission).where(Permission.user_mobile == mobile))
    existing = result.scalar_one_or_none()

    data = {
        "user_mobile": mobile,
        "camera": payload.camera,
        "sms": payload.sms,
        "storage": payload.storage,
        "location": payload.location,
        "completed": 1,
    }
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
    else:
        perm = Permission(**data)
        db.add(perm)
        await db.commit()
        await db.refresh(perm)
    await upsert_user_journey_status(db, mobile)
    return {"success": True}
