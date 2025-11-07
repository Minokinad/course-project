DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS subscribers CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS system_logs CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS ticket_messages CASCADE;

CREATE TABLE employees (
    employee_id   SERIAL PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    role          VARCHAR(50) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    login         VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE subscribers (
    subscriber_id SERIAL PRIMARY KEY,
    full_name     VARCHAR(255) NOT NULL,
    address       TEXT,
    phone_number  VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    balance       NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    email VARCHAR(255) UNIQUE,
    is_confirmed BOOLEAN DEFAULT FALSE,
    confirmation_token VARCHAR(255) UNIQUE,
    avatar_url VARCHAR(255)
);

CREATE TABLE services (
    service_id  SERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    price       NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    status      VARCHAR(50) NOT NULL
);

CREATE TABLE contracts (
    contract_id   SERIAL PRIMARY KEY,
    subscriber_id INTEGER NOT NULL REFERENCES subscribers(subscriber_id),
    service_id    INTEGER NOT NULL REFERENCES services(service_id),
    start_date    DATE NOT NULL,
    status        VARCHAR(50) NOT NULL
);

CREATE TABLE equipment (
    equipment_id  SERIAL PRIMARY KEY,
    contract_id   INTEGER REFERENCES contracts(contract_id),
    type          VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    mac_address VARCHAR(17) UNIQUE,
    status        VARCHAR(50) NOT NULL
);

CREATE TABLE payments (
    payment_id     SERIAL PRIMARY KEY,
    subscriber_id  INTEGER NOT NULL REFERENCES subscribers(subscriber_id),
    amount         NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    payment_date   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50) NOT NULL
);

CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    subscriber_id   INTEGER NOT NULL REFERENCES subscribers(subscriber_id) ON DELETE CASCADE,
    message         TEXT NOT NULL,
    type            VARCHAR(50) NOT NULL,
    related_url VARCHAR(255),
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    sent_date TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_subscriber_id ON notifications(subscriber_id);

CREATE TABLE system_logs (
    log_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    user_login VARCHAR(255)
);

CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    subscriber_id INTEGER NOT NULL REFERENCES subscribers(subscriber_id) ON DELETE CASCADE,
    assigned_to_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'Новая',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tickets_status ON tickets(status);

CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON tickets
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TABLE ticket_messages (
    message_id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    subscriber_id INTEGER REFERENCES subscribers(subscriber_id) ON DELETE SET NULL,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    message_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_author CHECK (subscriber_id IS NOT NULL OR employee_id IS NOT NULL)
);

CREATE INDEX idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);

-- Ограничение на минимальный баланс
ALTER TABLE subscribers ADD CONSTRAINT balance_check CHECK (balance >= -1000.00);

-- Ограничение на формат email (простая проверка на наличие '@' и точки)
ALTER TABLE subscribers ADD CONSTRAINT email_format_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Убедимся, что телефон не пустой (если он обязателен)
ALTER TABLE subscribers ALTER COLUMN phone_number SET NOT NULL;

ALTER TABLE subscribers ADD CONSTRAINT phone_number_format_check
CHECK (phone_number ~* '^\+?[0-9]+$');

-- Ограничение на роли сотрудников
ALTER TABLE employees ADD CONSTRAINT role_check CHECK (role IN ('Администратор', 'Менеджер', 'Технический специалист'));

-- Ограничение на статусы договоров
ALTER TABLE contracts ADD CONSTRAINT contract_status_check CHECK (status IN ('Активен', 'Приостановлен', 'Расторгнут', 'Ожидает активации'));

-- Ограничение на цену услуги (не может быть отрицательной)
ALTER TABLE services ADD CONSTRAINT price_check CHECK (price >= 0);

-- Ограничение на формат MAC-адреса
ALTER TABLE equipment ADD CONSTRAINT mac_address_format_check CHECK (mac_address ~* '^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$');