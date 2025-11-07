from datetime import date
from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services import contract_service
from src.auth.dependencies import require_tech, require_manager

router = APIRouter(prefix="/contracts", tags=["Contracts"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def list_contracts_page(
    request: Request,
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query('asc')
):
    contracts = await contract_service.fetch_all_contracts(sort_by=sort_by, order=order)
    return templates.TemplateResponse("contracts.html", {
        "request": request,
        "contracts": contracts,
        "active_page": "contracts",
        "sort_by": sort_by,
        "order": order
    })

@router.get("/new", response_class=HTMLResponse, dependencies=[Depends(require_manager)])
async def new_contract_form(request: Request):
    subscribers = await contract_service.fetch_all_subscribers_for_selection()
    services = await contract_service.fetch_all_services_for_selection()
    return templates.TemplateResponse("contract_form.html", {
        "request": request,
        "subscribers": subscribers,
        "services": services,
        "active_page": "contracts"
    })

@router.post("/new", dependencies=[Depends(require_manager)])
async def create_contract_action(
    request: Request,
    subscriber_id: int = Form(...),
    service_id: int = Form(...),
    start_date: date = Form(...)
):
    await contract_service.create_contract(
        subscriber_id, service_id, start_date, user_login=request.state.user_login
    )
    return RedirectResponse(url="/contracts", status_code=303)

@router.post("/{contract_id}/update-status", dependencies=[Depends(require_manager)])
async def update_contract_status_action(
    request: Request,
    contract_id: int,
    new_status: str = Form(...)
):
    await contract_service.update_contract_status(
        contract_id, new_status, user_login=request.state.user_login
    )
    return RedirectResponse(url="/contracts", status_code=303)