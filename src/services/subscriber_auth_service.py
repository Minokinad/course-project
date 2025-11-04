from src.db.connection import get_db_connection
from src.services.auth_service import verify_password, hash_password


async def get_subscriber_by_phone(phone: str):
    """Находит абонента по номеру телефона."""
    conn = await get_db_connection()
    query = "SELECT * FROM subscribers WHERE phone_number = $1"
    subscriber = await conn.fetchrow(query, phone)
    await conn.close()
    return subscriber


async def verify_subscriber_credentials(phone: str, password: str):
    """
    Проверяет, существует ли абонент с таким телефоном и верен ли пароль.
    """
    subscriber = await get_subscriber_by_phone(phone)
    if not subscriber or not subscriber['password_hash']:
        return None

    if not verify_password(password, subscriber['password_hash']):
        return None

    return subscriber


async def get_subscriber_payments(subscriber_id: int):
    """
    Получает историю платежей для конкретного абонента.
    """
    conn = await get_db_connection()
    query = "SELECT amount, payment_date, payment_method FROM payments WHERE subscriber_id = $1 ORDER BY payment_date DESC"
    payments = await conn.fetch(query, subscriber_id)
    await conn.close()
    return payments

async def get_subscriber_notifications(subscriber_id: int):
    """
    Получает историю уведомлений для конкретного абонента.
    """
    conn = await get_db_connection()
    query = "SELECT message, type, sent_date FROM notifications WHERE subscriber_id = $1 ORDER BY sent_date DESC"
    notifications = await conn.fetch(query, subscriber_id)
    await conn.close()
    return notifications

async def top_up_subscriber_balance(subscriber_id: int, amount: float):
    """
    Пополняет баланс абонента и создает запись о платеже.
    Выполняется в транзакции для обеспечения целостности данных.
    """
    conn = await get_db_connection()
    async with conn.transaction():
        # 1. Добавляем запись в историю платежей
        await conn.execute(
            "INSERT INTO payments (subscriber_id, amount, payment_method) VALUES ($1, $2, $3)",
            subscriber_id, amount, 'Пополнение через ЛК'
        )
        # 2. Обновляем баланс абонента
        await conn.execute(
            "UPDATE subscribers SET balance = balance + $1 WHERE subscriber_id = $2",
            amount, subscriber_id
        )
    await conn.close()


async def update_subscriber_contact_info(subscriber_id: int, full_name: str, address: str, phone: str):
    """
    Обновляет контактные данные абонента.
    """
    conn = await get_db_connection()
    # Проверяем, не занят ли новый номер телефона кем-то другим
    if phone:
        existing = await conn.fetchrow(
            "SELECT subscriber_id FROM subscribers WHERE phone_number = $1 AND subscriber_id != $2",
            phone, subscriber_id
        )
        if existing:
            await conn.close()
            return {"error": "Этот номер телефона уже используется другим абонентом."}

    await conn.execute(
        "UPDATE subscribers SET full_name = $1, address = $2, phone_number = $3 WHERE subscriber_id = $4",
        full_name, address, phone, subscriber_id
    )
    await conn.close()
    return {"success": True}

async def create_new_subscriber(full_name: str, address: str, phone: str, password: str):
    """
    Регистрирует нового абонента в системе.
    """
    # Проверяем, не занят ли уже номер телефона
    existing_subscriber = await get_subscriber_by_phone(phone)
    if existing_subscriber:
        return None  # Возвращаем None, если телефон уже используется

    # Хешируем пароль перед сохранением
    hashed_pass = hash_password(password)

    conn = await get_db_connection()
    query = """
    INSERT INTO subscribers (full_name, address, phone_number, password_hash, balance)
    VALUES ($1, $2, $3, $4, 0.00)
    RETURNING *
    """
    new_subscriber = await conn.fetchrow(query, full_name, address, phone, hashed_pass)
    await conn.close()
    return new_subscriber