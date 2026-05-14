from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd


KG_TO_LB = 2.2046226218


def to_lb(weight: float, unit: str) -> float:
    return float(weight) * KG_TO_LB if unit == "kg" else float(weight)


def to_kg(weight_lb: float) -> float:
    return float(weight_lb) / KG_TO_LB


def filter_by_range(df: pd.DataFrame, range_key: str) -> pd.DataFrame:
    if df.empty or range_key == "Todo":
        return df
    max_date = df["entry_date"].max()
    days = {"3 meses": 90, "6 meses": 180, "1 año": 365}[range_key]
    min_date = max_date - timedelta(days=days)
    return df[df["entry_date"] >= min_date]


def weekly_trend_lb(df: pd.DataFrame, window: int = 8) -> float:
    if len(df) < 3:
        return 0.0
    tail = df.tail(window).copy()
    x = (tail["entry_date"] - tail["entry_date"].min()).dt.days.to_numpy()
    y = tail["weight_lb"].to_numpy()
    slope_per_day = np.polyfit(x, y, 1)[0] if len(np.unique(x)) > 1 else 0.0
    return float(slope_per_day * 7)


def build_insights(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["📭 Aún no hay registros. Empieza hoy para activar insights automáticos."]
    insights: list[str] = []
    now = df["entry_date"].max()
    month_cutoff = now - pd.Timedelta(days=30)
    month_df = df[df["entry_date"] >= month_cutoff]
    if len(month_df) >= 2:
        delta = month_df["weight_lb"].iloc[-1] - month_df["weight_lb"].iloc[0]
        icon = "📈" if delta > 0 else "📉" if delta < 0 else "➡️"
        insights.append(f"{icon} Cambio en 30 días: {delta:+.1f} lb")
    recent = df.tail(5)
    if len(recent) >= 3 and (recent["weight_lb"].max() - recent["weight_lb"].min()) < 0.4:
        days_stable = (recent["entry_date"].iloc[-1] - recent["entry_date"].iloc[0]).days
        insights.append(f"⚠️ Peso estable durante {days_stable} días. Puedes ajustar calorías o actividad.")
    trend = weekly_trend_lb(df)
    if trend >= 0.4:
        insights.append("🔥 Ritmo excelente para volumen limpio.")
    elif trend <= -0.4:
        insights.append("🎯 Tendencia sólida de definición.")
    else:
        insights.append("🧠 Ritmo moderado y sostenible. Buen control de adherencia.")
    return insights
