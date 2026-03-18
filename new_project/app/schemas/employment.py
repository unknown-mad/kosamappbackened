from pydantic import BaseModel


class EmploymentDetailCreate(BaseModel):
    employerName: str | None = None
    designation: str | None = None
    monthlyIncome: float | None = None
    employmentType: str | None = None
    experienceYears: int | None = None
    officeAddress: str | None = None


class EmploymentDetailResponse(BaseModel):
    id: int
    customerId: int
    employerName: str | None
    designation: str | None
    monthlyIncome: float | None
    employmentType: str | None
    experienceYears: int | None
    officeAddress: str | None

    class Config:
        from_attributes = True
