from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas
from ..database import get_db
from ..services import ContactUsService

router = APIRouter(prefix="/contact-us", tags=["Contact Us"])


@router.post("/", response_model=schemas.ContactCreateResponse)
async def create_contact(contact: schemas.ContactCreate, db: AsyncSession = Depends(get_db)):
    created = await ContactUsService.create(db, contact)
    return schemas.ContactCreateResponse(
        id=created.id, name=created.name, email=created.email, phone=created.phone,
        created_at=created.created_at, updated_at=created.updated_at,
        saved_to="postgres.kosam_uat.contacts"
    )


@router.get("/", response_model=list[schemas.ContactResponse])
async def get_contacts(db: AsyncSession = Depends(get_db)):
    return await ContactUsService.get_all(db)
