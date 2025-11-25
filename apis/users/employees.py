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
from models import Users, FileType
from cruds import (
    get_employees,
    create_one_employee,
    email_exists_in_org,
    get_one_employee,
    construct_employee_details,
    create_remain,
    edit_employee_details,
    create_compensation,
    create_edit_uploaded_files,
    get_leave_requests,
    get_one_leave_type,
    save_leave_request,
    get_all_leave_types,
    create_holiday,
    holiday_exists,
    get_one_holiday,
    get_holidays,
)
from helpers import (
    validate_phone_number,
    validate_password,
    hash_password,
    verify_password,
    validate_correct_email,
)
from schemas import CreateEmployeeSchema, LeaveRequestSchema
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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
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


# create compensation
@user_router.post(
    "/compensation",
    status_code=status.HTTP_201_CREATED,
    tags=[emp_tag],
)
async def compensation(
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        comps = data.get("compensations", [])
        user_id = data.get("user_id")

        logger.info(f"UserID: {user_id}, comps: {comps}")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user id are required",
            )

        employee = await get_one_employee(db, user_id, current_user.organization_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        for comp in comps:
            logger.info(f"Compensation: {comp}")
            await create_compensation(
                db,
                employee.id,
                compensation_type=comp.get("compensation_type"),
                amount=comp.get("amount"),
            )
        # if not compensation_:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Failed to create compensation",
        #     )

        return {"detail": "Compensation created successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from create compensation")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from create compensation")
        logger.error(f"{e} : error from create compensation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# documents upload
@user_router.post(
    "/documents_upload",
    status_code=status.HTTP_201_CREATED,
    tags=[emp_tag],
)
async def documents_upload(
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_id: str = "",
):
    try:
        data = await request.json()
        file_name = data.get("file_name")
        file_url = data.get("file_url")
        file_type = data.get("file_type")
        user_id = data.get("user_id")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user id are required",
            )

        # validate file type using FileType Enum
        try:
            file_type_enum = FileType(file_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type",
            )

        employee = await get_one_employee(db, user_id, current_user.organization_id)
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found",
            )

        await create_edit_uploaded_files(
            db, employee.id, file_name, file_url, file_type, file_id
        )
        # if not documents:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Failed to create documents",
        #     )

        return {"detail": "Documents uploaded successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from documents upload")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from documents upload")
        logger.error(f"{e} : error from documents upload")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get leabe requests
@user_router.get(
    "/leave_requests",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
)
async def leave_requests(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date=Query(None),
    end_date=Query(None),
    leave_status=Query(None),
    leave_type=Query(None),
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0),
):
    try:
        if start_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date must be in this format YYYY-MM-DD",
                )
        if end_date:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="end_date must be in this format YYYY-MM-DD",
                )
        if leave_status:
            if leave_status not in ["pending", "approved", "rejected"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="leave_status must be in this format YYYY-MM-DD",
                )
        leave_reqs = await get_leave_requests(
            db,
            current_user.organization_id,
            start_date,
            end_date,
            leave_status,
            leave_type,
            page,
            per_page,
            current_user,
        )
        return {
            "detail": "Data fetched successfully",
            **leave_reqs,
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get leave requests")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get leave requests")
        logger.error(f"{e} : error from get leave requests")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# request for leave
@user_router.post(
    "/request_for_leave",
    status_code=status.HTTP_201_CREATED,
    tags=[emp_tag],
)
async def request_for_leave(
    request_data: LeaveRequestSchema,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Extract data from validated model
        leave_type_id = request_data.leave_type_id
        start_date_str = request_data.start_date
        end_date_str = request_data.end_date

        # Convert to datetime objects
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else start_date
        )

        # Check if leave type exists
        leave_type = await get_one_leave_type(db, leave_type_id)
        if not leave_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave Type not found",
            )

        # Calculate duration
        diff = (end_date - start_date).days + 1

        logger.info(
            f"The diff between end date: {end_date} and start date: {start_date} is: {diff}"
        )

        # Validate duration
        if diff > leave_type.duration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Leave duration ({diff} days) exceeds maximum ({leave_type.duration} days)",
            )

        # Save leave request
        await save_leave_request(
            db,
            current_user.id,
            leave_type_id,
            start_date,
            end_date,
            request_data.note,
            request_data.document_url,
            request_data.document_name,
        )

        # Return appropriate message
        message = (
            "Single day leave request created successfully"
            if diff == 1
            else f"{diff}-day leave request created successfully"
        )
        return {"detail": message}

    except HTTPException as http_exc:
        logger.exception("traceback error from request for leave")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from request for leave")
        logger.error(f"{e} : error from request for leave")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get leave types
@user_router.get(
    "/leave_types",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
    # response_model=List[MiscRoleSchema],
)
# @cache_it("leave_types", org=True)
async def get_leave_types(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        leave_types = await get_all_leave_types(db, current_user.organization_id)
        return {
            "detail": "Data fetched successfully",
            "data": [leave_type.to_dict() for leave_type in leave_types],
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get leave types")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get leave types")
        logger.error(f"{e} : error from get leave types")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


@user_router.get(
    "/employees_timeoff",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
)
async def employees_timeoff(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date=Query(None),
    end_date=Query(None),
    leave_status=Query(None),
    leave_type=Query(None),
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0),
):
    try:
        if start_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d")
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date must be in this format YYYY-MM-DD",
                )
        if end_date:
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d")
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="end_date must be in this format YYYY-MM-DD",
                )
        if leave_status:
            if leave_status not in ["pending", "approved", "rejected"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="leave_status must be in this format YYYY-MM-DD",
                )
        leave_reqs = await get_leave_requests(
            db,
            current_user.organization_id,
            start_date,
            end_date,
            leave_status,
            leave_type,
            page,
            per_page,
        )
        return {
            "detail": "Data fetched successfully",
            **leave_reqs,
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get leave requests")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get leave requests")
        logger.error(f"{e} : error from get leave requests")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# create holiday
@user_router.post(
    "/create_holiday",
    status_code=status.HTTP_201_CREATED,
    tags=[emp_tag],
)
async def create_holidays(
    request: Request,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        name = data.get("name")
        from_date = data.get("from_date")
        to_date = data.get("to_date")

        if not name or not from_date or not to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields",
            )

        if await holiday_exists(db, current_user.organization_id, name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Holiday already exists",
            )

        # convert from_date and to_date to datetime
        try:
            from_date = datetime.strptime(from_date, "%Y-%m-%d")
            to_date = datetime.strptime(to_date, "%Y-%m-%d")
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_date and to_date must be in this format YYYY-MM-DD",
            )

        # create holiday
        holiday = await create_holiday(
            db, current_user.organization_id, name, from_date, to_date
        )
        return {
            "detail": "Holiday created successfully",
            "data": holiday.to_dict(),
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from create holiday")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from create holiday")
        logger.error(f"{e} : error from create holiday")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# edit holiday
@user_router.patch(
    "/edit_holiday/{holiday_id}",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
)
async def edit_holiday(
    request: Request,
    holiday_id: str,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        name = data.get("name")
        from_date = data.get("from_date")
        to_date = data.get("to_date")

        holiday = await get_one_holiday(db, holiday_id, current_user.organization_id)
        if not holiday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holiday not found",
            )

        if name and name != holiday.name:
            if await holiday_exists(db, current_user.organization_id, name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Holiday with this name already exists",
                )

        if from_date:
            try:
                from_date = datetime.strptime(from_date, "%Y-%m-%d")
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="from_date must be in this format YYYY-MM-DD",
                )
        if to_date:
            try:
                to_date = datetime.strptime(to_date, "%Y-%m-%d")
            except:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="to_date must be in this format YYYY-MM-DD",
                )

        holiday.name = name or holiday.name
        holiday.from_date = from_date or holiday.from_date
        holiday.to_date = to_date or holiday.to_date

        db.commit()
        db.refresh(holiday)

        return {
            "detail": "Holiday updated successfully",
            "data": holiday.to_dict(),
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from edit holiday")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from edit holiday")
        logger.error(f"{e} : error from edit holiday")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# delete one holiday
@user_router.delete(
    "/delete_holiday/{holiday_id}",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
)
async def delete_holiday(
    holiday_id: str,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        holiday = await get_one_holiday(db, holiday_id, current_user.organization_id)
        if not holiday:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Holiday not found",
            )
        db.delete(holiday)
        db.commit()
        return {"detail": "Holiday deleted successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from delete holiday")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from delete holiday")
        logger.error(f"{e} : error from delete holiday")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )

# get holidays
@user_router.get(
    "/get_holidays",
    status_code=status.HTTP_200_OK,
    tags=[emp_tag],
)
async def get_all_holidays(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        holidays = await get_holidays(db, current_user.organization_id)
        return {
            "detail": "Data fetched successfully",
            "data": [holiday.to_dict() for holiday in holidays],
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get holidays")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get holidays")
        logger.error(f"{e} : error from get holidays")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
