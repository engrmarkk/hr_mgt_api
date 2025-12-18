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
)
from sqlalchemy.orm import relationship
from helpers import generate_uuid, format_datetime
from datetime import datetime, timedelta
from constants import OTP_EXPIRES


class Reasons(Base):
    __tablename__ = "reasons"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(50))
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    deleted = Column(Boolean, default=False)
    organization = relationship("Organization", backref="reason")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }


# industry model
class Industry(Base):
    __tablename__ = "industry"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(50))
    deleted = Column(Boolean, default=False)
    organization = relationship("Organization", back_populates="indust")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class Organization(Base):
    __tablename__ = "organization"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(50))
    domain = Column(String(50))
    size = Column(String(50))
    industry = Column(String(50), ForeignKey("industry.id"))
    indust = relationship("Industry", back_populates="organization")
    reason_id = Column(String(50), ForeignKey("reasons.id"))
    address = Column(Text, nullable=True)
    country = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    city = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(50), nullable=True)
    website = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    active = Column(Boolean, default=True)
    deleted = Column(Boolean, default=False)
    holidays = relationship("Holiday", back_populates="organization")
    users = relationship("Users", back_populates="organization")
    leave_types = relationship("LeaveType", back_populates="organization")
    work_hours = relationship("WorkHours", back_populates="organization")
    job_postings = relationship("JobPosting", backref="organization")
    departments = relationship("Department", backref="organization")
    job_stages = relationship("JobStages", backref="organization")


# holiday model
class Holiday(Base):
    __tablename__ = "holiday"
    id = Column(String(50), primary_key=True, default=generate_uuid)
    name = Column(String(100))
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    organization_id = Column(String(50), ForeignKey("organization.id"), nullable=True)
    organization = relationship("Organization", back_populates="holidays")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name.title(),
            "from_date": self.from_date,
            "to_date": self.to_date,
            "formatted_from_date": format_datetime(self.from_date),
            "formatted_to_date": format_datetime(self.to_date),
        }


# class SideMenu(Base):
#     __tablename__ = "side_menu"
#
#     id = Column(String(50), primary_key=True, default=generate_uuid)
#     name = Column(String(70), nullable=False)
#     icon = Column(String(200), nullable=True)
#     tag = Column(Integer, unique=True, nullable=False)
#     description = Column(String(200), nullable=True)
#     created_at = Column(DateTime, default=datetime.now)
#     deleted = Column(Boolean, default=False)
#
#     roles = relationship(
#         "RoleSideMenu", back_populates="side_menu", cascade="all, delete-orphan"
#     )
#     sub_side_menus = relationship(
#         "SubSideMenu", back_populates="side_menu", cascade="all, delete-orphan"
#     )
#
#     def __repr__(self):
#         return f"<SideMenu(id={self.id}, name={self.name}, tag={self.tag})>"
#
#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#             "icon": self.icon,
#             "tag": self.tag,
#             "description": self.description,
#             "sub_side_menus": [
#                 sub_side_menu.to_dict() for sub_side_menu in self.sub_side_menus
#             ],
#         }

#
# class SubSideMenu(Base):
#     __tablename__ = "sub_side_menu"
#     id = Column(String(50), primary_key=True, default=generate_uuid)
#     name = Column(String(70), nullable=False)
#     side_menu_id = Column(String(50), ForeignKey("side_menu.id"), nullable=False)
#
#     side_menu = relationship("SideMenu", back_populates="sub_side_menus")
#
#     roles = relationship(
#         "RoleSubSideMenu", back_populates="sub_side_menu", cascade="all, delete-orphan"
#     )
#
#     def __repr__(self):
#         return f"<SubSideMenu(id={self.id}, name={self.name})>"
#
#     def to_dict(self):
#         return {
#             "id": self.id,
#             "name": self.name,
#         }


# class RoleSideMenu(Base):
#     __tablename__ = "role_side_menu"
#     role_id = Column(String(50), ForeignKey("roles.id"), primary_key=True)
#     side_menu_id = Column(String(50), ForeignKey("side_menu.id"), primary_key=True)
#
#     role = relationship("Roles", back_populates="side_menus")
#     side_menu = relationship("SideMenu", back_populates="roles")
#
#     def __repr__(self):
#         return (
#             f"<RoleSideMenu(role_id={self.role_id}, side_menu_id={self.side_menu_id})>"
#         )
#
#
# class RoleSubSideMenu(Base):
#     __tablename__ = "role_sub_side_menu"
#     role_id = Column(String(50), ForeignKey("roles.id"), primary_key=True)
#     sub_side_menu_id = Column(
#         String(50), ForeignKey("sub_side_menu.id"), primary_key=True
#     )
#
#     role = relationship("Roles", back_populates="sub_side_menus")
#     sub_side_menu = relationship("SubSideMenu", back_populates="roles")
#
#     def __repr__(self):
#         return f"<RoleSubSideMenu(role_id={self.role_id}, sub_side_menu_id={self.sub_side_menu_id})>"


"""
async def manage_side_menus(data: dict, db: Session = Depends(get_db)):
    role_id = data.get("role_id")
    side_menu_ids = data.get("side_menu_ids", [])

    # Validate role existence
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if side_menu_ids:
        # Assign new side menus to the role
        for menu_id in side_menu_ids:
            side_menu = db.query(SideMenu).filter(SideMenu.id == menu_id).first()
            if side_menu:
                # Check if already assigned
                existing_mapping = db.query(RoleSideMenu).filter(
                    RoleSideMenu.role_id == role_id,
                    RoleSideMenu.side_menu_id == menu_id
                ).first()
                if not existing_mapping:
                    role_side_menu = RoleSideMenu(role_id=role_id, side_menu_id=menu_id)
                    db.add(role_side_menu)
            else:
                raise HTTPException(status_code=404, detail=f"Side menu {menu_id} not found")
    else:
        # Unassign all side menus from the role
        existing_mappings = db.query(RoleSideMenu).filter(RoleSideMenu.role_id == role_id).all()
        for mapping in existing_mappings:
            db.delete(mapping)

    db.commit()  # Commit the changes to the database
    return {"message": "Side menus updated successfully"}

"""
