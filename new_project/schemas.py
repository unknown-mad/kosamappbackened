from pydantic import BaseModel

class ContactCreate(BaseModel):
    name: str
    email: str
    phone: str

class ContactResponse(ContactCreate):
    id: int

    class Config:
        from_attributes = True