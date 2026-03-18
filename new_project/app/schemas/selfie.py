from pydantic import BaseModel


class SelfieCreate(BaseModel):
    selfieUrl: str | None = None


class SelfieResponse(BaseModel):
    id: int
    customerId: int
    selfieUrl: str | None
    verified: int

    class Config:
        from_attributes = True
