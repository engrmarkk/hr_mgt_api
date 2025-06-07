from fastapi import FastAPI, Request, HTTPException
from apis import ping_router, auth_router, user_router
from sockets import websocket_router
from database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from middlewares import MaintenanceMiddleware, RateLimitMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from utils.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from constants import (
    ALLOWED_ORIGINS,
    ALLOWED_METHODS,
    ALLOWED_HEADERS,
    SECRET_KEY,
    API_VERSION,
)

# noinspection PyProtectedMember
from slowapi import _rate_limit_exceeded_handler
from logger import logger

load_dotenv()

app = FastAPI(
    title="HR Management", description="Rest API for HR Management", version="1.0.0"
)


def create_app():
    # noinspection PyTypeChecker
    app.add_middleware(MaintenanceMiddleware)
    # noinspection PyTypeChecker
    app.add_middleware(RateLimitMiddleware)
    # noinspection PyTypeChecker
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS.split(","),
        # Example: "http://localhost:3000,https://example.com"
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS.split(","),
        allow_headers=ALLOWED_HEADERS.split(","),
    )

    # noinspection PyTypeChecker
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

    # noinspection PyUnresolvedReferences
    app.state.limiter = limiter

    # noinspection PyTypeChecker
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(RateLimitExceeded)
    async def custom_rate_limit_exceeded_handler(
        request: Request, exc: RateLimitExceeded
    ):
        logger.error(exc.detail)
        raise HTTPException(status_code=429, detail="Too many requests")

    Base.metadata.create_all(engine)

    app.include_router(ping_router)
    app.include_router(auth_router, prefix=f"/{API_VERSION}")
    app.include_router(user_router, prefix=f"/{API_VERSION}")
    app.include_router(websocket_router)
    return app
