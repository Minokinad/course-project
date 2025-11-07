from typing import Optional
from src.db.connection import get_db_connection


async def log_action(level: str, message: str, user_login: str):
    """
    Записывает действие в системный журнал.
    """
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO system_logs (level, message, user_login) VALUES ($1, $2, $3)",
            level, message, user_login
        )
    finally:
        await conn.close()


async def fetch_logs(limit: int = 100, sort_by: Optional[str] = None, order: Optional[str] = 'desc'):
    """
    Получает последние записи из системного журнала.
    """
    conn = await get_db_connection()

    allowed_sort_columns = ["timestamp", "level", "user_login"]

    query = f"SELECT * FROM system_logs"

    if sort_by in allowed_sort_columns:
        order_direction = "DESC" if order == 'desc' else "ASC"
        query += f" ORDER BY {sort_by} {order_direction}"
    else:
        query += " ORDER BY timestamp DESC"  # Сортировка по умолчанию

    query += " LIMIT $1"

    rows = await conn.fetch(query, limit)
    await conn.close()
    return rows