from datetime import date
from src.db.connection import get_db_connection


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

async def create_contract(subscriber_id: int, service_id: int, start_date: date):
    """
    Создает новый договор со статусом "Ожидает активации".
    """
    conn = await get_db_connection()
    await conn.execute(
        """
        INSERT INTO contracts (subscriber_id, service_id, start_date, status)
        VALUES ($1, $2, $3, 'Ожидает активации')
        """,
        subscriber_id, service_id, start_date
    )
    await conn.close()

async def update_contract_status(contract_id: int, new_status: str):
    """
    Обновляет статус указанного договора.
    """
    # Проверка на допустимые статусы для безопасности
    allowed_statuses = ['Активен', 'Приостановлен', 'Расторгнут']
    if new_status not in allowed_statuses:
        # В реальном приложении здесь лучше выбросить исключение или вернуть ошибку
        print(f"Попытка установить недопустимый статус: {new_status}")
        return

    conn = await get_db_connection()
    await conn.execute(
        "UPDATE contracts SET status = $1 WHERE contract_id = $2",
        new_status, contract_id
    )
    await conn.close()


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
    rows = await conn.fetch("SELECT service_id, name, price FROM services ORDER BY name")
    await conn.close()
    return rows