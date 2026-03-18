"""Loan approval / loan offer API - get loan offer from approval table."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import Approval, Profile
from .auth import get_mobile_from_token

router = APIRouter(prefix="/approval", tags=["Approval"])
security = HTTPBearer(auto_error=False)


@router.get("/loan-offer")
async def get_loan_offer(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Get loan offer from approval table for current user (latest approved offer)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    result = await db.execute(
        select(Approval)
        .where(Approval.customer_id == profile.id)
        .order_by(Approval.created_at.desc())
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Loan offer not found")
    return {
        "id": approval.id,
        "customerId": approval.customer_id,
        "loanId": approval.loan_id,
        "lenderName": approval.lender_name,
        "loanAmount": approval.loan_amount,
        "tenureMonths": approval.tenure_months,
        "roiMin": approval.roi_min,
        "roiMax": approval.roi_max,
        "interestRate": approval.interest_rate,
        "processingFee": approval.processing_fee,
        "emi": approval.emi,
        "status": approval.status,
    }


@router.get("/loan-offers")
async def list_loan_offers(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """List all loan offers from approval table for current user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    result = await db.execute(
        select(Approval)
        .where(Approval.customer_id == profile.id)
        .order_by(Approval.created_at.desc())
    )
    approvals = result.scalars().all()
    return [
        {
            "id": a.id,
            "customerId": a.customer_id,
            "loanId": a.loan_id,
            "lenderName": a.lender_name,
            "loanAmount": a.loan_amount,
            "tenureMonths": a.tenure_months,
            "roiMin": a.roi_min,
            "roiMax": a.roi_max,
            "interestRate": a.interest_rate,
            "processingFee": a.processing_fee,
            "emi": a.emi,
            "status": a.status,
        }
        for a in approvals
    ]
