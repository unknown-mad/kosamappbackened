"""Address API for React Native - save/get address by customer."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import Address, Profile
from ..schemas import AddressCreate
from ..services.journey_service import mark_step_complete
from .auth import get_mobile_from_token

router = APIRouter(prefix="/address", tags=["Address"])
security = HTTPBearer(auto_error=False)


@router.get("")
async def list_addresses(
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
    result = await db.execute(select(Address).where(Address.customer_id == profile.id))
    addrs = result.scalars().all()
    return [
        {
            "id": a.id,
            "customerId": a.customer_id,
            "addressType": a.address_type,
            "addressLine1": a.address_line1,
            "addressLine2": a.address_line2,
            "city": a.city,
            "state": a.state,
            "pincode": a.pincode,
        }
        for a in addrs
    ]


@router.post("")
async def save_address(
    payload: AddressCreate,
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
    addr = Address(
        customer_id=profile.id,
        user_mobile=mobile,
        address_type=payload.addressType,
        address_line1=payload.addressLine1,
        address_line2=payload.addressLine2,
        city=payload.city,
        state=payload.state,
        pincode=payload.pincode,
    )
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    await mark_step_complete(db, mobile, "address")
    return {
        "success": True,
        "id": addr.id,
        "customerId": addr.customer_id,
        "addressType": addr.address_type,
        "addressLine1": addr.address_line1,
        "addressLine2": addr.address_line2,
        "city": addr.city,
        "state": addr.state,
        "pincode": addr.pincode,
    }
