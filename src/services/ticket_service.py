from typing import Optional
from src.db.connection import get_db_connection
from src.services.log_service import log_action


async def create_ticket(subscriber_id: int, title: str, description: str):
    """
    Создание новой заявки от абонента.
    """
    conn = await get_db_connection()
    new_ticket_id = await conn.fetchval(
        """
        INSERT INTO tickets (subscriber_id, title, description, status)
        VALUES ($1, $2, $3, 'Новая') RETURNING ticket_id
        """,
        subscriber_id, title, description
    )
    await conn.close()
    await log_action(
        "INFO", f"Абонент (ID: {subscriber_id}) создал новую заявку ID: {new_ticket_id}.", f"subscriber_{subscriber_id}"
    )


async def fetch_tickets_by_subscriber_id(subscriber_id: int):
    """
    Получение всех заявок для конкретного абонента.
    """
    conn = await get_db_connection()
    tickets = await conn.fetch("SELECT * FROM tickets WHERE subscriber_id = $1 ORDER BY created_at DESC", subscriber_id)
    await conn.close()
    return tickets


async def fetch_all_tickets(status_filter: Optional[str] = None, sort_by: str = 'created_at', order: str = 'desc'):
    """
    Получение всех заявок для сотрудников с возможностью фильтрации и сортировки.
    """
    conn = await get_db_connection()

    allowed_sort_columns = {
        "ticket_id": "t.ticket_id",
        "created_at": "t.created_at",
        "updated_at": "t.updated_at",
        "status": "t.status",
        "subscriber_name": "s.full_name",
        "assignee_name": "e.name"
    }

    query = """
    SELECT
        t.*,
        s.full_name as subscriber_name,
        e.name as assignee_name
    FROM tickets t
    JOIN subscribers s ON t.subscriber_id = s.subscriber_id
    LEFT JOIN employees e ON t.assigned_to_id = e.employee_id
    """

    params = []
    if status_filter:
        query += " WHERE t.status = $1"
        params.append(status_filter)

    order_direction = "DESC" if order == 'desc' else "ASC"
    order_by_clause = f"ORDER BY {allowed_sort_columns.get(sort_by, 't.created_at')} {order_direction}"
    query += f" {order_by_clause}"

    tickets = await conn.fetch(query, *params)
    await conn.close()
    return tickets


async def fetch_ticket_by_id(ticket_id: int):
    """
    Получение одной заявки по ID, включая имена абонента и исполнителя.
    """
    conn = await get_db_connection()
    query = """
    SELECT
        t.*,
        s.full_name as subscriber_name,
        e.name as assignee_name
    FROM tickets t
    JOIN subscribers s ON t.subscriber_id = s.subscriber_id
    LEFT JOIN employees e ON t.assigned_to_id = e.employee_id
    WHERE t.ticket_id = $1
    """
    ticket = await conn.fetchrow(query, ticket_id)
    await conn.close()
    return ticket


async def update_ticket(ticket_id: int, status: str, assigned_to_id: Optional[int], user_login: str):
    """
    Обновление статуса и/или назначенного сотрудника для заявки.
    """
    conn = await get_db_connection()
    await conn.execute(
        "UPDATE tickets SET status = $1, assigned_to_id = $2 WHERE ticket_id = $3",
        status, assigned_to_id, ticket_id
    )
    await conn.close()
    await log_action(
        "INFO",
        f"Статус заявки ID: {ticket_id} изменен на '{status}'. Назначен сотрудник ID: {assigned_to_id or 'не назначен'}.",
        user_login
    )

async def fetch_messages_for_ticket(ticket_id: int):
    """
    Получает всю переписку по конкретной заявке.
    """
    conn = await get_db_connection()
    query = """
    SELECT
        m.message_id,
        m.message_text,
        m.created_at,
        m.subscriber_id,
        m.employee_id,
        -- Используем COALESCE, чтобы получить имя автора из нужной таблицы
        COALESCE(s.full_name, e.name) as author_name
    FROM ticket_messages m
    LEFT JOIN subscribers s ON m.subscriber_id = s.subscriber_id
    LEFT JOIN employees e ON m.employee_id = e.employee_id
    WHERE m.ticket_id = $1
    ORDER BY m.created_at ASC
    """
    messages = await conn.fetch(query, ticket_id)
    await conn.close()
    return messages


async def add_message_to_ticket(ticket_id: int, message_text: str, user_login: str, subscriber_id: int = None, employee_id: int = None):
    """
    Добавляет новое сообщение в заявку.
    """
    conn = await get_db_connection()
    # Обновляем поле updated_at у самой заявки, чтобы она "поднялась" в списке
    async with conn.transaction():
        await conn.execute(
            """
            INSERT INTO ticket_messages (ticket_id, subscriber_id, employee_id, message_text)
            VALUES ($1, $2, $3, $4)
            """,
            ticket_id, subscriber_id, employee_id, message_text
        )
        await conn.execute(
            "UPDATE tickets SET updated_at = NOW() WHERE ticket_id = $1",
            ticket_id
        )
    await conn.close()
    author_type = "Абонент" if subscriber_id else "Сотрудник"
    await log_action(
        "INFO",
        f"{author_type} (ID: {subscriber_id or employee_id}) добавил сообщение в заявку ID: {ticket_id}.",
        user_login
    )