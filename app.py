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
    grid_color = "rgba(255,255,255,0.05)" if st.session_state.theme == "dark" else "rgba(0,0,0,0.06)"
    fig.update_xaxes(gridcolor=grid_color, zeroline=False)
    fig.update_yaxes(gridcolor=grid_color, zeroline=False)
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


def missing_data_card(message):
    st.markdown(f'<div class="missing-data-card">{message}</div>', unsafe_allow_html=True)


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
    svg = f"""
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="100" rx="12" fill="{COLORS['primary']}"/>
        <circle cx="50" cy="40" r="22" fill="{COLORS['accent']}" opacity="0.3"/>
        <circle cx="50" cy="40" r="14" fill="{COLORS['accent']}" opacity="0.6"/>
        <circle cx="50" cy="40" r="8" fill="{COLORS['accent']}"/>
        <rect x="28" y="70" width="44" height="5" rx="2.5" fill="{COLORS['accent2']}" opacity="0.4"/>
        <rect x="35" y="80" width="30" height="5" rx="2.5" fill="{COLORS['accent2']}" opacity="0.25"/>
    </svg>
    """
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"


# ============================================================================
# IA / INSIGHTS AVANCEES
# ============================================================================
def generate_advanced_insights(df, lang, domain=""):
    """Génère une synthèse IA structurée en 4 axes."""
    t_ = TRANSLATIONS[lang]
    
    if df.empty:
        return {
            "what": "Aucune donnée disponible pour cette sélection.",
            "why": "Les filtres appliqués peuvent être trop restrictifs ou les données sont manquantes.",
            "attention": "Vérifiez les filtres et la période sélectionnée.",
            "action": "Élargissez les filtres ou chargez une période plus large."
        }
    
    df = df.copy()
    insights = {
        "what": "",
        "why": "",
        "attention": "",
        "action": ""
    }
    
    # 1. Ce qui s'est passé (WHAT)
    what_parts = []
    
    if "price" in df.columns and not df.empty:
        total_rev = df["price"].sum()
        n_orders = df["order_id"].nunique() if "order_id" in df.columns else 0
        what_parts.append(f"CA total de {total_rev:,.0f} R$ pour {n_orders:,} commandes")
        
        if "purchased_at" in df.columns:
            df["month"] = df["purchased_at"].dt.to_period("M")
            monthly = df.groupby("month")["price"].sum()
            if len(monthly) > 1:
                trend = t_["growth"] if monthly.iloc[-1] > monthly.iloc[-2] else t_["decline"]
                what_parts.append(f"tendance {trend} sur la période")
    
    if "avg_review_score" in df.columns:
        avg_score = df["avg_review_score"].mean()
        what_parts.append(f"note moyenne de {avg_score:.1f}/5")
    
    if "delivery_days" in df.columns:
        avg_delivery = df["delivery_days"].mean()
        late_rate = (df["is_late"].mean() * 100) if "is_late" in df.columns else 0
        what_parts.append(f"délai moyen de {avg_delivery:.1f} jours ({late_rate:.1f}% de retards)")
    
    insights["what"] = " | ".join(what_parts) if what_parts else "Données disponibles mais analyse en cours."
    
    # 2. Pourquoi (WHY) - Causes racines
    why_parts = []
    
    if "customer_state" in df.columns and "price" in df.columns:
        top_state = df.groupby("customer_state")["price"].sum().sort_values(ascending=False)
        if not top_state.empty and len(top_state) > 1:
            top_pct = (top_state.iloc[0] / top_state.sum() * 100)
            if top_pct > 30:
                why_parts.append(f"forte concentration des ventes dans {top_state.index[0]} ({top_pct:.1f}% du CA)")
    
    if "is_late" in df.columns:
        late_rate = df["is_late"].mean() * 100
        if late_rate > 10:
            if "customer_state" in df.columns:
                worst_state = df.groupby("customer_state")["is_late"].mean().sort_values(ascending=False)
                if not worst_state.empty:
                    why_parts.append(f"retards concentrés dans {worst_state.index[0]} ({worst_state.iloc[0]*100:.1f}%)")
    
    if "avg_review_score" in df.columns and "product_category" in df.columns:
        cat_scores = df.groupby("product_category")["avg_review_score"].mean().sort_values()
        if not cat_scores.empty and cat_scores.iloc[0] < 3.5:
            why_parts.append(f"mauvaises notes sur '{cat_scores.index[0]}' ({cat_scores.iloc[0]:.1f}/5)")
    
    if "delivery_days" in df.columns and "avg_review_score" in df.columns:
        corr = df["delivery_days"].corr(df["avg_review_score"])
        if pd.notna(corr) and corr < -0.2:
            why_parts.append(f"corrélation délai/note négative ({corr:.2f})")
    
    if "customer_unique_id" in df.columns:
        repeat_rate = (df.groupby("customer_unique_id")["order_id"].nunique() > 1).mean() * 100
        if repeat_rate < 15:
            why_parts.append(f"faible fidélisation ({repeat_rate:.1f}% de réachat)")
    
    insights["why"] = " | ".join(why_parts) if why_parts else "Aucune cause majeure identifiée dans les données actuelles."
    
    # 3. Ce qui mérite l'attention (ATTENTION)
    attention_parts = []
    
    if "is_late" in df.columns:
        late_rate = df["is_late"].mean() * 100
        if late_rate > 15:
            attention_parts.append(f"🔴 Taux de retard élevé ({late_rate:.1f}%)")
        elif late_rate > 8:
            attention_parts.append(f"🟡 Taux de retard à surveiller ({late_rate:.1f}%)")
    
    if "avg_review_score" in df.columns:
        avg_score = df["avg_review_score"].mean()
        if avg_score < 3.5:
            attention_parts.append(f"🔴 Note moyenne basse ({avg_score:.1f}/5)")
        elif avg_score < 4.0:
            attention_parts.append(f"🟡 Note moyenne en baisse ({avg_score:.1f}/5)")
    
    if "customer_unique_id" in df.columns:
        churn_rate = (df.groupby("customer_unique_id")["purchased_at"].max() < (df["purchased_at"].max() - timedelta(days=365))).mean() * 100 if "purchased_at" in df.columns else 0
        if churn_rate > 30:
            attention_parts.append(f"🔴 Taux de churn élevé ({churn_rate:.1f}%)")
    
    if "price" in df.columns:
        avg_basket = df["price"].mean() if "order_id" in df.columns else 0
        if avg_basket < 100:
            attention_parts.append(f"🟡 Panier moyen faible (R$ {avg_basket:.0f})")
    
    if "seller_id" in df.columns and "price" in df.columns:
        n_sellers = df["seller_id"].nunique()
        if n_sellers < 50:
            attention_parts.append(f"🟡 Faible nombre de vendeurs actifs ({n_sellers})")
    
    if not attention_parts:
        attention_parts.append("✅ Aucune anomalie majeure détectée")
    
    insights["attention"] = " | ".join(attention_parts)
    
    # 4. Ce que vous devriez faire (ACTION)
    action_parts = []
    
    if "is_late" in df.columns and df["is_late"].mean() * 100 > 10:
        action_parts.append("📦 Renégocier les délais transporteurs et ajuster les estimations de livraison")
    
    if "avg_review_score" in df.columns and df["avg_review_score"].mean() < 3.5:
        action_parts.append("⭐ Auditer les produits les moins bien notés et contacter les vendeurs concernés")
    
    if "customer_unique_id" in df.columns:
        repeat_rate = (df.groupby("customer_unique_id")["order_id"].nunique() > 1).mean() * 100
        if repeat_rate < 15:
            action_parts.append("💌 Mettre en place un programme de fidélisation et des campagnes de réactivation")
    
    if "customer_state" in df.columns and "price" in df.columns:
        top_state = df.groupby("customer_state")["price"].sum().sort_values(ascending=False)
        if not top_state.empty and len(top_state) > 1:
            top_pct = (top_state.iloc[0] / top_state.sum() * 100)
            if top_pct > 35:
                action_parts.append("🗺️ Diversifier l'acquisition client vers d'autres États")
    
    if "seller_id" in df.columns and "price" in df.columns:
        seller_share = df.groupby("seller_id")["price"].sum()
        top10_share = seller_share.sort_values(ascending=False).head(int(len(seller_share)*0.1)).sum() / seller_share.sum() * 100 if len(seller_share) > 0 else 0
        if top10_share > 60:
            action_parts.append("🏪 Diversifier le portefeuille vendeurs et recruter de nouveaux partenaires")
    
    if not action_parts:
        action_parts.append("📊 Maintenir les bonnes pratiques actuelles et surveiller les tendances")
    
    insights["action"] = " | ".join(action_parts)
    
    return insights


# ============================================================================
# CHAT
# ============================================================================
def answer_question(q, df, lang):
    q_lower = q.lower()
    
    if any(w in q_lower for w in ["chiffre", "ca", "revenue", "vente", "sales"]):
        if "price" in df.columns:
            total = df["price"].sum()
            return f"💰 Le chiffre d'affaires total est de {total:,.0f} R$."
        return "Données de chiffre d'affaires non disponibles."
    
    if any(w in q_lower for w in ["livraison", "delivery", "retard", "late"]):
        if "delivery_days" in df.columns:
            avg = df["delivery_days"].mean()
            late = (df["is_late"].mean() * 100) if "is_late" in df.columns else 0
            return f"📦 Délai moyen: {avg:.1f} jours. Taux de retard: {late:.1f}%."
        return "Données de livraison non disponibles."
    
    if any(w in q_lower for w in ["note", "avis", "review", "satisfaction"]):
        if "avg_review_score" in df.columns:
            avg = df["avg_review_score"].mean()
            good = (df["avg_review_score"] >= 4).mean() * 100
            return f"⭐ Note moyenne: {avg:.1f}/5. Bonnes notes: {good:.1f}%."
        return "Données d'avis non disponibles."
    
    if any(w in q_lower for w in ["client", "customer"]):
        if "customer_unique_id" in df.columns:
            n = df["customer_unique_id"].nunique()
            repeat = (df.groupby("customer_unique_id")["order_id"].nunique() > 1).mean() * 100 if "order_id" in df.columns else 0
            return f"👤 {n:,} clients uniques. Taux de réachat: {repeat:.1f}%."
        return "Données clients non disponibles."
    
    if any(w in q_lower for w in ["état", "etat", "state", "région", "region"]):
        if "customer_state" in df.columns and "price" in df.columns:
            top = df.groupby("customer_state")["price"].sum().sort_values(ascending=False)
            if not top.empty:
                return f"🗺️ L'État générant le plus de CA est {top.index[0]} avec {top.iloc[0]:,.0f} R$."
        return "Données géographiques non disponibles."
    
    if any(w in q_lower for w in ["vendeur", "seller"]):
        if "seller_id" in df.columns:
            n = df["seller_id"].nunique()
            top = df.groupby("seller_id")["price"].sum().sort_values(ascending=False).iloc[0] if "price" in df.columns else 0
            return f"🏪 {n:,} vendeurs actifs. Top vendeur: R$ {top:,.0f}."
        return "Données vendeurs non disponibles."
    
    if any(w in q_lower for w in ["paiement", "payment", "boleto"]):
        if "payment_type" in df.columns:
            top = df["payment_type"].value_counts()
            return f"💳 Le moyen de paiement le plus utilisé est '{top.index[0]}' ({top.iloc[0]:,} commandes)."
        return "Données de paiement non disponibles."
    
    return ("Je peux vous renseigner sur : le chiffre d'affaires, les livraisons, les avis clients, "
            "la répartition géographique, les vendeurs, les paiements et les statistiques générales.")


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
        
        col_lang1, col_lang2 = st.columns(2)
        with col_lang1:
            if st.button("Français", use_container_width=True):
                st.session_state.lang = "FR"
                st.rerun()
        with col_lang2:
            if st.button("English", use_container_width=True):
                st.session_state.lang = "EN"
                st.rerun()
        
        st.markdown("<hr class='brand-separator'>", unsafe_allow_html=True)
        
        st.markdown('<div class="nav-label">Navigation</div>', unsafe_allow_html=True)
        nav_options = [
            t('nav_sales'),
            t('nav_logistics'),
            t('nav_sellers'),
            t('nav_customers'),
        ]
        nav_selected = st.radio("", nav_options, label_visibility="collapsed")
        
        st.markdown("<hr class='brand-separator'>", unsafe_allow_html=True)
        theme_btn_label = t("theme_toggle") if st.session_state.theme == "dark" else t("theme_toggle_dark")
        if st.button(theme_btn_label, use_container_width=True):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
        
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
# SECTION: VENTES & MARCHE
# ============================================================================
def display_sales_market(df, df_all):
    st.markdown(f'<div class="section-header">{t("nav_sales")}</div>', unsafe_allow_html=True)
    
    # Sous-onglets
    sub_tabs = st.tabs([t('sub_overview'), t('sub_finance'), t('sub_geo')])
    
    with sub_tabs[0]:
        display_overview(df, df_all)
    
    with sub_tabs[1]:
        display_finance(df, df_all)
    
    with sub_tabs[2]:
        display_geo(df, df_all)


def display_overview(df, df_all):
    if "price" not in df.columns:
        st.warning(t("no_finance"))
        return
    
    valid = df[df["price"] > 0]
    valid_all = df_all[df_all["price"] > 0]
    
    if valid.empty:
        st.warning(t("no_finance"))
        return
    
    total_revenue = valid["price"].sum()
    total_orders = valid["order_id"].nunique() if "order_id" in valid.columns else 0
    unique_customers = valid["customer_unique_id"].nunique() if "customer_unique_id" in valid.columns else 0
    avg_basket = total_revenue / total_orders if total_orders > 0 else 0
    n_orders_all = valid_all["order_id"].nunique() if "order_id" in valid_all.columns else 0
    avg_basket_all = valid_all["price"].sum() / n_orders_all if n_orders_all > 0 else avg_basket
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
                daily_sales = valid.groupby(valid["purchased_at"].dt.date)["price"].sum().reset_index()
                daily_sales.columns = ["purchased_at", "price"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_sales["purchased_at"], y=daily_sales["price"], mode="lines",
                    line=dict(color=COLORS["accent"], width=2.5),
                    fill="tozeroy", fillcolor=COLORS["accent"] + "22",
                ))
                fig.add_annotation(
                    x=daily_sales["purchased_at"].iloc[-1] if len(daily_sales) > 0 else None,
                    y=daily_sales["price"].iloc[-1] if len(daily_sales) > 0 else None,
                    text=f"R$ {daily_sales['price'].iloc[-1]:,.0f}" if len(daily_sales) > 0 else "",
                    showarrow=False,
                    yshift=10,
                )
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_status")}</div>', unsafe_allow_html=True)
            if "status" in valid.columns and not valid.empty:
                status_counts = valid["status"].value_counts()
                fig = go.Figure(go.Pie(
                    labels=status_counts.index,
                    values=status_counts.values,
                    hole=0.5,
                    marker=dict(colors=PIE_COLORS),
                    textfont=dict(color=theme["text"]),
                    textinfo="percent+label",
                ))
                st.plotly_chart(style_fig(fig, height=240), use_container_width=True, config={"displayModeBar": False})


def display_finance(df, df_all):
    if "price" not in df.columns:
        st.warning(t("no_finance"))
        return
    
    valid = df[df["price"] > 0]
    if valid.empty:
        st.warning(t("no_finance"))
        return
    
    total_revenue = valid["price"].sum()
    total_payment = valid["total_payment_value"].sum() if "total_payment_value" in valid.columns else total_revenue
    n_orders = valid["order_id"].nunique() if "order_id" in valid.columns else 0
    avg_installments = valid["max_installments"].mean() if "max_installments" in valid.columns else None
    
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card(t("kpi_revenue"), f"R$ {total_revenue:,.0f}", featured=True)
    with c2:
        metric_card("Total encaissé" if st.session_state.lang == "FR" else "Total collected", f"R$ {total_payment:,.0f}")
    with c3:
        if avg_installments is not None:
            label = "Versements moyens" if st.session_state.lang == "FR" else "Avg installments"
            metric_card(label, f"{avg_installments:.1f}x")
        else:
            metric_card(t("kpi_orders"), f"{n_orders:,}")
    
    col_left, col_right = st.columns([1.6, 1])
    
    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_revenue_cum")}</div>', unsafe_allow_html=True)
            if "month_year" in valid.columns:
                monthly = valid.groupby("month_year")["price"].sum().reset_index().sort_values("month_year")
                monthly["cumulative"] = monthly["price"].cumsum()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly["month_year"],
                    y=monthly["cumulative"],
                    mode="lines+markers",
                    line=dict(color=COLORS["accent"], width=3),
                    marker=dict(color=COLORS["accent"], size=6),
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
                    marker=dict(colors=PIE_COLORS),
                    textfont=dict(color=theme["text"]),
                    textinfo="percent+label",
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})


def display_geo(df, df_all):
    if "customer_state" not in df.columns:
        st.warning(t("no_geo"))
        return
    
    valid = df[df["price"] > 0] if "price" in df.columns else df.copy()
    if valid.empty:
        st.warning(t("no_geo"))
        return
    
    st.caption(t("geo_intro"))
    
    has_revenue = "price" in valid.columns
    agg_dict = {"orders": ("order_id", "nunique")} if "order_id" in valid.columns else {}
    if has_revenue:
        agg_dict["revenue"] = ("price", "sum")
    if "is_late" in valid.columns:
        agg_dict["late_rate"] = ("is_late", "mean")
    if "avg_review_score" in valid.columns:
        agg_dict["avg_score"] = ("avg_review_score", "mean")
    
    state_agg = valid.groupby("customer_state").agg(**agg_dict).reset_index()
    if not has_revenue:
        state_agg["revenue"] = state_agg["orders"] if "orders" in state_agg.columns else 0
    
    state_agg_sorted = state_agg.sort_values("revenue", ascending=False)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if not state_agg_sorted.empty:
            top_row = state_agg_sorted.iloc[0]
            metric_card(t("kpi_top_state_revenue"),
                        f"{top_row['customer_state']}",
                        delta_text=f"R$ {top_row['revenue']:,.0f}" if has_revenue else f"{top_row['revenue']:,.0f} cmd.",
                        featured=True)
    with c2:
        if "orders" in state_agg_sorted.columns and not state_agg_sorted.empty:
            top_orders_row = state_agg.sort_values("orders", ascending=False).iloc[0]
            metric_card(t("kpi_top_state_orders"), f"{top_orders_row['customer_state']}",
                        delta_text=f"{top_orders_row['orders']:,.0f}")
    with c3:
        metric_card(t("kpi_states_covered"), f"{state_agg['customer_state'].nunique()}")
    
    latlon = find_latlon_cols(valid)
    view_options = [t("geo_view_choropleth")]
    if latlon:
        view_options.append(t("geo_view_points"))
    view = st.radio(t("geo_view_label"), view_options, horizontal=True, label_visibility="collapsed")
    
    mapbox_style = "carto-darkmatter" if st.session_state.theme == "dark" else "carto-positron"
    
    with st.container(border=True):
        map_rendered = False
        if view == t("geo_view_choropleth"):
            geojson = load_brazil_geojson()
            if geojson is not None:
                try:
                    fig = px.choropleth_mapbox(
                        state_agg, geojson=geojson, locations="customer_state",
                        featureidkey="properties.name", color="revenue",
                        color_continuous_scale=[theme["surface"], COLORS["accent"]],
                        mapbox_style=mapbox_style, zoom=2.6,
                        center={"lat": -14.2, "lon": -51.9}, opacity=0.85,
                        labels={"revenue": "CA (R$)" if has_revenue else "Commandes"},
                        hover_data={"orders": True, "revenue": ":.0f"},
                    )
                    fig.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0),
                                      paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    map_rendered = True
                except Exception:
                    map_rendered = False
        else:
            lat_c, lon_c = latlon
            pts = valid.dropna(subset=[lat_c, lon_c])
            try:
                fig = px.scatter_mapbox(
                    pts, lat=lat_c, lon=lon_c, zoom=2.6,
                    center={"lat": -14.2, "lon": -51.9}, opacity=0.55,
                    color="price" if has_revenue else None,
                    color_continuous_scale=[theme["surface"], COLORS["accent"]],
                    mapbox_style=mapbox_style,
                )
                fig.update_traces(marker=dict(size=5))
                fig.update_layout(height=420, margin=dict(l=0, r=0, t=0, b=0),
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                map_rendered = True
            except Exception:
                map_rendered = False
        
        if not map_rendered:
            fig = px.bar(state_agg_sorted, x="customer_state", y="revenue")
            fig.update_traces(marker_color=COLORS["accent"])
            st.plotly_chart(style_fig(fig, height=420), use_container_width=True, config={"displayModeBar": False})
            st.caption("Carte indisponible — affichage en barres.")


# ============================================================================
# SECTION: LOGISTIQUE & SATISFACTION
# ============================================================================
def display_logistics_satisfaction(df, df_all):
    st.markdown(f'<div class="section-header">{t("nav_logistics")}</div>', unsafe_allow_html=True)
    
    sub_tabs = st.tabs([t('sub_logistics'), t('sub_satisfaction')])
    
    with sub_tabs[0]:
        display_logistics(df, df_all)
    
    with sub_tabs[1]:
        display_satisfaction(df, df_all)


def display_logistics(df, df_all):
    if "delivery_days" not in df.columns:
        st.warning(t("no_delivery"))
        return
    
    valid = df[df["delivery_days"].notna()]
    valid_all = df_all[df_all["delivery_days"].notna()]
    
    if valid.empty:
        st.warning(t("no_delivery"))
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
            fig.add_vline(x=avg_delivery, line_dash="dash", line_color=COLORS["negative"],
                          annotation_text=f"Moy: {avg_delivery:.1f}j")
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_late_trend")}</div>', unsafe_allow_html=True)
            if "purchased_at" in valid.columns and "is_late" in valid.columns:
                v = valid.copy()
                v["month_year"] = v["purchased_at"].dt.to_period("M").astype(str)
                late_by_month = v.groupby("month_year")["is_late"].mean().reset_index()
                late_by_month["is_late"] = late_by_month["is_late"] * 100
                fig = go.Figure(go.Scatter(
                    x=late_by_month["month_year"],
                    y=late_by_month["is_late"],
                    mode="lines+markers",
                    line=dict(color=COLORS["accent2"], width=2.5),
                    marker=dict(color=COLORS["accent2"], size=8),
                ))
                fig.add_hline(y=late_rate, line_dash="dash", line_color=COLORS["negative"],
                              annotation_text=f"Moy: {late_rate:.1f}%")
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    if "customer_state" in valid.columns:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_delivery_state")}</div>', unsafe_allow_html=True)
            top_states = valid["customer_state"].value_counts().head(12).index
            v = valid[valid["customer_state"].isin(top_states)]
            fig = px.box(v, x="customer_state", y="delivery_days", color="customer_state",
                         color_discrete_sequence=[COLORS["accent2"]] * len(top_states))
            st.plotly_chart(style_fig(fig, height=280, show_legend=False), use_container_width=True, config={"displayModeBar": False})


def display_satisfaction(df, df_all):
    if "avg_review_score" not in df.columns:
        st.warning(t("no_reviews"))
        return
    
    valid = df[df["avg_review_score"].notna()]
    if valid.empty:
        st.warning(t("no_reviews"))
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
                number={"suffix": "/5", "font": {"color": theme["text"], "size": 28}},
                gauge={
                    "axis": {"range": [0, 5], "tickcolor": theme["muted"]},
                    "bar": {"color": COLORS["accent"]},
                    "steps": [
                        {"range": [0, 2], "color": COLORS["negative"] + "33"},
                        {"range": [2, 4], "color": COLORS["warning"] + "33"},
                        {"range": [4, 5], "color": COLORS["positive"] + "33"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": avg_score
                    }
                }
            ))
            fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10),
                             paper_bgcolor="rgba(0,0,0,0)", font=dict(color=theme["text"]))
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
                colors = [COLORS["positive"] if s >= 4 else COLORS["warning"] if s >= 3 else COLORS["negative"] for s in score_by_cat.values]
                fig = px.bar(x=score_by_cat.values, y=score_by_cat.index, orientation="h")
                fig.update_traces(marker_color=colors)
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    with col_b:
        if "delivery_days" in valid.columns:
            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("chart_delivery_score")}</div>', unsafe_allow_html=True)
                d = valid[valid["delivery_days"].notna()]
                if not d.empty:
                    fig = px.scatter(d, x="delivery_days", y="avg_review_score", opacity=0.4,
                                     trendline="ols", trendline_color_override=COLORS["negative"])
                    fig.update_traces(marker_color=COLORS["accent"], marker_size=6)
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    # Mots-clés négatifs
    with st.container(border=True):
        st.markdown(f'<div class="card-title">{t("chart_negative_keywords")}</div>', unsafe_allow_html=True)
        text_col = find_review_text_col(valid)
        if text_col is None:
            missing_data_card(t("no_review_text"))
        else:
            neg = valid.loc[valid["avg_review_score"] <= 2, text_col].dropna().astype(str)
            if neg.empty:
                st.info("Aucun avis négatif trouvé.")
            else:
                words = []
                for txt in neg:
                    tokens = re.findall(r"[a-zà-úA-ZÀ-Ú]+", txt.lower())
                    words.extend(w for w in tokens if len(w) > 3 and w not in STOPWORDS_PT)
                if words:
                    counter = Counter(words).most_common(15)
                    words, counts = zip(*counter)
                    fig = go.Figure(go.Bar(
                        x=list(counts), y=list(words), orientation="h",
                        marker_color=COLORS["negative"],
                    ))
                    fig.update_yaxes(autorange="reversed")
                    st.plotly_chart(style_fig(fig, height=380), use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Aucun mot-clé significatif trouvé dans les avis négatifs.")


# ============================================================================
# SECTION: VENDEURS & PAIEMENTS
# ============================================================================
def display_sellers_payments(df, df_all):
    st.markdown(f'<div class="section-header">{t("nav_sellers")}</div>', unsafe_allow_html=True)
    
    sub_tabs = st.tabs([t('sub_sellers'), t('sub_payments')])
    
    with sub_tabs[0]:
        display_sellers(df, df_all)
    
    with sub_tabs[1]:
        display_payments(df, df_all)


def display_sellers(df, df_all):
    if "seller_id" not in df.columns:
        st.warning(t("no_sellers"))
        return
    
    valid = df[df["price"] > 0] if "price" in df.columns else df.copy()
    valid = valid[valid["seller_id"].notna()]
    if valid.empty:
        st.warning(t("no_sellers"))
        return
    
    has_revenue = "price" in valid.columns
    agg = {"orders": ("order_id", "nunique")} if "order_id" in valid.columns else {}
    if has_revenue:
        agg["revenue"] = ("price", "sum")
    if "avg_review_score" in valid.columns:
        agg["avg_score"] = ("avg_review_score", "mean")
    
    seller_agg = valid.groupby("seller_id").agg(**agg).reset_index()
    sort_col = "revenue" if has_revenue else "orders"
    seller_agg_sorted = seller_agg.sort_values(sort_col, ascending=False).reset_index(drop=True)
    
    n_sellers = len(seller_agg_sorted)
    total = seller_agg_sorted[sort_col].sum()
    top10_n = max(1, int(np.ceil(n_sellers * 0.1)))
    top10_share = seller_agg_sorted.iloc[:top10_n][sort_col].sum() / total * 100 if total > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card(t("kpi_seller_count"), f"{n_sellers:,}", featured=True)
    with c2:
        if not seller_agg_sorted.empty:
            top_seller_id = str(seller_agg_sorted.iloc[0]["seller_id"])
            metric_card(t("kpi_top_seller"), top_seller_id[:14],
                        delta_text=f"R$ {seller_agg_sorted.iloc[0][sort_col]:,.0f}" if has_revenue else f"{seller_agg_sorted.iloc[0][sort_col]:,.0f} cmd.")
    with c3:
        metric_card(t("kpi_seller_concentration"), f"{top10_share:.1f}%")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_seller_revenue")}</div>', unsafe_allow_html=True)
            top10 = seller_agg_sorted.head(10)
            labels = top10["seller_id"].astype(str).str.slice(0, 10)
            fig = go.Figure(go.Bar(
                x=labels, y=top10[sort_col], marker_color=COLORS["accent"],
                text=[f"R$ {v:,.0f}" if has_revenue else f"{v:.0f}" for v in top10[sort_col]],
                textposition="outside"
            ))
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_seller_pareto")}</div>', unsafe_allow_html=True)
            pareto = seller_agg_sorted.copy()
            pareto["cum_pct"] = pareto[sort_col].cumsum() / total * 100 if total > 0 else 0
            pareto["seller_rank_pct"] = (np.arange(1, n_sellers + 1)) / n_sellers * 100
            fig = go.Figure(go.Scatter(
                x=pareto["seller_rank_pct"], y=pareto["cum_pct"], mode="lines",
                line=dict(color=COLORS["accent2"], width=2.5), fill="tozeroy",
                fillcolor=COLORS["accent2"] + "22",
            ))
            fig.add_hline(y=80, line_dash="dash", line_color=COLORS["negative"],
                          annotation_text="80%")
            fig.add_hline(y=20, line_dash="dash", line_color=COLORS["positive"],
                          annotation_text="20%")
            fig.update_xaxes(title="% des vendeurs" if st.session_state.lang == "FR" else "% of sellers")
            fig.update_yaxes(title="% du CA cumulé" if st.session_state.lang == "FR" else "% cumulative revenue")
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    if "avg_score" in seller_agg.columns:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_seller_score")}</div>', unsafe_allow_html=True)
            fig = px.histogram(seller_agg.dropna(subset=["avg_score"]), x="avg_score", nbins=20)
            fig.update_traces(marker_color=COLORS["accent"])
            st.plotly_chart(style_fig(fig, height=260), use_container_width=True, config={"displayModeBar": False})
    
    if "seller_state" in valid.columns and "customer_state" in valid.columns and "delivery_days" in valid.columns:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_seller_distance")}</div>', unsafe_allow_html=True)
            v = valid.dropna(subset=["seller_state", "customer_state", "delivery_days"]).copy()
            if not v.empty:
                v["origin"] = np.where(v["seller_state"] == v["customer_state"], t("same_state"), t("diff_state"))
                fig = px.box(v, x="origin", y="delivery_days", color="origin",
                             color_discrete_sequence=[COLORS["positive"], COLORS["negative"]])
                st.plotly_chart(style_fig(fig, height=260), use_container_width=True, config={"displayModeBar": False})


def display_payments(df, df_all):
    has_type = "payment_type" in df.columns
    installments_col = "max_installments" if "max_installments" in df.columns else (
        "payment_installments" if "payment_installments" in df.columns else None
    )
    
    if not has_type and installments_col is None:
        st.warning(t("no_payments"))
        return
    
    valid = df[df["price"] > 0] if "price" in df.columns else df.copy()
    if valid.empty:
        st.warning(t("no_payments"))
        return
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if has_type:
            metric_card(t("kpi_payment_types"), f"{valid['payment_type'].nunique()}", featured=True)
        else:
            metric_card(t("kpi_payment_types"), "—", featured=True)
    with c2:
        if installments_col:
            metric_card(t("kpi_avg_installments"), f"{valid[installments_col].mean():.1f}x")
        else:
            metric_card(t("kpi_avg_installments"), "—")
    with c3:
        total_payment = valid["total_payment_value"].sum() if "total_payment_value" in valid.columns else (
            valid["price"].sum() if "price" in valid.columns else 0)
        label = "Total encaissé" if st.session_state.lang == "FR" else "Total collected"
        metric_card(label, f"R$ {total_payment:,.0f}")
    
    col_left, col_right = st.columns([1, 1.3])
    
    with col_left:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_payment_type")}</div>', unsafe_allow_html=True)
            if has_type:
                counts = valid["payment_type"].value_counts()
                fig = go.Figure(go.Pie(
                    labels=counts.index, values=counts.values, hole=0.5,
                    marker=dict(colors=PIE_COLORS), textfont=dict(color=theme["text"]),
                    textinfo="percent+label",
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
            else:
                missing_data_card(t("no_payments"))
    
    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_installments_basket")}</div>', unsafe_allow_html=True)
            if installments_col and "price" in valid.columns:
                v = valid.dropna(subset=[installments_col])
                v = v[v[installments_col] > 0]
                if not v.empty:
                    by_installment = v.groupby(installments_col)["price"].mean().reset_index()
                    by_installment = by_installment[by_installment[installments_col] <= 18]
                    fig = go.Figure(go.Bar(
                        x=by_installment[installments_col], y=by_installment["price"],
                        marker_color=COLORS["accent2"],
                        text=[f"R$ {v:,.0f}" for v in by_installment["price"]],
                        textposition="outside"
                    ))
                    fig.update_xaxes(title="Nombre de versements" if st.session_state.lang == "FR" else "Number of installments")
                    fig.update_yaxes(title="Panier moyen (R$)" if st.session_state.lang == "FR" else "Avg basket (R$)")
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
                else:
                    missing_data_card(t("no_payments"))
            else:
                missing_data_card(t("no_payments"))


# ============================================================================
# SECTION: CLIENTS (RFM)
# ============================================================================
def display_customers_rfm(df, df_all, reference_date):
    st.markdown(f'<div class="section-header">{t("nav_customers")}</div>', unsafe_allow_html=True)
    
    if "price" not in df.columns:
        st.warning(t("no_customers"))
        return
    
    valid = df[df["price"] > 0]
    
    if "customer_unique_id" not in valid.columns or valid.empty:
        st.warning(t("no_customers"))
        return
    
    rfm = compute_rfm(valid, reference_date, st.session_state.lang)
    if rfm.empty:
        st.warning(t("no_customers"))
        return
    
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
                marker=dict(colors=PIE_COLORS),
                textfont=dict(color=theme["text"]),
                textinfo="percent+label",
            ))
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    with col_right:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_top_clients")}</div>', unsafe_allow_html=True)
            top_clients = rfm.nlargest(8, "monetary")
            labels = top_clients.index.astype(str).str.slice(0, 12)
            fig = go.Figure(go.Bar(
                x=labels,
                y=top_clients["monetary"],
                marker_color=COLORS["accent"],
                text=[f"R$ {v:,.0f}" for v in top_clients["monetary"]],
                textposition="outside"
            ))
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
    
    with st.container(border=True):
        st.markdown('<div class="card-title">R × F × M (échantillon)</div>', unsafe_allow_html=True)
        fig = px.scatter(
            rfm.reset_index(), x="frequency", y="monetary", color="segment",
            size="recency", size_max=18, opacity=0.6,
            color_discrete_sequence=PIE_COLORS,
        )
        fig.update_xaxes(title="Fréquence" if st.session_state.lang == "FR" else "Frequency")
        fig.update_yaxes(title="Monétaire (R$)" if st.session_state.lang == "FR" else "Monetary (R$)")
        st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})


def compute_rfm(valid, reference_date, lang):
    rfm = valid.groupby("customer_unique_id").agg(
        recency=("purchased_at", lambda x: (reference_date - x.max()).days if x.notna().any() else np.nan),
        frequency=("order_id", "nunique") if "order_id" in valid.columns else ("price", "count"),
        monetary=("price", "sum"),
    ).dropna()
    
    try:
        rfm["R_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
        rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
        rfm["M_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    except (ValueError, IndexError):
        rfm["R_score"] = pd.cut(rfm["recency"], bins=[-1, 30, 90, 180, 365, float("inf")], labels=[5, 4, 3, 2, 1]).astype(int)
        rfm["F_score"] = np.where(rfm["frequency"] > 1, 4, 2)
        rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), min(5, rfm["monetary"].nunique()),
                                  labels=False, duplicates="drop") + 1
    
    t_ = TRANSLATIONS[lang]
    
    def label_row(row):
        r, f = row["R_score"], row["F_score"]
        if r >= 4 and f >= 4:
            return t_["rfm_champions"]
        if r >= 3 and f >= 3:
            return t_["rfm_loyal"]
        if r >= 4 and f <= 2:
            return t_["rfm_new"]
        if r <= 2 and f >= 3:
            return t_["rfm_at_risk"]
        if r <= 2 and f <= 2:
            return t_["rfm_lost"]
        return t_["rfm_standard"]
    
    rfm["segment"] = rfm.apply(label_row, axis=1)
    return rfm


# ============================================================================
# SECTION: PROBLEMES & ACTIONS (filtré par domaine)
# ============================================================================
def detect_problems(df, reference_date, lang, domain=""):
    problems = []
    if df.empty:
        return problems
    
    valid = df.copy()
    
    # 1. Retards de livraison
    if "is_late" in valid.columns and valid["is_late"].notna().any():
        late_rate = valid["is_late"].mean() * 100
        sev = "high" if late_rate >= 15 else ("medium" if late_rate >= 8 else None)
        if sev:
            desc = f"{late_rate:.1f}% des commandes sont livrées en retard."
            action = "Renégocier les délais avec les transporteurs sur les zones les plus en retard."
            problems.append({"title": "Taux de retard de livraison élevé",
                              "severity": sev, "description": desc, "action": action})
    
    # 2. Satisfaction sous la moyenne
    if "avg_review_score" in valid.columns and valid["avg_review_score"].notna().any():
        avg_score = valid["avg_review_score"].mean()
        sev = "high" if avg_score < 3.5 else ("medium" if avg_score < 4.0 else None)
        if sev:
            desc = f"Note moyenne des avis : {avg_score:.2f}/5."
            action = "Investiguer les causes des mauvaises notes (qualité produit, description, emballage)."
            problems.append({"title": "Satisfaction client sous la moyenne",
                              "severity": sev, "description": desc, "action": action})
    
    # 3. Corrélation délai / note
    if "delivery_days" in valid.columns and "avg_review_score" in valid.columns:
        d = valid[["delivery_days", "avg_review_score"]].dropna()
        if len(d) >= 30:
            corr = d["delivery_days"].corr(d["avg_review_score"])
            if pd.notna(corr) and corr <= -0.2:
                desc = f"Corrélation délai/note : {corr:.2f} — plus la livraison est longue, plus la note baisse."
                action = "Prioriser la réduction des délais sur les commandes les plus à risque."
                problems.append({"title": "Les retards dégradent directement la satisfaction",
                                  "severity": "medium", "description": desc, "action": action})
    
    # 4. Fidélisation
    if "customer_unique_id" in valid.columns:
        freq = valid.groupby("customer_unique_id")["order_id"].nunique() if "order_id" in valid.columns else valid.groupby("customer_unique_id").size()
        repeat_rate = (freq > 1).mean() * 100
        if repeat_rate < 10:
            desc = f"Seulement {repeat_rate:.1f}% des clients ont commandé au moins une fois."
            action = "Mettre en place un programme de fidélité ou des relances email post-achat."
            problems.append({"title": "Faible fidélisation client",
                              "severity": "medium", "description": desc, "action": action})
    
    # 5. Concentration vendeurs
    if "seller_id" in valid.columns and "price" in valid.columns:
        rev_by_seller = valid.groupby("seller_id")["price"].sum().sort_values(ascending=False)
        total = rev_by_seller.sum()
        n_sellers = rev_by_seller.shape[0]
        if total > 0 and n_sellers > 0:
            top10_n = max(1, int(np.ceil(n_sellers * 0.1)))
            top10_share = rev_by_seller.iloc[:top10_n].sum() / total * 100
            if top10_share >= 60:
                desc = f"Les 10% de vendeurs les plus gros génèrent {top10_share:.1f}% du CA total."
                action = "Diversifier le portefeuille vendeurs pour réduire le risque de dépendance."
                problems.append({"title": "Forte concentration du CA sur peu de vendeurs",
                                  "severity": "low", "description": desc, "action": action})
    
    return problems


def display_problems(df, df_all, lang, reference_date, domain=""):
    st.markdown(f'<div class="section-header">{t("problems_title")}</div>', unsafe_allow_html=True)
    
    problems = detect_problems(df, reference_date, lang, domain)
    
    if not problems:
        st.info(t("problems_none"))
        return
    
    severity_order = {"high": 0, "medium": 1, "low": 2}
    problems.sort(key=lambda p: severity_order.get(p["severity"], 3))
    
    severity_label = {
        "high": t("severity_high"),
        "medium": t("severity_medium"),
        "low": t("severity_low"),
    }
    
    for p in problems:
        st.markdown(f"""
        <div class="problem-card problem-{p['severity']}">
            <div class="problem-badge problem-badge-{p['severity']}">{severity_label[p['severity']]}</div>
            <div class="problem-title">{p['title']}</div>
            <div class="problem-desc">{p['description']}</div>
            <div class="problem-action"><b>{t('problem_action_label')} :</b> {p['action']}</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# SECTION: SYNTHESE IA
# ============================================================================
def display_synthese(df, lang, domain=""):
    st.markdown(f'<div class="section-header">{t("synthese_title")}</div>', unsafe_allow_html=True)
    
    insights = generate_advanced_insights(df, lang, domain)
    
    col_avatar, col_content = st.columns([1, 4], gap="medium")
    
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
        sections = [
            ("synthese_what", insights["what"]),
            ("synthese_why", insights["why"]),
            ("synthese_attention", insights["attention"]),
            ("synthese_action", insights["action"]),
        ]
        
        for key, value in sections:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">{t(key)}</div>
                <div class="insight-body">{value}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# SECTION: CHAT
# ============================================================================
def display_chat(df, lang):
    st.markdown(f'<div class="section-header">{t("chat_title")}</div>', unsafe_allow_html=True)
    
    col_avatar, col_content = st.columns([1, 4], gap="medium")
    
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
        st.caption(t("chat_intro"))
        
        # Historique des messages
        for role, msg in st.session_state.chat_history[-10:]:
            if role == "user":
                who = "Vous" if st.session_state.lang == "FR" else "You"
                st.markdown(f"""
                <div class="chat-message chat-user">
                    <b style="color:{COLORS['accent']};">{who}</b><br>{msg}
                </div>
                """, unsafe_allow_html=True)
            else:
                who = "Assistant"
                st.markdown(f"""
                <div class="chat-message chat-assistant">
                    <b style="color:{COLORS['accent']};">{who}</b><br>{msg}
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
# FOOTER COMMUN
# ============================================================================
def display_common_sections(df, df_all, lang, reference_date, domain=""):
    """Affiche les sections communes en bas de chaque onglet."""
    st.markdown('<div class="section-end"></div>', unsafe_allow_html=True)
    
    # Problèmes & Actions
    display_problems(df, df_all, lang, reference_date, domain)
    
    # Synthèse IA
    display_synthese(df, lang, domain)
    
    # Chat
    display_chat(df, lang)


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
    
    reference_date = df_all["purchased_at"].max() if "purchased_at" in df_all.columns else pd.Timestamp.now()
    
    st.markdown(f'<div class="page-title">{t("app_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{t("app_subtitle")}</div>', unsafe_allow_html=True)
    
    lang = st.session_state.lang
    
    # Navigation principale
    if nav_selected == t('nav_sales'):
        display_sales_market(df, df_all)
        display_common_sections(df, df_all, lang, reference_date, "sales")
    
    elif nav_selected == t('nav_logistics'):
        display_logistics_satisfaction(df, df_all)
        display_common_sections(df, df_all, lang, reference_date, "logistics")
    
    elif nav_selected == t('nav_sellers'):
        display_sellers_payments(df, df_all)
        display_common_sections(df, df_all, lang, reference_date, "sellers")
    
    elif nav_selected == t('nav_customers'):
        display_customers_rfm(df, df_all, reference_date)
        display_common_sections(df, df_all, lang, reference_date, "customers")
    
    st.markdown(f"""
    <hr style="border-color:{theme['border']}; margin-top:32px;">
    <div style="text-align:center; color:{theme['muted']}; font-size:0.7rem; padding:12px 0;">
        Olist Analytics · Tableau de bord e-commerce · Données Olist
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
