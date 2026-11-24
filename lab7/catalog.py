"""Запросы каталога, общие для SQLite и PostgreSQL."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from psycopg2.extensions import connection as PostgresConnection


class Book(NamedTuple):
    """Строка каталога с названием категории."""

    id: int
    title: str
    category: str


class Catalog:
    """Объект каталога владеет одним соединением с базой."""

    _id_column = "INTEGER PRIMARY KEY AUTOINCREMENT"
    _param = "?"

    def __init__(
        self, connection: sqlite3.Connection | PostgresConnection,
    ) -> None:
        self.connection = connection
        self._cached_books = lru_cache(maxsize=32)(self._select_books)

    def initialize(self) -> None:
        """Создать две связанные таблицы, сохранив существующие записи."""
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY NOT NULL,
                    CHECK (length(trim(name)) > 0)
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS books (
                    id {self._id_column},
                    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                    category TEXT NOT NULL REFERENCES categories(name)
                )
            """)

    def add_book(self, title: str, category: str) -> int:
        """Добавить книгу и при необходимости создать категорию."""
        title, category = title.strip(), category.strip()
        if not title or not category:
            raise ValueError("Название и категория не должны быть пустыми.")
        param = self._param
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute(f"""
                INSERT INTO categories (name) VALUES ({param})
                ON CONFLICT (name) DO NOTHING
            """, (category,))
            cursor.execute(f"""
                INSERT INTO books (title, category) VALUES ({param}, {param})
                RETURNING id
            """, (title, category))
            book_id, = cursor.fetchone()
        self._cached_books.cache_clear()
        return book_id

    def list_books(self, category: str | None = None) -> tuple[Book, ...]:
        """Вернуть результат выборки с кэшем для каждого фильтра."""
        return self._cached_books(category)

    def cache_counts(self) -> tuple[int, int]:
        """Вернуть число попаданий и промахов кэша с последней очистки."""
        info = self._cached_books.cache_info()
        return info.hits, info.misses

    def _select_books(self, category: str | None) -> tuple[Book, ...]:
        query = """
            SELECT b.id, b.title, c.name
            FROM books b JOIN categories c ON b.category = c.name
        """
        params = ()
        if category is not None:
            query += f" WHERE c.name = {self._param}"
            params = (category,)
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute(query + " ORDER BY b.id", params)
            return tuple(Book(*row) for row in cursor.fetchall())

    def delete_book(self, book_id: int) -> bool:
        """Удалить одну книгу по ID и сообщить, была ли она в каталоге."""
        if type(book_id) is not int or not 1 <= book_id <= 2**63 - 1:
            raise ValueError("ID книги должен быть в пределах от 1 до 2^63-1.")
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute(
                f"DELETE FROM books WHERE id = {self._param}", (book_id,),
            )
            deleted = cursor.rowcount == 1
        if deleted:
            self._cached_books.cache_clear()
        return deleted

    def close(self) -> None:
        """Закрыть соединение с базой."""
        self.connection.close()


def open_sqlite(path: str | Path) -> Catalog:
    """Открыть файл SQLite или создать его по указанному пути."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON").close()
    return Catalog(connection)
