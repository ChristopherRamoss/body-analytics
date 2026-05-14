from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

import pandas as pd

from app.data.models import Profile

DB_PATH = Path("body_analytics.db")


class BodyDataStore(Protocol):
    def init(self) -> None: ...
    def get_profile(self) -> Profile: ...
    def upsert_profile(self, name: str, age: int) -> None: ...
    def add_weight_entry(self, entry_date: date, weight_lb: float) -> None: ...
    def get_weight_entries(self) -> pd.DataFrame: ...
    def get_goal_lb(self) -> float | None: ...
    def set_goal_lb(self, goal_lb: float) -> None: ...


class SQLiteBodyDataStore:
    """Local implementation designed to be replaceable by Google Sheets adapter."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS weight_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT NOT NULL,
                    weight_lb REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    goal_lb REAL NOT NULL
                )
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO profile (id, name, age) VALUES (1, 'Athlete', 28)"
            )

    def get_profile(self) -> Profile:
        with self._conn() as conn:
            row = conn.execute("SELECT name, age FROM profile WHERE id = 1").fetchone()
        if not row:
            return Profile()
        return Profile(name=row[0], age=int(row[1]))

    def upsert_profile(self, name: str, age: int) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO profile (id, name, age) VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name, age = excluded.age
                """,
                (name, age),
            )

    def add_weight_entry(self, entry_date: date, weight_lb: float) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO weight_entries (entry_date, weight_lb) VALUES (?, ?)",
                (entry_date.isoformat(), float(weight_lb)),
            )

    def get_weight_entries(self) -> pd.DataFrame:
        with self._conn() as conn:
            df = pd.read_sql_query(
                "SELECT entry_date, weight_lb FROM weight_entries ORDER BY entry_date ASC",
                conn,
            )
        if df.empty:
            return df
        df["entry_date"] = pd.to_datetime(df["entry_date"])
        return df

    def get_goal_lb(self) -> float | None:
        with self._conn() as conn:
            row = conn.execute("SELECT goal_lb FROM goals WHERE id = 1").fetchone()
        return None if row is None else float(row[0])

    def set_goal_lb(self, goal_lb: float) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO goals (id, goal_lb) VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET goal_lb = excluded.goal_lb
                """,
                (float(goal_lb),),
            )


class GoogleSheetsBodyDataStore:
    """Future-ready adapter placeholder. Keep interface parity with SQLiteBodyDataStore."""

    def __init__(self, spreadsheet_key: str) -> None:
        self.spreadsheet_key = spreadsheet_key

    def init(self) -> None:
        raise NotImplementedError("Implement with gspread + st.secrets on deployment.")
