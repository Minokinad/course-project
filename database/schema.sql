DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS equipment CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;
DROP TABLE IF EXISTS services CASCADE;
DROP TABLE IF EXISTS subscribers CASCADE;
DROP TABLE IF EXISTS employees CASCADE;

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
    password_hash VARCHAR(255) NOT NULL,
    balance       NUMERIC(10, 2) NOT NULL DEFAULT 0.00
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
    subscriber_id   INTEGER NOT NULL REFERENCES subscribers(subscriber_id),
    message         TEXT NOT NULL,
    type            VARCHAR(50) NOT NULL,
    sent_date       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
