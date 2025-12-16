from cruds import (
    edit_job_postings,
    get_one_job_posting,
    create_job_postings,
    get_job_postings,
)
from schemas import CreateJobPostingSchema
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
from datetime import datetime
from logger import logger
from database import get_db
from sqlalchemy.orm import Session
from apis.users import user_router

job_tag = "Job Postings"


# create job postings
@user_router.post("/job_postings", status_code=status.HTTP_201_CREATED, tags=[job_tag])
async def create_postings(
    request_data: CreateJobPostingSchema,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    try:
        title = request_data.title
        description = request_data.description
        location = request_data.location
        job_type = request_data.job_type
        quantity = request_data.quantity
        department_id = request_data.department_id
        organization_id = current_user.organization_id
        closing_date = request_data.closing_date
        min_salary = request_data.min_salary
        max_salary = request_data.max_salary

        await create_job_postings(
            db,
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
        )
        return {"detail": "Job posting created successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from create_job_postings")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from create_job_postings")
        logger.error(f"{e} : error from create_job_postings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# update job_posting
@user_router.patch(
    "/job_postings/{job_post_id}", status_code=status.HTTP_200_OK, tags=[job_tag]
)
async def update_job_posting(
    job_post_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    try:
        data = await request.json()
        title = data.get("title")
        description = data.get("description")
        location = data.get("location")
        job_type = data.get("job_type")
        quantity = data.get("quantity")
        department_id = data.get("department_id")
        closing_date = data.get("closing_date")
        min_salary = data.get("min_salary")
        max_salary = data.get("max_salary")
        status_ = data.get("status")

        if closing_date:
            try:
                closing_date = datetime.strptime(closing_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid closing date format",
                )

        if not await get_one_job_posting(db, job_post_id, current_user.organization_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found",
            )

        await edit_job_postings(
            db,
            job_post_id,
            title,
            description,
            location,
            job_type,
            quantity,
            department_id,
            current_user.organization_id,
            closing_date,
            min_salary,
            max_salary,
            status_,
        )
        return {"detail": "Job posting updated successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from update_job_posting")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from update_job_posting")
        logger.error(f"{e} : error from update_job_posting")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# delete job posting
@user_router.delete(
    "/job_postings/{job_post_id}", status_code=status.HTTP_200_OK, tags=[job_tag]
)
async def delete_posting(
    job_post_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    try:
        job_post = await get_one_job_posting(
            db, job_post_id, current_user.organization_id
        )
        if not job_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found",
            )
        db.delete(job_post)
        db.commit()
        return {"detail": "Job posting deleted successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from delete_posting")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from delete_posting")
        logger.error(f"{e} : error from delete_posting")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )


# get all job posts
@user_router.get("/job_postings", status_code=status.HTTP_200_OK, tags=[job_tag])
async def get_postings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0),
    start_date: str = None,
    end_date: str = None,
    job_status: str = None,
    job_type: str = None,
    department_id: str = None,
):
    try:
        res = await get_job_postings(
            db,
            job_status,
            job_type,
            department_id,
            current_user.organization_id,
            page,
            per_page,
            start_date,
            end_date,
        )
        return {"detail": "Posting fetched successfully", **res}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get_postings")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get_postings")
        logger.error(f"{e} : error from get_postings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
