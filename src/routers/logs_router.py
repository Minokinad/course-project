from typing import Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services import log_service
from src.auth.dependencies import require_admin
from src.templating import templates

router = APIRouter(prefix="/logs", tags=["System Logs"], dependencies=[Depends(require_admin)])

@router.get("", response_class=HTMLResponse)
async def system_logs_page(
    request: Request,
    sort_by: Optional[str] = Query(None),
    order: Optional[str] = Query('desc')
):
    logs = await log_service.fetch_logs(sort_by=sort_by, order=order)
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "active_page": "logs",
        "sort_by": sort_by,
        "order": order
    })