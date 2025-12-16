from fastapi import APIRouter

user_router = APIRouter(prefix="/users")

from .user import user_router
from .employees import user_router
from .job_post import user_router
