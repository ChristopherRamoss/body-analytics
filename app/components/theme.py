import streamlit as st


def apply_theme() -> None:
    st.set_page_config(page_title="Body Intelligence", page_icon="📊", layout="centered")
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
        html, body, [class*="css"], .stApp {font-family: 'DM Sans', sans-serif; background:#0b0b0f; color:#e5e7eb;}
        .block-container {padding-top: 1rem; padding-bottom: 4rem; max-width: 760px;}
        .card {background:#121218;border:1px solid #22242d;border-radius:18px;padding:14px 14px 12px;margin:8px 0;}
        .metric-title {color:#9ca3af;font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;}
        .metric-value {font-size:1.35rem;font-weight:700;color:#f3f4f6;}
        .accent {color:#e63946;}
        .green {color:#22c55e;}
        .stTabs [data-baseweb="tab"] {padding: 8px 12px; border-radius: 12px; background:#151720; margin-right:6px;}
        .stTabs [aria-selected="true"] {background:#e63946 !important; color:white !important;}
        .stButton button, .stDownloadButton button {background:#e63946;color:#fff;border:none;border-radius:12px;}
        .stSelectbox label, .stNumberInput label, .stTextInput label, .stDateInput label {color:#d1d5db;}
        </style>
        """,
        unsafe_allow_html=True,
    )
