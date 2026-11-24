# Лабораторная №7 - работа с СУБД в Python

Дерябин Илья Игоревич, группа 221341, вариант 5, лабораторная №7

Каталог книг с категориями. Одни и те же команды работают с файлом SQLite
или с базой PostgreSQL.

| Уровень | № | Задание | Где смотреть |
| --- | --- | --- | --- |
| Средний | 5 | Удалить запись | [catalog.py](lab7/catalog.py), метод `delete_book` |
| Средний | 7 | Создать несколько таблиц | `books` и `categories`, связанные внешним ключом |
| Средний | 1 | Создать БД SQLite и таблицу | `open_sqlite`, команда `init` |
| Повышенный | 6 | Работа с PostgreSQL через psycopg2 | [postgres.py](lab7/postgres.py), ключ `--backend postgres` |
| Повышенный | 8 | Кэширование запросов | `Catalog.list_books`, команда `cache-demo` |

## SQLite

Нужен Python 3.11 или новее со SQLite 3.35+ для `RETURNING`.
Команды PowerShell выполняются из корня репозитория.

~~~powershell
py -m venv .venv
$pythonExe = '.\.venv\Scripts\python.exe'
& $pythonExe -m pip install -r requirements-dev.txt
& $pythonExe -X utf8 main.py init
& $pythonExe -X utf8 main.py add 'Дюна' 'Романы'
& $pythonExe -X utf8 main.py list
& $pythonExe -X utf8 main.py cache-demo --category 'Романы'
& $pythonExe -X utf8 main.py delete 1
& $pythonExe -X utf8 main.py list
~~~

В новой базе список после добавления содержит `1 | Дюна | Романы`.
Если база уже есть, для удаления возьми ID из вывода команды `list`.
По умолчанию файл называется `books.sqlite3`. Другой путь указывается
перед командой, например `main.py --db demo.sqlite3 init`.

## PostgreSQL

В запущенном PostgreSQL создай отдельную базу `mtp_lab7`. Для уже
установленного локального сервера с ролью `postgres` можно использовать
`createdb -h 127.0.0.1 -U postgres -W mtp_lab7`.

~~~powershell
$env:LAB7_PG_DSN = 'host=127.0.0.1 port=5432 dbname=mtp_lab7 user=postgres'
$pgSecret = Read-Host 'Пароль PostgreSQL' -AsSecureString
$env:PGPASSWORD = [System.Net.NetworkCredential]::new('', $pgSecret).Password
& $pythonExe -X utf8 main.py --backend postgres init
& $pythonExe -X utf8 main.py --backend postgres add 'Солярис' 'Фантастика'
& $pythonExe -X utf8 main.py --backend postgres list --category 'Фантастика'
& $pythonExe -X utf8 main.py --backend postgres cache-demo
~~~

Для удаления используется та же команда `delete ID`. Пароль можно
также указать в [файле паролей libpq](https://www.postgresql.org/docs/18/libpq-pgpass.html).

## Кэш и тесты

`cache-demo` дважды вызывает одну выборку в рамках одного подключения.
Сначала счётчики показывают 0 попаданий и 1 промах, затем 1 попадание и
1 промах. Кэш хранит до 32 выборок, отдельно для каждого фильтра.
После успешного добавления или удаления он очищается. Изменения из другого
процесса видны при новом подключении.

~~~powershell
& $pythonExe -X utf8 -m unittest discover -s tests -v
& $pythonExe -m flake8 lab7 main.py tests
~~~

Чтобы включить два теста PostgreSQL, укажи DSN отдельной тестовой
базы в `LAB7_TEST_PG_DSN` перед запуском. Тесты создают временные
схемы с уникальными именами и удаляют их по завершении. GitHub Actions
запускает все тесты с отдельным контейнером PostgreSQL.

[Отчёт о проверке](docs/checks.md) ·
[GitHub Actions](https://github.com/EnroXD1/mtp-lab7-variant5/actions)
