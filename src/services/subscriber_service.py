from src.db.connection import get_db_connection

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
    conn = await get_db_connection()
    search_pattern = f"%{query}%"
    rows = await conn.fetch(
        "SELECT * FROM subscribers WHERE full_name ILIKE $1 ORDER BY subscriber_id",
        search_pattern
    )
    await conn.close()
    return rows

async def create_subscriber(full_name: str, address: str, phone: str, balance: float):
    conn = await get_db_connection()
    await conn.execute(
        "INSERT INTO subscribers (full_name, address, phone_number, balance) VALUES ($1, $2, $3, $4)",
        full_name, address, phone, balance
    )
    await conn.close()

async def update_subscriber(sub_id: int, full_name: str, address: str, phone: str, balance: float):
    conn = await get_db_connection()
    await conn.execute(
        """
        UPDATE subscribers
        SET full_name = $1, address = $2, phone_number = $3, balance = $4
        WHERE subscriber_id = $5
        """,
        full_name, address, phone, sub_id
    )
    await conn.close()

async def delete_subscriber(sub_id: int):
    conn = await get_db_connection()
    await conn.execute("DELETE FROM subscribers WHERE subscriber_id = $1", sub_id)
    await conn.close()