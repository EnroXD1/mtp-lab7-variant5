"""Хранение книг в локальной базе SQLite."""

import sqlite3
from contextlib import closing
from pathlib import Path


class Catalog:
    """Объект каталога владеет одним соединением с базой."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        """Создать таблицу, если её ещё нет."""
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL CHECK (length(trim(title)) > 0)
                )
            """)

    def close(self) -> None:
        """Закрыть соединение с базой."""
        self.connection.close()


def open_sqlite(path: str | Path) -> Catalog:
    """Открыть файл SQLite или создать его по указанному пути."""
    return Catalog(sqlite3.connect(path))
