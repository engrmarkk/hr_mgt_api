from database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Float,
    Text,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship
from helpers import generate_uuid, format_datetime
from datetime import datetime, timedelta
from constants import OTP_EXPIRES
from enum import Enum


class EmploymentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_BOARDING = "on boarding"
    ON_LEAVE = "on leave"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    PROBATION = "probation"
    RESIGNED = "resigned"


class MaritalStatus(Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


class Relationship(Enum):
    SISTER = "sister"
    BROTHER = "brother"
    FATHER = "father"
    MOTHER = "mother"
    SON = "son"
    DAUGHTER = "daughter"
    WIFE = "wife"
    HUSBAND = "husband"
    SPOUSE = "spouse"
    COUSIN = "cousin"
    FRIEND = "friend"


class EmploymentType(Enum):
    FULL_TIME = "full time"
    PART_TIME = "part time"
    CONTRACT = "contract"
    INTERN = "intern"
    FREELANCE = "freelance"
    VOLUNTEER = "volunteer"


class WorkMode(Enum):
    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"


class FileType(Enum):
    PAYSLIP = "payslip"
    PERSONAL = "personal"


class Roles(Base):
    __tablename__ = "roles"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("Users", backref="role")
    # side_menus = relationship(
    #     "RoleSideMenu", back_populates="role", cascade="all, delete-orphan"
    # )
    # sub_side_menus = relationship(
    #     "RoleSubSideMenu", back_populates="role", cascade="all, delete-orphan"
    # )

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class Department(Base):
    __tablename__ = "departments"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("Users", backref="department")


class Users(Base):
    __tablename__ = "users"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50), unique=True)
    password = Column(Text)
    phone_number = Column(String(50), unique=True, nullable=True)
    date_joined = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, default=datetime.now)
    is_superadmin = Column(Boolean, default=False)
    active = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    organization_id = Column(String(50), ForeignKey("organization.id"), nullable=True)
    organization = relationship("Organization", back_populates="users")
    role_id = Column(String(50), ForeignKey("roles.id"), nullable=True)
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=True)
    user_sessions = relationship("UserSessions", backref="user", uselist=False)
    emergency_contact = relationship("EmergencyContact", backref="user", uselist=False)
    uploaded_files = relationship("UploadedFiles", backref="user", uselist=True)
    user_profile = relationship("UserProfile", backref="user", uselist=False)
    employment_details = relationship(
        "EmploymentDetails", backref="user", uselist=False
    )
    health_insurance = relationship("HealthInsurance", backref="user", uselist=False)
    bank_details = relationship("BankDetails", backref="user", uselist=False)
    compensation = relationship("Compensation", backref="user", uselist=True)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone_number": self.phone_number,
            "role_id": self.role_id,
            "role": self.role.name if self.role else None,
            "email_verified": self.email_verified,
            "department": self.department.name if self.department else None,
            "created_at": format_datetime(self.created_at),
            "last_login": format_datetime(self.last_login),
            "date_joined": (
                format_datetime(self.date_joined) if self.date_joined else None
            ),
            "user_profile": self.user_profile.to_dict() if self.user_profile else {},
            "employment_details": (
                self.employment_details.to_dict() if self.employment_details else {}
            ),
            "health_insurance": (
                self.health_insurance.to_dict() if self.health_insurance else {}
            ),
            "bank_details": self.bank_details.to_dict() if self.bank_details else {},
            "emergency_contact": (
                self.emergency_contact.to_dict() if self.emergency_contact else {}
            ),
            "uploaded_files": (
                self.uploaded_files.to_dict() if self.uploaded_files else {}
            ),
        }

    def to_dict_2(self):
        return {
            "id": self.id,
            "name": f"{self.last_name} {self.first_name}".title(),
            "job_title": (
                self.employment_details.job_title if self.employment_details else ""
            ),
            "line_manager": "John Doe",
            "email": self.email,
            "department": self.department.name if self.department else "",
            "office": self.organization.name if self.organization else "",
            "employment_status": (
                self.employment_details.employment_status.value
                if self.employment_details
                else EmploymentStatus.ACTIVE.value
            ),
            "account": "activated" if self.active else "deactivated",
        }


class UserProfile(Base):
    __tablename__ = "user_profile"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    gender = Column(SQLAlchemyEnum(Gender), default=Gender.MALE, nullable=False)
    address = Column(Text, nullable=True)
    country = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(50), nullable=True)
    tax_id = Column(String(50), nullable=True)
    city = Column(String(50), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    marital_status = Column(
        SQLAlchemyEnum(MaritalStatus), default=MaritalStatus.SINGLE, nullable=False
    )

    def to_dict(self):
        return {
            "address": self.address,
            "country": self.country,
            "state": self.state,
            "postal_code": self.postal_code,
            "city": self.city,
            "date_of_birth": self.date_of_birth,
            "marital_status": self.marital_status,
        }


class EmploymentDetails(Base):
    __tablename__ = "employment_details"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    employment_id = Column(String(50), nullable=True)
    job_title = Column(String(70), nullable=True)
    join_date = Column(DateTime, nullable=True)
    employment_status = Column(
        SQLAlchemyEnum(EmploymentStatus),
        default=EmploymentStatus.ACTIVE,
        nullable=False,
    )
    employment_type = Column(
        SQLAlchemyEnum(EmploymentType), default=EmploymentType.FULL_TIME, nullable=False
    )
    work_mode = Column(
        SQLAlchemyEnum(WorkMode), default=WorkMode.ONSITE, nullable=False
    )


class Compensation(Base):
    __tablename__ = "compensation"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    compensation_type = Column(String(50), nullable=True)
    amount = Column(Float, nullable=True)

    def to_dict(self):
        return {
            "compensation_type": self.compensation_type,
            "amount": self.amount,
        }


class HealthInsurance(Base):
    __tablename__ = "health_insurance"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    health_insurance = Column(String(50), nullable=True)
    health_insurance_number = Column(String(50), nullable=True)


class BankDetails(Base):
    __tablename__ = "bank_details"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    bank_name = Column(String(50), nullable=True)
    account_number = Column(String(50), nullable=True)


class UserSessions(Base):
    __tablename__ = "user_sessions"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"))
    token = Column(String(10))
    salt = Column(String(70))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    expired_at = Column(
        DateTime,
        default=datetime.now() + timedelta(minutes=OTP_EXPIRES),
        onupdate=datetime.now() + timedelta(minutes=OTP_EXPIRES),
    )
    used = Column(Boolean, default=False)


# emergency contact
class EmergencyContact(Base):
    __tablename__ = "emergency_contact"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50), unique=True)
    phone_number = Column(String(50), unique=True)
    relationship = Column(
        SQLAlchemyEnum(Relationship), default=Relationship.FRIEND, nullable=False
    )
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(String(50), ForeignKey("users.id"))


class UploadedFiles(Base):
    __tablename__ = "uploaded_files"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    file_name = Column(String(100))
    file_url = Column(String(100))
    file_type = Column(
        SQLAlchemyEnum(FileType), default=FileType.PERSONAL, nullable=True
    )
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(String(50), ForeignKey("users.id"))

    def to_dict(self):
        return {
            "id": self.id,
            "file_name": self.file_name,
            "file_url": self.file_url,
            "file_type": self.file_type,
            "created_at": self.created_at,
        }
