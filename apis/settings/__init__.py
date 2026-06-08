from fastapi import APIRouter
import json
from schemas import EditCompanySchema, CreateDepartmentSchema
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
from cruds import (
    get_department_tree,
    get_one_dept,
    edit_one_department,
    create_one_department,
    department_exists,
)

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


# department tree
@settings_router.get("/department_tree", tags=[settings_tag])
async def get_depart_tree(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        print("current_user", current_user.organization_id)
        dpt_tree = await get_department_tree(db, current_user.organization_id)
        return {"detail": "Department tree fetched successfully", "data": dpt_tree}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get dept tree")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get dept tree")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# edit one department
@settings_router.patch("/edit_one_department/{dept_id}", tags=[settings_tag])
async def edit_a_department(
    dept_id: str,
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        position = data.get("position")
        parent_id = data.get("parent_id")

        # if dept id exist
        dpt_exist = await get_one_dept(db, dept_id)
        if not dpt_exist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
            )

        if parent_id:
            if not await get_one_dept(db, parent_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent department not found",
                )

        await edit_one_department(db, dept_id, position, parent_id)

        return {"detail": "Department edited successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from edit dept")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from edit dept")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# create department
@settings_router.post("/create_department", tags=[settings_tag])
async def create_department(
    request: CreateDepartmentSchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        name = request.name
        parent_id = request.parent_id

        if await department_exists(db, name, current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Department already exists"
            )

        if not await get_one_dept(db, parent_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent department not found",
            )

        await create_one_department(
            db, current_user.organization_id, name, None, parent_id
        )

        return {"detail": "Department created successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from create department")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from create department")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
