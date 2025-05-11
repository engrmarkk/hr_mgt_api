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
