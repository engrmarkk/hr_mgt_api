from fastapi import APIRouter
import json
from schemas import EditCompanySchema
from fastapi import (
    APIRouter,
    status,
    Depends,
    HTTPException,
    Request,
    Query,
    BackgroundTasks,
)
from security import get_current_user
from models import Users
from datetime import datetime, timezone
from logger import logger
from database import get_db
from sqlalchemy.orm import Session
from connections import redis_conn

settings_router = APIRouter(prefix="/settings")

settings_tag = "Settings"


@settings_router.patch("/edit_company", tags=[settings_tag])
async def edit_company(
    request: EditCompanySchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        name = request.name
        website = request.website
        phone = request.phone
        email = request.email

        if name:
            current_user.organization.name = name
        if website:
            current_user.organization.website = website
        if phone:
            current_user.organization.phone = phone
        if email:
            current_user.organization.email = email

        db.commit()

        return {"detail": "Company edited successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from edit company")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from edit company")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
