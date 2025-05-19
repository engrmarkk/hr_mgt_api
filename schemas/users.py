from pydantic import BaseModel, EmailStr, field_serializer, HttpUrl
from typing import Optional
from datetime import datetime


class RoleSchema(BaseModel):
    name: str


class ShowUserProfile(BaseModel):
    address: Optional[str]
    country: Optional[str]
    state: Optional[str]
    city: Optional[str]
    date_of_birth: Optional[str]
    marital_status: Optional[str]


class ShowUserSchema(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone_number: Optional[str]
    role_id: Optional[str]
    role: Optional[RoleSchema]
    email_verified: Optional[bool]
    created_at: Optional[datetime]
    user_profile: Optional[ShowUserProfile]

    @field_serializer("role_id")
    def role_id_display(self, value):
        return value

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d-%B-%Y %H:%M:%S") if v else None,
            RoleSchema: lambda v: v.name.title() if v else None,
            ShowUserProfile: lambda v: (
                {
                    "address": v.address.title() if v.address else None,
                    "country": v.country.title() if v.country else None,
                    "state": v.state.title() if v.state else None,
                    "city": v.city.title() if v.city else None,
                    "date_of_birth": v.date_of_birth,  # Assuming no formatting needed here
                    "marital_status": (
                        v.marital_status.title() if v.marital_status else None
                    ),
                }
                if v
                else None
            ),
            str: lambda v: v.title() if v else None,
            EmailStr: lambda v: v.lower() if v else None,
        }
        from_attributes = True


class LoginSchema(BaseModel):
    email: str
    password: str


class RegisterSchema(BaseModel):
    name: str
    email: str
    password: str


class CompleteRegSchema(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    address: str
    country: str
    state: str
    city: str
    organization_name: str
    organization_address: str
    organization_state: str
    organization_city: str
    organization_phone: str
    organization_email: str
    organization_website: HttpUrl
    organization_country: str
    role: Optional[str] = None
    role_id: Optional[str] = None


# verify email schema
class VerifyEmailSchema(BaseModel):
    email: str
    otp: str


# resend otp schema
class ResendOTPSchema(BaseModel):
    email: str


class ChangePasswordSchema(BaseModel):
    old_password: str
    confirm_password: str
    password: str


class ResetTokenSchema(BaseModel):
    salt: str
    password: str
    confirm_password: str


class ConfirmTokenSchema(BaseModel):
    email: str
    token: str


class CreateEmployeeSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    date_joined: str
