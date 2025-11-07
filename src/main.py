from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt

from src.templating import templates
from src.services import service_service

from src.routers import (
    subscribers_router, auth_router, cabinet_router,
    service_router, equipment_router, contracts_router,
    employees_router, reports_router, logs_router, tickets_router
)
from src.services.auth_service import get_employee_by_login
from src.services.subscriber_service import fetch_subscriber_by_id
from src.services import subscriber_service, employee_service
from src.config import settings


app = FastAPI(title="АИС Интернет-провайдера")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Перехватывает ошибки валидации Pydantic и возвращает страницу
    с формой, подсвеченными ошибками и введенными данными.
    """
    # Собираем ошибки в удобный словарь: { 'field_name': 'error message' }
    errors = {}
    for error in exc.errors():
        field_name = error['loc'][-1]
        errors[field_name] = error['msg']

    # Пытаемся получить данные из формы, чтобы вернуть их пользователю
    try:
        form_data = await request.form()
    except Exception:
        form_data = {}

    # Карта для сопоставления URL и шаблона с формой
    template_map = {
        "/auth/register": "register.html",
        "/subscribers/new": "subscriber_form.html",
        f"/subscribers/{request.path_params.get('sub_id')}/edit": "subscriber_form.html",
        "/employees/new": "employee_form.html",
        f"/employees/{request.path_params.get('emp_id')}/edit": "employee_form.html",
        "/equipment/new": "equipment_form.html",
        f"/equipment/{request.path_params.get('eq_id')}/edit": "equipment_form.html",
        "/services/new": "service_form.html",
        f"/services/{request.path_params.get('service_id')}/edit": "service_form.html",
    }

    template_name = template_map.get(str(request.url.path))

    # Контекст для передачи в шаблон
    context = {
        "request": request,
        "errors": errors,
        "form": form_data
    }

    if template_name:
        # Для форм редактирования нужно подгрузить существующий объект
        if 'sub_id' in request.path_params:
            subscriber = await subscriber_service.fetch_subscriber_by_id(request.path_params['sub_id'])
            context['subscriber'] = subscriber
        if 'emp_id' in request.path_params:
            employee = await employee_service.fetch_employee_by_id(request.path_params['emp_id'])
            context['employee'] = employee
        # Добавьте похожие блоки для equipment и service, если нужно...

        return templates.TemplateResponse(
            template_name,
            context,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    # Стандартный ответ, если шаблон не найден
    return HTMLResponse(
        content=f"Validation Error: {exc.errors()}",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

@app.middleware("http")
async def add_user_to_context(request: Request, call_next):
    token = request.cookies.get("access_token")
    user = None
    if token:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            login_or_id: str = payload.get("sub")
            role: str = payload.get("role")

            if role == "subscriber":
                user = await fetch_subscriber_by_id(int(login_or_id))
                if user:
                    user = dict(user)
                    user['role'] = 'subscriber'
            else:
                user = await get_employee_by_login(login_or_id)

        except (JWTError, ValueError, KeyError):
            pass

    request.state.user = user
    request.state.user_login = user['login'] if user and 'login' in user else "Anonymous"

    response = await call_next(request)
    return response


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_router.router)
app.include_router(cabinet_router.router)
app.include_router(subscribers_router.router)
app.include_router(service_router.router)
app.include_router(equipment_router.router)
app.include_router(contracts_router.router)
app.include_router(employees_router.router)
app.include_router(reports_router.router)
app.include_router(logs_router.router)
app.include_router(tickets_router.router)


@app.get("/")
async def root(request: Request):
    """
    Главный маршрутизатор.
    - Для неавторизованных пользователей показывает главную страницу.
    - Для авторизованных - перенаправляет в соответствующий раздел.
    """
    # Middleware уже определил пользователя и поместил его в request.state
    user = request.state.user

    # 1. Если пользователь не авторизован
    if not user:
        # Показываем ему публичную главную страницу с услугами
        active_services = await service_service.fetch_all_services(status_filter="Активна")
        return templates.TemplateResponse(
            "landing_page.html",
            {
                "request": request,
                "services": active_services
            }
        )

    # 2. Если пользователь авторизован, проверяем его роль
    if user.get("role") == "subscriber":
        # Это абонент -> перенаправляем в его личный кабинет
        return RedirectResponse(url="/subscriber/cabinet")
    else:
        # Это сотрудник (любая роль) -> перенаправляем на страницу с абонентами
        return RedirectResponse(url="/subscribers")