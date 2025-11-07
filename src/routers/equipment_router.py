from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services import equipment_service
from src.auth.dependencies import require_tech

router = APIRouter(prefix="/equipment", tags=["Equipment"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def list_equipment_page(
    request: Request,
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query('asc')
):
    """
    Отображает страницу со списком всего оборудования.
    """
    equipment = await equipment_service.fetch_all_equipment(sort_by=sort_by, order=order)
    return templates.TemplateResponse("equipment.html", {
        "request": request,
        "equipment": equipment,
        "active_page": "equipment",
        "sort_by": sort_by,
        "order": order
    })

@router.get("/new", response_class=HTMLResponse)
async def new_equipment_form(request: Request):
    """
    Отображает форму для добавления нового оборудования.
    """
    contracts = await equipment_service.fetch_available_contracts_for_linking()
    return templates.TemplateResponse("equipment_form.html", {
        "request": request,
        "equipment": None,
        "contracts": contracts,
        "active_page": "equipment"
    })

@router.post("/new")
async def create_equipment_action(
    type: str = Form(...),
    serial_number: str = Form(...),
    status: str = Form(...),
    contract_id: str = Form("")
):
    """
    Обрабатывает создание нового оборудования.
    """
    # Преобразуем пустую строку в None для contract_id
    c_id = int(contract_id) if contract_id else None
    await equipment_service.create_equipment(type, serial_number, status, c_id)
    return RedirectResponse(url="/equipment", status_code=303)


@router.get("/{eq_id}/edit", response_class=HTMLResponse)
async def edit_equipment_form(request: Request, eq_id: int):
    """
    Отображает форму для редактирования существующего оборудования.
    """
    equipment = await equipment_service.fetch_equipment_by_id(eq_id)
    if not equipment:
        return RedirectResponse(url="/equipment", status_code=404)

    contracts = await equipment_service.fetch_available_contracts_for_linking(
        current_contract_id=equipment['contract_id']
    )
    return templates.TemplateResponse("equipment_form.html", {
        "request": request,
        "equipment": equipment,
        "contracts": contracts,
        "active_page": "equipment"
    })


@router.post("/{eq_id}/edit")
async def update_equipment_action(
    eq_id: int,
    type: str = Form(...),
    serial_number: str = Form(...),
    status: str = Form(...),
    contract_id: str = Form("")
):
    """
    Обрабатывает обновление данных оборудования, включая привязку к договору.
    """
    c_id = int(contract_id) if contract_id else None
    await equipment_service.update_equipment(eq_id, type, serial_number, status, c_id)
    return RedirectResponse(url="/equipment", status_code=303)


@router.delete("/{eq_id}", response_class=HTMLResponse)
async def delete_equipment_htmx(eq_id: int):
    """
    Обрабатывает удаление оборудования (для HTMX).
    """
    await equipment_service.delete_equipment(eq_id)
    return HTMLResponse(content="", status_code=200)