from fastapi import APIRouter, status, Depends, HTTPException, Request
from security import get_current_user
from sqlalchemy.orm import Session
from models import Users
from cruds import (
    get_steps,
    save_user_data,
    phone_number_exists,
    create_organization,
    get_all_reasons,
    create_role,
    check_if_org_in_orgtable,
    get_roles,
    get_all_industries,
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
    CreateOrgSchema
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
    status_code=status.HTTP_200_OK,
    # response_model=List[MiscRoleSchema],
)
async def get_all_roles(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        roles = await get_roles(db)
        return {"data": [role.to_dict() for role in roles]}
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

# get all indeustries
@user_router.get(
    "/get_industries",
    status_code=status.HTTP_200_OK,
)
async def get_industries(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        industries = await get_all_industries(db)
        return {"data": [ind.to_dict() for ind in industries]}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get industries")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get industries")
        logger.error(f"{e} : error from get industries")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get reasons
@user_router.get(
    "/get_reasons",
    status_code=status.HTTP_200_OK,
)
async def get_reasons(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        reasons = await get_all_reasons(db)
        return {"data": [reason.to_dict() for reason in reasons]}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get reasons")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get reasons")
        logger.error(f"{e} : error from get reasons")
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


# create company
@user_router.post(
    "/create_company",
    status_code=status.HTTP_201_CREATED,
)
async def create_company(
    request_data: CreateOrgSchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        name = request_data.name
        domain = request_data.domain
        size = request_data.size
        industry = request_data.industry_id
        role_id = request_data.role_id
        role = request_data.role
        reason_id = request_data.reason_id
        res = await create_organization(
            name, domain, size, industry, role_id, role, reason_id, current_user, db
        )
        return {"detail": "Successful", "steps": await get_steps(db, current_user)}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from create company")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from create company")
        logger.error(f"{e} : error from create company")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


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
