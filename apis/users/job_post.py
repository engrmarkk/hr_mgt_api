import json
from cruds import (
    edit_job_postings,
    get_one_job_posting,
    create_job_postings,
    get_job_postings,
    get_job_postings_apply,
    get_job_post,
    create_application,
    get_job_stages,
    can_apply,
    get_applicants_hist,
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
from datetime import datetime, timezone
from logger import logger
from database import get_db
from sqlalchemy.orm import Session
from apis.users import user_router
from helpers import get_ip_address
from connections import redis_conn

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

        # closing date should not be backwards
        if closing_date is not None:
            if closing_date.tzinfo:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.utcnow()

            # Compare
            if closing_date < now:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Closing date should not be in the past",
                )

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
        redis_conn.partial_delete("applicant_job_post:")
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


# get applicants
@user_router.get("/job_applicants", status_code=status.HTTP_200_OK, tags=[job_tag])
async def get_applicants(
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0),
    job_stage_id: str = None,
    search: str = None,
):
    try:
        res = await get_applicants_hist(
            db, page, per_page, job_stage_id, search, current_user.organization_id
        )
        return {"detail": "Applicant fetched successfully", **res}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from get_applicants")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from get_applicants")
        logger.error(f"{e} : error from get_applicants")
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


@user_router.get(
    "/job_postings_apply/{browser_id}", status_code=status.HTTP_200_OK, tags=[job_tag]
)
async def get_postings_applicant(
    browser_id: str,
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, gt=0),
    per_page: int = Query(10, gt=0),
    start_date: str = None,
    end_date: str = None,
    job_status: str = None,
    job_type: str = None,
    department_id: str = None,
    organization_id: str = None,
):
    try:
        key = f"applicant_job_post:{page}:{per_page}:{start_date}:{end_date}:{job_status}:{job_type}:{department_id}:{organization_id}"
        res = redis_conn.get(key)
        if res:
            logger.info("From Redis @get_postings_applicant")
            res = json.loads(res)
            return {"detail": "Posting fetched successfully", **res}
        user_agent = request.headers.get("user-agent")
        res = await get_job_postings_apply(
            db,
            job_status,
            job_type,
            department_id,
            organization_id,
            page,
            per_page,
            start_date,
            end_date,
            user_agent,
            browser_id,
        )
        redis_conn.set(key, json.dumps(res), expire=600)
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


# apply for a job
@user_router.post(
    "/apply_job/{job_post_id}", status_code=status.HTTP_200_OK, tags=[job_tag]
)
async def apply_job(
    job_post_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()

        job_post = await get_job_post(db, job_post_id)
        if not job_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job listing",
            )
        full_name = data.get("full_name")
        email = data.get("email")
        phone_number = data.get("phone_number")
        resume = data.get("resume")
        cover_letter = data.get("cover_letter")
        browser_id = data.get("browser_id")
        user_agent = request.headers.get("user-agent")
        ip_address = get_ip_address(request)

        if await can_apply(
            db,
            job_post_id,
            browser_id,
            user_agent,
            email=email,
            phone_number=phone_number,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You have already applied for this job",
            )

        await create_application(
            db,
            full_name,
            email,
            phone_number,
            resume,
            cover_letter,
            user_agent,
            ip_address,
            job_post_id,
            job_post.organization_id,
            browser_id,
        )
        job_post.applied_count += 1
        db.commit()
        redis_conn.partial_delete("applicant_job_post:")
        return {"detail": "Application submitted successfully"}
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


# get job stages
@user_router.get("/job_stages", status_code=status.HTTP_200_OK, tags=[job_tag])
async def job_stages(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        key = f"job_stages:{current_user.organization_id}"
        res = redis_conn.get(key)
        if res:
            logger.info("redis get @job_stages")
            return {
                "detail": "Job stages fetched successfully",
                "data": json.loads(res),
            }
        res = await get_job_stages(db, current_user.organization_id)
        redis_conn.set(key, json.dumps(res), expire=6000)
        return {"detail": "Job stages fetched successfully", "data": res}
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
