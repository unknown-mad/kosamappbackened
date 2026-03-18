import logging
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from .. import model, schemas

logger = logging.getLogger(__name__)


class ContactUsService:
    """Service layer for contact us operations. Data saved to postgres.kosam_uat.contacts"""

    @staticmethod
    async def create(db: AsyncSession, contact: schemas.ContactCreate):
        # Check if contact exists with same email or phone
        conditions = [model.Contact.email == contact.email]
        if contact.phone:
            conditions.append(model.Contact.phone == contact.phone)
        result = await db.execute(select(model.Contact).where(or_(*conditions)))
        existing = result.scalars().first()

        if existing:
            # Update existing record
            existing.name = contact.name
            existing.email = contact.email
            existing.phone = contact.phone
            await db.commit()
            await db.refresh(existing)
            logger.info("Contact us updated (existing email/phone): id=%s, email=%s -> postgres.kosam_uat.contacts", existing.id, existing.email)
            return existing

        # Create new record
        db_contact = model.Contact(**contact.model_dump())
        db.add(db_contact)
        await db.commit()
        await db.refresh(db_contact)
        logger.info("Contact us saved: id=%s, email=%s -> postgres.kosam_uat.contacts", db_contact.id, db_contact.email)
        return db_contact

    @staticmethod
    async def get_all(db: AsyncSession):
        result = await db.execute(select(model.Contact))
        return result.scalars().all()
