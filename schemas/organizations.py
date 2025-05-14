from pydantic import BaseModel
from typing import Optional


class OrgSchema(BaseModel):
    name: str
    address: str
    state: str
    city: str
    phone: str
    email: str
    website: str
    country: str

    class Config:
        from_attributes = True


class ShowOrgSchema(BaseModel):
    organization: Optional[OrgSchema] = None


# create organization
class CreateOrgSchema(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    size: Optional[str] = None
    industry_id: Optional[str] = None
    role_id: Optional[str] = None
    role: Optional[str] = None
    reason_id: Optional[str] = None
