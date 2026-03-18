"""Lenders list API - returns lender offers for the current user.

This uses records from kosam_uat.lender_assignments as dummy data.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import BureauScore, LenderAssignment, Profile
from ..schemas import LenderResponse
from .auth import get_mobile_from_token


router = APIRouter(prefix="/lenders", tags=["Lenders"])
security = HTTPBearer(auto_error=False)


@router.get("", response_model=list[LenderResponse])
async def list_lenders(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Return lender offers for this user, creating dummy ones if none exist."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Find customer profile by mobile (so we can scope offers per customer if needed later)
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for user")

    # Fetch existing assignments for this user (by user_mobile or customer_id)
    result = await db.execute(
        select(LenderAssignment)
        .where(
            (LenderAssignment.user_mobile == mobile) | (LenderAssignment.customer_id == profile.id)
        )
        .order_by(LenderAssignment.created_at.desc())
    )
    assignments = result.scalars().all()

    # If none exist, create dummy lenders for this user
    if not assignments:
        bureau_result = await db.execute(
            select(BureauScore)
            .where(BureauScore.user_mobile == mobile)
            .order_by(BureauScore.created_at.desc())
        )
        bureau = bureau_result.scalar_one_or_none()
        loan_id = bureau.loan_id if bureau else None

        dummy_data = [
            {
                "name": "ABC Bank",
                "logo_url": None,
                "website": "https://example.com/abc",
                "roi_min": 12.0,
                "roi_max": 18.0,
                "processing_fee_min": 1,
                "processing_fee_max": 2,
                "loan_amount_min": 50000,
                "loan_amount_max": 500000,
                "tenure_min_months": 6,
                "tenure_max_months": 60,
                "recommended": True,
                "reason": "Best match for your profile",
            },
            {
                "name": "XYZ Finance",
                "logo_url": None,
                "website": "https://example.com/xyz",
                "roi_min": 10.5,
                "roi_max": 16.5,
                "processing_fee_min": 0,
                "processing_fee_max": 1,
                "loan_amount_min": 100000,
                "loan_amount_max": 750000,
                "tenure_min_months": 12,
                "tenure_max_months": 72,
                "recommended": False,
                "reason": "Alternative offer",
            },
            {
                "name": "PQR NBFC",
                "logo_url": None,
                "website": "https://example.com/pqr",
                "roi_min": 13.0,
                "roi_max": 20.0,
                "processing_fee_min": 2,
                "processing_fee_max": 3,
                "loan_amount_min": 25000,
                "loan_amount_max": 300000,
                "tenure_min_months": 3,
                "tenure_max_months": 36,
                "recommended": False,
                "reason": "Quick disbursal",
            },
        ]
        for d in dummy_data:
            a = LenderAssignment(
                user_mobile=mobile,
                customer_id=profile.id,
                loan_id=loan_id,
                lender_id=None,
                name=d["name"],
                lender_name=d["name"],
                logo_url=d["logo_url"],
                website=d["website"],
                roi_min=d["roi_min"],
                roi_max=d["roi_max"],
                processing_fee_min=d["processing_fee_min"],
                processing_fee_max=d["processing_fee_max"],
                loan_amount_min=d["loan_amount_min"],
                loan_amount_max=d["loan_amount_max"],
                tenure_min_months=d["tenure_min_months"],
                tenure_max_months=d["tenure_max_months"],
                tenure_min=d["tenure_min_months"],
                tenure_max=d["tenure_max_months"],
                recommended=d["recommended"],
                reason=d["reason"],
                status="pending",
            )
            db.add(a)
        await db.commit()

        result = await db.execute(
            select(LenderAssignment)
            .where(
                (LenderAssignment.user_mobile == mobile) | (LenderAssignment.customer_id == profile.id)
            )
            .order_by(LenderAssignment.created_at.desc())
        )
        assignments = result.scalars().all()

    # Map from LenderAssignment to LenderResponse
    def _roi(v):
        return float(v) if v is not None else 0.0

    def _int(v):
        return int(v) if v is not None else 0

    return [
        LenderResponse(
            id=a.id,
            name=(a.name or a.lender_name) or "",
            logoUrl=a.logo_url,
            website=a.website,
            roiMin=_roi(a.roi_min),
            roiMax=_roi(a.roi_max),
            processingFeeMin=_int(a.processing_fee_min),
            processingFeeMax=_int(a.processing_fee_max),
            loanAmountMin=_int(a.loan_amount_min),
            loanAmountMax=_int(a.loan_amount_max),
            tenureMinMonths=_int(a.tenure_min_months) or _int(a.tenure_min),
            tenureMaxMonths=_int(a.tenure_max_months) or _int(a.tenure_max),
            recommended=a.recommended or False,
            reason=a.reason,
        )
        for idx, a in enumerate(assignments)
    ]

