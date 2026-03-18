from pydantic import BaseModel


class ReferenceCreate(BaseModel):
    name: str
    relation: str | None = None
    mobile: str


class ReferenceResponse(BaseModel):
    id: int
    customerId: int
    name: str
    relation: str | None
    mobile: str

    class Config:
        from_attributes = True
