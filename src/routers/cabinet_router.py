from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services import subscriber_auth_service, subscriber_service
from src.auth.dependencies import require_subscriber_login, get_current_subscriber

router = APIRouter(prefix="/subscriber", tags=["Subscriber Cabinet"])
templates = Jinja2Templates(directory="templates")


# Главная страница кабинета (теперь это дашборд)
@router.get("/cabinet", response_class=HTMLResponse, dependencies=[Depends(require_subscriber_login)])
async def subscriber_cabinet_dashboard(request: Request, current_subscriber: dict = Depends(get_current_subscriber)):
    contracts = await subscriber_auth_service.get_subscriber_contracts(current_subscriber['subscriber_id'])
    # Обновляем данные абонента на случай, если баланс изменился
    subscriber_info = await subscriber_service.fetch_subscriber_by_id(current_subscriber['subscriber_id'])

    return templates.TemplateResponse("subscriber_cabinet.html", {
        "request": request,
        "subscriber": subscriber_info,
        "contracts": contracts,
        "active_page": "cabinet"
    })


# Страница истории платежей
@router.get("/payments", response_class=HTMLResponse, dependencies=[Depends(require_subscriber_login)])
async def subscriber_payments_page(request: Request, current_subscriber: dict = Depends(get_current_subscriber)):
    payments = await subscriber_auth_service.get_subscriber_payments(current_subscriber['subscriber_id'])
    return templates.TemplateResponse("subscriber_payments.html", {
        "request": request,
        "payments": payments,
        "active_page": "payments"
    })


# Страница уведомлений
@router.get("/notifications", response_class=HTMLResponse, dependencies=[Depends(require_subscriber_login)])
async def subscriber_notifications_page(request: Request, current_subscriber: dict = Depends(get_current_subscriber)):
    notifications = await subscriber_auth_service.get_subscriber_notifications(current_subscriber['subscriber_id'])
    return templates.TemplateResponse("subscriber_notifications.html", {
        "request": request,
        "notifications": notifications,
        "active_page": "notifications"
    })


# Страница редактирования профиля
@router.get("/edit", response_class=HTMLResponse, dependencies=[Depends(require_subscriber_login)])
async def subscriber_edit_page(request: Request, current_subscriber: dict = Depends(get_current_subscriber)):
    return templates.TemplateResponse("subscriber_edit_form.html", {
        "request": request,
        "subscriber": current_subscriber,
        "active_page": "edit"
    })


# Обработка формы редактирования
@router.post("/edit")
async def subscriber_edit_form(
        request: Request,
        current_subscriber: dict = Depends(require_subscriber_login),
        full_name: str = Form(...),
        address: str = Form(...),
        phone_number: str = Form(...)
):
    result = await subscriber_auth_service.update_subscriber_contact_info(
        current_subscriber['subscriber_id'], full_name, address, phone_number
    )
    if result.get("error"):
        return templates.TemplateResponse("subscriber_edit_form.html", {
            "request": request,
            "subscriber": current_subscriber,
            "active_page": "edit",
            "error": result.get("error")
        })
    return RedirectResponse(url="/subscriber/cabinet", status_code=303)


# Обработка формы пополнения баланса
@router.post("/top-up")
async def subscriber_top_up(
        current_subscriber: dict = Depends(require_subscriber_login),
        amount: float = Form(...)
):
    if amount <= 0:
        # Можно добавить обработку ошибки в шаблоне, но для простоты просто перенаправляем
        return RedirectResponse(url="/subscriber/cabinet", status_code=303)

    await subscriber_auth_service.top_up_subscriber_balance(current_subscriber['subscriber_id'], amount)
    return RedirectResponse(url="/subscriber/cabinet", status_code=303)


# Выход из системы
@router.post("/logout")
async def subscriber_logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("access_token")
    return response