from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..model import BureauScore, LenderAssignment, Permission, Profile, UserJourneyStatus


ALL_STEPS = [
    "permissions",
    "profile",
    "bureau",
    "lender_assignment",
    "banking",
    "loan_offer",
    "loan_detail",
    "kyc",
    "selfie",
    "address",
    "reference",
    "account",
    "employment",
    "emandate",
    "e_sign",
    "home",
]

VALID_STEPS_TO_MARK = {
    "banking",
    "loan_offer",
    "loan_detail",
    "kyc",
    "selfie",
    "address",
    "reference",
    "account",
    "employment",
    "emandate",
    "e_sign",
}


async def upsert_user_journey_status(
    db: AsyncSession,
    mobile: str,
    mark_complete: str | None = None,
    *,
    force_lender_assignment: bool = False,
) -> dict:

    # ------------------------
    # Fetch data
    # ------------------------

    perm_result = await db.execute(
        select(Permission).where(Permission.user_mobile == mobile)
    )
    permission = perm_result.scalar_one_or_none()

    profile_result = await db.execute(
        select(Profile).where(Profile.user_mobile == mobile)
    )
    profile = profile_result.scalar_one_or_none()

    bureau_result = await db.execute(
        select(BureauScore)
        .where(BureauScore.user_mobile == mobile)
        .order_by(BureauScore.created_at.desc())
    )
    bureau = bureau_result.scalars().first()

    lender_assignment = None
    if profile:
        lender_result = await db.execute(
            select(LenderAssignment).where(
                LenderAssignment.customer_id == profile.id,
                LenderAssignment.status == "accepted",
            ).order_by(LenderAssignment.updated_at.desc())
        )
        lender_assignment = lender_result.scalars().first()

    # ------------------------
    # Completion flags
    # ------------------------

    permissions_completed = bool(permission and permission.completed)
    profile_completed = bool(profile)
    bureau_completed = bool(bureau)
    bureau_approved = bool(bureau and bureau.approved) if bureau else False
    lender_assignment_completed = force_lender_assignment or bool(lender_assignment)

    # ------------------------
    # Get existing status
    # ------------------------

    if profile:
        result = await db.execute(
            select(UserJourneyStatus).where(UserJourneyStatus.customer_id == profile.id)
        )
        status = result.scalars().first()

        if not status:
            result = await db.execute(
                select(UserJourneyStatus)
                .where(UserJourneyStatus.user_mobile == mobile)
                .order_by(UserJourneyStatus.customer_id.desc().nulls_last())
            )
            status = result.scalars().first()

    else:
        result = await db.execute(
            select(UserJourneyStatus).where(UserJourneyStatus.user_mobile == mobile)
        )
        status = result.scalars().first()

    def _get(name: str) -> bool:
        return bool(getattr(status, name, 0) or 0) if status else False

    banking_completed = _get("banking_completed")
    loan_offer_completed = _get("loan_offer_completed")
    loan_detail_completed = _get("loan_detail_completed")
    kyc_completed = _get("kyc_completed")
    selfie_completed = _get("selfie_completed")
    address_completed = _get("address_completed")
    reference_completed = _get("reference_completed")
    account_completed = _get("account_completed")
    employment_completed = _get("employment_completed")
    emandate_completed = _get("emandate_completed")
    e_sign_completed = _get("e_sign_completed")

    # ------------------------
    # Mark step complete
    # ------------------------

    if mark_complete:
        if mark_complete not in VALID_STEPS_TO_MARK:
            raise HTTPException(status_code=400, detail="Invalid step")

        step_order = [
            "banking",
            "loan_offer",
            "loan_detail",
            "kyc",
            "selfie",
            "address",
            "reference",
            "account",
            "employment",
            "emandate",
            "e_sign",
        ]

        index = step_order.index(mark_complete)

        flags = [
            "banking_completed",
            "loan_offer_completed",
            "loan_detail_completed",
            "kyc_completed",
            "selfie_completed",
            "address_completed",
            "reference_completed",
            "account_completed",
            "employment_completed",
            "emandate_completed",
            "e_sign_completed",
        ]

        for i in range(index + 1):
            locals()[flags[i]] = True

    # ------------------------
    # Determine current step
    # ------------------------

    if not permissions_completed:
        step = "permissions"
    elif not profile_completed:
        step = "profile"
    elif not bureau_completed:
        step = "bureau"
    elif bureau_completed and not bureau_approved:
        step = "home"
    elif not lender_assignment_completed:
        step = "lender_assignment"
    elif not banking_completed:
        step = "banking"
    elif not loan_offer_completed:
        step = "loan_offer"
    elif not loan_detail_completed:
        step = "loan_detail"
    elif not kyc_completed:
        step = "kyc"
    elif not selfie_completed:
        step = "selfie"
    elif not address_completed:
        step = "address"
    elif not reference_completed:
        step = "reference"
    elif not account_completed:
        step = "account"
    elif not employment_completed:
        step = "employment"
    elif not emandate_completed:
        step = "emandate"
    elif not e_sign_completed:
        step = "e_sign"
    else:
        step = "home"

    # ------------------------
    # Save status
    # ------------------------

    status_data = {
        "user_mobile": mobile,
        "customer_id": profile.id if profile else None,
        "current_step": step,
        "permissions_completed": 1 if permissions_completed else 0,
        "profile_completed": 1 if profile_completed else 0,
        "bureau_completed": 1 if bureau_completed else 0,
        "lender_assignment_completed": 1 if lender_assignment_completed else 0,
        "banking_completed": 1 if banking_completed else 0,
        "loan_offer_completed": 1 if loan_offer_completed else 0,
        "loan_detail_completed": 1 if loan_detail_completed else 0,
        "kyc_completed": 1 if kyc_completed else 0,
        "selfie_completed": 1 if selfie_completed else 0,
        "address_completed": 1 if address_completed else 0,
        "reference_completed": 1 if reference_completed else 0,
        "account_completed": 1 if account_completed else 0,
        "employment_completed": 1 if employment_completed else 0,
        "emandate_completed": 1 if emandate_completed else 0,
        "e_sign_completed": 1 if e_sign_completed else 0,
    }

    if status:
        for k, v in status_data.items():
            setattr(status, k, v)
    else:
        status = UserJourneyStatus(**status_data)
        db.add(status)

    await db.commit()

    # ------------------------
    # Return frontend response
    # ------------------------

    return {
        "step": step,
        "permissionsCompleted": permissions_completed,
        "profileCompleted": profile_completed,
        "bureauCompleted": bureau_completed,
        "lenderAssignmentCompleted": lender_assignment_completed,
        "bankingCompleted": banking_completed,
        "loanOfferCompleted": loan_offer_completed,
        "loanDetailCompleted": loan_detail_completed,
        "kycCompleted": kyc_completed,
        "selfieCompleted": selfie_completed,
        "addressCompleted": address_completed,
        "referenceCompleted": reference_completed,
        "accountCompleted": account_completed,
        "employmentCompleted": employment_completed,
        "emandateCompleted": emandate_completed,
        "eSignCompleted": e_sign_completed,
        "allSteps": ALL_STEPS,
    }


async def mark_step_complete(db: AsyncSession, mobile: str, step_name: str) -> dict:
    return await upsert_user_journey_status(db, mobile, mark_complete=step_name)