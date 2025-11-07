from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse

from src.services import auth_service, subscriber_auth_service
from src.db.connection import get_db_connection
from src.templating import templates

import re

router = APIRouter(prefix="/auth", tags=["Unified Auth"])

# --- ЕДИНАЯ СТРАНИЦА ВХОДА ---
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("unified_login.html", {"request": request})

@router.post("/login")
async def login_form(request: Request, username: str = Form(...), password: str = Form(...)):
    employee = await auth_service.get_employee_by_login(username)
    if employee and auth_service.verify_password(password, employee['password_hash']):
        access_token = auth_service.create_access_token(data={"sub": employee['login'], "role": employee['role']})
        response = RedirectResponse(url="/subscribers", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response

    result = await subscriber_auth_service.verify_subscriber_credentials(username, password)

    if result and not result.get("error"):
        subscriber = result
        access_token = auth_service.create_access_token(
            data={"sub": str(subscriber['subscriber_id']), "role": "subscriber"})
        response = RedirectResponse(url="/subscriber/cabinet", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response


    error_message = result.get("error") if result else "Неверный логин или пароль"
    return templates.TemplateResponse(
        "unified_login.html",
        {"request": request, "error": error_message}
    )

@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """
    Отображает страницу с формой регистрации.
    """
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_form(
        request: Request,
        full_name: str = Form(..., max_length=100),
        address: str = Form(..., max_length=255),
        phone_number: str = Form(..., max_length=20, pattern=r'^\+?[0-9]+$'),
        email: str = Form(..., max_length=100),
        password: str = Form(..., min_length=6)
):
    if not re.fullmatch(r"\+?[0-9\s\-\(\)]+", phone_number):
        return templates.TemplateResponse("register.html", {
            "request": request, "error": "Неверный формат номера телефона.", "form": await request.form()
        }, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    result = await subscriber_auth_service.create_new_subscriber(
        full_name, address, phone_number, password, email
    )


@router.get("/confirm/{token}", response_class=HTMLResponse)
async def confirm_email(request: Request, token: str):
    """Обрабатывает переход по ссылке из письма."""
    conn = await get_db_connection()
    user = await conn.fetchrow("SELECT * FROM subscribers WHERE confirmation_token = $1", token)

    if not user:
        await conn.close()
        return templates.TemplateResponse("confirmation_feedback.html", {"request": request, "success": False,
                                                                         "message": "Неверная или устаревшая ссылка подтверждения."})

    await conn.execute("UPDATE subscribers SET is_confirmed = TRUE, confirmation_token = NULL WHERE subscriber_id = $1",
                       user['subscriber_id'])
    await conn.close()

    return templates.TemplateResponse("confirmation_feedback.html", {"request": request, "success": True,
                                                                     "message": "Ваш email успешно подтвержден! Теперь вы можете войти."})