"""Команды учебного каталога книг."""

import argparse
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import psycopg2

from lab7.catalog import Catalog, open_sqlite
from lab7.postgres import open_postgres


def init_catalog(catalog: Catalog, args: argparse.Namespace) -> int:
    """Подготовить две таблицы в выбранной базе."""
    catalog.initialize()
    print("Таблицы books и categories готовы.")
    return 0


def add_book(catalog: Catalog, args: argparse.Namespace) -> int:
    """Записать книгу и вывести присвоенный ID."""
    book_id = catalog.add_book(args.title, args.category)
    print(f"Добавлена книга #{book_id}.")
    return 0


def list_books(catalog: Catalog, args: argparse.Namespace) -> int:
    """Напечатать каталог с учётом фильтра."""
    books = catalog.list_books(args.category)
    if not books:
        print("Книги не найдены.")
    for book in books:
        print(f"{book.id} | {book.title} | {book.category}")
    return 0


def delete_book(catalog: Catalog, args: argparse.Namespace) -> int:
    """Сообщить, удалось ли удалить книгу."""
    if not catalog.delete_book(args.id):
        print(f"Книга #{args.id} не найдена.", file=sys.stderr)
        return 1
    print(f"Книга #{args.id} удалена.")
    return 0


def demo_cache(catalog: Catalog, args: argparse.Namespace) -> int:
    """Дважды прочитать одну выборку в рамках одного подключения."""
    for number in (1, 2):
        books = catalog.list_books(args.category)
        hits, misses = catalog.cache_counts()
        print(
            f"Запрос {number}: записей={len(books)}, "
            f"попаданий={hits}, промахов={misses}"
        )
    return 0


def main() -> int:
    """Разобрать команду, открыть выбранную базу и выполнить операцию."""
    parser = argparse.ArgumentParser(description="Каталог книг, МТП №7")
    parser.add_argument("--backend", choices=("sqlite", "postgres"),
                        default="sqlite", help="СУБД (по умолчанию sqlite)")
    parser.add_argument("--db", type=Path, default=Path("books.sqlite3"),
                        help="Путь к файлу SQLite")
    commands = parser.add_subparsers(dest="command", required=True)

    command = commands.add_parser("init", help="Создать таблицы")
    command.set_defaults(handler=init_catalog)

    command = commands.add_parser("add", help="Добавить книгу")
    command.add_argument("title", help="Название")
    command.add_argument("category", help="Категория")
    command.set_defaults(handler=add_book)

    command = commands.add_parser("delete", help="Удалить книгу по ID")
    command.add_argument("id", type=int)
    command.set_defaults(handler=delete_book)

    for name, handler, help_text in (
        ("list", list_books, "Показать книги"),
        ("cache-demo", demo_cache, "Сравнить две одинаковые выборки"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--category", help="Фильтр по категории")
        command.set_defaults(handler=handler)

    args = parser.parse_args()
    try:
        if args.backend == "postgres":
            catalog = open_postgres(os.environ.get("LAB7_PG_DSN", ""))
        else:
            if args.command != "init" and not args.db.is_file():
                raise ValueError("Файл базы не найден. Выполни команду init.")
            catalog = open_sqlite(args.db)
        with closing(catalog):
            return args.handler(catalog, args)
    except (ValueError, sqlite3.Error, psycopg2.Error) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
