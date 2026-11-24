"""Интеграционные проверки с реальным PostgreSQL."""

import os
import unittest
from contextlib import closing
from uuid import uuid4

from psycopg2 import IntegrityError, sql

from lab7.catalog import Book
from lab7.postgres import open_postgres

TEST_DSN = os.environ.get("LAB7_TEST_PG_DSN")


@unittest.skipUnless(TEST_DSN, "Нужна отдельная база LAB7_TEST_PG_DSN")
class PostgresTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = self.enterContext(closing(open_postgres(TEST_DSN)))
        self.database = self.catalog.connection
        self.schema = sql.Identifier(f"lab7_test_{uuid4().hex}")
        with self.database, self.database.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(self.schema))
            search_path = sql.SQL("SET search_path TO {}").format(self.schema)
            cursor.execute(search_path)
        self.addCleanup(self.drop_schema)
        self.catalog.initialize()

    def drop_schema(self) -> None:
        with self.database, self.database.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(self.schema),
            )

    def test_insert_list_and_delete_on_postgres(self) -> None:
        keep = self.catalog.add_book("O'Reilly", "IT")
        remove = self.catalog.add_book("Дюна", "Романы")
        self.assertGreater(remove, keep)
        self.catalog.initialize()
        self.assertEqual(self.catalog.list_books("Романы"), (
            Book(remove, "Дюна", "Романы"),
        ))
        self.assertTrue(self.catalog.delete_book(remove))
        self.assertFalse(self.catalog.delete_book(remove))
        self.assertEqual(self.catalog.list_books(), (
            Book(keep, "O'Reilly", "IT"),
        ))

    def test_foreign_key_and_rollback(self) -> None:
        with self.assertRaises(IntegrityError):
            with self.database, self.database.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO books (title, category) VALUES (%s, %s)
                """, ("Книга", "Нет такой категории"))
        self.assertEqual(self.catalog.list_books(), ())
        book_id = self.catalog.add_book("Книга", "Новая категория")
        self.assertEqual(self.catalog.list_books()[0].id, book_id)
