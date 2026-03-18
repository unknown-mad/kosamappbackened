"""Debug journey data for a given mobile.

This helps verify what the backend sees for a particular user.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import BureauScore, LenderAssignment, Permission, Profile, UserJourneyStatus


router = APIRouter(prefix="/debug/journey", tags=["Debug"])


@router.get("/{mobile}")
async def debug_journey(mobile: str, db: AsyncSession = Depends(get_db)):
    """Return raw journey-related data and computed step for a mobile."""
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

    # Lender assignment (by customer id, if profile exists)
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

    # Current row in user_journey_status (if any)
    status_result = await db.execute(
        select(UserJourneyStatus).where(UserJourneyStatus.user_mobile == mobile)
    )
    status = status_result.scalar_one_or_none()

    return {
        "mobile": mobile,
        "computedStep": step,
        "permissions": None
        if not permission
        else {
            "id": permission.id,
            "completed": permission.completed,
        },
        "profile": None
        if not profile
        else {
            "id": profile.id,
            "fullName": profile.full_name,
            "pan": profile.pan,
        },
        "bureauScore": None
        if not bureau
        else {
            "id": bureau.id,
            "score": bureau.score,
            "approved": bureau.approved,
        },
        "lenderAssignment": None
        if not lender_assignment
        else {
            "id": lender_assignment.id,
            "customerId": lender_assignment.customer_id,
            "loanId": lender_assignment.loan_id,
        },
        "userJourneyStatus": None
        if not status
        else {
            "id": status.id,
            "userMobile": status.user_mobile,
            "customerId": status.customer_id,
            "currentStep": status.current_step,
            "permissionsCompleted": status.permissions_completed,
            "profileCompleted": status.profile_completed,
            "bureauCompleted": status.bureau_completed,
            "lenderAssignmentCompleted": status.lender_assignment_completed,
        },
    }

