from __future__ import annotations

import sqlite3
import pandas as pd
import streamlit as st
from datetime import date
from pathlib import Path
from typing import Protocol
from streamlit.errors import StreamlitSecretNotFoundError

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
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def init(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weight_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT NOT NULL,
                    weight_lb REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    goal_lb REAL NOT NULL
                )
            """)
            conn.execute("INSERT OR IGNORE INTO profile (id, name, age) VALUES (1, 'Athlete', 28)")

    def get_profile(self) -> Profile:
        with self._conn() as conn:
            row = conn.execute("SELECT name, age FROM profile WHERE id = 1").fetchone()
        return Profile(name=row[0], age=int(row[1])) if row else Profile()

    def upsert_profile(self, name: str, age: int) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO profile (id, name, age) VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET name = excluded.name, age = excluded.age
            """, (name, age))

    def add_weight_entry(self, entry_date: date, weight_lb: float) -> None:
        with self._conn() as conn:
            conn.execute("INSERT INTO weight_entries (entry_date, weight_lb) VALUES (?, ?)",
                         (entry_date.isoformat(), float(weight_lb)))

    def get_weight_entries(self) -> pd.DataFrame:
        with self._conn() as conn:
            df = pd.read_sql_query("SELECT entry_date, weight_lb FROM weight_entries ORDER BY entry_date ASC", conn)
        if not df.empty:
            df["entry_date"] = pd.to_datetime(df["entry_date"])
        return df

    def get_goal_lb(self) -> float | None:
        with self._conn() as conn:
            row = conn.execute("SELECT goal_lb FROM goals WHERE id = 1").fetchone()
        return float(row[0]) if row else None

    def set_goal_lb(self, goal_lb: float) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO goals (id, goal_lb) VALUES (1, ?)
                ON CONFLICT(id) DO UPDATE SET goal_lb = excluded.goal_lb
            """, (float(goal_lb),))

class GoogleSheetsBodyDataStore:
    def __init__(self, spreadsheet_key: str) -> None:
        self.spreadsheet_key = spreadsheet_key
        import gspread
        
        # Carga credenciales desde st.secrets
        creds = dict(st.secrets["gcp_service_account"])
        self.client = gspread.service_account_from_dict(creds)
        self.sheet = self.client.open_by_key(spreadsheet_key)
        print(f"DEBUG: Conectado exitosamente a la hoja {spreadsheet_key}")

    def _ws(self, title: str):
        try:
            return self.sheet.worksheet(title)
        except Exception:
            # Si no existe la pestaña, la crea con encabezados
            ws = self.sheet.add_worksheet(title=title, rows=1000, cols=10)
            return ws

    def init(self) -> None:
        # Inicializar Pestaña Profile
        p_ws = self._ws("profile")
        if not p_ws.get_all_values():
            p_ws.update("A1:B2", [["name", "age"], ["Athlete", 28]])

        # Inicializar Pestaña Weights
        w_ws = self._ws("weights")
        if not w_ws.get_all_values():
            w_ws.update("A1:B1", [["entry_date", "weight_lb"]])

        # Inicializar Pestaña Goals
        g_ws = self._ws("goals")
        if not g_ws.get_all_values():
            g_ws.update("A1:A1", [["goal_lb"]])

    def get_profile(self) -> Profile:
        ws = self._ws("profile")
        data = ws.get_all_values()
        if len(data) < 2: return Profile()
        return Profile(name=data[1][0], age=int(data[1][1]) if data[1][1] else 28)

    def upsert_profile(self, name: str, age: int) -> None:
        ws = self._ws("profile")
        ws.update("A2:B2", [[name, age]])

    def add_weight_entry(self, entry_date: date, weight_lb: float) -> None:
        ws = self._ws("weights")
        ws.append_row([entry_date.isoformat(), float(weight_lb)], value_input_option="USER_ENTERED")

    def get_weight_entries(self) -> pd.DataFrame:
        ws = self._ws("weights")
        data = ws.get_all_values()
        if len(data) < 2: return pd.DataFrame(columns=["entry_date", "weight_lb"])
        df = pd.DataFrame(data[1:], columns=data[0])
        df["weight_lb"] = pd.to_numeric(df["weight_lb"])
        df["entry_date"] = pd.to_datetime(df["entry_date"])
        return df.sort_values("entry_date")

    def get_goal_lb(self) -> float | None:
        ws = self._ws("goals")
        data = ws.get_all_values()
        if len(data) < 2 or not data[1][0]: return None
        return float(data[1][0])

    def set_goal_lb(self, goal_lb: float) -> None:
        ws = self._ws("goals")
        ws.update("A2", [[float(goal_lb)]])

@st.cache_resource # <--- Esto evita reconectar y pedir datos en cada refresco
def get_datastore() -> BodyDataStore:
    try:
        backend = str(st.secrets.get("DATA_BACKEND", "sqlite")).lower()
        key = str(st.secrets.get("GOOGLE_SHEETS_KEY", "")).strip()
    except Exception:
        return SQLiteBodyDataStore()

    if backend == "gsheets" and key:
        try:
            ds = GoogleSheetsBodyDataStore(key)
            ds.init()
            return ds
        except Exception as e:
                    # Si el error es el 429, aquí podrías mostrar un mensaje más amigable
                    if "429" in str(e):
                        st.error("Límite de Google Sheets alcanzado. Espera 60 segundos.")
                    else:
                        st.error(f"Error conectando a Google Sheets: {e}")
                    return SQLiteBodyDataStore()
    
    return SQLiteBodyDataStore()