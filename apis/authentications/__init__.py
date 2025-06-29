from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks
from schemas import (
    RegisterSchema,
    LoginSchema,
    VerifyEmailSchema,
    ResendOTPSchema,
    ResetTokenSchema,
    ConfirmTokenSchema,
)
from cruds import (
    email_exists,
    create_or_update_user_session,
    save_user_email_password,
    save_user_data,
    # save_default_side_menus,
    save_default_roles,
    get_steps,
    get_user_via_salt,
    create_remain,
)
from helpers import (
    validate_password,
    validate_correct_email,
    verify_password,
    generate_token,
    hash_password,
    generate_salt,
)
from database import get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from security import create_access_token
from models import UserSessions
from datetime import datetime, timedelta
from constants import OTP_EXPIRES, EXCEPTION_MESSAGE
from logger import logger
from services.email import send_email

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        email = login_data.email
        password = login_data.password

        logger.info(f"{email}: email")
        logger.info(f"{password}: password")
        # background_tasks.add_task(save_default_side_menus, db)
        # save_default_side_menus(db)
        # await save_default_roles(db)

        valid_email_status, res = await validate_correct_email(email)

        if not valid_email_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)

        user = await email_exists(db, res)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
            )

        if not await verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials"
            )

        if not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
            )

        if not user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified"
            )

        access_token = create_access_token(data={"sub": user.id})
        user.last_login = datetime.now()
        db.commit()
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "steps": await get_steps(db, user),
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from login")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )


# For Swagger UI login interface
@auth_router.post(
    "/get_token",
    status_code=status.HTTP_200_OK,
    description="This is for Swagger UI login interface",
)
async def get_token(
    login_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    try:
        email = login_data.username
        password = login_data.password

        valid_email_status, res = await validate_correct_email(email)

        if not valid_email_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)

        user = await email_exists(db, res)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
            )

        if not await verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Credentials"
            )

        if not user.active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
            )

        # if not user.email_verified:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified"
        #     )

        access_token = create_access_token(data={"sub": user.id})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "steps": await get_steps(db, user),
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from login")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )


# register
@auth_router.post("/register", status_code=status.HTTP_200_OK)
async def register(
    register_data: RegisterSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        name = register_data.name
        email = register_data.email
        password = register_data.password

        valid_email_status, res = await validate_correct_email(email)

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Name is required"
            )

        names = name.split(" ")
        if len(names) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pls input your full name",
            )

        if not valid_email_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)

        pass_res = validate_password(password)

        if pass_res:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=pass_res
            )

        user = await email_exists(db, res)

        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot register with this email",
            )

        last_name = names[0]
        first_name = names[1]

        user = await save_user_data(db, last_name, first_name, res, password)

        access_token = create_access_token(data={"sub": user.id})

        background_tasks.add_task(create_remain, user.id)

        return {
            "detail": "User registered successfully",
            "access_token": access_token,
            "token_type": "bearer",
        }
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from register")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from register")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )


# verify email
@auth_router.patch("/verify_email", status_code=status.HTTP_200_OK)
async def verify_email(verify_data: VerifyEmailSchema, db: Session = Depends(get_db)):
    try:
        email = verify_data.email
        otp = verify_data.otp

        valid_email_status, res = await validate_correct_email(email)

        if not valid_email_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
        user = await email_exists(db, res)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email does not belong to any user",
            )

        if user.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
            )

        if user.user_sessions.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP"
            )

        # check if the otp has expired
        if user.user_sessions.expired_at < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired"
            )

        if user.user_sessions.token != otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP"
            )

        user.email_verified = True
        user.user_sessions.used = True
        db.commit()
        # send_mail.delay(
        #     {
        #         "email": email,
        #         "subject": "Welcome",
        #         "template_name": "welcome.html",
        #         "name": user.username.title(),
        #     }
        # )
        return {"detail": "Email verified"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from verify email")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from verify email")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )


# resend otp
@auth_router.post("/resend_otp", status_code=status.HTTP_200_OK)
async def resend_otp(
    request_data: ResendOTPSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        email = request_data.email
        valid_email_status, res = await validate_correct_email(email)

        if not valid_email_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
        user = await email_exists(db, res)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email does not belong to any user",
            )
        # if user.email_verified:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        #     )
        token = generate_token()
        await create_or_update_user_session(db, user, token=token)

        db.commit()
        saved_otp = user.user_sessions.token
        logger.info(f"saved_otp: {saved_otp}")
        background_tasks.add_task(
            send_email,
            {
                "email": email,
                "subject": "Reset Password",
                "template_name": "otp.html",
                "token": saved_otp,
            },
        )
        return {"detail": "OTP sent successfully", "email": res}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from resend otp")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from resend otp")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )


# reset password request
@auth_router.post(
    "/reset_password_request",
    status_code=status.HTTP_200_OK,
)
async def reset_password_req(
    request_data: ResendOTPSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        email = request_data.email
        valid_email_status, res = await validate_correct_email(email)

        if not valid_email_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
        user = await email_exists(db, res)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        token = generate_token()
        resp = await create_or_update_user_session(db, user, token=token)

        background_tasks.add_task(
            send_email,
            {
                "email": email,
                "subject": "Reset Password",
                "template_name": "otp.html",
                "token": resp.token,
            },
        )
        return {"detail": "Token sent"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from reset password request")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from reset password request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )


# reset password
@auth_router.post("/confirm_token", status_code=status.HTTP_200_OK)
async def confirm_token(
    request_data: ConfirmTokenSchema, db: Session = Depends(get_db)
):
    try:
        email = request_data.email
        token = request_data.token

        valid_email_status, res = await validate_correct_email(email)

        if not valid_email_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res)
        user = await email_exists(db, res)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Pls input your token"
            )
        if user.user_sessions.used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Token"
            )
        if user.user_sessions.expired_at < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Token has expired"
            )
        print(user.user_sessions.token, token)
        if user.user_sessions.token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Token"
            )

        salt = generate_salt()

        user.user_sessions.salt = salt
        user.user_sessions.used = True
        db.commit()
        return {"detail": "Pls Reset your password", "salt": salt}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from reset password")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from reset password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )


@auth_router.post("/reset_password", status_code=status.HTTP_200_OK)
async def reset_password(request_data: ResetTokenSchema, db: Session = Depends(get_db)):
    try:
        salt = request_data.salt
        password = request_data.password
        confirm_password = request_data.confirm_password

        user = await get_user_via_salt(db, salt)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        resp = validate_password(password)
        if resp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resp)
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not match",
            )

        user.password = hash_password(password)
        user.user_sessions.used_token = True
        db.commit()
        return {"detail": "Password Reset successfully"}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback error from reset password")
        raise http_exc
    except Exception as e:
        logger.exception("traceback error from reset password")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )
