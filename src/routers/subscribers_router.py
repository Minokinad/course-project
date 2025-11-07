import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Request, Form, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.services import subscriber_service, contract_service
from src.auth.dependencies import require_manager, require_admin, require_tech

router = APIRouter(prefix="/subscribers", tags=["Subscribers"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")



@router.get("", response_class=HTMLResponse)
async def list_subscribers_page(
    request: Request,
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query('asc')
):
    subscribers = await subscriber_service.fetch_all_subscribers(sort_by=sort_by, order=order)
    return templates.TemplateResponse("subscribers.html", {
        "request": request,
        "subscribers": subscribers,
        "active_page": "subscribers",
        "message": request.query_params.get("message"), # Для сообщений после импорта
        "sort_by": sort_by,
        "order": order
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
    request: Request,
    full_name: str = Form(...), address: str = Form(""),
    phone_number: str = Form(""), balance: float = Form(0.0)
):
    await subscriber_service.create_subscriber(
        full_name, address, phone_number, balance, user_login=request.state.user_login
    )
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
    request: Request,
    sub_id: int, full_name: str = Form(...), address: str = Form(""),
    phone_number: str = Form(""), balance: float = Form(0.0)
):
    await subscriber_service.update_subscriber(
        sub_id, full_name, address, phone_number, balance, user_login=request.state.user_login
    )
    return RedirectResponse(url="/subscribers", status_code=303)

@router.delete("/{sub_id}", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def delete_subscriber_htmx(request: Request, sub_id: int):
    result = await subscriber_service.delete_subscriber(sub_id, user_login=request.state.user_login)

    if result.get("error"):
        error_html = f"""
        <tr class="table-danger" hx-swap-oob="true" id="error-row-{sub_id}">
            <td colspan="6">{result['error']} <button class="btn btn-sm btn-link" onclick="this.closest('tr').remove()">OK</button></td>
        </tr>
        """
        return HTMLResponse(content=f'<tr id="subscriber-row-{sub_id}">{error_html}</tr>', status_code=409)

    return HTMLResponse(content="", status_code=200)


def json_converter(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)

@router.get("/export/json", dependencies=[Depends(require_admin)])
async def export_subscribers_to_json():
    subscribers = await subscriber_service.fetch_all_subscribers()
    subscribers_list = [dict(sub) for sub in subscribers]

    json_data = json.dumps(subscribers_list, default=json_converter, indent=4, ensure_ascii=False)

    return JSONResponse(
        content=json.loads(json_data),
        headers={"Content-Disposition": f"attachment; filename=subscribers_{date.today()}.json"}
    )


@router.get("/import/json", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
async def import_json_form(request: Request):
    """
    Страница с формой для загрузки JSON файла.
    """
    return templates.TemplateResponse("import_form.html", {
        "request": request,
        "active_page": "subscribers",
        "import_url": "/subscribers/import/json"
    })

@router.post("/import/json", dependencies=[Depends(require_admin)])
async def import_subscribers_from_json(request: Request, file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Неверный формат файла. Требуется JSON.")

    content = await file.read()
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError()
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Не удалось прочитать JSON или формат данных некорректен (ожидается список абонентов).")

    count = await subscriber_service.import_subscribers_from_list(data, user_login=request.state.user_login)
    message = f"Успешно импортировано {count} абонентов."
    return RedirectResponse(url=f"/subscribers?message={message}", status_code=303)