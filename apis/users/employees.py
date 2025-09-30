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
from sqlalchemy.orm import Session
from models import Users
from cruds import (
    get_employees,
    create_one_employee,
    email_exists_in_org,
    get_one_employee,
    construct_employee_details,
    create_remain,
    edit_employee_details
)
from helpers import (
    validate_phone_number,
    validate_password,
    hash_password,
    verify_password,
    validate_correct_email,
)
from schemas import CreateEmployeeSchema
from typing import List
from database import get_db
from utils import limiter
from logger import logger
from connections import redis_conn
import json
from apis.users import user_router
from datetime import datetime
from decorators import cache_it


emp_tag = "Employees"


@user_router.get(
    "/employees",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
    # response_model=List[MiscRoleSchema],
)
@cache_it("employees", org=True)
async def get_all_employees(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0),
):
    try:
        employees = await get_employees(
            db, page, per_page, current_user.organization_id
        )
        return employees
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get employees")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get employees")
        logger.error(f"{e} : error from get employees")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get one employee
@user_router.get(
    "/employee/{employee_id}",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
)
# @cache_it("employee", user=True)
async def get_employee(
    employee_id: str,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        employee = await get_one_employee(db, employee_id, current_user.organization_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )
        employee_dict = await construct_employee_details(employee)
        return employee_dict
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get one employee")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get one employee")
        logger.error(f"{e} : error from get one employee")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# create employee
@user_router.post(
    "/create_employee",
    status_code=status.HTTP_201_CREATED,
    tags=[emp_tag],
)
async def create_employee(
    request_data: CreateEmployeeSchema,
    background_tasks: BackgroundTasks,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        first_name = request_data.first_name
        last_name = request_data.last_name
        email = request_data.email
        date_joined = request_data.date_joined

        res = await validate_correct_email(email)
        logger.info(f"res: {res}")

        if not res[0]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res[1])

        # convert date_joined to datetime and make sure its in this format YYYY-MM-DD
        try:
            date_joined = datetime.strptime(date_joined, "%Y-%m-%d")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="date joined must be in this format YYYY-MM-DD",
            )

        # if email exists
        if await email_exists_in_org(db, res[1], current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists in this organization",
            )

        user = await create_one_employee(
            db, last_name, first_name, res[1], date_joined, current_user.organization_id
        )
        background_tasks.add_task(create_remain, user.id)
        return {"detail": "Successful", "user_id": user.id}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from create employee")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from create employee")
        logger.error(f"{e} : error from create employee")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# edit employee
@user_router.put(
    "/edit_employee/{employee_id}",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
)
async def edit_employee(
    employee_id: str,
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        edit_type: str = data.get("edit_type")
        data: dict = data.get("data")

        logger.info(f"Edit Type: {edit_type}: Data:{data}")

        if edit_type not in {"general", "job", "payroll"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid edit type",
            )
        employee = await get_one_employee(db, employee_id, current_user.organization_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )
        
        res = await edit_employee_details(employee, edit_type, data, db)
        if res:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=res
        )
        return {"detail": "Successful"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from edit employee")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from edit employee")
        logger.error(f"{e} : error from edit employee")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
