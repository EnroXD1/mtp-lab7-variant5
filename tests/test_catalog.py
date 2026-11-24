"""Проверки каталога на реальных временных базах SQLite."""

import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from lab7.catalog import Book, open_sqlite


class SQLiteTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = self.enterContext(TemporaryDirectory())
        self.path = Path(directory) / "books.sqlite3"
        self.catalog = self.enterContext(closing(open_sqlite(self.path)))
        self.catalog.initialize()

    def test_file_and_tables_exist(self) -> None:
        self.assertTrue(self.path.is_file())
        with closing(sqlite3.connect(self.path)) as database:
            tables = database.execute("""
                SELECT name FROM sqlite_master WHERE type = 'table'
            """).fetchall()
        self.assertEqual(set(tables), {("books",), ("categories",)})

    def test_initialize_twice_preserves_persisted_rows(self) -> None:
        book_id = self.catalog.add_book("Мастер и Маргарита", "Романы")
        with closing(open_sqlite(self.path)) as reopened:
            reopened.initialize()
            self.assertEqual(reopened.list_books(), (
                Book(book_id, "Мастер и Маргарита", "Романы"),
            ))

    def test_categories_are_reused(self) -> None:
        first = self.catalog.add_book("Чистый код", " IT ")
        second = self.catalog.add_book("Алгоритмы", "IT")
        self.catalog.add_book("Дюна", "Романы")
        self.assertEqual(self.catalog.list_books("IT"), (
            Book(first, "Чистый код", "IT"), Book(second, "Алгоритмы", "IT"),
        ))
        with closing(sqlite3.connect(self.path)) as database:
            rows = database.execute("SELECT name FROM categories").fetchall()
        self.assertEqual(set(rows), {("IT",), ("Романы",)})

    def test_title_with_apostrophe(self) -> None:
        book_id = self.catalog.add_book("O'Reilly", "IT")
        self.assertEqual(self.catalog.list_books(), (
            Book(book_id, "O'Reilly", "IT"),
        ))

    def test_foreign_key_rejects_unknown_category(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with self.catalog.connection as database:
                database.execute("""
                    INSERT INTO books (title, category) VALUES ('Книга', 'Нет')
                """)
        self.assertEqual(self.catalog.list_books(), ())

    def test_blank_title_or_category_is_rejected(self) -> None:
        for title, category in ((" ", "IT"), ("Книга", " ")):
            with self.subTest(title=title, category=category):
                with self.assertRaises(ValueError):
                    self.catalog.add_book(title, category)
        self.assertEqual(self.catalog.list_books(), ())
