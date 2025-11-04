from src.db.connection import get_db_connection


async def fetch_all_services():
    """
    Получает список всех услуг, предоставляемых провайдером.
    """
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT * FROM services ORDER BY name")
    await conn.close()
    return rows