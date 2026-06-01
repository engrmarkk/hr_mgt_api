from pydantic import BaseModel
from typing import Optional


class OrgSchema(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None

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
