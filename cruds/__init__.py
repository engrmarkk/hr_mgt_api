from models import (
    Users,
    UserSessions,
    Roles,
    SubSideMenu,
    Organization,
    SideMenu,
    UserProfile,
    Gender,
    MaritalStatus,
)
from helpers import hash_password
from constants import SESSION_EXPIRES, OTP_EXPIRES
from datetime import datetime, timedelta

# from celery_config.utils.cel_workers import send_mail
from fastapi import Request, HTTPException
from logger import logger
from sqlalchemy import func


# if email exists (fastapi)
async def email_exists(db, email: str):
    return db.query(Users).filter(Users.email.ilike(email)).first()


async def check_if_user_in_usertable(db):
    return db.query(Users).first()


async def check_if_org_in_orgtable(db):
    return db.query(Organization).first()


# save user with just email and password
async def save_user_email_password(db, email, password):
    user = Users(email=email, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# phone number exists
async def phone_number_exists(db, phone_number):
    return db.query(Users).filter(Users.phone_number == phone_number).first()


async def save_user_profile(
    db,
    user_id,
    gender=Gender.MALE,
    address=None,
    country=None,
    state=None,
    city=None,
    date_of_birth=None,
    marital_status=MaritalStatus.SINGLE,
):
    try:
        user_profile = UserProfile(
            user_id=user_id,
            gender=gender,
            address=address,
            country=country,
            state=state,
            city=city,
            date_of_birth=date_of_birth,
            marital_status=marital_status,
        )
        db.add(user_profile)
        db.commit()
        return user_profile
    except Exception as e:
        db.rollback()
        raise None


async def create_or_update_user_session(db, user, otp=None, token=None):
    user_session = db.query(UserSessions).filter_by(user_id=user.id).first()
    if user_session:
        if token:
            user_session.token = token
            user_session.used_token = False
            user_session.token_expired_date = datetime.now() + timedelta(
                minutes=SESSION_EXPIRES
            )
        if otp:
            user_session.otp = otp
            user_session.used_otp = False
            user_session.otp_expired_date = datetime.now() + timedelta(
                minutes=OTP_EXPIRES
            )
    else:
        user_session = UserSessions(user_id=user.id)
        if token:
            user_session.token = token
            user_session.used_token = False
            user_session.token_expired_date = datetime.now() + timedelta(
                minutes=SESSION_EXPIRES
            )
        if otp:
            user_session.otp = otp
            user_session.used_otp = False
            user_session.otp_expired_date = datetime.now() + timedelta(
                minutes=OTP_EXPIRES
            )
        db.add(user_session)
    db.commit()
    return user_session


# extract user_id from request for rate limit
def get_user_id_from_request(request: Request):
    user_id = request.state.user_id
    logger.info(f"user_id: {user_id}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


def save_user_data(db, data):
    pass


async def create_organization(
    db, name, address, country, state, city, phone, email, website
):
    organization = Organization(
        name=name,
        address=address,
        country=country,
        state=state,
        city=city,
        phone=phone,
        email=email,
        website=website,
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


async def create_role(db, name):
    existing_role = db.query(Roles).filter(Roles.name.ilike(name)).first()
    if existing_role:
        return existing_role
    role = Roles(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


# get side mennus
async def get_side_menus(db):
    menus = (
        db.query(SideMenu)
        .filter(SideMenu.deleted == False)
        .order_by(SideMenu.tag)
        .all()
    )
    return [menu.to_dict() for menu in menus]


# get roles
async def get_roles(db):
    roles = db.query(Roles).order_by(Roles.name).all()
    return roles


def save_default_side_menus(db):
    # Sample JSON data
    side_menus = [
        {
            "name": "Dashboard",
            "icon_url": "https://example.com/icons/dashboard.png",
            "tag": 1,
            "description": "Access to the main dashboard.",
            "sub_side_menus": [],
        },
        {
            "name": "Employees",
            "tag": 2,
            "icon_url": "https://example.com/icons/users.png",
            "description": "Manage users and their roles.",
            "sub_side_menus": [],
        },
        {
            "name": "Admins",
            "tag": 10,
            "icon_url": "https://example.com/icons/users.png",
            "description": "Manage users and their roles.",
            "sub_side_menus": [],
        },
        {
            "name": "Settings",
            "tag": 7,
            "icon_url": "https://example.com/icons/settings.png",
            "description": "Configure application settings.",
            "sub_side_menus": [],
        },
        {
            "name": "Reports",
            "tag": 9,
            "icon_url": "https://example.com/icons/reports.png",
            "description": "View and generate reports.",
            "sub_side_menus": [],
        },
        {
            "name": "Notifications",
            "tag": 4,
            "icon_url": "https://example.com/icons/notifications.png",
            "description": "Manage notifications and alerts.",
            "sub_side_menus": [],
        },
        {
            "name": "Analytics",
            "tag": 3,
            "icon_url": "https://example.com/icons/analytics.png",
            "description": "View analytics and statistics.",
            "sub_side_menus": [],
        },
        {
            "name": "Events",
            "tag": 5,
            "icon_url": "https://example.com/icons/events.png",
            "description": "Access and manage events.",
            "sub_side_menus": [],
        },
        {
            "name": "Projects",
            "tag": 6,
            "icon_url": "https://example.com/icons/projects.png",
            "description": "Manage projects and tasks.",
            "sub_side_menus": [],
        },
        {
            "name": "Help",
            "tag": 8,
            "icon_url": "https://example.com/icons/help.png",
            "description": "Access help and documentation.",
            "sub_side_menus": [],
        },
    ]

    # Save data to the database
    for menu in side_menus:
        # Check if a SideMenu with the same name already exists
        existing_menu = (
            db.query(SideMenu).filter(SideMenu.name.ilike(menu["name"])).first()
        )

        if not existing_menu:  # If no existing entry found, add it
            side_menu = SideMenu(
                name=menu["name"],
                icon=menu["icon_url"],
                tag=menu["tag"],
                description=menu.get("description"),  # Use get to avoid KeyError
            )
            db.add(side_menu)

            for sub_menu in menu.get("sub_side_menus", []):  # Use get to avoid KeyError
                if (
                    not db.query(SubSideMenu)
                    .filter(SubSideMenu.name.ilike(sub_menu["name"]))
                    .first()
                ):
                    sub_side_menu = SubSideMenu(
                        name=sub_menu["name"], side_menu_id=side_menu.id
                    )
                    db.add(sub_side_menu)

    # Commit the session after the loop to save all changes at once
    db.commit()

    return side_menus


# save default role
async def save_default_roles(db):
    roles = [
        {"name": "Super Admin"},
        {"name": "Admin"},
        {"name": "Human Resources"},
        {"name": "Staff"},
    ]
    for role in roles:
        await create_role(db, role["name"])

    return roles


# def create_sub_side_menu(db, name, side_menu_id):
#     sub_side_menu = SubSideMenu(name=name, side_menu_id=side_menu_id)
#     db.add(sub_side_menu)
#     db.commit()
#     db.refresh(sub_side_menu)
#     return sub_side_menu
