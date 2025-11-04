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


async def fetch_logs(limit: int = 100):
    """
    Получает последние записи из системного журнала.
    """
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT $1", limit)
    await conn.close()
    return rows