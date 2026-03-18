from pydantic import BaseModel


class AccountCreate(BaseModel):
    accountType: str | None = None
    bankName: str | None = None
    accountNumberMasked: str | None = None
    upiId: str | None = None
    status: str | None = "pending"


class AccountResponse(BaseModel):
    id: int
    customerId: int
    accountType: str | None
    bankName: str | None
    accountNumberMasked: str | None
    upiId: str | None
    status: str | None

    class Config:
        from_attributes = True
