import json

from models import (
    Users,
    UserSessions,
    Roles,
    # SubSideMenu,
    Organization,
    # SideMenu,
    BankDetails,
    HealthInsurance,
    UserProfile,
    EmergencyContact,
    EmploymentDetails,
    Gender,
    MaritalStatus,
    Industry,
    Reasons,
    FileType,
    Relationship,
    EmploymentStatus,
    EmploymentType,
    WorkMode,
    Compensation,
    UploadedFiles,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    Holiday,
    WorkHours,
    Attendance,
    JobPosting,
    AppliedCandidates,
    JobStages,
    Department,
)
from helpers import hash_password, get_service_year
from constants import SESSION_EXPIRES, DEFAULT_PASSWORD
from datetime import datetime, timedelta, date

# from celery_config.utils.cel_workers import send_mail
from fastapi import Request, HTTPException
from logger import logger
from sqlalchemy import func, desc, asc, case
from helpers import validate_phone_number, validate_correct_email
from connections import redis_conn


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


async def save_user_data(db, last_name, first_name, email, password):
    user = Users(
        last_name=last_name,
        first_name=first_name,
        email=email,
        password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def get_user_via_salt(db, salt: str):
    user_sess = db.query(UserSessions).filter(UserSessions.salt == salt).first()
    if user_sess:
        return user_sess.user
    return None


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


async def get_employees(db, page: int, per_page: int, org_id: str):
    try:
        # Calculate offset
        offset = (page - 1) * per_page

        # Query to get employees for the specified organization, ordered by created_at
        emps = (
            db.query(Users)
            .filter(Users.organization_id == org_id)
            .order_by(desc(Users.created_at))  # Order by created_at in descending order
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Optionally, you can also return the total count of employees for the organization
        total_count = db.query(Users).filter(Users.organization_id == org_id).count()

        return {
            "employees": [
                emp.to_dict_2() for emp in emps
            ],  # Assuming you have a to_dict method
            "total_items": total_count,
            "total_pages": (total_count + per_page - 1) // per_page,
            "page": page,
            "per_page": per_page,
        }
    except Exception as e:
        logger.exception(e)
        return {}


async def get_one_employee(db, user_id, organization_id):
    user = (
        db.query(Users).filter_by(id=user_id, organization_id=organization_id).first()
    )
    return user


async def email_exists_in_org(db, email: str, org_id: str):
    return (
        db.query(Users)
        .filter(Users.email == email, Users.organization_id == org_id)
        .first()
    )


async def create_one_employee(
    db, last_name, first_name, email, date_joined, organization_id
):
    user = Users(
        last_name=last_name,
        first_name=first_name,
        email=email,
        organization_id=organization_id,
        date_joined=date_joined,
        password=hash_password(DEFAULT_PASSWORD),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


async def create_or_update_user_session(db, user, otp=None, token=None):
    user_session = db.query(UserSessions).filter_by(user_id=user.id).first()

    if not user_session:
        user_session = UserSessions(user_id=user.id)
        db.add(user_session)
    user_session.token = token
    user_session.used = False
    user_session.expired_at = datetime.now() + timedelta(minutes=SESSION_EXPIRES)
    db.commit()
    return user_session


# get all industries
async def get_all_industries(db):
    # get the ones not deleted and order by name
    return (
        db.query(Industry)
        .filter(Industry.deleted == False)
        .order_by(Industry.name)
        .all()
    )


# get all reasons
async def get_all_reasons(db):
    # get the ones not deleted and order by name
    return (
        db.query(Reasons).filter(Reasons.deleted == False).order_by(Reasons.name).all()
    )


# extract user_id from request for rate limit
def get_user_id_from_request(request: Request):
    user_id = request.state.user_id
    logger.info(f"user_id: {user_id}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


async def create_organization(
    name, domain, size, industry, role_id, role, reason_id, current_user, db
):
    if current_user.organization_id:
        current_user.organization.name = name or current_user.organization.name
        current_user.organization.domain = domain or current_user.organization.domain
        current_user.organization.size = size or current_user.organization.size
        current_user.organization.industry = (
            industry or current_user.organization.industry
        )
        current_user.organization.reason_id = (
            reason_id or current_user.organization.reason_id
        )
        current_user.role_id = (
            role_id
            if role_id
            else create_role(db, role).id if role else current_user.role_id
        )
        db.commit()
        return current_user.organization

    organization = Organization(
        name=name,
        domain=domain,
        size=size,
        industry=industry,
        reason_id=reason_id,
    )
    db.add(organization)
    logger.info(f"organization: {organization}")
    print(f"organizationID: {organization.id}")
    current_user.role_id = (
        role_id
        if role_id
        else create_role(db, role).id if role else current_user.role_id
    )
    current_user.organization = organization
    db.commit()
    db.refresh(organization)
    return organization


def create_role(db, name):
    existing_role = db.query(Roles).filter(Roles.name.ilike(name)).first()
    if existing_role:
        return existing_role
    role = Roles(name=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


# get side mennus
# async def get_side_menus(db):
#     menus = (
#         db.query(SideMenu)
#         .filter(SideMenu.deleted == False)
#         .order_by(SideMenu.tag)
#         .all()
#     )
#     return [menu.to_dict() for menu in menus]


# get roles
async def get_roles(db):
    roles = db.query(Roles).order_by(Roles.name).all()
    return roles


# def save_default_side_menus(db):
#     # Sample JSON data
#     side_menus = [
#         {
#             "name": "Dashboard",
#             "icon_url": "https://example.com/icons/dashboard.png",
#             "tag": 1,
#             "description": "Access to the main dashboard.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Employees",
#             "tag": 2,
#             "icon_url": "https://example.com/icons/users.png",
#             "description": "Manage users and their roles.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Admins",
#             "tag": 10,
#             "icon_url": "https://example.com/icons/users.png",
#             "description": "Manage users and their roles.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Settings",
#             "tag": 7,
#             "icon_url": "https://example.com/icons/settings.png",
#             "description": "Configure application settings.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Reports",
#             "tag": 9,
#             "icon_url": "https://example.com/icons/reports.png",
#             "description": "View and generate reports.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Notifications",
#             "tag": 4,
#             "icon_url": "https://example.com/icons/notifications.png",
#             "description": "Manage notifications and alerts.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Analytics",
#             "tag": 3,
#             "icon_url": "https://example.com/icons/analytics.png",
#             "description": "View analytics and statistics.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Events",
#             "tag": 5,
#             "icon_url": "https://example.com/icons/events.png",
#             "description": "Access and manage events.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Projects",
#             "tag": 6,
#             "icon_url": "https://example.com/icons/projects.png",
#             "description": "Manage projects and tasks.",
#             "sub_side_menus": [],
#         },
#         {
#             "name": "Help",
#             "tag": 8,
#             "icon_url": "https://example.com/icons/help.png",
#             "description": "Access help and documentation.",
#             "sub_side_menus": [],
#         },
#     ]
#
#     # Save data to the database
#     for menu in side_menus:
#         # Check if a SideMenu with the same name already exists
#         existing_menu = (
#             db.query(SideMenu).filter(SideMenu.name.ilike(menu["name"])).first()
#         )
#
#         if not existing_menu:  # If no existing entry found, add it
#             side_menu = SideMenu(
#                 name=menu["name"],
#                 icon=menu["icon_url"],
#                 tag=menu["tag"],
#                 description=menu.get("description"),  # Use get to avoid KeyError
#             )
#             db.add(side_menu)
#
#             for sub_menu in menu.get("sub_side_menus", []):  # Use get to avoid KeyError
#                 if (
#                     not db.query(SubSideMenu)
#                     .filter(SubSideMenu.name.ilike(sub_menu["name"]))
#                     .first()
#                 ):
#                     sub_side_menu = SubSideMenu(
#                         name=sub_menu["name"], side_menu_id=side_menu.id
#                     )
#                     db.add(sub_side_menu)
#
#     # Commit the session after the loop to save all changes at once
#     db.commit()
#
#     return side_menus


# save default role
async def save_default_roles(db):
    roles = [
        {"name": "Super Admin"},
        {"name": "Admin"},
        {"name": "Human Resources"},
        {"name": "Staff"},
    ]
    for role in roles:
        create_role(db, role["name"])

    return roles


# def create_sub_side_menu(db, name, side_menu_id):
#     sub_side_menu = SubSideMenu(name=name, side_menu_id=side_menu_id)
#     db.add(sub_side_menu)
#     db.commit()
#     db.refresh(sub_side_menu)
#     return sub_side_menu


async def get_steps(db, current_user):
    steps = {"first_step": False if not current_user.organization_id else True}
    org = (
        db.query(Organization)
        .filter(Organization.id == current_user.organization_id)
        .first()
    )
    steps["first_step"] = (
        False if not org or not all([org.name, org.domain, org.size]) else True
    )
    steps["second_step"] = False if not org or not org.industry else True
    steps["third_step"] = False if not current_user.role_id else True
    steps["fourth_step"] = False if not org or not org.reason_id else True
    return steps


async def construct_employee_details(user):
    general = {
        "fullname": f"{user.first_name} {user.last_name}",
        "gender": user.user_profile.gender if user.user_profile else "",
        "email": user.email,
        "nationality": user.user_profile.country if user.user_profile else "",
        "phone_number": user.phone_number,
        "health_care": (
            user.health_insurance.health_insurance if user.health_insurance else ""
        ),
        "address": user.user_profile.address if user.user_profile else "",
        "postal_code": user.user_profile.postal_code if user.user_profile else "",
        "state": user.user_profile.state if user.user_profile else "",
        "city": user.user_profile.city if user.user_profile else "",
        "country": user.user_profile.country if user.user_profile else "",
        "marital_status": user.user_profile.marital_status if user.user_profile else "",
        "personal_tax_id": user.user_profile.tax_id if user.user_profile else "",
        "date_of_birth": user.user_profile.date_of_birth if user.user_profile else "",
        "social_insurance": (
            user.health_insurance.health_insurance_number
            if user.health_insurance
            else ""
        ),
        "emergency_contact_last_name": (
            user.emergency_contact.last_name if user.emergency_contact else ""
        ),
        "emergency_contact_first_name": (
            user.emergency_contact.first_name if user.emergency_contact else ""
        ),
        "emergency_contact_relationship": (
            user.emergency_contact.relationship if user.emergency_contact else ""
        ),
        "emergency_contact_phone_number": (
            user.emergency_contact.phone_number if user.emergency_contact else ""
        ),
        "emergency_contact_email": (
            user.emergency_contact.email if user.emergency_contact else ""
        ),
    }

    job = {
        "employee_id": (
            user.employment_details.employment_id if user.employment_details else ""
        ),
        "service_year": get_service_year(user.employment_details.join_date),
        "join_date": (
            user.employment_details.join_date if user.employment_details else ""
        ),
    }

    payroll = {
        "employment_status": (
            user.employment_details.employment_status.value
            if user.employment_details
            else ""
        ),
        "job_title": (
            user.employment_details.job_title if user.employment_details else ""
        ),
        "employment_type": (
            user.employment_details.employment_type.value
            if user.employment_details
            else ""
        ),
        "work_mode": (
            user.employment_details.work_mode.value if user.employment_details else ""
        ),
        "compensation": (
            [comp.to_dict() for comp in user.compensation] if user.compensation else []
        ),
    }

    document = {
        "personal": (
            [
                doc.to_dict()
                for doc in user.uploaded_files
                if doc.file_type == FileType.PERSONAL
            ]
            if user.uploaded_files
            else []
        ),
        "payslip": (
            [
                doc.to_dict()
                for doc in user.uploaded_files
                if doc.file_type == FileType.PAYSLIP
            ]
            if user.uploaded_files
            else []
        ),
    }

    return {"general": general, "job": job, "payroll": payroll, "document": document}


async def edit_employee_details(user, edit_type, data, db):
    try:
        logger.info(f"Edit Type in function: {edit_type}")
        if edit_type == "general":
            full_name = data.get("fullname")
            if full_name:
                user.first_name = full_name.split(" ")[0]
                user.last_name = full_name.split(" ")[1]
            email = data.get("email")
            if email:
                # check if email exist
                if (
                    await email_exists_in_org(db, email, user.organization_id)
                    and email != user.email
                ):
                    return "Email already exists in this organization"
                user.email = email
            phone_number = data.get("phone_number")
            if phone_number:
                # validate phone number and check if phone number exist
                if validate_phone_number(phone_number):
                    return "Invalid phone number"
                if (
                    await phone_number_exists(db, phone_number)
                    and phone_number != user.phone_number
                ):
                    return "Phone number already exist"
                user.phone_number = phone_number
            if data.get("gender"):
                user.user_profile.gender = Gender(data.get("gender").lower())
            user.user_profile.country = data.get(
                "nationality", user.user_profile.country
            )
            if data.get("marital_status"):
                user.user_profile.marital_status = MaritalStatus(
                    data.get("marital_status").lower()
                )
            user.user_profile.tax_id = data.get(
                "personal_tax_id", user.user_profile.tax_id
            )
            user.user_profile.date_of_birth = data.get(
                "date_of_birth", user.user_profile.date_of_birth
            )
            user.user_profile.postal_code = data.get(
                "postal_code", user.user_profile.postal_code
            )
            user.user_profile.state = data.get("state", user.user_profile.state)
            user.user_profile.city = data.get("city", user.user_profile.city)
            user.user_profile.country = data.get("country", user.user_profile.country)
            user.health_insurance.health_insurance = data.get(
                "health_care", user.health_insurance.health_insurance
            )
            user.health_insurance.health_insurance_number = data.get(
                "social_insurance", user.health_insurance.health_insurance_number
            )
            user.user_profile.address = data.get("address", user.user_profile.address)
            user.emergency_contact.first_name = data.get(
                "emergency_contact_first_name", user.emergency_contact.first_name
            )
            user.emergency_contact.last_name = data.get(
                "emergency_contact_last_name", user.emergency_contact.last_name
            )
            emergency_contact_phone_number = data.get("emergency_contact_phone_number")
            if emergency_contact_phone_number:
                if validate_phone_number(emergency_contact_phone_number):
                    return "Invalid phone number"
                user.emergency_contact.phone_number = emergency_contact_phone_number
            emergency_contact_email = data.get("emergency_contact_email")
            if emergency_contact_email:
                res, _ = await validate_correct_email(emergency_contact_email)
                if not res:
                    return "Invalid email"
                user.emergency_contact.email = emergency_contact_email
            emergency_contact_relationship = data.get("emergency_contact_relationship")
            if emergency_contact_relationship:
                user.emergency_contact.relationship = Relationship(
                    emergency_contact_relationship.lower()
                )

            db.commit()
        elif edit_type == "job":
            user.employment_details.job_title = data.get(
                "job_title", user.employment_details.job_title
            )
            user.employment_details.employment_type = data.get(
                "employment_type", user.employment_details.employment_type
            )
            user.employment_details.work_mode = data.get(
                "work_mode", user.employment_details.work_mode
            )
            user.employment_details.join_date = data.get(
                "join_date", user.employment_details.join_date
            )
            # emplyee id
            user.employment_details.employment_id = data.get(
                "employment_id", user.employment_details.employment_id
            )
            db.commit()
        elif edit_type == "payroll":
            employment_details_employment_status = data.get("employment_status")
            if employment_details_employment_status:
                user.employment_details.employment_status = EmploymentStatus(
                    employment_details_employment_status.lower()
                )
            user.employment_details.job_title = data.get(
                "job_title", user.employment_details.job_title
            )
            employment_details_employment_type = data.get("employment_type")
            if employment_details_employment_type:
                user.employment_details.employment_type = EmploymentType(
                    employment_details_employment_type.lower()
                )
            employment_details_work_mode = data.get("work_mode")
            if employment_details_work_mode:
                user.employment_details.work_mode = WorkMode(
                    employment_details_work_mode.lower()
                )
            db.commit()
        else:
            return "Invalid Type"

        return None
    except Exception as e:
        logger.exception("traceback error from edit employee details")
        return "Error editing emaployee"


def create_remain(user_id: str):
    from database import get_db

    # Get an actual session from the generator
    db_gen = get_db()  # This returns a generator
    db = next(db_gen)  # Get the session object from generator

    try:
        logger.info("Remain created start, user_id: %s", user_id)

        em = EmploymentDetails(user_id=user_id)
        emg = EmergencyContact(user_id=user_id)
        hih = HealthInsurance(user_id=user_id)
        bd = BankDetails(user_id=user_id)
        up = UserProfile(user_id=user_id)

        db.add_all([em, emg, hih, bd, up])
        db.commit()

        logger.info("Remain created successfully for user %s", user_id)
    except Exception as e:
        db.rollback()
        logger.error("Background task failed")
    finally:
        try:
            next(
                db_gen
            )  # Closes the generator (executes the finally block in get_db())
        except StopIteration:
            pass  # Generator is already exhausted


async def create_compensation(db, user_id, compensation_type, amount):
    try:
        logger.info(
            f"UserID: {user_id}, CompType: {compensation_type}, Amount: {amount}"
        )
        if not compensation_type:
            return False
        existing_compensation = (
            db.query(Compensation)
            .filter_by(user_id=user_id, compensation_type=compensation_type)
            .first()
        )

        if existing_compensation:
            existing_compensation.amount = amount or existing_compensation.amount
            db.commit()
            return existing_compensation

        compensation = Compensation(
            user_id=user_id,
            compensation_type=compensation_type,
            amount=amount,
        )
        db.add(compensation)
        db.commit()
        logger.info(f"Done saving {compensation_type}")
        return compensation
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


# create/edit uploaded files
# the id will be optional, if its available, check if thr filr exists and update it
async def create_edit_uploaded_files(
    db, user_id, file_name, file_url, file_type, upload_id=None
):
    try:
        if upload_id:
            uploaded_file = (
                db.query(UploadedFiles).filter_by(id=upload_id, user_id=user_id).first()
            )
            if not uploaded_file:
                return None
            uploaded_file.file_name = file_name
            uploaded_file.file_url = file_url
            uploaded_file.file_type = FileType(file_type)
            db.commit()
            return uploaded_file
        uploaded_file = UploadedFiles(
            user_id=user_id,
            file_name=file_name,
            file_url=file_url,
            file_type=FileType(file_type),
        )
        db.add(uploaded_file)
        db.commit()
        return uploaded_file
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


async def get_leave_requests(
    db,
    organization_id,
    start_date,
    end_date,
    leave_status,
    leave_type,
    page,
    per_page,
    user=None,
):
    try:
        # Base query
        base_query = (
            db.query(LeaveRequest)
            .join(Users, LeaveRequest.user_id == Users.id)
            .filter(Users.organization_id == organization_id)
        )

        # Filters
        if user:
            base_query = base_query.filter(LeaveRequest.user_id == user.id)
        if start_date:
            base_query = base_query.filter(LeaveRequest.start_date >= start_date)
        if end_date:
            base_query = base_query.filter(LeaveRequest.end_date <= end_date)
        if leave_status:
            base_query = base_query.filter(
                LeaveRequest.status == LeaveStatus(leave_status)
            )
        if leave_type:
            base_query = base_query.filter(LeaveRequest.leave_type_id == leave_type)

        # Count total items BEFORE pagination
        total_items = base_query.count()

        # Apply pagination
        leave_requests = base_query.offset((page - 1) * per_page).limit(per_page).all()

        # Calculate total pages
        total_pages = (total_items + per_page - 1) // per_page  # Ceiling division

        return {
            "data": [lr.to_dict() for lr in leave_requests],
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
        }

    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


async def get_one_leave_type(db, leave_type_id):
    return db.query(LeaveType).filter_by(id=leave_type_id).first()


# save leave request
async def save_leave_request(
    db, user_id, leave_type_id, start_date, end_date, note, document_url, document_name
):
    try:
        leave_request = LeaveRequest(
            user_id=user_id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            note=note,
            document_url=document_url,
            document_name=document_name,
        )
        db.add(leave_request)
        db.commit()
        return leave_request
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


async def get_all_leave_types(db, organization_id):
    try:
        leave_types = (
            db.query(LeaveType)
            .filter_by(organization_id=organization_id)
            .order_by(asc(LeaveType.name))
            .all()
        )
        return leave_types
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


# create leave type
async def create_leave_type(db, organization_id, leave_type_name, leave_type_duration):
    try:
        if (
            db.query(LeaveType)
            .filter(
                LeaveType.organization_id == organization_id,
                LeaveType.name.ilike(leave_type_name),
            )
            .first()
        ):
            return None
        leave_type = LeaveType(
            organization_id=organization_id,
            name=leave_type_name,
            duration=leave_type_duration,
        )
        db.add(leave_type)
        db.commit()
        return leave_type
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


# create holiday
async def create_holiday(db, organization_id, name, from_date, to_date):
    try:
        holiday = Holiday(
            organization_id=organization_id,
            name=name,
            from_date=from_date,
            to_date=to_date,
        )
        db.add(holiday)
        db.commit()
        return holiday
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


# holiday already exist
async def holiday_exists(db, organization_id, name):
    try:
        holiday = (
            db.query(Holiday)
            .filter(
                Holiday.organization_id == organization_id, Holiday.name.ilike(name)
            )
            .first()
        )
        return holiday
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


# get one holiday by id
async def get_one_holiday(db, holiday_id, organization_id):
    try:
        holiday = (
            db.query(Holiday)
            .filter_by(id=holiday_id, organization_id=organization_id)
            .first()
        )
        return holiday
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


# get holidays, order by from_date desc
async def get_holidays(db, organization_id):
    try:
        holidays = (
            db.query(Holiday)
            .filter_by(organization_id=organization_id)
            .order_by(desc(Holiday.from_date))
            .all()
        )
        return holidays
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


async def get_work_hours(db, organization_id):
    try:
        work_hours = (
            db.query(WorkHours).filter_by(organization_id=organization_id).first()
        )
        return work_hours
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


async def set_work_hours(db, organization_id, start_time, end_time):
    try:
        work_hrs = await get_work_hours(db, organization_id)
        if work_hrs:
            work_hrs.start_time = start_time
            work_hrs.end_time = end_time
            db.commit()
            return work_hrs
        work_hours = WorkHours(
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time,
        )
        db.add(work_hours)
        db.commit()
        return work_hours
    except Exception as e:
        db.rollback()
        logger.exception("Background task failed")
        return None


# get current clock in record (so that the user can clock out) for that day
async def get_current_clock_in(db, user_id):
    try:
        attendance = (
            db.query(Attendance)
            .filter(
                Attendance.user_id == user_id,
                func.date(Attendance.created_at) == date.today(),
                Attendance.check_in.isnot(None),
                Attendance.check_out.is_(None),
            )
            .first()
        )
        return attendance
    except Exception as e:
        db.rollback()
        logger.exception("Get current clock_in failed")
        return None


# create attendace
async def create_attendance(db, user_id, note, action, location, organization_id):
    try:
        attendance = await get_current_clock_in(db, user_id)
        if attendance:
            if action == "clock_in":
                attendance.check_in = datetime.now().time()
                attendance.clock_in_location = location
            else:
                attendance.check_out = datetime.now().time()
                attendance.clock_out_location = location
            db.commit()
            return attendance
        wrk_hrs = await get_work_hours(db, organization_id)
        attendance = Attendance(
            user_id=user_id,
            note=note,
            check_in=datetime.now().time() if action == "clock_in" else None,
            check_out=datetime.now().time() if action == "clock_out" else None,
            clock_in_location=location if action == "clock_in" else None,
            clock_out_location=location if action == "clock_out" else None,
            start_time=wrk_hrs.start_time,
            end_time=wrk_hrs.end_time,
        )
        db.add(attendance)
        db.commit()
        return attendance
    except Exception as e:
        db.rollback()
        logger.exception("Create attendance failed")
        return None


# has clocked out today already
async def has_clocked_out_today(db, user_id):
    try:
        attendance = (
            db.query(Attendance)
            .filter(
                Attendance.user_id == user_id,
                func.date(Attendance.created_at) == date.today(),
                Attendance.check_in.isnot(None),
                Attendance.check_out.isnot(None),
            )
            .first()
        )
        return attendance
    except Exception as e:
        db.rollback()
        logger.exception("Has clocked out today failed")
        return None


# has attendace today already
async def has_attendance_today(db, user_id):
    try:
        attendance = (
            db.query(Attendance)
            .filter(
                Attendance.user_id == user_id,
                func.date(Attendance.created_at) == date.today(),
            )
            .first()
        )
        return attendance
    except Exception as e:
        db.rollback()
        logger.exception("Has attendance today failed")
        return None


# get my attendace and order by desc created_at
async def get_my_attendance(
    db, user_id, page, per_page, start_date=None, end_date=None, hr=False
):
    try:
        query = db.query(Attendance).filter(Attendance.user_id == user_id)

        if start_date:
            query = query.filter(Attendance.created_at >= start_date)
        if end_date:
            query = query.filter(Attendance.created_at <= end_date)

        total_items = query.count()
        total_pages = (total_items + per_page - 1) // per_page

        attendance_records = (
            query.order_by(desc(Attendance.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        attendance_dicts = [record.employee_dict(hr) for record in attendance_records]

        response = {
            "data": attendance_dicts,
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
        }

        return response

    except Exception as e:
        db.rollback()
        logger.exception("Get my attendance failed")
        return None


async def get_compensation_paginated(
    db, page: int, per_page: int, organization_id: str
):
    """
    Get paginated compensation matrix filtered by organization_id
    Using LEFT JOIN for employment details
    """

    # Step 1: Get all distinct compensation types for this organization
    type_subquery = (
        db.query(Compensation.compensation_type)
        .join(Users, Users.id == Compensation.user_id)
        .filter(
            Compensation.compensation_type.isnot(None),
            Users.organization_id == organization_id,
        )
        .distinct()
        .subquery()
    )

    # Step 2: Get users count for pagination
    users_count = (
        db.query(func.count(Users.id))
        .filter(
            Users.organization_id == organization_id,
            Users.id.in_(db.query(Compensation.user_id).distinct()),
        )
        .scalar()
    )

    if not users_count:
        return {
            "data": [],
            "types": [],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": 0,
                "pages": 0,
                "has_next": False,
                "has_prev": False,
            },
        }

    # Step 3: Get compensation types
    types_result = db.query(type_subquery.c.compensation_type).all()
    compensation_types = [t[0] for t in types_result]

    # Step 4: Build CASE statements for each compensation type
    case_statements = []
    for comp_type in compensation_types:
        case_stmt = func.sum(
            case(
                (Compensation.compensation_type == comp_type, Compensation.amount),
                else_=0,
            )
        ).label(comp_type)
        case_statements.append(case_stmt)

    # Add total amount
    case_statements.append(func.sum(Compensation.amount).label("total_amount"))

    # Step 5: Main query with organization filter - Using LEFT OUTER JOIN
    query = (
        db.query(
            Compensation.user_id,
            Users.first_name,
            Users.last_name,
            Users.email,
            EmploymentDetails.employment_id,
            *case_statements,
        )
        .join(Users, Users.id == Compensation.user_id)
        .outerjoin(
            EmploymentDetails, EmploymentDetails.user_id == Users.id
        )  # LEFT JOIN
        .filter(Users.organization_id == organization_id)
        .group_by(
            Compensation.user_id,
            Users.first_name,
            Users.last_name,
            Users.email,
            EmploymentDetails.employment_id,
            Users.date_joined,
        )
        .order_by(desc(Users.date_joined))
    )

    # Step 6: Apply pagination
    offset = (page - 1) * per_page
    results = query.offset(offset).limit(per_page).all()

    # Step 7: Format results
    data = []
    for row in results:
        user_id = row[0]
        first_name = row[1]
        last_name = row[2]
        email = row[3]
        employment_id = row[4]  # Could be None if LEFT JOIN doesn't find a match
        full_name = (
            f"{first_name} {last_name}".strip() if first_name or last_name else ""
        )

        compensations = {}

        # Compensation types start at index 5
        for i, comp_type in enumerate(compensation_types):
            amount = row[i + 5] or 0
            compensations[comp_type] = float(amount)

        total = float(row[-1] or 0)

        data.append(
            {
                "user_id": user_id,
                "full_name": full_name,
                "email": email,
                "employment_id": employment_id,
                "compensations": compensations,
                "total": total,
            }
        )

    # Step 8: Calculate pagination info
    total_pages = (users_count + per_page - 1) // per_page if users_count > 0 else 0
    redis_conn.set("compensation_types", json.dumps(compensation_types))

    return {
        "data": data,
        "types": compensation_types,
        "page": page,
        "per_page": per_page,
        "total": users_count,
        "pages": total_pages,
    }


async def get_user_pay_roll(db, user_id):
    try:
        # 1. Get compensation types from Redis
        comp_cached = redis_conn.get("compensation_types")
        if comp_cached is None:
            return []

        compensations = json.loads(comp_cached)
        if not compensations:
            return []

        # 2. Query user's compensations
        users_comps = (
            db.query(Compensation)
            .filter_by(user_id=user_id)
            .order_by(Compensation.compensation_type.asc())
            .all()
        )

        if not users_comps:
            # Return zero entries for all compensation types
            return [{"compensation_type": comp, "amount": 0} for comp in compensations]

        # 3. Convert to dict and build lookup set
        comp_list = [comp.to_dict() for comp in users_comps]

        existing_types = {comp.get("compensation_type") for comp in comp_list}
        comp_list.extend(
            [
                {"compensation_type": comp, "amount": 0}
                for comp in compensations
                if comp not in existing_types
            ]
        )

        comp_list.sort(key=lambda x: list(x.keys())[0])

        return comp_list

    except Exception as e:
        logger.exception(f"Error in get_user_pay_roll for user {user_id}: {e}")
        return []


async def get_attendance_date_range(db, user_id):
    """Get first and last attendance dates for a user and total duration"""
    # Get first attendance date
    first_attendance = (
        db.query(Attendance.created_at)
        .filter_by(user_id=user_id)
        .order_by(Attendance.created_at.asc())
        .first()
    )

    # Get last attendance date
    last_attendance = (
        db.query(Attendance.created_at)
        .filter_by(user_id=user_id)
        .order_by(Attendance.created_at.desc())
        .first()
    )

    if not first_attendance or not last_attendance:
        return {"duration": "-", "total_duration": 0}

    first_date = first_attendance[0].date() if first_attendance[0] else None
    last_date = last_attendance[0].date() if last_attendance[0] else None

    if first_date and last_date:
        total_duration = (last_date - first_date).days + 1  # Inclusive
    else:
        total_duration = 0

    return {"duration": {first_date} - {last_date}, "total_duration": total_duration}


# get user by user_id
async def get_user_by_id(db, user_id):
    return db.query(Users).filter_by(id=user_id).first()


# create job postings
async def create_job_postings(
    db,
    title,
    description,
    location,
    job_type,
    quantity,
    department_id,
    organization_id,
    closing_date,
    min_salary=0,
    max_salary=0,
):
    job_post = JobPosting(
        title=title,
        description=description,
        location=location,
        job_type=job_type,
        quantity=quantity,
        department_id=department_id,
        organization_id=organization_id,
        closing_date=closing_date,
        min_salary=min_salary,
        max_salary=max_salary,
    )
    db.add(job_post)
    db.commit()
    return job_post


# edit job postings
async def edit_job_postings(
    db,
    job_post_id,
    title,
    description,
    location,
    job_type,
    quantity,
    department_id,
    organization_id,
    closing_date,
    min_salary,
    max_salary,
    status,
):
    job_post = await get_one_job_posting(db, job_post_id, organization_id)
    job_post.title = title or job_post.title
    job_post.description = description or job_post.description
    job_post.location = location or job_post.location
    job_post.job_type = job_type or job_post.job_type
    job_post.quantity = quantity or job_post.quantity
    if min_salary:
        job_post.min_salary = min_salary
    if max_salary:
        job_post.max_salary = max_salary
    job_post.status = status or job_post.status
    job_post.department_id = department_id or job_post.department_id
    if closing_date:
        job_post.closing_date = closing_date
    db.add(job_post)
    db.commit()
    return job_post


# get one job posting
async def get_one_job_posting(db, job_post_id, organization_id):
    return (
        db.query(JobPosting)
        .filter_by(id=job_post_id, organization_id=organization_id)
        .first()
    )


# get all job posts
async def get_job_postings(
    db,
    status,
    job_type,
    department_id,
    organization_id,
    page,
    per_page,
    start_date,
    end_date,
):
    try:
        query = db.query(JobPosting).filter_by(organization_id=organization_id)
        if status:
            query = query.filter_by(status=status)
        if job_type:
            query = query.filter_by(job_type=job_type)
        if department_id:
            query = query.filter_by(department_id=department_id)
        if start_date:
            query = query.filter(JobPosting.created_at >= start_date)
        if end_date:
            query = query.filter(JobPosting.created_at <= end_date)

        total_count = query.count()

        offset = (page - 1) * per_page
        total_pages = (total_count + per_page - 1) // per_page

        job_postings = (
            query.order_by(desc(JobPosting.created_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )

        return {
            "postings": [job_post.to_dict() for job_post in job_postings],
            "total_items": total_count,
            "total_pages": total_pages,
            "page": page,
            "per_page": per_page,
        }
    except Exception as e:
        logger.exception(f"Error in get_job_postings: {e}")
        return {
            "postings": [],
            "total_items": 0,
            "total_pages": 0,
            "page": 0,
            "per_page": 0,
        }


# get departments
async def get_departments(db, organization_id):
    result = (
        db.query(Department)
        .filter_by(organization_id=organization_id)
        .order_by(Department.name.asc())
        .all()
    )
    return [department.to_dict() for department in result]


# department exist
async def department_exists(db, name, organization_id):
    return (
        db.query(Department)
        .filter(
            Department.name.ilike(name), Department.organization_id == organization_id
        )
        .first()
    )


# create one department
async def create_one_dpt(db, organization_id, name):
    dpt = Department(name=name, organization_id=organization_id)
    db.add(dpt)
    db.commit()
    return dpt
