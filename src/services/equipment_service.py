from typing import Optional
from src.db.connection import get_db_connection


async def fetch_all_equipment():
    """
    Получает список всего оборудования в системе.
    Если оборудование привязано к договору, также возвращает имя абонента.
    """
    conn = await get_db_connection()
    query = """
    SELECT
        e.equipment_id, e.type, e.serial_number, e.status, e.contract_id,
        s.subscriber_id, s.full_name as subscriber_name
    FROM equipment e
    LEFT JOIN contracts c ON e.contract_id = c.contract_id
    LEFT JOIN subscribers s ON c.subscriber_id = s.subscriber_id
    ORDER BY e.equipment_id
    """
    rows = await conn.fetch(query)
    await conn.close()
    return rows

async def fetch_equipment_by_id(equipment_id: int):
    """
    Получает одно устройство по его ID.
    """
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT * FROM equipment WHERE equipment_id = $1", equipment_id)
    await conn.close()
    return row

async def create_equipment(type: str, serial_number: str, status: str, contract_id: Optional[int]):
    """
    Добавляет новое оборудование в базу данных.
    """
    conn = await get_db_connection()
    await conn.execute(
        """
        INSERT INTO equipment (type, serial_number, status, contract_id)
        VALUES ($1, $2, $3, $4)
        """,
        type, serial_number, status, contract_id
    )
    await conn.close()


async def update_equipment(equipment_id: int, type: str, serial_number: str, status: str, contract_id: Optional[int]):
    """
    Обновляет информацию об оборудовании, включая его привязку к договору.
    """
    conn = await get_db_connection()
    await conn.execute(
        """
        UPDATE equipment
        SET type = $1, serial_number = $2, status = $3, contract_id = $4
        WHERE equipment_id = $5
        """,
        type, serial_number, status, contract_id, equipment_id
    )
    await conn.close()


async def delete_equipment(equipment_id: int):
    """
    Удаляет оборудование из системы.
    """
    conn = await get_db_connection()
    await conn.execute("DELETE FROM equipment WHERE equipment_id = $1", equipment_id)
    await conn.close()


async def fetch_available_contracts_for_linking(current_contract_id: Optional[int] = None):
    """
    Получает список договоров, к которым еще не привязано оборудование.
    Позволяет включить в список текущий договор, если он редактируется.
    """
    conn = await get_db_connection()
    # Запрос выбирает все договоры, ID которых нет в списке 'занятых' ID в таблице equipment.
    # Если передан current_contract_id, он также будет включен в список,
    # чтобы можно было оставить текущую привязку.
    query = """
    SELECT c.contract_id, c.status, s.full_name
    FROM contracts c
    JOIN subscribers s ON c.subscriber_id = s.subscriber_id
    WHERE c.contract_id NOT IN (
        SELECT contract_id FROM equipment WHERE contract_id IS NOT NULL
    )
    """
    if current_contract_id:
        query += " OR c.contract_id = $1"
        rows = await conn.fetch(query, current_contract_id)
    else:
        rows = await conn.fetch(query)

    await conn.close()
    return rows