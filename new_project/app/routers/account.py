"""Account (bank/UPI) API for React Native - save/get account by customer."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import Account, Profile
from ..schemas import AccountCreate
from ..services.journey_service import mark_step_complete
from .auth import get_mobile_from_token

router = APIRouter(prefix="/account", tags=["Account"])
security = HTTPBearer(auto_error=False)


@router.get("")
async def get_account(
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
    result = await db.execute(select(Account).where(Account.customer_id == profile.id))
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "id": acc.id,
        "customerId": acc.customer_id,
        "accountType": acc.account_type,
        "bankName": acc.bank_name,
        "accountNumberMasked": acc.account_number_masked,
        "upiId": acc.upi_id,
        "status": acc.status,
    }


@router.post("")
async def save_account(
    payload: AccountCreate,
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
    result = await db.execute(select(Account).where(Account.customer_id == profile.id))
    existing = result.scalar_one_or_none()
    data = {
        "customer_id": profile.id,
        "user_mobile": mobile,
        "account_type": payload.accountType,
        "bank_name": payload.bankName,
        "account_number_masked": payload.accountNumberMasked,
        "upi_id": payload.upiId,
        "status": payload.status or "pending",
    }
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        row = existing
    else:
        acc = Account(**data)
        db.add(acc)
        await db.commit()
        await db.refresh(acc)
        row = acc
    await mark_step_complete(db, mobile, "account")
    return {
        "success": True,
        "id": row.id,
        "customerId": row.customer_id,
        "accountType": row.account_type,
        "bankName": row.bank_name,
        "accountNumberMasked": row.account_number_masked,
        "upiId": row.upi_id,
        "status": row.status,
    }
