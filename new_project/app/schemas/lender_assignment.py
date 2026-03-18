from pydantic import BaseModel


class LenderAssignmentCreate(BaseModel):
    """customer_id and loan_id are set by backend from Profile and BureauScore."""
    lenderName: str
    roiMin: int
    roiMax: int
    processingFeeMin: int
    processingFeeMax: int
    loanAmountMin: int
    loanAmountMax: int
    tenureMin: int
    tenureMax: int


class LenderResponse(BaseModel):
    id: int
    name: str
    logoUrl: str | None = None
    website: str | None = None
    roiMin: float
    roiMax: float
    processingFeeMin: int
    processingFeeMax: int
    loanAmountMin: int
    loanAmountMax: int
    tenureMinMonths: int
    tenureMaxMonths: int
    recommended: bool
    reason: str | None = None

