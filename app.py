"""
Olist Analytics — Tableau de bord professionnel.
Structure : 4 onglets avec sous-onglets internes.
Chaque onglet intègre : Synthèse IA (4 axes), Problèmes & Actions, Assistant IA.
"""

import base64
import os
import re
from collections import Counter
from datetime import timedelta

import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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

BRAZIL_GEOJSON_URL = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson"

STOPWORDS_PT = {
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "não", "uma", "os",
    "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "seu",
    "sua", "ou", "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até",
    "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "seus", "quem", "nas", "me",
    "esse", "eles", "você", "essa", "num", "nem", "suas", "meu", "às", "minha", "numa",
    "pelos", "elas", "qual", "nós", "lhe", "deles", "essas", "esses", "pelas", "este",
    "dele", "tu", "te", "vocês", "vos", "lhes", "meus", "minhas", "teu", "tua", "teus",
    "tuas", "nosso", "nossa", "nossos", "nossas", "dela", "delas", "esta", "estes", "estas",
    "aquele", "aquela", "aqueles", "aquelas", "isto", "aquilo", "estou", "está", "estamos",
    "estão", "estive", "esteve", "estivemos", "estiveram", "produto", "recebi", "comprei",
}

# ============================================================================
# COULEURS
# ============================================================================
COLORS = {
    "primary": "#1B2A4A",
    "primary_light": "#2A3F6A",
    "accent": "#C9A84C",
    "accent2": "#4A8C8C",
    "surface": "#F7F8FA",
    "surface_dark": "#1A1E2E",
    "text": "#1A1E2E",
    "text_light": "#6B7A8F",
    "text_white": "#F0F2F8",
    "border": "#E2E6EE",
    "positive": "#3A8C6B",
    "negative": "#C95A5A",
    "warning": "#E8A838",
    "gradient_primary": "linear-gradient(135deg, #1B2A4A 0%, #2A3F6A 100%)",
    "gradient_accent": "linear-gradient(135deg, #C9A84C 0%, #B8953A 100%)",
}

PIE_COLORS = [COLORS["accent"], COLORS["accent2"], COLORS["primary_light"],
              COLORS["positive"], COLORS["negative"], "#8A7A5A", "#5A6E8A"]

# ============================================================================
# I18N
# ============================================================================
TRANSLATIONS = {
    "FR": {
        "app_title": "Olist Analytics",
        "app_subtitle": "Tableau de bord e-commerce",
        "nav_sales": "📊 Ventes & Marché",
        "nav_logistics": "🚚 Logistique & Satisfaction",
        "nav_sellers": "🏪 Vendeurs & Paiements",
        "nav_customers": "👤 Clients",
        "sub_overview": "Vue d'ensemble",
        "sub_finance": "Finance",
        "sub_geo": "Carte",
        "sub_logistics": "Logistique",
        "sub_satisfaction": "Satisfaction",
        "sub_sellers": "Vendeurs",
        "sub_payments": "Paiements",
        "sub_rfm": "RFM",
        "theme_toggle": "Thème clair",
        "theme_toggle_dark": "Thème sombre",
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
        "kpi_top_state_revenue": "1er État (CA)",
        "kpi_top_state_orders": "1er État (commandes)",
        "kpi_states_covered": "États couverts",
        "kpi_seller_count": "Vendeurs actifs",
        "kpi_top_seller": "Top vendeur (CA)",
        "kpi_seller_concentration": "CA du top 10% vendeurs",
        "kpi_payment_types": "Moyens de paiement",
        "kpi_avg_installments": "Versements moyens",
        "chart_sales": "📈 Évolution des ventes",
        "chart_status": "📊 Répartition des statuts",
        "chart_categories": "🏷️ Top catégories",
        "chart_states": "🗺️ Top États",
        "chart_delivery_dist": "📦 Distribution des délais",
        "chart_delivery_state": "🗺️ Délai par État",
        "chart_late_trend": "⏰ Évolution du taux de retard",
        "chart_score_dist": "⭐ Distribution des notes",
        "chart_score_category": "⭐ Note moyenne par catégorie",
        "chart_delivery_score": "📦 Délai vs note",
        "chart_score_price": "💰 Prix vs note",
        "chart_negative_keywords": "🔍 Mots-clés dans les avis négatifs",
        "chart_seller_revenue": "🏆 Top 10 vendeurs (CA)",
        "chart_seller_pareto": "📊 Concentration du CA (Pareto)",
        "chart_seller_score": "⭐ Distribution des notes vendeurs",
        "chart_seller_distance": "📦 Délai selon origine",
        "chart_payment_type": "💳 Moyens de paiement",
        "chart_installments_basket": "📊 Panier moyen par versements",
        "chart_segments": "🎯 Segments RFM",
        "chart_top_clients": "🏆 Top clients (CA)",
        "chart_revenue_cum": "📈 CA cumulé",
        "chart_revenue_category": "🏷️ CA par catégorie",
        "geo_view_label": "Type de carte",
        "geo_view_choropleth": "Carte par État",
        "geo_view_points": "Carte de points",
        "geo_table_title": "Classement des États",
        "geo_intro": "Répartition géographique des ventes et de la logistique.",
        "synthese_title": "🧠 Synthèse IA",
        "synthese_what": "📌 Ce qui s'est passé",
        "synthese_why": "🔍 Pourquoi (la cause)",
        "synthese_attention": "⚠️ Ce qui mérite votre attention",
        "synthese_action": "💡 Ce que vous devriez faire",
        "problems_title": "🚨 Problèmes & Actions",
        "problems_intro": "Problèmes détectés automatiquement à partir des données filtrées.",
        "problems_none": "✅ Aucun problème significatif détecté.",
        "problem_action_label": "Action recommandée",
        "severity_high": "🔴 Critique",
        "severity_medium": "🟡 À surveiller",
        "severity_low": "🟢 Point d'attention",
        "chat_title": "💬 Assistant IA",
        "chat_intro": "Posez vos questions sur les données",
        "chat_placeholder": "Ex: Quel est le CA total ?...",
        "no_data": "Aucune donnée disponible",
        "no_geo": "Données géographiques non disponibles",
        "no_delivery": "Données de livraison non disponibles",
        "no_reviews": "Données d'avis non disponibles",
        "no_customers": "Données clients non disponibles",
        "no_finance": "Données financières non disponibles",
        "no_sellers": "Données vendeurs non disponibles",
        "no_payments": "Données de paiement non disponibles",
        "no_review_text": "Aucun texte d'avis disponible",
        "rfm_champions": "🌟 Champions",
        "rfm_loyal": "❤️ Clients fidèles",
        "rfm_new": "✨ Nouveaux clients",
        "rfm_at_risk": "⚠️ À risque",
        "rfm_lost": "💔 Perdus",
        "rfm_standard": "📊 Standard",
        "same_state": "Même État",
        "diff_state": "Autre État",
        "growth": "croissance",
        "decline": "baisse",
        "stable": "stable",
    },
    "EN": {
        "app_title": "Olist Analytics",
        "app_subtitle": "E-commerce Dashboard",
        "nav_sales": "📊 Sales & Market",
        "nav_logistics": "🚚 Logistics & Satisfaction",
        "nav_sellers": "🏪 Sellers & Payments",
        "nav_customers": "👤 Customers",
        "sub_overview": "Overview",
        "sub_finance": "Finance",
        "sub_geo": "Map",
        "sub_logistics": "Logistics",
        "sub_satisfaction": "Satisfaction",
        "sub_sellers": "Sellers",
        "sub_payments": "Payments",
        "sub_rfm": "RFM",
        "theme_toggle": "Light theme",
        "theme_toggle_dark": "Dark theme",
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
        "kpi_top_state_revenue": "#1 state (revenue)",
        "kpi_top_state_orders": "#1 state (orders)",
        "kpi_states_covered": "States covered",
        "kpi_seller_count": "Active sellers",
        "kpi_top_seller": "Top seller (revenue)",
        "kpi_seller_concentration": "Revenue share of top 10% sellers",
        "kpi_payment_types": "Payment methods",
        "kpi_avg_installments": "Avg installments",
        "chart_sales": "📈 Sales evolution",
        "chart_status": "📊 Status distribution",
        "chart_categories": "🏷️ Top categories",
        "chart_states": "🗺️ Top states",
        "chart_delivery_dist": "📦 Delivery distribution",
        "chart_delivery_state": "🗺️ Delivery by state",
        "chart_late_trend": "⏰ Late rate trend",
        "chart_score_dist": "⭐ Rating distribution",
        "chart_score_category": "⭐ Avg rating by category",
        "chart_delivery_score": "📦 Delivery vs rating",
        "chart_score_price": "💰 Price vs rating",
        "chart_negative_keywords": "🔍 Keywords in negative reviews",
        "chart_seller_revenue": "🏆 Top 10 sellers (revenue)",
        "chart_seller_pareto": "📊 Revenue concentration (Pareto)",
        "chart_seller_score": "⭐ Seller rating distribution",
        "chart_seller_distance": "📦 Delivery time by origin",
        "chart_payment_type": "💳 Payment methods",
        "chart_installments_basket": "📊 Avg basket by installments",
        "chart_segments": "🎯 RFM segments",
        "chart_top_clients": "🏆 Top clients (revenue)",
        "chart_revenue_cum": "📈 Cumulative revenue",
        "chart_revenue_category": "🏷️ Revenue by category",
        "geo_view_label": "Map type",
        "geo_view_choropleth": "Choropleth map",
        "geo_view_points": "Point map",
        "geo_table_title": "State ranking",
        "geo_intro": "Geographic distribution of sales and logistics.",
        "synthese_title": "🧠 AI Summary",
        "synthese_what": "📌 What happened",
        "synthese_why": "🔍 Why (root cause)",
        "synthese_attention": "⚠️ What needs your attention",
        "synthese_action": "💡 What you should do",
        "problems_title": "🚨 Problems & Actions",
        "problems_intro": "Problems automatically detected from the filtered data.",
        "problems_none": "✅ No significant problem detected.",
        "problem_action_label": "Recommended action",
        "severity_high": "🔴 Critical",
        "severity_medium": "🟡 Watch closely",
        "severity_low": "🟢 Worth noting",
        "chat_title": "💬 AI Assistant",
        "chat_intro": "Ask about the data",
        "chat_placeholder": "E.g.: What's the total revenue?...",
        "no_data": "No data available",
        "no_geo": "Geographic data not available",
        "no_delivery": "Delivery data not available",
        "no_reviews": "Review data not available",
        "no_customers": "Customer data not available",
        "no_finance": "Financial data not available",
        "no_sellers": "Seller data not available",
        "no_payments": "Payment data not available",
        "no_review_text": "No review text available",
        "rfm_champions": "🌟 Champions",
        "rfm_loyal": "❤️ Loyal customers",
        "rfm_new": "✨ New customers",
        "rfm_at_risk": "⚠️ At risk",
        "rfm_lost": "💔 Lost",
        "rfm_standard": "📊 Standard",
        "same_state": "Same state",
        "diff_state": "Other state",
        "growth": "growth",
        "decline": "decline",
        "stable": "stable",
    }
}

# ============================================================================
# THEME
# ============================================================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "lang" not in st.session_state:
    st.session_state.lang = "FR"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


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
# CSS
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

.filter-section {{
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {theme["muted"]};
    font-weight: 600;
    margin: 12px 0 8px 0;
}}

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

.data-note {{
    color: {theme["muted"]};
    font-size: 0.7rem;
    font-style: italic;
    margin-top: -6px;
    margin-bottom: 12px;
}}

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
    font-size: 1.1rem;
    font-weight: 600;
    color: {theme["text"]};
    margin: 12px 0 10px 0;
}}
.sub-header {{
    font-size: 0.95rem;
    font-weight: 600;
    color: {theme["text"]};
    margin: 8px 0 6px 0;
}}

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
    line-height: 1.5;
}}

.problem-card {{
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    border-left: 4px solid {theme["border"]};
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
}}
.problem-high {{ border-left-color: {COLORS["negative"]}; }}
.problem-medium {{ border-left-color: {COLORS["warning"]}; }}
.problem-low {{ border-left-color: {COLORS["positive"]}; }}
.problem-badge {{
    display: inline-block;
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 20px;
    margin-bottom: 6px;
}}
.problem-badge-high {{ background: rgba(201,90,90,0.15); color: {COLORS["negative"]}; }}
.problem-badge-medium {{ background: rgba(232,168,56,0.15); color: {COLORS["warning"]}; }}
.problem-badge-low {{ background: rgba(58,140,107,0.15); color: {COLORS["positive"]}; }}
.problem-title {{
    font-weight: 700;
    font-size: 0.95rem;
    color: {theme["text"]};
    margin-bottom: 4px;
}}
.problem-desc {{
    font-size: 0.85rem;
    color: {theme["muted"]};
    margin-bottom: 6px;
    line-height: 1.4;
}}
.problem-action {{
    font-size: 0.82rem;
    color: {theme["text"]};
    background: {theme["surface"]};
    padding: 8px 10px;
    border-radius: 6px;
    line-height: 1.4;
}}

.missing-data-card {{
    background: {theme["card"]};
    border: 1px dashed {theme["card_border"]};
    border-radius: 10px;
    padding: 16px 18px;
    color: {theme["muted"]};
    font-size: 0.85rem;
    line-height: 1.5;
}}

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

.section-end {{
    margin-top: 28px;
    padding-top: 16px;
    border-top: 2px solid {theme["border"]};
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}

.sonar-avatar-wrap {{
    border-radius: 14px;
    padding: 16px;
    background: {theme["card"]};
    border: 1px solid {theme["card_border"]};
    text-align: center;
}}
.sonar-avatar-img {{
    width: 100%;
    max-width: 100px;
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

.tabs {{
    display: flex;
    gap: 4px;
    margin-bottom: 12px;
    border-bottom: 1px solid {theme["border"]};
    padding-bottom: 8px;
}}
.tab-btn {{
    padding: 6px 16px;
    border-radius: 8px 8px 0 0;
    font-weight: 500;
    font-size: 0.82rem;
    cursor: pointer;
    border: none;
    background: transparent;
    color: {theme["muted"]};
}}
.tab-btn:hover {{
    color: {theme["text"]};
}}
.tab-btn-active {{
    background: {theme["card"]};
    border-bottom: 2px solid {COLORS["accent"]};
    color: {theme["text"]};
}}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CHARGEMENT DES DONNEES
# ============================================================================
@st.cache_data
def load_data():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parquet_path = os.path.join(base_dir, "data", "fct_orders.parquet")

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
                df[col] = pd.to_datetime(df[col], errors="coerce")

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
            df["customer_state_code"] = df["customer_state"]
            df["customer_state"] = df["customer_state"].map(BR_STATES).fillna(df["customer_state"])

        if "seller_state" in df.columns:
            df["seller_state"] = df["seller_state"].fillna("Inconnu")
            df["seller_state_code"] = df["seller_state"]
            df["seller_state"] = df["seller_state"].map(BR_STATES).fillna(df["seller_state"])

        if "purchased_at" in df.columns:
            df["month_year"] = df["purchased_at"].dt.to_period("M").astype(str)

        if "max_installments" not in df.columns and "payment_installments" in df.columns:
            df["max_installments"] = df["payment_installments"]

        return df

    except Exception as e:
        st.error(f"Erreur: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_brazil_geojson():
    try:
        import requests
        resp = requests.get(BRAZIL_GEOJSON_URL, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def find_latlon_cols(df):
    candidates = [
        ("customer_lat", "customer_lng"),
        ("customer_lat", "customer_lon"),
        ("customer_latitude", "customer_longitude"),
        ("geolocation_lat", "geolocation_lng"),
        ("lat", "lng"),
        ("lat", "lon"),
        ("latitude", "longitude"),
    ]
    for lat_c, lon_c in candidates:
        if lat_c in df.columns and lon_c in df.columns:
            return lat_c, lon_c
    return None


def find_review_text_col(df):
    for c in ["review_comment_message", "review_text", "comment", "review_comment"]:
        if c in df.columns:
            return c
    return None


# ============================================================================
# HELPERS
# ============================================================================
def t(key):
    return TRANSLATIONS[st.session_state.lang].get(key, key)


def style_fig(fig, height=280, show_legend=True):
    fig.update_layout(
        template="plotly_dark" if st.session_state.theme == "dark" else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family="Inter, sans-serif"),
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    grid_color = "rgba(255,255,255,0.05)" if st.session_state.theme == "dark" else "rgba(0
