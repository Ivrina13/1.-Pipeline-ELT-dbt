"""
Bloc 4 : Store — stockage / mise en cache des donnees et de l'etat de session.
Orchestre extract.py (lecture brute) + clean.py (nettoyage), avec cache Streamlit.
"""
import pandas as pd
import streamlit as st

from core.extract import read_raw_data
from core.clean import clean_data


@st.cache_data
def load_data() -> pd.DataFrame | None:
    """Charge et nettoie les donnees (mis en cache par Streamlit)."""
    raw = read_raw_data()
    if raw is None:
        return None
    return clean_data(raw)


def get_reference_date(df_all: pd.DataFrame) -> pd.Timestamp:
    """Date de reference pour les calculs de recence (RFM, etc.)."""
    if "purchased_at" in df_all.columns:
        return df_all["purchased_at"].max()
    return pd.Timestamp.now()
