from functools import wraps
from fastapi import Depends, status, HTTPException, Request
from database import get_db
from sqlalchemy.orm import Session
from security import get_current_user
from models import Users
from logger import logger
from connections import redis_conn
import json


def email_verified():
    def decorator(func):
        @wraps(func)
        async def wrapper(
            request: Request,
            current_user: Users = Depends(get_current_user),
            db: Session = Depends(get_db),
            *args,
            **kwargs,
        ):
            if not current_user.verify_email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email not verified",
                )
            return await func(request, current_user, db, *args, **kwargs)

        return wrapper

    return decorator


# get the result from the  decorator
def cache_it(red_key: str, org: bool = False, user: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            redkey = (
                f"{red_key}:{current_user.id}"
                if user
                else (f"{red_key}:{current_user.organization_id}" if org else red_key)
            )
            result = redis_conn.get(redkey)
            if result:
                logger.info("get result from decorator redis")
                return json.loads(result)
            result = await func(*args, **kwargs)
            redis_conn.set(redkey, json.dumps(result))
            return result

        return wrapper

    return decorator
