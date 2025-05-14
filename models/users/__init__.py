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
from helpers import generate_uuid
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


class Roles(Base):
    __tablename__ = "roles"

    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("Users", backref="role")
    side_menus = relationship(
        "RoleSideMenu", back_populates="role", cascade="all, delete-orphan"
    )
    sub_side_menus = relationship(
        "RoleSubSideMenu", back_populates="role", cascade="all, delete-orphan"
    )

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
            "created_at": self.created_at,
            "user_profile": self.user_profile.to_dict() if self.user_profile else None,
        }


class UserProfile(Base):
    __tablename__ = "user_profile"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    gender = Column(SQLAlchemyEnum(Gender), default=Gender.MALE, nullable=False)
    address = Column(Text, nullable=True)
    country = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
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
    salary = Column(Float, nullable=True)


class HealthInsurance(Base):
    __tablename__ = "health_insurance"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    health_insurance = Column(String(50), nullable=True)
    health_insurance_number = Column(String(50), nullable=True)


class UserEmployment(Base):
    __tablename__ = "user_employment"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    user_id = Column(String(50), ForeignKey("users.id"), unique=True)
    employment_id = Column(String(50), nullable=True)
    job_title = Column(String(70), nullable=True)
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
    salary = Column(Float, nullable=True)


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
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(String(50), ForeignKey("users.id"))
