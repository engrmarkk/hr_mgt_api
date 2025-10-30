from fastapi import APIRouter, status, Depends, HTTPException, Request
from security import get_current_user
from sqlalchemy.orm import Session
from database import get_db
import traceback
from models import Users
from utils.rate_limit import limiter
from logger import logger
from cruds import create_leave_type
from constants import EXCEPTION_MESSAGE


admin_router = APIRouter(prefix="/admin", tags=["Admins"])


@admin_router.post("/create_leave_type", status_code=status.HTTP_200_OK)
async def create_leavetype(
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        leave_type_name = data.get("name")
        leave_type_duration = data.get("duration")
        leave_type = await create_leave_type(
            db, current_user.organization_id, leave_type_name, int(leave_type_duration)
        )
        return {"msg": "Leave type created successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from login")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )
