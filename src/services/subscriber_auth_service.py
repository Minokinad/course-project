import secrets
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from src.config import settings
from src.db.connection import get_db_connection
from src.services.auth_service import verify_password, hash_password

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_confirmation_email(email_to: str, token: str):
    """Отправляет письмо с ссылкой для подтверждения."""
    # В реальном приложении этот URL лучше вынести в .env
    confirmation_url = f"http://127.0.0.1:8000/auth/confirm/{token}"

    html_content = f"""
    <h3>Подтверждение регистрации</h3>
    <p>Здравствуйте!</p>
    <p>Спасибо за регистрацию в АИС Интернет-провайдера. Пожалуйста, подтвердите ваш адрес электронной почты, перейдя по ссылке ниже:</p>
    <p><a href="{confirmation_url}">Подтвердить мой email</a></p>
    <p>Если вы не регистрировались, просто проигнорируйте это письмо.</p>
    """

    message = MessageSchema(
        subject="Подтверждение регистрации в АИС",
        recipients=[email_to],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def get_subscriber_by_phone(phone: str):
    """Находит абонента по номеру телефона."""
    conn = await get_db_connection()
    query = "SELECT * FROM subscribers WHERE phone_number = $1"
    subscriber = await conn.fetchrow(query, phone)
    await conn.close()
    return subscriber


async def verify_subscriber_credentials(email: str, password: str):
    """
    Проверяет, существует ли абонент с таким email, верен ли пароль и подтвержден ли аккаунт.
    Возвращает словарь с ошибкой или запись пользователя.
    """
    conn = await get_db_connection()
    subscriber = await conn.fetchrow("SELECT * FROM subscribers WHERE email = $1", email)
    await conn.close()

    if not subscriber or not verify_password(password, subscriber['password_hash']):
        return {"error": "Неверный email или пароль."}

    if not subscriber['is_confirmed']:
        # Можно добавить логику повторной отправки письма, но пока просто сообщим
        return {"error": "Ваш аккаунт не подтвержден. Проверьте свою электронную почту (включая папку 'Спам')."}

    # Если все проверки пройдены, возвращаем пользователя
    return dict(subscriber)


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


async def create_new_subscriber(full_name: str, address: str, phone: str, password: str, email: str):
    """
    Регистрирует нового абонента, но не активирует его до подтверждения email.
    """
    conn = await get_db_connection()
    # Проверяем, не занят ли уже email
    existing_by_email = await conn.fetchrow("SELECT subscriber_id FROM subscribers WHERE email = $1", email)
    if existing_by_email:
        await conn.close()
        return {"error": "Этот email уже зарегистрирован."}

    # Проверяем, не занят ли уже номер телефона
    existing_by_phone = await conn.fetchrow("SELECT subscriber_id FROM subscribers WHERE phone_number = $1", phone)
    if existing_by_phone:
        await conn.close()
        return {"error": "Этот номер телефона уже зарегистрирован."}

    hashed_pass = hash_password(password)
    confirmation_token = secrets.token_urlsafe(32)

    query = """
    INSERT INTO subscribers (full_name, address, phone_number, password_hash, balance, email, is_confirmed, confirmation_token)
    VALUES ($1, $2, $3, $4, 0.00, $5, FALSE, $6)
    RETURNING *
    """
    new_subscriber = await conn.fetchrow(query, full_name, address, phone, hashed_pass, email, confirmation_token)
    await conn.close()

    if new_subscriber:
        # Отправляем письмо только если пользователь успешно создан
        await send_confirmation_email(email, confirmation_token)
        return dict(new_subscriber)

    return None