from func import get_user_id_from_request
from slowapi import Limiter
from constants import REDIS_HOST, REDIS_PORT

limiter = Limiter(
    key_func=get_user_id_from_request,
    storage_uri=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
)
