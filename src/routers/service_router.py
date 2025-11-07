from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services import service_service
from src.auth.dependencies import require_tech, require_admin

router = APIRouter(prefix="/services", tags=["Services"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def list_services_page(
    request: Request,
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query('asc')
):
    """
    Отображает страницу со списком всех доступных услуг.
    """
    services = await service_service.fetch_all_services(sort_by=sort_by, order=order)
    return templates.TemplateResponse("services.html", {
        "request": request,
        "services": services,
        "active_page": "services",
        "sort_by": sort_by,
        "order": order
    })

# --- Функции для администратора ---

@router.get("/new", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def new_service_form(request: Request):
    """
    Отображает форму для создания новой услуги.
    """
    return templates.TemplateResponse("service_form.html", {
        "request": request,
        "service": None,
        "active_page": "services"
    })

@router.post("/new", dependencies=[Depends(require_admin)])
async def create_service_action(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    status: str = Form(...)
):
    """
    Обрабатывает создание новой услуги.
    """
    await service_service.create_service(name, description, price, status)
    return RedirectResponse(url="/services", status_code=303)


@router.get("/{service_id}/edit", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def edit_service_form(request: Request, service_id: int):
    """
    Отображает форму для редактирования услуги.
    """
    service = await service_service.fetch_service_by_id(service_id)
    return templates.TemplateResponse("service_form.html", {
        "request": request,
        "service": service,
        "active_page": "services"
    })


@router.post("/{service_id}/edit", dependencies=[Depends(require_admin)])
async def update_service_action(
    service_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    status: str = Form(...)
):
    """
    Обрабатывает обновление данных услуги.
    """
    await service_service.update_service(service_id, name, description, price, status)
    return RedirectResponse(url="/services", status_code=303)


@router.delete("/{service_id}", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def delete_service_htmx(request: Request, service_id: int):
    """
    Обрабатывает удаление услуги.
    """
    await service_service.delete_service(service_id, user_login=request.state.user_login)
    return HTMLResponse(content="", status_code=200)