from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.services import auth_service, subscriber_auth_service

router = APIRouter(prefix="/auth", tags=["Unified Auth"])
templates = Jinja2Templates(directory="templates")

# --- ЕДИНАЯ СТРАНИЦА ВХОДА ---
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("unified_login.html", {"request": request})

@router.post("/login")
async def login_form(request: Request, username: str = Form(...), password: str = Form(...)):
    # 1. Пытаемся залогинить как сотрудника
    employee = await auth_service.get_employee_by_login(username)
    if employee and auth_service.verify_password(password, employee['password_hash']):
        # Успех! Это сотрудник.
        access_token = auth_service.create_access_token(data={"sub": employee['login'], "role": employee['role']})
        response = RedirectResponse(url="/subscribers", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response

    # 2. Если не получилось, пытаемся залогинить как абонента
    subscriber = await subscriber_auth_service.verify_subscriber_credentials(username, password)
    if subscriber:
        # Успех! Это абонент.
        access_token = auth_service.create_access_token(data={"sub": str(subscriber['subscriber_id']), "role": "subscriber"})
        response = RedirectResponse(url="/subscriber/cabinet", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response

    # 3. Если ничего не подошло - ошибка
    return templates.TemplateResponse(
        "unified_login.html",
        {"request": request, "error": "Неверный логин/телефон или пароль"}
    )

# --- ВЫХОД (теперь один для всех) ---

@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register_form(
    request: Request,
    full_name: str = Form(...),
    address: str = Form(...),
    phone_number: str = Form(...),
    password: str = Form(...)
):
    new_subscriber = await subscriber_auth_service.create_new_subscriber(
        full_name, address, phone_number, password
    )

    if not new_subscriber:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Номер телефона уже зарегистрирован"}
        )

    access_token = auth_service.create_access_token(
        data={"sub": str(new_subscriber['subscriber_id']), "role": "subscriber"}
    )
    response = RedirectResponse(url="/subscriber/cabinet", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response