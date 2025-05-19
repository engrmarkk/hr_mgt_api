from fastapi import APIRouter

user_router = APIRouter(prefix="/users")

from .user import user_router
from .employees import user_router
