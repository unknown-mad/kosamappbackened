from pydantic import BaseModel


class ProfileCreate(BaseModel):
    fullName: str
    pan: str
    dateOfBirth: str
    fatherName: str
    pincode: str
    employmentType: str
    loanPurpose: str
