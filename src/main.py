from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt

from src.routers import (
    subscribers_router, auth_router, cabinet_router,
    service_router, equipment_router, contracts_router
)
from src.services.auth_service import get_employee_by_login
from src.services.subscriber_service import fetch_subscriber_by_id
from src.config import settings

app = FastAPI(title="АИС Интернет-провайдера")


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
    response = await call_next(request)
    return response


app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(cabinet_router.router)
app.include_router(subscribers_router.router)
app.include_router(service_router.router)
app.include_router(equipment_router.router)
app.include_router(contracts_router.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/auth/login")