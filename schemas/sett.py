from pydantic import BaseModel, EmailStr, field_serializer, HttpUrl, field_validator
from typing import Optional
from datetime import datetime


class EditCompanySchema(BaseModel):
    name: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    email: Optional[str]
