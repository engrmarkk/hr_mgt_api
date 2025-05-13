from fastapi import APIRouter, status, Depends, HTTPException, Request
from security import get_current_user
from sqlalchemy.orm import Session
from models import Users
from cruds import (
    save_user_data,
    phone_number_exists,
    create_organization,
    create_role,
    check_if_org_in_orgtable,
    get_roles,
    save_user_profile,
)
from helpers import (
    validate_phone_number,
    validate_password,
    hash_password,
    verify_password,
)
from schemas import (
    ShowUserSchema,
    CompleteRegSchema,
    ChangePasswordSchema,
    MiscRoleSchema,
)
from typing import List
from database import get_db
from utils import limiter
from logger import logger
from connections import redis_conn
import json


user_router = APIRouter(prefix="/users", tags=["Users"])


# default roles
@user_router.get(
    "/default_roles",
    status_code=status.HTTP_201_CREATED,
    response_model=List[MiscRoleSchema],
)
async def get_all_roles(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        roles = await get_roles(db)
        return roles
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get default role")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get default role")
        logger.error(f"{e} : error from get default role")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


@user_router.get("", status_code=status.HTTP_200_OK, response_model=ShowUserSchema)
# @limiter.limit("1/minute")
async def get_user(
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Who are you?"
        )
    return current_user


@user_router.post(
    "/complete_registration",
    status_code=status.HTTP_200_OK,
)
async def complete_registration(
    user_data: CompleteRegSchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid User"
        )
    if await check_if_org_in_orgtable(db):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration already completed",
        )

    organization_name = user_data.organization_name
    organization_address = user_data.organization_address
    organization_state = user_data.organization_state
    organization_city = user_data.organization_city
    organization_phone = user_data.organization_phone
    organization_email = user_data.organization_email
    organization_website = user_data.organization_website
    organization_country = user_data.organization_country

    first_name = user_data.first_name
    last_name = user_data.last_name
    state = user_data.state
    country = user_data.country
    city = user_data.city
    role = user_data.role
    role_id = user_data.role_id
    phone_number = user_data.phone_number
    address = user_data.address

    if not role_id and not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Role not provided"
        )
    if role and role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can either choose role or you create a new role",
        )

    val_phone = validate_phone_number(phone_number)
    if val_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=val_phone)

    if await phone_number_exists(db, phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Phone number already exists"
        )

    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.phone_number = phone_number
    # current_user.address = address
    # current_user.country = country
    # current_user.state = state
    # current_user.city = city
    current_user.email_verified = True
    if role:
        current_user.role = await create_role(db, role)
    else:
        current_user.role_id = role_id
    await save_user_profile(
        db, current_user.id, address=address, country=country, state=state, city=city
    )
    db.commit()

    await create_organization(
        db,
        organization_name,
        organization_address,
        organization_country,
        organization_state,
        organization_city,
        organization_phone,
        organization_email,
        str(organization_website),
    )

    return {"detail": "User data saved"}


# change password
@user_router.patch(
    "/change_password",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request_data: ChangePasswordSchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        password = request_data.password
        old_password = request_data.old_password
        confirm_password = request_data.confirm_password
        res = verify_password(old_password, current_user.password)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Old password"
            )
        val_res = validate_password(password)
        if val_res:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=val_res)
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
            )
        current_user.password = hash_password(password)
        db.commit()
        return {"detail": "Password changed"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from change password")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from change password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
