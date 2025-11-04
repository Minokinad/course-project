from src.db.connection import get_db_connection
from src.services.log_service import log_action

# ... (первые три функции без изменений)
async def fetch_all_subscribers():
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT * FROM subscribers ORDER BY subscriber_id")
    await conn.close()
    return rows

async def fetch_subscriber_by_id(sub_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT * FROM subscribers WHERE subscriber_id = $1", sub_id)
    await conn.close()
    return row

async def search_subscribers(query: str):
    """
    Ищет абонентов по ФИО, адресу или номеру телефона.
    """
    conn = await get_db_connection()
    search_pattern = f"%{query}%"
    rows = await conn.fetch(
        """
        SELECT * FROM subscribers
        WHERE full_name ILIKE $1 OR address ILIKE $1 OR phone_number ILIKE $1
        ORDER BY subscriber_id
        """,
        search_pattern
    )
    await conn.close()
    return rows


async def create_subscriber(full_name: str, address: str, phone: str, balance: float, user_login: str):
    conn = await get_db_connection()
    new_id = await conn.fetchval(
        "INSERT INTO subscribers (full_name, address, phone_number, balance) VALUES ($1, $2, $3, $4) RETURNING subscriber_id",
        full_name, address, phone, balance
    )
    await conn.close()
    await log_action("INFO", f"Создан новый абонент '{full_name}' (ID: {new_id}).", user_login)


async def update_subscriber(sub_id: int, full_name: str, address: str, phone_number: str, balance: float, user_login: str):
    conn = await get_db_connection()
    await conn.execute(
        """
        UPDATE subscribers
        SET full_name = $1, address = $2, phone_number = $3, balance = $4
        WHERE subscriber_id = $5
        """,
        full_name, address, phone_number, balance, sub_id
    )
    await conn.close()
    await log_action("INFO", f"Обновлены данные абонента '{full_name}' (ID: {sub_id}).", user_login)


async def delete_subscriber(sub_id: int, user_login: str):
    conn = await get_db_connection()
    # Сначала получим имя для лога
    sub_name = await conn.fetchval("SELECT full_name FROM subscribers WHERE subscriber_id = $1", sub_id)
    await conn.execute("DELETE FROM subscribers WHERE subscriber_id = $1", sub_id)
    await conn.close()
    await log_action("WARNING", f"Удален абонент '{sub_name}' (ID: {sub_id}).", user_login)


async def import_subscribers_from_list(subscribers: list, user_login: str) -> int:
    """
    Импортирует список абонентов в базу данных.
    Пропускает абонентов, если поля некорректны.
    """
    conn = await get_db_connection()
    count = 0
    for sub in subscribers:
        # Простая валидация - проверяем наличие обязательного поля
        if 'full_name' in sub and isinstance(sub['full_name'], str):
            await conn.execute(
                """
                INSERT INTO subscribers (full_name, address, phone_number, balance)
                VALUES ($1, $2, $3, $4)
                """,
                sub.get('full_name'),
                sub.get('address', ''),
                sub.get('phone_number', ''),
                sub.get('balance', 0.0)
            )
            count += 1
    await conn.close()
    if count > 0:
        await log_action("INFO", f"Выполнен импорт {count} абонентов из JSON.", user_login)
    return count