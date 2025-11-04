from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services import subscriber_service, contract_service
from src.auth.dependencies import require_manager, require_admin, require_tech

# Защищаем все роуты в этом файле, требуя аутентификации
router = APIRouter(prefix="/subscribers", tags=["Subscribers"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def list_subscribers_page(request: Request):
    subscribers = await subscriber_service.fetch_all_subscribers()
    return templates.TemplateResponse("subscribers.html", {
        "request": request,
        "subscribers": subscribers,
        "active_page": "subscribers"
    })

@router.post("/search", response_class=HTMLResponse)
async def search_subscribers_htmx(request: Request, search_query: str = Form("")):
    subscribers = await subscriber_service.search_subscribers(search_query)
    return templates.TemplateResponse("partials/subscriber_rows.html", {"request": request, "subscribers": subscribers})

@router.get("/new", response_class=HTMLResponse, dependencies=[Depends(require_manager)])
async def new_subscriber_form(request: Request):
    return templates.TemplateResponse("subscriber_form.html", {"request": request, "subscriber": None, "active_page": "subscribers"})

@router.post("/new", dependencies=[Depends(require_manager)])
async def create_subscriber_form(
    full_name: str = Form(...), address: str = Form(""),
    phone_number: str = Form(""), balance: float = Form(0.0)
):
    await subscriber_service.create_subscriber(full_name, address, phone_number, balance)
    return RedirectResponse(url="/subscribers", status_code=303)


@router.get("/{sub_id}", response_class=HTMLResponse)
async def view_subscriber_details(request: Request, sub_id: int):
    subscriber = await subscriber_service.fetch_subscriber_by_id(sub_id)
    if not subscriber:
        return RedirectResponse(url="/subscribers", status_code=404)

    contracts = await contract_service.fetch_contracts_by_subscriber_id(sub_id)
    return templates.TemplateResponse(
        "subscriber_detail.html",
        {
            "request": request,
            "subscriber": subscriber,
            "contracts": contracts,
            "active_page": "subscribers"
        }
    )

@router.get("/{sub_id}/edit", response_class=HTMLResponse, dependencies=[Depends(require_manager)])
async def edit_subscriber_form(request: Request, sub_id: int):
    subscriber = await subscriber_service.fetch_subscriber_by_id(sub_id)
    return templates.TemplateResponse("subscriber_form.html", {
        "request": request,
        "subscriber": subscriber,
        "active_page": "subscribers"
    })


@router.post("/{sub_id}/edit", dependencies=[Depends(require_manager)])
async def update_subscriber_form(
    sub_id: int, full_name: str = Form(...), address: str = Form(""),
    phone_number: str = Form(""), balance: float = Form(0.0)
):
    await subscriber_service.update_subscriber(sub_id, full_name, address, phone_number, balance)
    return RedirectResponse(url="/subscribers", status_code=303)

@router.delete("/{sub_id}", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def delete_subscriber_htmx(sub_id: int):
    await subscriber_service.delete_subscriber(sub_id)
    return HTMLResponse(content="", status_code=200)