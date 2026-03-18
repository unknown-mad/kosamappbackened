"""Profile API for React Native."""
import random
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import BureauScore, Permission, Profile
from ..schemas import ProfileCreate
from ..services.journey_service import upsert_user_journey_status
from .auth import get_mobile_from_token

router = APIRouter(tags=["Profile"])
security = HTTPBearer(auto_error=False)


@router.post("")
async def save_profile(
    payload: ProfileCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    perm_result = await db.execute(select(Permission).where(Permission.user_mobile == mobile))
    permission = perm_result.scalar_one_or_none()

    result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    existing = result.scalar_one_or_none()
    data = {
        "permission_id": permission.id if permission else None,
        "full_name": payload.fullName,
        "pan": payload.pan,
        "date_of_birth": payload.dateOfBirth,
        "father_name": payload.fatherName,
        "pincode": payload.pincode,
        "employment_type": payload.employmentType,
        "loan_purpose": payload.loanPurpose,
        "user_mobile": mobile,
    }
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        customer_id = existing.id
    else:
        profile = Profile(**data)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        customer_id = profile.id

    # Create bureau score for user, linked to customer
    approved = random.random() > 0.3
    score = int(650 + random.random() * 200) if approved else int(300 + random.random() * 220)
    bureau = BureauScore(
        user_mobile=mobile,
        customer_id=customer_id,
        score=score,
        approved=1 if approved else 0,
    )
    db.add(bureau)
    await db.flush()
    bureau.loan_id = bureau.id
    await db.commit()
    await db.refresh(bureau)
    await upsert_user_journey_status(db, mobile)
    return {"success": True, "bureauScore": {"approved": approved, "score": score, "loanId": bureau.loan_id}}
