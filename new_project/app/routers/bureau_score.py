"""Bureau score API - fetch from bureau_scores table."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..model import BureauScore
from .auth import get_mobile_from_token

router = APIRouter(prefix="/bureau-score", tags=["Bureau Score"])
security = HTTPBearer(auto_error=False)


@router.get("")
async def get_bureau_score(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing token")
    mobile = await get_mobile_from_token(credentials.credentials, db)
    if not mobile:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(
        select(BureauScore)
        .where(BureauScore.user_mobile == mobile)
        .order_by(BureauScore.created_at.desc())
    )
    bureau = result.scalar_one_or_none()
    if not bureau:
        raise HTTPException(status_code=404, detail="Bureau score not found")

    return {"approved": bool(bureau.approved), "score": bureau.score}
