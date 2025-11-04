from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services import service_service
from src.auth.dependencies import require_tech

router = APIRouter(prefix="/services", tags=["Services"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def list_services_page(request: Request):
    """
    Отображает страницу со списком всех доступных услуг.
    Доступно для всех авторизованных сотрудников.
    """
    services = await service_service.fetch_all_services()
    return templates.TemplateResponse("services.html", {
        "request": request,
        "services": services,
        "active_page": "services"
    })