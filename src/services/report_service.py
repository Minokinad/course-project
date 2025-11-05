from datetime import date
from src.db.connection import get_db_connection

async def get_payment_summary(start_date: date, end_date: date):
    """
    Формирует СВОДНЫЙ отчет по платежам за указанный период.
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
    if summary and summary['total_payments'] > 0:
        return summary
    return {"total_payments": 0, "total_amount": 0}


async def get_all_payments_for_period(start_date: date, end_date: date):
    """
    Формирует ДЕТАЛЬНЫЙ список всех платежей за указанный период.
    """
    conn = await get_db_connection()
    query = """
    SELECT
        p.payment_id,
        p.amount,
        p.payment_date,
        p.payment_method,
        s.subscriber_id,
        s.full_name as subscriber_name
    FROM payments p
    LEFT JOIN subscribers s ON p.subscriber_id = s.subscriber_id
    WHERE p.payment_date >= $1 AND p.payment_date < $2::date + interval '1 day'
    ORDER BY p.payment_date DESC
    """
    rows = await conn.fetch(query, start_date, end_date)
    await conn.close()
    return rows