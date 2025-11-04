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