"""Проверка кэша по реально выполненным запросам SQLite."""

import unittest
from contextlib import closing

from lab7.catalog import Book, open_sqlite


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = self.enterContext(closing(open_sqlite(":memory:")))
        self.catalog.initialize()
        self.selects = []
        self.catalog.connection.set_trace_callback(self.record_select)

    def record_select(self, query: str) -> None:
        if query.lstrip().startswith("SELECT"):
            self.selects.append(query)

    def test_repeat_skips_sql_and_different_filters_have_separate_keys(self):
        book_id = self.catalog.add_book("Дюна", "Романы")
        expected = (Book(book_id, "Дюна", "Романы"),)
        self.assertEqual(self.catalog.list_books(), expected)
        self.assertEqual(self.catalog.list_books(None), expected)
        self.assertEqual(self.catalog.list_books("Романы"), expected)
        self.assertEqual(self.catalog.list_books("IT"), ())
        self.assertEqual(self.catalog.list_books("IT"), ())
        self.assertEqual(len(self.selects), 3)
        self.assertEqual(self.catalog.cache_counts(), (2, 3))

    def test_insert_refreshes_previously_empty_result(self) -> None:
        self.assertEqual(self.catalog.list_books("IT"), ())
        book_id = self.catalog.add_book("Чистый код", "IT")
        self.assertEqual(self.catalog.list_books("IT"), (
            Book(book_id, "Чистый код", "IT"),
        ))
        self.assertEqual(len(self.selects), 2)

    def test_delete_refreshes_both_all_and_filtered_lists(self) -> None:
        book_id = self.catalog.add_book("Дюна", "Романы")
        self.assertEqual(len(self.catalog.list_books()), 1)
        self.assertEqual(len(self.catalog.list_books("Романы")), 1)
        self.assertTrue(self.catalog.delete_book(book_id))
        self.assertEqual(self.catalog.list_books(), ())
        self.assertEqual(self.catalog.list_books("Романы"), ())
        self.assertEqual(len(self.selects), 4)

    def test_cache_does_not_share_results_between_databases(self) -> None:
        self.catalog.add_book("Дюна", "Романы")
        self.assertEqual(len(self.catalog.list_books()), 1)
        with closing(open_sqlite(":memory:")) as other:
            other.initialize()
            self.assertEqual(other.list_books(), ())
