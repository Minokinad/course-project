from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services import report_service
from src.auth.dependencies import require_admin

router = APIRouter(prefix="/reports", tags=["Reports"], dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory="templates")

@router.get("", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    start_date: date = Query(date.today() - timedelta(days=30)),
    end_date: date = Query(date.today())
):
    payment_summary = await report_service.get_payment_summary(start_date, end_date)
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "start_date": start_date,
        "end_date": end_date,
        "payment_summary": payment_summary,
        "active_page": "reports"
    })