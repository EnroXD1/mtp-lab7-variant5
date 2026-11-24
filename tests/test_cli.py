"""Проверка сценария запуска из командной строки."""

import os
from pathlib import Path
import subprocess
import sys
import unittest
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.pop("LAB7_PG_DSN", None)
        return subprocess.run(
            [sys.executable, "-X", "utf8", "main.py", *args],
            cwd=ROOT, env=env, capture_output=True, encoding="utf-8",
            timeout=15,
        )

    def test_sqlite_lifecycle_in_separate_processes(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "library with spaces.sqlite3"

            def command(*args: str, code: int = 0) -> str:
                result = self.run_cli("--db", str(path), *args)
                self.assertEqual(result.returncode, code, result.stderr)
                return result.stdout

            command("list", code=1)
            self.assertFalse(path.exists())
            command("init")
            command("add", "Дюна", "Романы")
            command("add", "Алгоритмы", "IT")
            filtered = command("list", "--category", "Романы")
            self.assertEqual(filtered.strip(), "1 | Дюна | Романы")
            demo = command("cache-demo", "--category", "Романы")
            self.assertIn("попаданий=0, промахов=1", demo)
            self.assertIn("попаданий=1, промахов=1", demo)
            command("delete", "1")
            command("delete", "1", code=1)
            self.assertEqual(command("list").strip(), "2 | Алгоритмы | IT")

    def test_missing_postgres_configuration(self) -> None:
        result = self.run_cli("--backend", "postgres", "init")
        self.assertEqual(result.returncode, 1)
        self.assertIn("LAB7_PG_DSN", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
