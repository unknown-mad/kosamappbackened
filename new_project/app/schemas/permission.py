from pydantic import BaseModel


class PermissionCreate(BaseModel):
    camera: int = 0
    sms: int = 0
    storage: int = 0
    location: int = 0
