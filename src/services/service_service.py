from typing import Optional
from src.db.connection import get_db_connection
from src.services.log_service import log_action


async def fetch_all_services(sort_by: Optional[str] = None, order: Optional[str] = 'asc'):
    """
    Получает список всех услуг, предоставляемых провайдером.
    """
    conn = await get_db_connection()

    allowed_sort_columns = ["service_id", "name", "price", "status"]

    query = "SELECT * FROM services"

    if sort_by in allowed_sort_columns:
        order_direction = "DESC" if order == 'desc' else "ASC"
        query += f" ORDER BY {sort_by} {order_direction}"
    else:
        query += " ORDER BY name"  # Сортировка по умолчанию

    rows = await conn.fetch(query)
    await conn.close()
    return rows


async def fetch_service_by_id(service_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT * FROM services WHERE service_id = $1", service_id)
    await conn.close()
    return row


async def create_service(name: str, description: str, price: float, status: str):
    conn = await get_db_connection()
    await conn.execute(
        "INSERT INTO services (name, description, price, status) VALUES ($1, $2, $3, $4)",
        name, description, price, status
    )
    await conn.close()
    # Логирование для создания пока опустим, т.к. нет user_login


async def update_service(service_id: int, name: str, description: str, price: float, status: str):
    conn = await get_db_connection()
    await conn.execute(
        "UPDATE services SET name = $1, description = $2, price = $3, status = $4 WHERE service_id = $5",
        name, description, price, status, service_id
    )
    await conn.close()
    # Логирование для обновления пока опустим


async def delete_service(service_id: int, user_login: str):
    conn = await get_db_connection()
    service_name = await conn.fetchval("SELECT name FROM services WHERE service_id = $1", service_id)
    await conn.execute("DELETE FROM services WHERE service_id = $1", service_id)
    await conn.close()
    await log_action("WARNING", f"Удалена услуга '{service_name}' (ID: {service_id}).", user_login)