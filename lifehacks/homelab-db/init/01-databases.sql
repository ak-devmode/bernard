-- Runs once, on first init of an empty volume. One database per domain; each app owns
-- its schema and applies it idempotently itself, so this file only creates the shells.
CREATE DATABASE todo_pulse;
CREATE DATABASE home;
\connect home
CREATE EXTENSION IF NOT EXISTS timescaledb;
