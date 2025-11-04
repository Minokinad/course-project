from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services import equipment_service
from src.auth.dependencies import require_tech

router = APIRouter(prefix="/equipment", tags=["Equipment"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def list_equipment_page(request: Request):
    """
    Отображает страницу со списком всего оборудования.
    Доступно для всех авторизованных сотрудников.
    """
    equipment = await equipment_service.fetch_all_equipment()
    return templates.TemplateResponse("equipment.html", {
        "request": request,
        "equipment": equipment,
        "active_page": "equipment"
    })