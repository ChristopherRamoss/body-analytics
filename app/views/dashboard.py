from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from app.components.theme import apply_theme
from app.data.database import SQLiteBodyDataStore
from app.utils.metrics import build_insights, filter_by_range, to_kg, to_lb, weekly_trend_lb


def _profile_level(weight_lb: float | None) -> str:
    if weight_lb is None:
        return "Iniciando"
    if weight_lb < 140:
        return "Lean Focus"
    if weight_lb < 180:
        return "Balanced"
    return "Power Build"


def render_dashboard() -> None:
    apply_theme()
    db = SQLiteBodyDataStore()
    db.init()

    st.title("Body Intelligence")
    st.caption("Seguimiento corporal")

    tabs = st.tabs(["Resumen", "Registro", "Meta", "Insights"])
    df = db.get_weight_entries()
    profile = db.get_profile()
    current_lb = float(df["weight_lb"].iloc[-1]) if not df.empty else None

    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div class='card'><div class='metric-title'>Nombre</div><div class='metric-value'>{profile.name}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='card'><div class='metric-title'>Edad</div><div class='metric-value'>{profile.age} años</div></div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            value = f"{current_lb:.1f} lb" if current_lb else "--"
            st.markdown(f"<div class='card'><div class='metric-title'>Peso actual</div><div class='metric-value'>{value}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='card'><div class='metric-title'>Estado físico</div><div class='metric-value accent'>{_profile_level(current_lb)}</div></div>", unsafe_allow_html=True)

        st.markdown("### Evolución")
        time_range = st.segmented_control("Rango", ["3 meses", "6 meses", "1 año", "Todo"], default="6 meses")
        plot_df = filter_by_range(df, time_range) if time_range else df
        if plot_df.empty:
            st.info("Agrega registros para ver la evolución.")
        else:
            line = (
                alt.Chart(plot_df)
                .mark_line(point=alt.OverlayMarkDef(color="#630000", size=70), color="#e63946", interpolate="monotone")
                .encode(
                    x=alt.X("entry_date:T", title=None, axis=alt.Axis(labelColor="#9ca3af", format="%d %b")),
                    y=alt.Y("weight_lb:Q", title="lb", axis=alt.Axis(labelColor="#9ca3af")),
                    tooltip=[alt.Tooltip("entry_date:T", title="Fecha"), alt.Tooltip("weight_lb:Q", title="Peso (lb)", format=".1f")],
                )
                .properties(height=280)
            )
            st.altair_chart(line, use_container_width=True)
            history = plot_df.sort_values("entry_date", ascending=False).copy()
            history["change"] = history["weight_lb"].diff(-1).fillna(0)
            for _, r in history.iterrows():
                delta = r["change"]
                icon = "⬆️" if delta > 0 else "⬇️" if delta < 0 else "➡️"
                st.markdown(
                    f"<div class='card'><b>{r['entry_date'].strftime('%d %b %Y')}</b><br>{r['weight_lb']:.1f} lb · {icon} {delta:+.1f} lb</div>",
                    unsafe_allow_html=True,
                )

    with tabs[1]:
        with st.form("profile_form"):
            st.subheader("Perfil")
            name = st.text_input("Nombre", value=profile.name)
            age = st.number_input("Edad", min_value=12, max_value=90, value=profile.age)
            if st.form_submit_button("Guardar perfil"):
                db.upsert_profile(name, int(age))
                st.success("Perfil actualizado")

        with st.form("weight_form"):
            st.subheader("Registrar peso")
            c1, c2 = st.columns([2, 1])
            with c1:
                w = st.number_input("Peso", min_value=50.0, max_value=700.0, value=150.0, step=0.1)
            with c2:
                unit = st.selectbox("Unidad", ["lb", "kg"])
            d = st.date_input("Fecha", value=date.today())
            if st.form_submit_button("Guardar registro"):
                db.add_weight_entry(d, to_lb(w, unit))
                st.success("Peso registrado")

    with tabs[2]:
        st.subheader("Meta corporal")
        goal = db.get_goal_lb() or (current_lb + 5 if current_lb else 150.0)
        new_goal = st.number_input("Meta (lb)", min_value=60.0, max_value=700.0, value=float(goal), step=0.5)
        if st.button("Guardar meta"):
            db.set_goal_lb(new_goal)
            goal = new_goal
            st.success("Meta guardada")
        if current_lb:
            gap = goal - current_lb
            pace = weekly_trend_lb(df)
            remaining_weeks = abs(gap / pace) if pace != 0 and (gap * pace) > 0 else None
            st.markdown(f"<div class='card'><div class='metric-title'>Meta</div><div class='metric-value'>{goal:.1f} lb</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card'><div class='metric-title'>Actual</div><div class='metric-value'>{current_lb:.1f} lb</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card'><div class='metric-title'>Faltan</div><div class='metric-value accent'>{gap:+.1f} lb</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card'><div class='metric-title'>Ritmo actual</div><div class='metric-value green'>{pace:+.2f} lb/semana</div></div>", unsafe_allow_html=True)
            eta = f"~{remaining_weeks:.1f} semanas" if remaining_weeks else "Sin tendencia suficiente"
            st.markdown(f"<div class='card'><div class='metric-title'>Tiempo estimado</div><div class='metric-value'>{eta}</div></div>", unsafe_allow_html=True)
            st.caption(f"Referencia: {current_lb:.1f} lb = {to_kg(current_lb):.1f} kg")
        else:
            st.info("Necesitas registros de peso para calcular tu progreso hacia la meta.")

    with tabs[3]:
        st.subheader("Insights automáticos")
        for ins in build_insights(df):
            st.markdown(f"<div class='card'>{ins}</div>", unsafe_allow_html=True)

    with st.expander("Arquitectura preparada para Google Sheets"):
        st.markdown(
            """
- Capa de datos desacoplada en `app/data/database.py` con interfaz homogénea.
- Implementación activa: `SQLiteBodyDataStore`.
- Implementación futura: `GoogleSheetsBodyDataStore` (gspread + `st.secrets`).
- Para Streamlit Cloud: guardar credenciales en `.streamlit/secrets.toml`.
            """
        )
