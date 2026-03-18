from typing import Literal

from pydantic import BaseModel

AddressType = Literal["rent", "own"]


class AddressCreate(BaseModel):
    addressType: AddressType | None = None
    addressLine1: str
    addressLine2: str | None = None
    city: str
    state: str
    pincode: str


class AddressResponse(BaseModel):
    id: int
    customerId: int
    addressType: str | None
    addressLine1: str
    addressLine2: str | None
    city: str
    state: str
    pincode: str

    class Config:
        from_attributes = True
