from src.db.connection import get_db_connection


async def fetch_all_equipment():
    """
    Получает список всего оборудования в системе.
    Если оборудование привязано к договору, также возвращает имя абонента.
    """
    conn = await get_db_connection()
    # Исправленный запрос, который объединяет equipment, contracts и subscribers
    query = """
    SELECT
        e.equipment_id, e.type, e.serial_number, e.status,
        s.subscriber_id, s.full_name as subscriber_name
    FROM equipment e
    LEFT JOIN contracts c ON e.contract_id = c.contract_id
    LEFT JOIN subscribers s ON c.subscriber_id = s.subscriber_id
    ORDER BY e.equipment_id
    """
    rows = await conn.fetch(query)
    await conn.close()
    return rows