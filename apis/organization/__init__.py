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
    get_side_menus,
)
from helpers import (
    validate_phone_number,
    validate_password,
    hash_password,
    verify_password,
)
from schemas import ShowOrgSchema, MiscMenuSchema
from database import get_db
import traceback
from utils.rate_limit import limiter
from logger import logger


org_router = APIRouter(prefix="/org", tags=["Organizations"])


# default roles
@org_router.get(
    "/get_organization",
    status_code=status.HTTP_200_OK,
    response_model=ShowOrgSchema,
)
async def get_organization(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        org = await check_if_org_in_orgtable(db)
        return {"organization": org}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get organization")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get organization")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get_side_menus
@org_router.get(
    "/get_side_menus",
    status_code=status.HTTP_200_OK,
    # response_model=MiscMenuSchema,
)
async def get_all_side_menus(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        menus = await get_side_menus(db)
        return {"data": menus}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get side menu")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get side menu")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
