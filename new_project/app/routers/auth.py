"""OTP send/verify for React Native login."""
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import (
    BureauScore,
    LenderAssignment,
    OTP,
    Permission,
    Profile,
    Token,
    UserJourneyStatus,
)
from ..schemas import SendOTPRequest, VerifyOTPRequest

router = APIRouter(prefix="/otp", tags=["Auth"])


@router.get("")
async def otp_health():
    """Check that /api/otp is reachable (no auth, no DB)."""
    return {"ok": True, "message": "OTP API ready"}


@router.post("/send")
async def send_otp(req: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    try:
        otp_value = "123456"  # Dev: fixed OTP
        db_otp = OTP(mobile=req.mobile, otp=otp_value)
        db.add(db_otp)
        await db.commit()
        return {"success": True, "message": "OTP sent"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.post("/verify")
async def verify_otp(req: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OTP).where(OTP.mobile == req.mobile).order_by(OTP.created_at.desc())
    )
    otp_row = result.scalars().first()
    valid_otp = otp_row.otp if otp_row else "123456"
    if req.otp != valid_otp and req.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if otp_row:
        otp_row.used = 1
        await db.commit()

    # Create access token
    token = secrets.token_urlsafe(32)
    db_token = Token(token=token, mobile=req.mobile)
    db.add(db_token)
    await db.commit()

    # Compute current journey step for this user (same rules as /user/journey)
    mobile = req.mobile

    # Permissions
    perm_result = await db.execute(select(Permission).where(Permission.user_mobile == mobile))
    permission = perm_result.scalar_one_or_none()

    # Profile / customer
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()

    # Bureau score (latest)
    bureau_result = await db.execute(
        select(BureauScore)
        .where(BureauScore.user_mobile == mobile)
        .order_by(BureauScore.created_at.desc())
    )
    bureau = bureau_result.scalar_one_or_none()

    # Lender assignment (accepted one - customer can have multiple pending)
    lender_assignment = None
    if profile:
        lender_result = await db.execute(
            select(LenderAssignment)
            .where(
                LenderAssignment.customer_id == profile.id,
                LenderAssignment.status == "accepted",
            )
            .order_by(LenderAssignment.created_at.desc())
        )
        lender_assignment = lender_result.scalars().first()

    permissions_completed = bool(permission and permission.completed)
    profile_completed = bool(profile)
    bureau_completed = bool(bureau)
    lender_assignment_completed = bool(lender_assignment)

    if not permissions_completed:
        step = "permissions"
    elif not profile_completed:
        step = "profile"
    elif not bureau_completed:
        step = "bureau"
    elif not lender_assignment_completed:
        step = "lender_assignment"
    else:
        step = "home"

    # Upsert into user_journey_status table based on user_mobile
    status_result = await db.execute(
        select(UserJourneyStatus).where(UserJourneyStatus.user_mobile == mobile)
    )
    status = status_result.scalar_one_or_none()
    status_data = {
        "user_mobile": mobile,
        "customer_id": profile.id if profile else None,
        "current_step": step,
        "permissions_completed": 1 if permissions_completed else 0,
        "profile_completed": 1 if profile_completed else 0,
        "bureau_completed": 1 if bureau_completed else 0,
        "lender_assignment_completed": 1 if lender_assignment_completed else 0,
    }
    if status:
        for k, v in status_data.items():
            setattr(status, k, v)
    else:
        status = UserJourneyStatus(**status_data)
        db.add(status)
    await db.commit()

    return {"access_token": token, "token_type": "bearer", "step": step}


async def get_mobile_from_token(token: str, db: AsyncSession) -> str | None:
    result = await db.execute(select(Token).where(Token.token == token))
    row = result.scalar_one_or_none()
    return row.mobile if row else None
