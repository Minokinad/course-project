from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services import contract_service
from src.auth.dependencies import require_tech

# Защищаем все роуты в этом файле, требуя аутентификации
router = APIRouter(prefix="/contracts", tags=["Contracts"], dependencies=[Depends(require_tech)])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def list_contracts_page(request: Request):
    """
    Отображает страницу со списком всех договоров в системе.
    Доступно для всех авторизованных сотрудников.
    """
    contracts = await contract_service.fetch_all_contracts()
    return templates.TemplateResponse("contracts.html", {
        "request": request,
        "contracts": contracts,
        "active_page": "contracts"
    })