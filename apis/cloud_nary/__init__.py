from fastapi import APIRouter, status, Depends, HTTPException, Request
from logger import logger
from helpers import convert_binary, generate_signature
from database import get_db
import cloudinary.uploader
import cloudinary.api
import cloudinary_config
from sqlalchemy.orm import Session
from cloudinary_config import cloudinary
import time
from constants import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

cloudinary_router = APIRouter(prefix="/cloudinary", tags=["Cloudinary"])


@cloudinary_router.post("/manage-file", status_code=status.HTTP_201_CREATED)
async def upload_file(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        file = data.get("file", None)
        public_id = data.get("public_id", None)
        action = data.get("action", None)
        folder = data.get("folder", None)

        logger.info(f"data: {data}")

        if not action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action is required",
            )

        if action == "upload" and not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is required",
            )

        if not public_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Public ID is required",
            )

        file = convert_binary(file) if action == "upload" else None

        params_to_sign = {
            "public_id": public_id,
            "timestamp": int(time.time()),
        }
        signature = generate_signature(params_to_sign, CLOUDINARY_API_SECRET)

        params_to_sign["signature"] = signature

        params_to_sign["folder"] = folder if folder else None

        if action == "upload":
            result = cloudinary.uploader.upload(file, **params_to_sign)
            logger.info(f"result: {result}")
            file_url = result["secure_url"]

            return {
                "data": {
                    "file_url": file_url,
                    "public_id": public_id,
                    "signature": signature,
                },
            }
        elif action == "destroy":
            params_to_sign["public_id"] = (
                f"{folder}/{public_id}" if folder else public_id
            )
            result = cloudinary.uploader.destroy(**params_to_sign)
            logger.info(f"result: {result}")

            if result["result"] == "ok":
                return {
                    "message": "File deleted successfully",
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File not found",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action",
            )
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from get available wallets")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from get available wallets")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Network Error"
        )
