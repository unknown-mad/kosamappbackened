"""Lender assignment API - assign lender terms to a customer/loan."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import BureauScore, Lender, LenderAssignment, Profile
from ..schemas import LenderAssignmentCreate
from ..services.journey_service import upsert_user_journey_status
from .auth import get_mobile_from_token


router = APIRouter(prefix="/lender-assignment", tags=["Lender Assignment"])
security = HTTPBearer(auto_error=False)


@router.post("")
async def create_lender_assignment(
    payload: LenderAssignmentCreate,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Find customer profile by mobile
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found for user")

    # Find latest bureau score for this user to get loan_id
    result = await db.execute(
        select(BureauScore)
        .where(BureauScore.user_mobile == mobile)
        .order_by(BureauScore.created_at.desc())
    )
    bureau = result.scalar_one_or_none()
    if not bureau:
        raise HTTPException(status_code=400, detail="Bureau score not found for user")

    assignment = LenderAssignment(
        user_mobile=mobile,
        customer_id=profile.id,
        loan_id=bureau.loan_id,
        lender_id=None,
        name=payload.lenderName,
        lender_name=payload.lenderName,
        roi_min=float(payload.roiMin),
        roi_max=float(payload.roiMax),
        processing_fee_min=payload.processingFeeMin,
        processing_fee_max=payload.processingFeeMax,
        loan_amount_min=payload.loanAmountMin,
        loan_amount_max=payload.loanAmountMax,
        tenure_min=payload.tenureMin,
        tenure_max=payload.tenureMax,
        tenure_min_months=payload.tenureMin,
        tenure_max_months=payload.tenureMax,
        status="pending",
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    await upsert_user_journey_status(db, mobile)
    return {"success": True, "id": assignment.id}


@router.get("/current")
async def get_current_lender_and_product(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    For lender screen: fetch assigned lender from lender_assignments
    and product details from lenders table for current user.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Find customer profile by mobile
    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for user")

    # Latest lender assignment for this customer (can have multiple)
    assignment_result = await db.execute(
        select(LenderAssignment)
        .where(LenderAssignment.customer_id == profile.id)
        .order_by(LenderAssignment.created_at.desc())
    )
    assignment = assignment_result.scalars().first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Lender assignment not found")

    lender = None
    if assignment.lender_id is not None:
        lender_result = await db.execute(select(Lender).where(Lender.id == assignment.lender_id))
        lender = lender_result.scalar_one_or_none()

    return {
        "assignment": {
            "id": assignment.id,
            "customerId": assignment.customer_id,
            "loanId": assignment.loan_id,
            "lenderId": assignment.lender_id,
            "lenderName": assignment.lender_name,
            "roiMin": assignment.roi_min,
            "roiMax": assignment.roi_max,
            "processingFeeMin": assignment.processing_fee_min,
            "processingFeeMax": assignment.processing_fee_max,
            "loanAmountMin": assignment.loan_amount_min,
            "loanAmountMax": assignment.loan_amount_max,
            "tenureMin": assignment.tenure_min,
            "tenureMax": assignment.tenure_max,
            "status": assignment.status,
        },
        "lender": None
        if not lender
        else {
            "id": lender.id,
            "name": lender.name,
            "roiMin": lender.roi_min,
            "roiMax": lender.roi_max,
            "processingFeeMin": lender.processing_fee_min,
            "processingFeeMax": lender.processing_fee_max,
            "loanAmountMin": lender.loan_amount_min,
            "loanAmountMax": lender.loan_amount_max,
            "tenureMin": lender.tenure_min,
            "tenureMax": lender.tenure_max,
        },
    }


@router.get("")
async def list_lender_assignments(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """List all lender assignments for current user (for lender list screen)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for user")

    assignments_result = await db.execute(
        select(LenderAssignment)
        .where(LenderAssignment.customer_id == profile.id)
        .order_by(LenderAssignment.created_at.desc())
    )
    assignments = assignments_result.scalars().all()

    return [
        {
            "id": a.id,
            "customerId": a.customer_id,
            "loanId": a.loan_id,
            "lenderId": a.lender_id,
            "lenderName": a.lender_name,
            "roiMin": a.roi_min,
            "roiMax": a.roi_max,
            "processingFeeMin": a.processing_fee_min,
            "processingFeeMax": a.processing_fee_max,
            "loanAmountMin": a.loan_amount_min,
            "loanAmountMax": a.loan_amount_max,
            "tenureMin": a.tenure_min,
            "tenureMax": a.tenure_max,
            "status": a.status,
        }
        for a in assignments
    ]


@router.post("/{assignment_id}/accept")
async def accept_lender_assignment(
    assignment_id: int,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Mark a lender assignment as accepted by the current user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    profile_result = await db.execute(select(Profile).where(Profile.user_mobile == mobile))
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for user")

    assignment_result = await db.execute(
        select(LenderAssignment).where(
            LenderAssignment.id == assignment_id,
            LenderAssignment.customer_id == profile.id,
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Lender assignment not found")

    assignment.status = "accepted"
    await db.commit()
    await db.refresh(assignment)
    await upsert_user_journey_status(db, mobile, force_lender_assignment=True)
    return {"success": True, "id": assignment.id, "status": assignment.status}

