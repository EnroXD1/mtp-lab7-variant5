"""Подключение к PostgreSQL через psycopg2."""

import psycopg2

from lab7.catalog import Catalog


class PostgresCatalog(Catalog):
    """Те же операции с синтаксисом параметров и ID PostgreSQL."""

    _id_column = "BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
    _param = "%s"


def open_postgres(dsn: str) -> PostgresCatalog:
    """Открыть настроенную базу данных с ограничением времени подключения."""
    if not dsn.strip():
        raise ValueError("Укажи параметры подключения в LAB7_PG_DSN.")
    return PostgresCatalog(psycopg2.connect(dsn, connect_timeout=5))
