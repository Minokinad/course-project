from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from jose import JWTError, jwt

from src.config import settings
from src.services.auth_service import get_employee_by_login
from src.services.subscriber_service import fetch_subscriber_by_id

# Эта зависимость теперь очень простая: она просто читает данные из request.state

async def get_current_user(request: Request) -> Optional[dict]:
    return getattr(request.state, "user", None)

# Эта зависимость проверяет результат get_current_user и выполняет перенаправление
async def require_login(current_user: Optional[dict] = Depends(get_current_user)):
    if current_user is None or current_user.get("role") == "subscriber":
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login"}
        )
    return current_user

# Эта часть остается без изменений, она будет работать с новой логикой
def require_role(required_roles: list[str]):
    async def role_checker(current_user: dict = Depends(require_login)):
        if current_user['role'] not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав доступа")
    return role_checker

# Эти зависимости тоже остаются без изменений

require_admin = require_role(["Администратор"])
require_manager = require_role(["Администратор", "Менеджер"])
require_tech = require_role(["Администратор", "Менеджер", "Технический специалист"])

async def get_current_subscriber(request: Request) -> Optional[dict]:
    user = getattr(request.state, "user", None)
    if user and user.get("role") == "subscriber":
        return user
    return None

async def require_subscriber_login(current_subscriber: Optional[dict] = Depends(get_current_subscriber)):
    if current_subscriber is None:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/subscriber/login"}
        )
    return current_subscriber