from pydantic import BaseModel
from typing import Optional


class MiscMenuSchema(BaseModel):
    name: str
    description: Optional[str]
    icon_url: Optional[str]
    tag: int

    class Config:
        from_attributes = True


class MiscRoleSchema(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True
