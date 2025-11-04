from datetime import date
from src.db.connection import get_db_connection
from src.services.log_service import log_action

# ... (первые две функции без изменений)
async def fetch_contracts_by_subscriber_id(subscriber_id: int):
    """
    Получает все договоры для конкретного абонента.
    """
    conn = await get_db_connection()
    query = """
    SELECT c.contract_id, c.start_date, c.status, s.name as service_name, s.price
    FROM contracts c
    JOIN services s ON c.service_id = s.service_id
    WHERE c.subscriber_id = $1
    ORDER BY c.start_date DESC
    """
    contracts = await conn.fetch(query, subscriber_id)
    await conn.close()
    return contracts


async def fetch_all_contracts():
    """
    Получает все договоры в системе с информацией об абонентах и услугах.
    """
    conn = await get_db_connection()
    query = """
    SELECT
        c.contract_id, c.start_date, c.status,
        s.name as service_name,
        sub.full_name as subscriber_name, sub.subscriber_id
    FROM contracts c
    JOIN services s ON c.service_id = s.service_id
    JOIN subscribers sub ON c.subscriber_id = sub.subscriber_id
    ORDER BY c.start_date DESC
    """
    contracts = await conn.fetch(query)
    await conn.close()
    return contracts


async def create_contract(subscriber_id: int, service_id: int, start_date: date, user_login: str):
    """
    Создает новый договор со статусом "Ожидает активации".
    """
    conn = await get_db_connection()
    new_contract_id = await conn.fetchval(
        """
        INSERT INTO contracts (subscriber_id, service_id, start_date, status)
        VALUES ($1, $2, $3, 'Ожидает активации')
        RETURNING contract_id
        """,
        subscriber_id, service_id, start_date
    )
    await conn.close()
    await log_action(
        "INFO", f"Создан новый договор ID: {new_contract_id} для абонента ID: {subscriber_id}.", user_login
    )

async def update_contract_status(contract_id: int, new_status: str, user_login: str):
    """
    Обновляет статус указанного договора.
    """
    allowed_statuses = ['Активен', 'Приостановлен', 'Расторгнут']
    if new_status not in allowed_statuses:
        await log_action(
            "WARNING", f"Попытка установить недопустимый статус '{new_status}' для договора ID: {contract_id}.", user_login
        )
        return

    conn = await get_db_connection()
    await conn.execute(
        "UPDATE contracts SET status = $1 WHERE contract_id = $2",
        new_status, contract_id
    )
    await conn.close()
    await log_action(
        "INFO", f"Статус договора ID: {contract_id} изменен на '{new_status}'.", user_login
    )


async def fetch_all_subscribers_for_selection():
    """
    Получает ID и ФИО всех абонентов для использования в выпадающих списках.
    """
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT subscriber_id, full_name FROM subscribers ORDER BY full_name")
    await conn.close()
    return rows

async def fetch_all_services_for_selection():
    """
    Получает ID и название всех услуг для использования в выпадающих списках.
    """
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT service_id, name, price FROM services WHERE status = 'Активна' ORDER BY name")
    await conn.close()
    return rows