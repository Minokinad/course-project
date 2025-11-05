from datetime import date, timedelta
from fastapi import APIRouter, Request, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

import pandas as pd
from io import BytesIO

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

@router.get("/export/json", response_class=JSONResponse)
async def export_report_to_json(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Экспортирует ДЕТАЛЬНЫЙ отчет по всем платежам за период в JSON.
    """
    payments_list = await report_service.get_all_payments_for_period(start_date, end_date)

    report_data = {
        "report_type": "Detailed Payments Report",
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "payments": payments_list
    }

    filename = f"detailed_payments_report_{start_date}_to_{end_date}.json"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    # ИСПРАВЛЕНИЕ: Используем jsonable_encoder для корректного преобразования
    # всех типов данных (включая Decimal и datetime) перед отправкой.
    json_compatible_content = jsonable_encoder(report_data)

    return JSONResponse(content=json_compatible_content, headers=headers)

# Добавьте этот новый эндпоинт в конец файла
@router.get("/export/excel", response_class=StreamingResponse)
async def export_report_to_excel(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    """
    Экспортирует детальный отчет по платежам за период в формат Excel (.xlsx).
    """
    payments_list = await report_service.get_all_payments_for_period(start_date, end_date)

    # Создаем DataFrame из списка платежей
    df = pd.DataFrame(payments_list)

    # Переименовываем колонки для более читаемого отчета
    if not df.empty:
        df = df.rename(columns={
            'payment_id': 'ID Платежа',
            'amount': 'Сумма',
            'payment_date': 'Дата платежа',
            'payment_method': 'Способ оплаты',
            'subscriber_id': 'ID Абонента',
            'subscriber_name': 'ФИО Абонента'
        })
        # Упорядочиваем колонки
        df = df[['ID Платежа', 'Дата платежа', 'ФИО Абонента', 'ID Абонента', 'Сумма', 'Способ оплаты']]

    # Создаем Excel-файл в памяти
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Payments Report')
    output.seek(0)

    filename = f"payments_report_{start_date}_to_{end_date}.xlsx"
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    return StreamingResponse(output, media_type=media_type, headers=headers)