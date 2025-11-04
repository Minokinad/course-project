from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Пароли для сотрудников
employee_passwords = {
    "admin": "admin_pass",
    "manager": "manager_pass",
    "tech": "tech_pass"
}


# Пароли для абонентов
subscriber_passwords = {
    "Иванов": '1112233',
    "Петров": '2223344',
    "Сидорова": '3334455',
    "Козлов": '4445566',
    "Новикова": '5556677',
    "Васильев": '6667788',
    "Зайцева": '7778899',
    "Павлов": '8889900',
    "Романова": '9990011',
    "Волков": '1122334'
}

print("--- Хеши для СОТРУДНИКОВ ---")
for login, password in employee_passwords.items():
    hashed_password = pwd_context.hash(password)
    print(f"-- Пользователь '{login}', пароль '{password}':")
    print(f"'{hashed_password}'\n")

print("\n--- Хеши для АБОНЕНТОВ ---")
for name, password in subscriber_passwords.items():
    hashed_password = pwd_context.hash(password)
    print(f"-- Абонент '{name}', пароль '{password}':")
    print(f"'{hashed_password}'\n")