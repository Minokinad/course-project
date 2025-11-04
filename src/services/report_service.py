from datetime import date
from src.db.connection import get_db_connection

async def get_payment_summary(start_date: date, end_date: date):
    """
    Формирует отчет по платежам за указанный период.
    Возвращает общее количество платежей и их суммарный объем.
    """
    conn = await get_db_connection()
    query = """
    SELECT
        COUNT(payment_id) as total_payments,
        SUM(amount) as total_amount
    FROM payments
    WHERE payment_date >= $1 AND payment_date < $2::date + interval '1 day'
    """
    summary = await conn.fetchrow(query, start_date, end_date)
    await conn.close()
    # Если за период не было платежей, fetchrow вернет None
    if summary and summary['total_payments'] > 0:
        return summary
    return {"total_payments": 0, "total_amount": 0}