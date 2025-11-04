from typing import Optional
from src.db.connection import get_db_connection
from src.services.auth_service import hash_password
from src.services.log_service import log_action

async def fetch_all_employees():
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT employee_id, name, email, login, role FROM employees ORDER BY name")
    await conn.close()
    return rows

async def fetch_employee_by_id(emp_id: int):
    conn = await get_db_connection()
    row = await conn.fetchrow("SELECT employee_id, name, email, login, role FROM employees WHERE employee_id = $1", emp_id)
    await conn.close()
    return row

async def create_employee(name: str, email: str, login: str, password: str, role: str, user_login: str):
    hashed_pass = hash_password(password)
    conn = await get_db_connection()
    await conn.execute(
        "INSERT INTO employees (name, email, login, password_hash, role) VALUES ($1, $2, $3, $4, $5)",
        name, email, login, hashed_pass, role
    )
    await conn.close()
    await log_action("INFO", f"Создан новый сотрудник '{name}' (логин: '{login}') с ролью '{role}'.", user_login)


async def update_employee(emp_id: int, name: str, email: str, login: str, role: str, password: Optional[str], user_login: str):
    conn = await get_db_connection()
    if password:
        hashed_pass = hash_password(password)
        await conn.execute(
            "UPDATE employees SET name = $1, email = $2, login = $3, role = $4, password_hash = $5 WHERE employee_id = $6",
            name, email, login, role, hashed_pass, emp_id
        )
        log_message = f"Обновлены данные и пароль сотрудника '{name}' (ID: {emp_id})."
    else:
        await conn.execute(
            "UPDATE employees SET name = $1, email = $2, login = $3, role = $4 WHERE employee_id = $5",
            name, email, login, role, emp_id
        )
        log_message = f"Обновлены данные сотрудника '{name}' (ID: {emp_id})."

    await conn.close()
    await log_action("INFO", log_message, user_login)


async def delete_employee(emp_id: int, user_login: str):
    conn = await get_db_connection()
    emp_info = await conn.fetchrow("SELECT login, name FROM employees WHERE employee_id = $1", emp_id)
    await conn.execute("DELETE FROM employees WHERE employee_id = $1", emp_id)
    await conn.close()
    await log_action("WARNING", f"Удален сотрудник '{emp_info['name']}' (логин: '{emp_info['login']}', ID: {emp_id}).", user_login)