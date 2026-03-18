"""Employment detail API for React Native - save/get employment by customer."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import EmploymentDetail, Profile
from ..schemas import EmploymentDetailCreate
from ..services.journey_service import mark_step_complete
from .auth import get_mobile_from_token

router = APIRouter(prefix="/employment", tags=["Employment"])
security = HTTPBearer(auto_error=False)


@router.get("")
async def get_employment(
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
    result = await db.execute(
        select(EmploymentDetail).where(EmploymentDetail.customer_id == profile.id)
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employment detail not found")
    return {
        "id": emp.id,
        "customerId": emp.customer_id,
        "employerName": emp.employer_name,
        "designation": emp.designation,
        "monthlyIncome": emp.monthly_income,
        "employmentType": emp.employment_type,
        "experienceYears": emp.experience_years,
        "officeAddress": emp.office_address,
    }


@router.post("")
async def save_employment(
    payload: EmploymentDetailCreate,
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
    result = await db.execute(
        select(EmploymentDetail).where(EmploymentDetail.customer_id == profile.id)
    )
    existing = result.scalar_one_or_none()
    data = {
        "customer_id": profile.id,
        "user_mobile": mobile,
        "employer_name": payload.employerName,
        "designation": payload.designation,
        "monthly_income": payload.monthlyIncome,
        "employment_type": payload.employmentType,
        "experience_years": payload.experienceYears,
        "office_address": payload.officeAddress,
    }
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        await db.commit()
        await db.refresh(existing)
        row = existing
    else:
        emp = EmploymentDetail(**data)
        db.add(emp)
        await db.commit()
        await db.refresh(emp)
        row = emp
    await mark_step_complete(db, mobile, "employment")
    return {
        "success": True,
        "id": row.id,
        "customerId": row.customer_id,
        "employerName": row.employer_name,
        "designation": row.designation,
        "monthlyIncome": row.monthly_income,
        "employmentType": row.employment_type,
        "experienceYears": row.experience_years,
        "officeAddress": row.office_address,
    }
