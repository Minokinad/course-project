from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services import log_service
from src.auth.dependencies import require_admin

router = APIRouter(prefix="/logs", tags=["System Logs"], dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def system_logs_page(request: Request):
    logs = await log_service.fetch_logs()
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "active_page": "logs"
    })