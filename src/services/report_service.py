from datetime import date, timedelta
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


async def get_daily_payment_dynamics(start_date: date, end_date: date):
    """
    Агрегирует сумму платежей по каждому дню в заданном периоде.
    Возвращает словарь с датами (labels) и суммами (data).
    """
    conn = await get_db_connection()
    query = """
    SELECT
        date_trunc('day', payment_date)::date as day,
        SUM(amount) as daily_total
    FROM payments
    WHERE payment_date >= $1 AND payment_date < $2::date + interval '1 day'
    GROUP BY day
    ORDER BY day;
    """
    rows = await conn.fetch(query, start_date, end_date)
    await conn.close()

    labels = []
    data = []

    date_map = {row['day']: float(row['daily_total']) for row in rows}
    current_date = start_date
    while current_date <= end_date:
        labels.append(current_date.strftime('%d.%m.%Y'))
        data.append(date_map.get(current_date, 0))
        current_date += timedelta(days=1)

    return {"labels": labels, "data": data}

async def get_payment_methods_distribution(start_date: date, end_date: date):
    """
    Считает количество платежей по каждому способу оплаты.
    """
    conn = await get_db_connection()
    query = """
    SELECT
        payment_method,
        COUNT(payment_id) as count
    FROM payments
    WHERE payment_date >= $1 AND payment_date < $2::date + interval '1 day'
    GROUP BY payment_method
    ORDER BY count DESC;
    """
    rows = await conn.fetch(query, start_date, end_date)
    await conn.close()

    # Готовим данные для Chart.js
    labels = [row['payment_method'] for row in rows]
    data = [row['count'] for row in rows]

    return {"labels": labels, "data": data}