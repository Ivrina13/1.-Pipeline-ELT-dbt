"""
Olist Analytics — Tableau de bord professionnel.
Multi-onglets, synthèse IA intégrée, traduction FR/EN, thème sombre.
Lancer avec : streamlit run app.py
"""
import base64
from pathlib import Path

import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(page_title="Olist Analytics", layout="wide",
                    initial_sidebar_state="expanded")

BR_STATES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
}

# ============================================================================
# COULEURS PROFESSIONNELLES
# Palette : bleu profond, gris ardoise, accents or et teal
# ============================================================================
COLORS = {
    "primary": "#1B2A4A",      # Bleu profond
    "primary_light": "#2A3F6A",
    "accent": "#C9A84C",       # Or
    "accent2": "#4A8C8C",      # Teal
    "surface": "#F7F8FA",
    "surface_dark": "#1A1E2E",
    "text": "#1A1E2E",
    "text_light": "#6B7A8F",
    "text_white": "#F0F2F8",
    "border": "#E2E6EE",
    "positive": "#3A8C6B",
    "negative": "#C95A5A",
    "gradient_primary": "linear-gradient(135deg, #1B2A4A 0%, #2A3F6A 100%)",
    "gradient_accent": "linear-gradient(135deg, #C9A84C 0%, #B8953A 100%)",
}

# ============================================================================
# I18N
# ============================================================================
TRANSLATIONS = {
    "FR": {
        "app_title": "Olist Analytics",
        "app_subtitle": "Tableau de bord e-commerce",
        "nav_overview": "Vue d'ensemble",
        "nav_logistics": "Logistique",
        "nav_satisfaction": "Satisfaction",
        "nav_customers": "Clients",
        "nav_finance": "Finance",
        "nav_synthese": "Synthèse IA",
        "nav_chat": "Assistant IA",
        "theme_toggle": "Thème clair",
        "filters_title": "Filtres",
        "filter_period": "Période",
        "filter_state": "État",
        "filter_status": "Statut",
        "filter_category": "Catégorie",
        "filter_min_score": "Note minimale",
        "filter_reset": "Réinitialiser",
        "data_rows": "lignes disponibles",
        "kpi_revenue": "Chiffre d'affaires",
        "kpi_orders": "Commandes",
        "kpi_customers": "Clients uniques",
        "kpi_avg_basket": "Panier moyen",
        "kpi_avg_delivery": "Délai moyen",
        "kpi_median_delivery": "Délai médian",
        "kpi_late_rate": "Taux de retard",
        "kpi_good_reviews": "Bonnes notes (4-5)",
        "kpi_bad_reviews": "Mauvaises notes (1-2)",
        "kpi_review_count": "Volume d'avis",
        "kpi_avg_score": "Note moyenne",
        "kpi_repeat_rate": "Taux de réachat",
        "kpi_churn_rate": "Inactifs (+1 an)",
        "kpi_total_customers": "Total clients",
        "chart_sales": "Évolution des ventes",
        "chart_status": "Répartition des statuts",
        "chart_categories": "Top catégories",
        "chart_states": "Top États",
        "chart_delivery_dist": "Distribution des délais",
        "chart_delivery_state": "Délai par État",
        "chart_late_trend": "Évolution du taux de retard",
        "chart_score_dist": "Distribution des notes",
        "chart_score_category": "Note moyenne par catégorie",
        "chart_delivery_score": "Délai vs note",
        "chart_segments": "Segmentation clients",
        "chart_top_clients": "Top clients (par CA)",
        "chart_revenue_cum": "CA cumulé",
        "chart_revenue_category": "CA par catégorie",
        "chat_placeholder": "Posez votre question sur les données...",
        "chat_intro": "Assistant IA pour analyser les données Olist",
        "synthese_intro": "Analyse générée automatiquement à partir des données",
    },
    "EN": {
        "app_title": "Olist Analytics",
        "app_subtitle": "E-commerce Dashboard",
        "nav_overview": "Overview",
        "nav_logistics": "Logistics",
        "nav_satisfaction": "Satisfaction",
        "nav_customers": "Customers",
        "nav_finance": "Finance",
        "nav_synthese": "AI Summary",
        "nav_chat": "AI Assistant",
        "theme_toggle": "Light theme",
        "filters_title": "Filters",
        "filter_period": "Period",
        "filter_state": "State",
        "filter_status": "Status",
        "filter_category": "Category",
        "filter_min_score": "Min rating",
        "filter_reset": "Reset",
        "data_rows": "rows available",
        "kpi_revenue": "Revenue",
        "kpi_orders": "Orders",
        "kpi_customers": "Unique customers",
        "kpi_avg_basket": "Avg basket",
        "kpi_avg_delivery": "Avg delivery",
        "kpi_median_delivery": "Median delivery",
        "kpi_late_rate": "Late rate",
        "kpi_good_reviews": "Good ratings (4-5)",
        "kpi_bad_reviews": "Poor ratings (1-2)",
        "kpi_review_count": "Review volume",
        "kpi_avg_score": "Avg rating",
        "kpi_repeat_rate": "Repeat rate",
        "kpi_churn_rate": "Inactive (+1 year)",
        "kpi_total_customers": "Total customers",
        "chart_sales": "Sales evolution",
        "chart_status": "Status distribution",
        "chart_categories": "Top categories",
        "chart_states": "Top states",
        "chart_delivery_dist": "Delivery distribution",
        "chart_delivery_state": "Delivery by state",
        "chart_late_trend": "Late rate trend",
        "chart_score_dist": "Rating distribution",
        "chart_score_category": "Avg rating by category",
        "chart_delivery_score": "Delivery vs rating",
        "chart_segments": "Customer segments",
        "chart_top_clients": "Top clients",
        "chart_revenue_cum": "Cumulative revenue",
        "chart_revenue_category": "Revenue by category",
        "chat_placeholder": "Ask about the data...",
        "chat_intro": "AI assistant for Olist data analysis",
        "synthese_intro": "Automated analysis from data",
    }
}

# ============================================================================
# IA / INSIGHTS (version simplifiée mais fonctionnelle)
# ============================================================================
def generate_insights(df, lang):
    """Génère des insights à partir des données."""
    insights = []
    t = TRANSLATIONS[lang]
    
    if df.empty:
        return {t.get("no_data", "No data"): "Aucune donnée disponible pour générer des insights."}
    
    # Revenue insight
    if "price" in df.columns:
        total_rev = df["price"].sum()
        insights.append((
            f"CA total: {total_rev:,.0f} R$",
            f"Le chiffre d'affaires total s'élève à {total_rev:,.0f} R$."
        ))
        
        # Monthly trend
        if "purchased_at" in df.columns:
            df["month"] = df["purchased_at"].dt.to_period("M")
            monthly = df.groupby("month")["price"].sum()
            if len(monthly) > 1:
                trend = "croissance" if monthly.iloc[-1] > monthly.iloc[-2] else "baisse"
                insights.append((
                    f"Tendance: {trend}",
                    f"Le CA mensuel est en {trend} par rapport au mois précédent."
                ))
    
    # Delivery insight
    if "delivery_days" in df.columns:
        avg_delivery = df["delivery_days"].mean()
        insights.append((
            f"Délai moyen: {avg_delivery:.1f} jours",
            f"Le délai de livraison moyen est de {avg_delivery:.1f} jours."
        ))
    
    # Satisfaction insight
    if "avg_review_score" in df.columns:
        avg_score = df["avg_review_score"].mean()
        insights.append((
            f"Note moyenne: {avg_score:.1f}/5",
            f"La note moyenne des avis est de {avg_score:.1f}/5."
        ))
    
    # Customer insight
    if "customer_unique_id" in df.columns:
        n_customers = df["customer_unique_id"].nunique()
        insights.append((
            f"Base clients: {n_customers:,}",
            f"La base de clients compte {n_customers:,} clients uniques."
        ))
    
    return {f"{i+1}. {title}": body for i, (title, body) in enumerate(insights[:6])}

def answer_question(q, df, lang):
    """Répond aux questions sur les données."""
    q_lower = q.lower()
    
    # Réponses simples basées sur les mots-clés
    if any(w in q_lower for w in ["chiffre", "ca", "revenue", "vente", "sales"]):
        if "price" in df.columns:
            total = df["price"].sum()
            return f"Le chiffre d'affaires total est de {total:,.0f} R$."
        return "Données de chiffre d'affaires non disponibles."
    
    if any(w in q_lower for w in ["livraison", "delivery", "retard", "late"]):
        if "delivery_days" in df.columns:
            avg = df["delivery_days"].mean()
            late = (df["is_late"].mean() * 100) if "is_late" in df.columns else 0
            return f"Délai moyen: {avg:.1f} jours. Taux de retard: {late:.1f}%."
        return "Données de livraison non disponibles."
    
    if any(w in q_lower for w in ["note", "avis", "review", "satisfaction"]):
        if "avg_review_score" in df.columns:
            avg = df["avg_review_score"].mean()
            return f"Note moyenne des avis: {avg:.1f}/5."
        return "Données d'avis non disponibles."
    
    if any(w in q_lower for w in ["client", "customer"]):
        if "customer_unique_id" in df.columns:
            n = df["customer_unique_id"].nunique()
            return f"La base de clients compte {n:,} clients uniques."
        return "Données clients non disponibles."
    
    return "Je peux vous renseigner sur: le chiffre d'affaires, les livraisons, les avis clients et les statistiques générales."

# ============================================================================
# THEME
# ============================================================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "lang" not in st.session_state:
    st.session_state.lang = "FR"

def get_theme():
    if st.session_state.theme == "dark":
        return {
            "bg": "radial-gradient(circle at 15% 0%, #0F1422 0%, #090C15 45%, #060810 100%)",
            "card": "#131927",
            "card_border": "rgba(255,255,255,0.06)",
            "sidebar": "#0B0F1A",
            "text": "#ECEEF4",
            "muted": "#7A88A0",
            "surface": "#1A2235",
            "border": "rgba(255,255,255,0.08)",
        }
    else:
        return {
            "bg": "radial-gradient(circle at 15% 0%, #F0F2F8 0%, #F7F8FA 45%, #FFFFFF 100%)",
            "card": "#FFFFFF",
            "card_border": "#E8EAEF",
            "sidebar": "#FFFFFF",
            "text": "#1A1E2E",
            "muted": "#6B7A8F",
            "surface": "#F5F6FA",
            "border": "#E2E6EE",
        }

theme = get_theme()

# ============================================================================
# CSS (sans emoji)
# ============================================================================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, sans-serif;
}}

.stApp {{
    background: {theme["bg"]};
    color: {theme["text"]};
}}

.block-container {{
    padding-top: 1.8rem;
    padding-bottom: 2.5rem;
    max-width: 1300px;
}}

[data-testid="stSidebar"] {{
    background: {theme["sidebar"]};
    border-right: 1px solid {theme["border"]};
    padding-top: 1.2rem;
}}

/* Brand */
.brand-title {{
    font-size: 1.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: {COLORS["accent"]};
}}
.brand-subtitle {{
    color: {theme["muted"]};
    font-size: 0.8rem;
    margin-top: 2px;
    font-weight: 400;
}}
.brand-separator {{
    border: none;
    border-top: 1px solid {theme["border"]};
    margin: 14px 0 16px 0;
}}

/* Cards */
.card {{
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}}
.card-featured {{
    background: {COLORS["gradient_primary"]};
    border: none;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}}
.card-featured .card-title {{
    color: rgba(255,255,255,0.6);
}}
.card-featured .big-number {{
    color: #FFFFFF;
}}
.card-title {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {theme["muted"]};
    font-weight: 600;
    margin-bottom: 4px;
}}
.big-number {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {theme["text"]};
    letter-spacing: -0.02em;
}}
.delta-up {{
    color: {COLORS["positive"]};
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 4px;
}}
.delta-down {{
    color: {COLORS["negative"]};
    font-size: 0.75rem;
    font-weight: 500;
    margin-top: 4px;
}}
.delta-neutral {{
    color: {theme["muted"]};
    font-size: 0.75rem;
    font-weight: 400;
    margin-top: 4px;
}}

/* Navigation */
.nav-label {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {theme["muted"]};
    font-weight: 600;
    padding: 0 8px 8px 8px;
}}
.stRadio > div {{
    flex-direction: column;
    gap: 2px;
}}
.stRadio > div > label {{
    padding: 8px 12px !important;
    border-radius: 8px !important;
    margin-bottom: 1px;
    font-weight: 500 !important;
    color: {theme["muted"]} !important;
}}
.stRadio > div > label:has(input:checked) {{
    background: rgba(201, 168, 76, 0.12) !important;
}}
.stRadio > div > label:has(input:checked) p {{
    color: {COLORS["accent"]} !important;
    font-weight: 600 !important;
}}

/* Filters */
.filter-section {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {theme["muted"]};
    font-weight: 600;
    margin: 12px 0 8px 0;
}}

/* Buttons */
.stButton > button {{
    background: {COLORS["gradient_accent"]};
    color: #FFFFFF !important;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 16px;
    width: 100%;
}}
.stButton > button:hover {{
    opacity: 0.9;
}}

/* Data */
.data-note {{
    color: {theme["muted"]};
    font-size: 0.7rem;
    font-style: italic;
    margin-top: -6px;
    margin-bottom: 12px;
}}

/* Page header */
.page-title {{
    font-size: 1.8rem;
    font-weight: 700;
    color: {theme["text"]};
    letter-spacing: -0.02em;
}}
.page-subtitle {{
    color: {theme["muted"]};
    font-size: 0.9rem;
    margin-bottom: 16px;
}}
.section-header {{
    font-size: 1rem;
    font-weight: 600;
    color: {theme["text"]};
    margin: 12px 0 10px 0;
}}

/* Insight cards */
.insight-card {{
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    border-left: 3px solid {COLORS["accent"]};
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}}
.insight-title {{
    font-weight: 600;
    font-size: 0.85rem;
    color: {theme["text"]};
}}
.insight-body {{
    font-size: 0.8rem;
    color: {theme["muted"]};
    margin-top: 2px;
    line-height: 1.4;
}}

/* Chat */
.chat-message {{
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 6px;
    font-size: 0.85rem;
    line-height: 1.5;
}}
.chat-user {{
    background: {theme["surface"]};
    border: 1px solid {theme["card_border"]};
}}
.chat-assistant {{
    background: rgba(201, 168, 76, 0.08);
    border: 1px solid rgba(201, 168, 76, 0.15);
}}

/* Misc */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

/* Sonar avatar */
.sonar-avatar-wrap {{
    border-radius: 14px;
    padding: 16px;
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    text-align: center;
}}
.sonar-avatar-img {{
    width: 100%;
    max-width: 160px;
    border-radius: 10px;
}}
.sonar-avatar-name {{
    font-weight: 700;
    font-size: 0.9rem;
    margin-top: 6px;
    color: {theme["text"]};
}}
.sonar-avatar-role {{
    color: {theme["muted"]};
    font-size: 0.75rem;
}}
.sonar-dot {{
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {COLORS["positive"]};
    margin-right: 6px;
}}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CHARGEMENT DES DONNEES
# ============================================================================
@st.cache_data
def load_data():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        parquet_path = os.path.join(BASE_DIR, "data", "fct_orders.parquet")

        if not os.path.exists(parquet_path):
            return None

        conn = duckdb.connect(database=":memory:")
        conn.execute(f"""
            CREATE TABLE fct_orders AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)

        df = conn.execute("SELECT * FROM fct_orders").df()
        conn.close()

        if df.empty:
            return None

        date_cols = ["purchased_at", "approved_at", "shipped_at", "delivered_at", "estimated_delivery_at"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        if "estimated_delivery_at" in df.columns and "estimated_delivery" not in df.columns:
            df["estimated_delivery"] = df["estimated_delivery_at"]

        if "delivered_at" in df.columns and "purchased_at" in df.columns:
            if "delivery_days" not in df.columns:
                df["delivery_days"] = (df["delivered_at"] - df["purchased_at"]).dt.days
            if "is_late" not in df.columns and "estimated_delivery" in df.columns:
                df["is_late"] = df["delivered_at"] > df["estimated_delivery"]

        if "price" in df.columns:
            df["price"] = df["price"].astype(float)

        if "product_category" in df.columns:
            df["product_category"] = df["product_category"].fillna("Non categorise")

        if "customer_state" in df.columns:
            df["customer_state"] = df["customer_state"].fillna("Inconnu")
            df["customer_state"] = df["customer_state"].map(BR_STATES).fillna(df["customer_state"])

        if "purchased_at" in df.columns:
            df["month_year"] = df["purchased_at"].dt.to_period('M').astype(str)

        return df

    except Exception as e:
        st.error(f"Erreur: {e}")
        return None

# ============================================================================
# HELPERS
# ============================================================================
def t(key):
    return TRANSLATIONS[st.session_state.lang].get(key, key)

def style_fig(fig, height=280):
    fig.update_layout(
        template="plotly_dark" if st.session_state.theme == "dark" else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family="Inter, sans-serif"),
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)" if st.session_state.theme == "dark" else "rgba(0,0,0,0.06)",
                     zeroline=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.05)" if st.session_state.theme == "dark" else "rgba(0,0,0,0.06)",
                     zeroline=False)
    return fig

def metric_card(label, value, delta_text=None, delta_up=True, featured=False):
    delta_html = ""
    if delta_text:
        cls = "delta-up" if delta_up else "delta-down"
        delta_html = f'<div class="{cls}">{delta_text}</div>'
    card_class = "card-featured" if featured else "card"
    st.markdown(f"""
    <div class="{card_class}">
        <div class="card-title">{label}</div>
        <div class="big-number">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def apply_filters(df, filters):
    df_filtered = df.copy()

    if "date_range" in filters and len(filters["date_range"]) == 2 and "purchased_at" in df.columns:
        start, end = filters["date_range"]
        df_filtered = df_filtered[
            (df_filtered["purchased_at"].dt.date >= start) &
            (df_filtered["purchased_at"].dt.date <= end)
        ]

    if filters.get("state") and filters["state"] != "Tous" and "customer_state" in df.columns:
        df_filtered = df_filtered[df_filtered["customer_state"] == filters["state"]]

    if filters.get("status") and "status" in df.columns:
        df_filtered = df_filtered[df_filtered["status"].isin(filters["status"])]

    if filters.get("category") and filters["category"] != "Toutes" and "product_category" in df.columns:
        df_filtered = df_filtered[df_filtered["product_category"] == filters["category"]]

    if "min_score" in filters and "avg_review_score" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["avg_review_score"] >= filters["min_score"]]

    return df_filtered

def generate_avatar_b64():
    # Avatar par défaut (généré en SVG)
    svg = f"""
    <svg width="160" height="160" viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="160" height="160" rx="16" fill="{COLORS['primary']}"/>
        <circle cx="80" cy="65" r="35" fill="{COLORS['accent']}" opacity="0.3"/>
        <circle cx="80" cy="65" r="22" fill="{COLORS['accent']}" opacity="0.6"/>
        <circle cx="80" cy="65" r="12" fill="{COLORS['accent']}"/>
        <rect x="45" y="110" width="70" height="8" rx="4" fill="{COLORS['accent2']}" opacity="0.4"/>
        <rect x="55" y="125" width="50" height="8" rx="4" fill="{COLORS['accent2']}" opacity="0.25"/>
    </svg>
    """
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"

# ============================================================================
# SIDEBAR
# ============================================================================
def sidebar(df):
    with st.sidebar:
        st.markdown(f"""
        <div class="brand-title">Olist Analytics</div>
        <div class="brand-subtitle">{t('app_subtitle')}</div>
        <hr class="brand-separator">
        """, unsafe_allow_html=True)

        # Language toggle
        col_lang1, col_lang2 = st.columns(2)
        with col_lang1:
            if st.button("Français" if st.session_state.lang == "FR" else "French", use_container_width=True):
                st.session_state.lang = "FR"
                st.rerun()
        with col_lang2:
            if st.button("English" if st.session_state.lang == "EN" else "Anglais", use_container_width=True):
                st.session_state.lang = "EN"
                st.rerun()

        st.markdown("<hr class='brand-separator'>", unsafe_allow_html=True)

        # Navigation
        st.markdown(f'<div class="nav-label">Navigation</div>', unsafe_allow_html=True)
        nav_selected = st.radio(
            "",
            [t('nav_overview'), t('nav_logistics'), t('nav_satisfaction'),
             t('nav_customers'), t('nav_finance'), t('nav_synthese'), t('nav_chat')],
            label_visibility="collapsed"
        )

        # Theme toggle
        st.markdown("<hr class='brand-separator'>", unsafe_allow_html=True)
        if st.button("☀️" if st.session_state.theme == "dark" else "🌙", use_container_width=True):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

        # Filters
        st.markdown("<hr class='brand-separator'>", unsafe_allow_html=True)
        st.markdown(f'<div class="filter-section">{t("filters_title")}</div>', unsafe_allow_html=True)

        filters = {}

        if "purchased_at" in df.columns and not df["purchased_at"].isna().all():
            min_date = df["purchased_at"].min().date()
            max_date = df["purchased_at"].max().date()
            filters["date_range"] = st.date_input(t("filter_period"), [min_date, max_date])

        if "customer_state" in df.columns:
            states = ["Tous"] + sorted(df["customer_state"].dropna().unique().tolist())
            filters["state"] = st.selectbox(t("filter_state"), states)

        if "status" in df.columns:
            statuses = sorted(df["status"].dropna().unique().tolist())
            filters["status"] = st.multiselect(t("filter_status"), statuses, default=statuses)

        if "product_category" in df.columns:
            categories = ["Toutes"] + sorted(df["product_category"].dropna().unique().tolist())
            filters["category"] = st.selectbox(t("filter_category"), categories)

        if "avg_review_score" in df.columns:
            filters["min_score"] = st.slider(t("filter_min_score"), 1.0, 5.0, 1.0, 0.5)

        if st.button(t("filter_reset"), use_container_width=True):
            st.rerun()

        st.markdown("<hr class='brand-separator'>", unsafe_allow_html=True)
        st.caption(f"{len(df):,} {t('data_rows')}")

        return nav_selected, filters

# ============================================================================
# SECTION: OVERVIEW
# ============================================================================
def display_overview(df, df_all):
    valid = df[df["price"] > 0]
    valid_all = df_all[df_all["price"] > 0]

    total_revenue = valid["price"].sum()
    total_orders = valid["order_id"].nunique()
    unique_customers = valid["customer_unique_id"].nunique()
    avg_basket = total_revenue / total_orders if total_orders > 0 else 0
    avg_basket_all = valid_all["price"].sum() / valid_all["order_id"].nunique() if valid_all["order_id"].nunique() > 0 else 0
    basket_delta = avg_basket - avg_basket_all

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card(t("kpi_revenue"), f"R$ {total_revenue:,.0f}", featured=True)
    with c2:
        metric_card(t("kpi_orders"), f"{total_orders:,}")
    with c3:
        metric_card(t("kpi_customers"), f"{unique_customers:,}")
    with c4:
        metric_card(t("kpi_avg_basket"), f"R$ {avg_basket:,.2f}",
                    delta_text=f"{abs(basket_delta):.2f} vs avg", delta_up=basket_delta >= 0)

    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_sales")}</div>', unsafe_allow_html=True)
            if "purchased_at" in valid.columns and not valid.empty:
                daily_sales = valid.groupby("purchased_at")["price"].sum().reset_index()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_sales["purchased_at"], y=daily_sales["price"], mode="lines",
                    line=dict(color=COLORS["accent"], width=2.5),
                    fill="tozeroy", fillcolor=COLORS["accent"] + "22",
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

        if "product_category" in valid.columns and not valid.empty:
            top_cats = valid.groupby("product_category")["price"].sum().sort_values(ascending=False).head(6)
            total_cat_rev = valid["price"].sum()
            fig = go.Figure(go.Bar(
                x=top_cats.values,
                y=top_cats.index,
                orientation="h",
                marker_color=COLORS["accent"],
                text=[f"R$ {v:,.0f}" for v in top_cats.values],
                textposition="outside"
            ))
            fig.update_layout(height=240)
            st.plotly_chart(style_fig(fig, height=240), use_container_width=True, config={"displayModeBar": False})

    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_status")}</div>', unsafe_allow_html=True)
            if "status" in valid.columns and not valid.empty:
                status_counts = valid["status"].value_counts()
                fig = go.Figure(go.Pie(
    labels=cat_rev.index,
    values=cat_rev.values,
    hole=0.5,
    marker=dict(colors=[COLORS["accent"], COLORS["accent2"], COLORS["primary_light"],
                        COLORS["positive"], COLORS["negative"], "#8A7A5A"]),
    textfont=dict(color=theme["text"])
))
                st.plotly_chart(style_fig(fig, height=240), use_container_width=True, config={"displayModeBar": False})

        if "customer_state" in valid.columns and not valid.empty:
            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("chart_states")}</div>', unsafe_allow_html=True)
                top_states = valid["customer_state"].value_counts().head(5)
                fig = go.Figure(go.Bar(
                    x=top_states.index,
                    y=top_states.values,
                    marker_color=COLORS["accent2"]
                ))
                st.plotly_chart(style_fig(fig, height=200), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: LOGISTICS
# ============================================================================
def display_logistics(df, df_all):
    if "delivery_days" not in df.columns:
        st.warning("Les données de livraison ne sont pas disponibles.")
        return

    valid = df[df["delivery_days"].notna()]
    valid_all = df_all[df_all["delivery_days"].notna()]

    if valid.empty:
        st.warning("Aucune donnée de livraison valide pour cette sélection.")
        return

    avg_delivery = valid["delivery_days"].mean()
    median_delivery = valid["delivery_days"].median()
    late_rate = valid["is_late"].mean() * 100 if "is_late" in valid.columns else 0
    late_rate_all = valid_all["is_late"].mean() * 100 if "is_late" in valid_all.columns and not valid_all.empty else late_rate
    late_delta = late_rate - late_rate_all

    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        metric_card(t("kpi_avg_delivery"), f"{avg_delivery:.1f} j", featured=True)
    with c2:
        metric_card(t("kpi_median_delivery"), f"{median_delivery:.1f} j")
    with c3:
        metric_card(t("kpi_late_rate"), f"{late_rate:.1f}%",
                    delta_text=f"{abs(late_delta):.1f} pts vs avg", delta_up=late_delta < 0)

    col_left, col_right = st.columns([1, 1.6])

    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_delivery_dist")}</div>', unsafe_allow_html=True)
            fig = px.histogram(valid, x="delivery_days", nbins=25)
            fig.update_traces(marker_color=COLORS["accent"])
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_late_trend")}</div>', unsafe_allow_html=True)
            if "purchased_at" in valid.columns:
                v = valid.copy()
                v["month_year"] = v["purchased_at"].dt.to_period('M').astype(str)
                late_by_month = v.groupby("month_year")["is_late"].mean().reset_index()
                late_by_month["is_late"] = late_by_month["is_late"] * 100
                fig = go.Figure(go.Scatter(
                    x=late_by_month["month_year"],
                    y=late_by_month["is_late"],
                    mode="lines+markers",
                    line=dict(color=COLORS["accent2"], width=2.5),
                    marker=dict(color=COLORS["accent2"], size=6)
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    if "customer_state" in valid.columns:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_delivery_state")}</div>', unsafe_allow_html=True)
            fig = px.box(valid, x="customer_state", y="delivery_days")
            fig.update_traces(marker_color=COLORS["accent2"])
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: SATISFACTION
# ============================================================================
def display_satisfaction(df, df_all):
    if "avg_review_score" not in df.columns:
        st.warning("Les données d'avis ne sont pas disponibles.")
        return

    valid = df[df["avg_review_score"].notna()]
    if valid.empty:
        st.warning("Aucune donnée d'avis valide pour cette sélection.")
        return

    avg_score = valid["avg_review_score"].mean()
    good_rate = (valid["avg_review_score"] >= 4).mean() * 100
    bad_rate = (valid["avg_review_score"] <= 2).mean() * 100

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        metric_card(t("kpi_good_reviews"), f"{good_rate:.1f}%", featured=True)
    with c2:
        metric_card(t("kpi_bad_reviews"), f"{bad_rate:.1f}%")
    with c3:
        metric_card(t("kpi_review_count"), f"{len(valid):,}")

    col_left, col_right = st.columns([1, 1.6])

    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("kpi_avg_score")}</div>', unsafe_allow_html=True)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(avg_score, 2),
                number={'suffix': "/5", 'font': {'color': theme["text"], 'size': 28}},
                gauge={
                    'axis': {'range': [0, 5], 'tickcolor': theme["muted"]},
                    'bar': {'color': COLORS["accent"]},
                    'bgcolor': theme["card"],
                    'borderwidth': 0,
                }
            ))
            fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_score_dist")}</div>', unsafe_allow_html=True)
            v = valid.copy()
            v["review_score_rounded"] = v["avg_review_score"].round()
            fig = px.histogram(v, x="review_score_rounded", nbins=5)
            fig.update_traces(marker_color=COLORS["accent"])
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    col_a, col_b = st.columns(2)
    with col_a:
        if "product_category" in valid.columns:
            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("chart_score_category")}</div>', unsafe_allow_html=True)
                score_by_cat = valid.groupby("product_category")["avg_review_score"].mean().sort_values(ascending=False).head(8)
                fig = px.bar(x=score_by_cat.values, y=score_by_cat.index, orientation="h")
                fig.update_traces(marker_color=COLORS["accent2"])
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    with col_b:
        if "delivery_days" in valid.columns:
            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("chart_delivery_score")}</div>', unsafe_allow_html=True)
                d = valid[valid["delivery_days"].notna()]
                if not d.empty:
                    fig = px.scatter(d, x="delivery_days", y="avg_review_score", opacity=0.4)
                    fig.update_traces(marker_color=COLORS["accent"], marker_size=5)
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: CUSTOMERS
# ============================================================================
def display_customers(df, df_all):
    valid = df[df["price"] > 0]

    if "customer_unique_id" not in valid.columns or valid.empty:
        st.warning("Les données clients ne sont pas disponibles pour cette sélection.")
        return

    rfm = valid.groupby("customer_unique_id").agg({
        "purchased_at": lambda x: (pd.Timestamp.now() - x.max()).days if not x.empty else 999,
        "order_id": "nunique",
        "price": "sum"
    }).rename(columns={"purchased_at": "recency", "order_id": "frequency", "price": "monetary"})

    rfm["segment"] = pd.cut(rfm["recency"], bins=[0, 30, 90, 180, 365, float('inf')],
                            labels=["Actif", "Recent", "Moyen", "Ancien", "Inactif"])

    repeat_rate = (rfm["frequency"] > 1).mean() * 100
    churn_rate = (rfm["recency"] > 365).mean() * 100

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card(t("kpi_repeat_rate"), f"{repeat_rate:.1f}%", featured=True)
    with c2:
        metric_card(t("kpi_churn_rate"), f"{churn_rate:.1f}%")
    with c3:
        metric_card(t("kpi_total_customers"), f"{len(rfm):,}")

    col_left, col_right = st.columns([1, 1.4])

    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_segments")}</div>', unsafe_allow_html=True)
            seg_counts = rfm["segment"].value_counts()
            fig = go.Figure(go.Pie(
                labels=seg_counts.index,
                values=seg_counts.values,
                hole=0.5,
                marker=dict(colors=[COLORS["accent"], COLORS["accent2"], COLORS["primary_light"], COLORS["positive"], COLORS["negative"]]),
                textfont=dict(color=theme["text"])
            ))
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_top_clients")}</div>', unsafe_allow_html=True)
            top_clients = rfm.nlargest(8, "monetary")
            fig = go.Figure(go.Bar(
                x=top_clients.index.str[:12],
                y=top_clients["monetary"],
                marker_color=COLORS["accent"],
                text=[f"R$ {v:,.0f}" for v in top_clients["monetary"]],
                textposition="outside"
            ))
            fig.update_layout(height=280)
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: FINANCE
# ============================================================================
def display_finance(df, df_all):
    valid = df[df["price"] > 0]
    if valid.empty:
        st.warning("Aucune donnée financière pour cette sélection.")
        return

    total_revenue = valid["price"].sum()
    total_payment = valid["total_payment_value"].sum() if "total_payment_value" in valid.columns else total_revenue
    n_orders = valid["order_id"].nunique()
    avg_installments = valid["max_installments"].mean() if "max_installments" in valid.columns else None

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card(t("kpi_revenue"), f"R$ {total_revenue:,.0f}", featured=True)
    with c2:
        metric_card("Total encaissé", f"R$ {total_payment:,.0f}")
    with c3:
        if avg_installments is not None:
            metric_card("Versements moyens", f"{avg_installments:.1f}x")
        else:
            metric_card(t("kpi_orders"), f"{n_orders:,}")

    col_left, col_right = st.columns([1.6, 1])

    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_revenue_cum")}</div>', unsafe_allow_html=True)
            if "purchased_at" in valid.columns:
                monthly = valid.groupby("month_year")["price"].sum().reset_index().sort_values("month_year")
                monthly["cumulative"] = monthly["price"].cumsum()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly["month_year"],
                    y=monthly["cumulative"],
                    mode="lines",
                    line=dict(color=COLORS["accent"], width=3),
                    fill="tozeroy",
                    fillcolor=COLORS["accent"] + "22",
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    with col_right:
        if "product_category" in valid.columns:
            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("chart_revenue_category")}</div>', unsafe_allow_html=True)
                cat_rev = valid.groupby("product_category")["price"].sum().sort_values(ascending=False).head(6)
                fig = go.Figure(go.Pie(
                    labels=cat_rev.index,
                    values=cat_rev.values,
                    hole=0.5,
                    marker=dict(colors=[COLORS["accent"], COLORS["accent2"], COLORS["primary_light"],
                                        COLORS["positive"], COLORS["negative"], "#8A7A5A"]),
                    textfont=dict(color=theme["text"])
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: SYNTHESE IA
# ============================================================================
def display_synthese(df, lang):
    st.markdown(f'<div class="section-header">{t("nav_synthese")}</div>', unsafe_allow_html=True)

    col_avatar, col_content = st.columns([1, 3.2], gap="large")

    with col_avatar:
        avatar_url = generate_avatar_b64()
        st.markdown(f"""
        <div class="sonar-avatar-wrap">
            <img src="{avatar_url}" class="sonar-avatar-img" />
            <div class="sonar-avatar-name">Analytics AI</div>
            <div class="sonar-avatar-role">Assistant IA</div>
        </div>
        """, unsafe_allow_html=True)

    with col_content:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
            <span class="sonar-dot"></span>
            <span style="font-weight:600; font-size:1rem;">Analyse des données</span>
        </div>
        """, unsafe_allow_html=True)

        insights = generate_insights(df, lang)

        for title, body in insights.items():
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">{title}</div>
                <div class="insight-body">{body}</div>
            </div>
            """, unsafe_allow_html=True)

        st.caption(t("synthese_intro"))

        # Afficher un résumé statistique
        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        with st.expander("📊 Statistiques détaillées"):
            if not df.empty:
                cols_to_show = []
                if "price" in df.columns:
                    cols_to_show.append("price")
                if "delivery_days" in df.columns:
                    cols_to_show.append("delivery_days")
                if "avg_review_score" in df.columns:
                    cols_to_show.append("avg_review_score")

                if cols_to_show:
                    stats = df[cols_to_show].describe().round(2)
                    st.dataframe(stats, use_container_width=True)


# ============================================================================
# SECTION: CHAT IA
# ============================================================================
def display_chat(df, lang):
    st.markdown(f'<div class="section-header">{t("nav_chat")}</div>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    col_avatar, col_content = st.columns([1, 3.2], gap="large")

    with col_avatar:
        avatar_url = generate_avatar_b64()
        st.markdown(f"""
        <div class="sonar-avatar-wrap">
            <img src="{avatar_url}" class="sonar-avatar-img" />
            <div class="sonar-avatar-name">Analytics AI</div>
            <div class="sonar-avatar-role">Assistant IA</div>
        </div>
        """, unsafe_allow_html=True)

    with col_content:
        # Header avec reset
        header_col, reset_col = st.columns([4, 1])
        with header_col:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                <span class="sonar-dot"></span>
                <span style="font-weight:600; font-size:1rem;">{t("chat_intro")}</span>
                <span style="color:{theme['muted']}; font-size:0.75rem;">({len(st.session_state.chat_history)} messages)</span>
            </div>
            """, unsafe_allow_html=True)
        with reset_col:
            if st.button("↺ Réinitialiser", key="reset_chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        # Affichage de l'historique
        for role, msg in st.session_state.chat_history:
            if role == "user":
                st.markdown(f"""
                <div class="chat-message chat-user">
                    <b style="color:{COLORS['accent']};">Vous</b><br>{msg}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message chat-assistant">
                    <b style="color:{COLORS['accent']};">Assistant</b><br>{msg}
                </div>
                """, unsafe_allow_html=True)

        # Input
        q = st.chat_input(t("chat_placeholder"))
        if q:
            st.session_state.chat_history.append(("user", q))
            ans = answer_question(q, df, lang)
            st.session_state.chat_history.append(("assistant", ans))
            st.rerun()


# ============================================================================
# MAIN
# ============================================================================
def main():
    df_all = load_data()

    if df_all is None:
        st.error("Impossible de charger les données. Vérifiez que le fichier 'data/fct_orders.parquet' existe.")
        st.stop()

    nav_selected, filters = sidebar(df_all)
    df = apply_filters(df_all, filters)

    # Header
    st.markdown(f'<div class="page-title">{t("app_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{t("app_subtitle")}</div>', unsafe_allow_html=True)

    # Navigation
    nav_map = {
        t('nav_overview'): display_overview,
        t('nav_logistics'): display_logistics,
        t('nav_satisfaction'): display_satisfaction,
        t('nav_customers'): display_customers,
        t('nav_finance'): display_finance,
        t('nav_synthese'): lambda d, da: display_synthese(d, st.session_state.lang),
        t('nav_chat'): lambda d, da: display_chat(d, st.session_state.lang),
    }

    if nav_selected in nav_map:
        nav_map[nav_selected](df, df_all)

    # Footer
    st.markdown(f"""
    <hr style="border-color:{theme['border']}; margin-top:32px;">
    <div style="text-align:center; color:{theme['muted']}; font-size:0.7rem; padding:12px 0;">
        Olist Analytics · Tableau de bord e-commerce · Données Olist
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
