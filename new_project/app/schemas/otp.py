from pydantic import BaseModel


class SendOTPRequest(BaseModel):
    mobile: str


class VerifyOTPRequest(BaseModel):
    mobile: str
    otp: str
