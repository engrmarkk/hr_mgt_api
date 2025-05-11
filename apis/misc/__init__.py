from fastapi import APIRouter, status, Depends, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from logger import logger
from schemas import MiscMenuSchema
from models import SideMenu
from constants import EXCEPTION_MESSAGE

misc_router = APIRouter(prefix="/misc", tags=["Miscellaneous"])


@misc_router.post("/side_menu", status_code=status.HTTP_200_OK)
async def create_side_menu(menu_data: MiscMenuSchema, db: Session = Depends(get_db)):
    try:
        name = menu_data.name
        description = menu_data.description
        icon_url = menu_data.icon_url
        tag = menu_data.tag

        side_menu = SideMenu(name=name, description=description, icon=icon_url, tag=tag)
        db.add(side_menu)
        db.commit()
        db.refresh(side_menu)
        return {"detail": "Side menu created successfully", "id": side_menu.id}
    except HTTPException as http_exc:
        # Log the HTTPException if needed
        logger.exception("traceback from login")
        raise http_exc
    except Exception as e:
        logger.exception("traceback from login")
        logger.error(f"{e} : error from login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=EXCEPTION_MESSAGE
        )
