from datetime import datetime
from pydantic import BaseModel


class ContactCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None


class ContactResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ContactCreateResponse(ContactResponse):
    saved_to: str = "postgres.kosam_uat.contacts"
