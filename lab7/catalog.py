"""Хранение книг в локальной базе SQLite."""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import NamedTuple


class Book(NamedTuple):
    """Строка каталога с названием категории."""

    id: int
    title: str
    category: str


class Catalog:
    """Объект каталога владеет одним соединением с базой."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        """Создать две связанные таблицы, сохранив существующие записи."""
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY NOT NULL,
                    CHECK (length(trim(name)) > 0)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
                    category TEXT NOT NULL REFERENCES categories(name)
                )
            """)

    def add_book(self, title: str, category: str) -> int:
        """Добавить книгу и при необходимости создать категорию."""
        title, category = title.strip(), category.strip()
        if not title or not category:
            raise ValueError("Название и категория не должны быть пустыми.")
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute("""
                INSERT INTO categories (name) VALUES (?)
                ON CONFLICT (name) DO NOTHING
            """, (category,))
            cursor.execute("""
                INSERT INTO books (title, category) VALUES (?, ?) RETURNING id
            """, (title, category))
            book_id, = cursor.fetchone()
        return book_id

    def list_books(self, category: str | None = None) -> tuple[Book, ...]:
        """Найти все книги или книги выбранной категории."""
        query = """
            SELECT b.id, b.title, c.name
            FROM books b JOIN categories c ON b.category = c.name
        """
        params = ()
        if category is not None:
            query += " WHERE c.name = ?"
            params = (category,)
        with self.connection, closing(self.connection.cursor()) as cursor:
            cursor.execute(query + " ORDER BY b.id", params)
            return tuple(Book(*row) for row in cursor.fetchall())

    def close(self) -> None:
        """Закрыть соединение с базой."""
        self.connection.close()


def open_sqlite(path: str | Path) -> Catalog:
    """Открыть файл SQLite или создать его по указанному пути."""
    connection = sqlite3.connect(path)
    with closing(connection.execute("PRAGMA foreign_keys = ON")):
        pass
    return Catalog(connection)
