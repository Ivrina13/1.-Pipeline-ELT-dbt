"""
Olist Analytics — Tableau de bord professionnel.
Couvre : vue d'ensemble, géospatial, logistique, satisfaction (+ mots-clés avis négatifs),
vendeurs/marketplace, paiements, clients (RFM business, sans ML), finance,
diagnostic problème/action, synthèse IA, assistant IA. FR/EN, thème sombre.

Toutes les sections au-delà de la table agrégée fct_orders.parquet (vendeurs, paiements,
texte des avis) sont conditionnelles : si les colonnes nécessaires n'existent pas, l'app
affiche un message explicite au lieu de planter.

Lancer avec : streamlit run app.py
"""
import base64
import os
import re
from collections import Counter

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
    "para", "pois", "porque", "sobre", "todo", "toda", "todos", "todas", "outro", "outra",
}

# ============================================================================
# COULEURS PROFESSIONNELLES
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
        "nav_overview": "Vue d'ensemble",
        "nav_geo": "Carte & Géo",
        "nav_logistics": "Logistique",
        "nav_satisfaction": "Satisfaction",
        "nav_sellers": "Vendeurs",
        "nav_payments": "Paiements",
        "nav_customers": "Clients",
        "nav_finance": "Finance",
        "nav_problems": "Problèmes & Actions",
        "nav_synthese": "Synthèse IA",
        "nav_chat": "Assistant IA",
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
        "chart_sales": "Évolution des ventes",
        "chart_status": "Répartition des statuts",
        "chart_categories": "Top catégories",
        "chart_states": "Top États",
        "chart_delivery_dist": "Distribution des délais",
        "chart_delivery_state": "Délai par État (top 12 en volume)",
        "chart_late_trend": "Évolution du taux de retard",
        "chart_score_dist": "Distribution des notes",
        "chart_score_category": "Note moyenne par catégorie",
        "chart_delivery_score": "Délai vs note",
        "chart_score_price": "Prix vs note",
        "chart_negative_keywords": "Mots-clés fréquents dans les avis négatifs",
        "chart_seller_revenue": "Top 10 vendeurs (CA)",
        "chart_seller_pareto": "Concentration du CA par vendeur (courbe de Pareto)",
        "chart_seller_score": "Distribution des notes vendeurs",
        "chart_seller_distance": "Délai selon origine (même État vs autre État)",
        "chart_payment_type": "Répartition des moyens de paiement",
        "chart_installments_basket": "Panier moyen par nombre de versements",
        "chart_segments": "Segments RFM",
        "chart_top_clients": "Top clients (par CA)",
        "chart_revenue_cum": "CA cumulé",
        "chart_revenue_category": "CA par catégorie",
        "geo_view_label": "Type de carte",
        "geo_view_choropleth": "Carte par État",
        "geo_view_points": "Carte de points",
        "geo_table_title": "Classement des États",
        "geo_fallback_note": "Carte indisponible (connexion réseau ou version Plotly) — repli en graphique à barres.",
        "geo_intro": "Répartition géographique des ventes et de la logistique sur le territoire brésilien.",
        "problems_intro": "Problèmes détectés automatiquement à partir des données filtrées, avec une action recommandée pour chacun.",
        "problems_none": "Aucun problème significatif détecté sur cette sélection au regard des seuils définis.",
        "problem_action_label": "Action recommandée",
        "severity_high": "Critique",
        "severity_medium": "À surveiller",
        "severity_low": "Point d'attention",
        "chat_placeholder": "Posez votre question sur les données...",
        "chat_intro": "Assistant IA pour analyser les données Olist",
        "synthese_intro": "Analyse générée automatiquement à partir des données",
        "stats_expander": "Statistiques détaillées",
        "no_geo": "Les données d'État client ne sont pas disponibles pour cette sélection.",
        "no_delivery": "Les données de livraison ne sont pas disponibles.",
        "no_reviews": "Les données d'avis ne sont pas disponibles.",
        "no_customers": "Les données clients ne sont pas disponibles pour cette sélection.",
        "no_finance": "Aucune donnée financière pour cette sélection.",
        "no_sellers": "La colonne 'seller_id' n'existe pas dans fct_orders.parquet. Pour activer cet onglet, il faut enrichir la table avec l'identifiant vendeur (et idéalement seller_state).",
        "no_payments": "Aucune colonne de paiement (payment_type, max_installments...) n'a été trouvée dans fct_orders.parquet.",
        "no_review_text": "Aucune colonne de texte d'avis (review_comment_message...) n'a été trouvée : l'analyse de mots-clés n'est pas disponible sur cette table agrégée.",
        "rfm_champions": "Champions",
        "rfm_loyal": "Clients fidèles",
        "rfm_new": "Nouveaux clients",
        "rfm_at_risk": "À risque",
        "rfm_lost": "Perdus",
        "rfm_standard": "Standard",
        "same_state": "Même État",
        "diff_state": "Autre État",
    },
    "EN": {
        "app_title": "Olist Analytics",
        "app_subtitle": "E-commerce Dashboard",
        "nav_overview": "Overview",
        "nav_geo": "Map & Geo",
        "nav_logistics": "Logistics",
        "nav_satisfaction": "Satisfaction",
        "nav_sellers": "Sellers",
        "nav_payments": "Payments",
        "nav_customers": "Customers",
        "nav_finance": "Finance",
        "nav_problems": "Problems & Actions",
        "nav_synthese": "AI Summary",
        "nav_chat": "AI Assistant",
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
        "chart_sales": "Sales evolution",
        "chart_status": "Status distribution",
        "chart_categories": "Top categories",
        "chart_states": "Top states",
        "chart_delivery_dist": "Delivery distribution",
        "chart_delivery_state": "Delivery by state (top 12 by volume)",
        "chart_late_trend": "Late rate trend",
        "chart_score_dist": "Rating distribution",
        "chart_score_category": "Avg rating by category",
        "chart_delivery_score": "Delivery vs rating",
        "chart_score_price": "Price vs rating",
        "chart_negative_keywords": "Frequent keywords in negative reviews",
        "chart_seller_revenue": "Top 10 sellers (revenue)",
        "chart_seller_pareto": "Revenue concentration by seller (Pareto curve)",
        "chart_seller_score": "Seller rating distribution",
        "chart_seller_distance": "Delivery time by origin (same state vs other state)",
        "chart_payment_type": "Payment method breakdown",
        "chart_installments_basket": "Avg basket by number of installments",
        "chart_segments": "RFM segments",
        "chart_top_clients": "Top clients",
        "chart_revenue_cum": "Cumulative revenue",
        "chart_revenue_category": "Revenue by category",
        "geo_view_label": "Map type",
        "geo_view_choropleth": "Choropleth map",
        "geo_view_points": "Point map",
        "geo_table_title": "State ranking",
        "geo_fallback_note": "Map unavailable (network or Plotly version) — falling back to bar chart.",
        "geo_intro": "Geographic distribution of sales and logistics across Brazil.",
        "problems_intro": "Problems automatically detected from the filtered data, each with a recommended action.",
        "problems_none": "No significant problem detected in this selection given the defined thresholds.",
        "problem_action_label": "Recommended action",
        "severity_high": "Critical",
        "severity_medium": "Watch closely",
        "severity_low": "Worth noting",
        "chat_placeholder": "Ask about the data...",
        "chat_intro": "AI assistant for Olist data analysis",
        "synthese_intro": "Automated analysis from data",
        "stats_expander": "Detailed statistics",
        "no_geo": "Customer state data is not available for this selection.",
        "no_delivery": "Delivery data is not available.",
        "no_reviews": "Review data is not available.",
        "no_customers": "Customer data is not available for this selection.",
        "no_finance": "No financial data for this selection.",
        "no_sellers": "The 'seller_id' column doesn't exist in fct_orders.parquet. To enable this tab, enrich the table with the seller identifier (ideally seller_state too).",
        "no_payments": "No payment column (payment_type, max_installments...) was found in fct_orders.parquet.",
        "no_review_text": "No review text column (review_comment_message...) was found: keyword analysis is not available on this aggregated table.",
        "rfm_champions": "Champions",
        "rfm_loyal": "Loyal customers",
        "rfm_new": "New customers",
        "rfm_at_risk": "At risk",
        "rfm_lost": "Lost",
        "rfm_standard": "Standard",
        "same_state": "Same state",
        "diff_state": "Other state",
    }
}

# ============================================================================
# IA / INSIGHTS
# ============================================================================
def generate_insights(df, lang):
    """Génère des insights à partir des données (ne mute jamais le df d'origine)."""
    insights = []
    t_ = TRANSLATIONS[lang]

    if df.empty:
        return {t_.get("no_data", "No data"): "Aucune donnée disponible pour générer des insights."}

    df = df.copy()

    if "price" in df.columns:
        total_rev = df["price"].sum()
        insights.append((
            f"CA total: {total_rev:,.0f} R$",
            f"Le chiffre d'affaires total s'élève à {total_rev:,.0f} R$."
        ))

        if "purchased_at" in df.columns:
            df["month"] = df["purchased_at"].dt.to_period("M")
            monthly = df.groupby("month")["price"].sum()
            if len(monthly) > 1:
                trend = "croissance" if monthly.iloc[-1] > monthly.iloc[-2] else "baisse"
                insights.append((
                    f"Tendance: {trend}",
                    f"Le CA mensuel est en {trend} par rapport au mois précédent."
                ))

    if "delivery_days" in df.columns:
        avg_delivery = df["delivery_days"].mean()
        insights.append((
            f"Délai moyen: {avg_delivery:.1f} jours",
            f"Le délai de livraison moyen est de {avg_delivery:.1f} jours."
        ))

    if "avg_review_score" in df.columns:
        avg_score = df["avg_review_score"].mean()
        insights.append((
            f"Note moyenne: {avg_score:.1f}/5",
            f"La note moyenne des avis est de {avg_score:.1f}/5."
        ))

    if "customer_unique_id" in df.columns:
        n_customers = df["customer_unique_id"].nunique()
        insights.append((
            f"Base clients: {n_customers:,}",
            f"La base de clients compte {n_customers:,} clients uniques."
        ))

    if "seller_id" in df.columns:
        n_sellers = df["seller_id"].nunique()
        insights.append((
            f"Vendeurs actifs: {n_sellers:,}",
            f"La marketplace compte {n_sellers:,} vendeurs actifs sur la période."
        ))

    if "payment_type" in df.columns:
        top_payment = df["payment_type"].value_counts()
        if not top_payment.empty:
            insights.append((
                f"Paiement dominant: {top_payment.index[0]}",
                f"Le moyen de paiement le plus utilisé est '{top_payment.index[0]}' ({top_payment.iloc[0]:,} commandes)."
            ))

    return {f"{i+1}. {title}": body for i, (title, body) in enumerate(insights[:8])}


def answer_question(q, df, lang):
    """Répond aux questions sur les données."""
    q_lower = q.lower()

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

    if any(w in q_lower for w in ["état", "etat", "state", "région", "region", "carte", "map"]):
        if "customer_state" in df.columns and "price" in df.columns:
            top = df.groupby("customer_state")["price"].sum().sort_values(ascending=False)
            if not top.empty:
                return f"L'État générant le plus de CA est {top.index[0]} avec {top.iloc[0]:,.0f} R$."
        return "Données géographiques non disponibles."

    if any(w in q_lower for w in ["vendeur", "seller", "marketplace"]):
        if "seller_id" in df.columns:
            n = df["seller_id"].nunique()
            return f"La marketplace compte {n:,} vendeurs actifs sur cette sélection."
        return "Données vendeurs non disponibles dans fct_orders.parquet (pas de colonne seller_id)."

    if any(w in q_lower for w in ["paiement", "payment", "carte bancaire", "boleto", "versement", "installment"]):
        if "payment_type" in df.columns:
            top = df["payment_type"].value_counts()
            return f"Le moyen de paiement le plus utilisé est '{top.index[0]}' ({top.iloc[0]:,} commandes)."
        return "Données de paiement non disponibles dans fct_orders.parquet."

    return ("Je peux vous renseigner sur : le chiffre d'affaires, les livraisons, les avis clients, "
            "la répartition géographique, les vendeurs, les paiements et les statistiques générales.")


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
    font-size: 1rem;
    font-weight: 600;
    color: {theme["text"]};
    margin: 12px 0 10px 0;
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
    line-height: 1.4;
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
.problem-medium {{ border-left-color: {COLORS["accent"]}; }}
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
.problem-badge-medium {{ background: rgba(201,168,76,0.15); color: {COLORS["accent"]}; }}
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

        # Colonne d'installments : on uniformise le nom si une variante existe
        if "max_installments" not in df.columns and "payment_installments" in df.columns:
            df["max_installments"] = df["payment_installments"]

        return df

    except Exception as e:
        st.error(f"Erreur: {e}")
        return None


@st.cache_data(show_spinner=False)
def load_brazil_geojson():
    """Charge le geojson des États brésiliens. Retourne None en cas d'échec réseau."""
    try:
        import requests
        resp = requests.get(BRAZIL_GEOJSON_URL, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _build_choropleth(data, geojson, color_col, color_scale, style, labels, hover_data):
    """Construit la carte choroplèthe en s'adaptant à la version de Plotly installée :
    Plotly >= 6 a renommé choropleth_mapbox en choropleth_map (map_style au lieu de mapbox_style)."""
    kwargs = dict(
        data_frame=data, geojson=geojson, locations="customer_state",
        featureidkey="properties.name", color=color_col,
        color_continuous_scale=color_scale, zoom=2.6,
        center={"lat": -14.2, "lon": -51.9}, opacity=0.85,
        labels=labels, hover_data=hover_data,
    )
    if hasattr(px, "choropleth_map"):
        kwargs["map_style"] = style
        return px.choropleth_map(**kwargs)
    kwargs["mapbox_style"] = style
    return px.choropleth_mapbox(**kwargs)


def _build_scatter_map(data, lat_c, lon_c, color_col, color_scale, style):
    """Construit la carte de points en s'adaptant à la version de Plotly installée."""
    kwargs = dict(
        data_frame=data, lat=lat_c, lon=lon_c, zoom=2.6,
        center={"lat": -14.2, "lon": -51.9}, opacity=0.55,
    )
    if color_col:
        kwargs["color"] = color_col
        kwargs["color_continuous_scale"] = color_scale
    if hasattr(px, "scatter_map"):
        kwargs["map_style"] = style
        return px.scatter_map(**kwargs)
    kwargs["mapbox_style"] = style
    return px.scatter_mapbox(**kwargs)


def find_latlon_cols(df):
    """Cherche des colonnes lat/lon parmi les noms usuels du dataset Olist."""
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


def style_fig(fig, height=280):
    fig.update_layout(
        template="plotly_dark" if st.session_state.theme == "dark" else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"], family="Inter, sans-serif"),
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
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
            t('nav_overview'), t('nav_geo'), t('nav_logistics'), t('nav_satisfaction'),
            t('nav_sellers'), t('nav_payments'), t('nav_customers'), t('nav_finance'),
            t('nav_problems'), t('nav_synthese'), t('nav_chat'),
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
# SECTION: OVERVIEW
# ============================================================================
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
    total_orders = valid["order_id"].nunique()
    unique_customers = valid["customer_unique_id"].nunique() if "customer_unique_id" in valid.columns else 0
    avg_basket = total_revenue / total_orders if total_orders > 0 else 0
    n_orders_all = valid_all["order_id"].nunique()
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
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

        if "product_category" in valid.columns and not valid.empty:
            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("chart_categories")}</div>', unsafe_allow_html=True)
                top_cats = valid.groupby("product_category")["price"].sum().sort_values(ascending=False).head(6)
                fig = go.Figure(go.Bar(
                    x=top_cats.values,
                    y=top_cats.index,
                    orientation="h",
                    marker_color=COLORS["accent"],
                    text=[f"R$ {v:,.0f}" for v in top_cats.values],
                    textposition="outside"
                ))
                st.plotly_chart(style_fig(fig, height=240), use_container_width=True, config={"displayModeBar": False})

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
# SECTION: GEO / CARTE
# ============================================================================
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
    agg_dict = {"orders": ("order_id", "nunique")}
    if has_revenue:
        agg_dict["revenue"] = ("price", "sum")
    if "is_late" in valid.columns:
        agg_dict["late_rate"] = ("is_late", "mean")
    if "avg_review_score" in valid.columns:
        agg_dict["avg_score"] = ("avg_review_score", "mean")

    state_agg = valid.groupby("customer_state").agg(**agg_dict).reset_index()
    if not has_revenue:
        state_agg["revenue"] = state_agg["orders"]

    state_agg_sorted = state_agg.sort_values("revenue", ascending=False)

    c1, c2, c3 = st.columns(3)
    with c1:
        top_row = state_agg_sorted.iloc[0]
        metric_card(t("kpi_top_state_revenue"),
                    f"{top_row['customer_state']}",
                    delta_text=f"R$ {top_row['revenue']:,.0f}" if has_revenue else f"{top_row['revenue']:,.0f} cmd.",
                    featured=True)
    with c2:
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
                    fig = _build_choropleth(
                        state_agg, geojson, "revenue",
                        [theme["surface"], COLORS["accent"]], mapbox_style,
                        labels={"revenue": "CA (R$)" if has_revenue else "Commandes"},
                        hover_data={"orders": True, "revenue": ":.0f"},
                    )
                    fig.update_layout(
                        margin=dict(l=0, r=0, t=0, b=0), height=460,
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color=theme["text"]),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                    map_rendered = True
                except Exception:
                    map_rendered = False
        else:
            lat_c, lon_c = latlon
            pts = valid.dropna(subset=[lat_c, lon_c])
            try:
                fig = _build_scatter_map(
                    pts, lat_c, lon_c,
                    "price" if has_revenue else None,
                    [theme["surface"], COLORS["accent"]], mapbox_style,
                )
                fig.update_traces(marker=dict(size=5))
                fig.update_layout(
                    margin=dict(l=0, r=0, t=0, b=0), height=460,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=theme["text"]),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                map_rendered = True
            except Exception:
                map_rendered = False

        if not map_rendered:
            fig = px.bar(state_agg_sorted, x="customer_state", y="revenue")
            fig.update_traces(marker_color=COLORS["accent"])
            st.plotly_chart(style_fig(fig, height=420), use_container_width=True, config={"displayModeBar": False})
            st.caption(t("geo_fallback_note"))

    with st.container(border=True):
        st.markdown(f'<div class="card-title">{t("geo_table_title")}</div>', unsafe_allow_html=True)
        display_cols = ["customer_state", "orders"]
        rename_map = {"customer_state": t("filter_state"), "orders": t("kpi_orders")}
        if has_revenue:
            display_cols.append("revenue")
            rename_map["revenue"] = t("kpi_revenue")
        if "late_rate" in state_agg.columns:
            display_cols.append("late_rate")
            rename_map["late_rate"] = t("kpi_late_rate")
        if "avg_score" in state_agg.columns:
            display_cols.append("avg_score")
            rename_map["avg_score"] = t("kpi_avg_score")

        table = state_agg_sorted[display_cols].head(15).rename(columns=rename_map).reset_index(drop=True)
        if t("kpi_revenue") in table.columns:
            table[t("kpi_revenue")] = table[t("kpi_revenue")].round(0)
        if t("kpi_late_rate") in table.columns:
            table[t("kpi_late_rate")] = (table[t("kpi_late_rate")] * 100).round(1)
        if t("kpi_avg_score") in table.columns:
            table[t("kpi_avg_score")] = table[t("kpi_avg_score")].round(2)
        st.dataframe(table, use_container_width=True, hide_index=True)


# ============================================================================
# SECTION: LOGISTICS
# ============================================================================
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
                    marker=dict(color=COLORS["accent2"], size=6)
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    if "customer_state" in valid.columns:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_delivery_state")}</div>', unsafe_allow_html=True)
            top_states = valid["customer_state"].value_counts().head(12).index
            v = valid[valid["customer_state"].isin(top_states)]
            fig = px.box(v, x="customer_state", y="delivery_days")
            fig.update_traces(marker_color=COLORS["accent2"])
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: SATISFACTION
# ============================================================================
def extract_negative_keywords(df, top_n=15):
    text_col = find_review_text_col(df)
    if text_col is None or "avg_review_score" not in df.columns:
        return None
    neg = df.loc[df["avg_review_score"] <= 2, text_col].dropna().astype(str)
    if neg.empty:
        return None
    words = []
    for txt in neg:
        tokens = re.findall(r"[a-zà-úA-ZÀ-Ú]+", txt.lower())
        words.extend(w for w in tokens if len(w) > 3 and w not in STOPWORDS_PT)
    if not words:
        return None
    return Counter(words).most_common(top_n)


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
                    "bgcolor": theme["card"],
                    "borderwidth": 0,
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

    if "price" in valid.columns:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t("chart_score_price")}</div>', unsafe_allow_html=True)
            d = valid[(valid["price"] > 0) & valid["price"].notna()]
            if not d.empty:
                fig = px.scatter(d, x="price", y="avg_review_score", opacity=0.35)
                fig.update_traces(marker_color=COLORS["accent2"], marker_size=5)
                st.plotly_chart(style_fig(fig, height=260), use_container_width=True, config={"displayModeBar": False})

    with st.container(border=True):
        st.markdown(f'<div class="card-title">{t("chart_negative_keywords")}</div>', unsafe_allow_html=True)
        keywords = extract_negative_keywords(valid)
        if keywords is None:
            missing_data_card(t("no_review_text"))
        else:
            words, counts = zip(*keywords)
            fig = go.Figure(go.Bar(
                x=list(counts), y=list(words), orientation="h",
                marker_color=COLORS["negative"],
            ))
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(style_fig(fig, height=380), use_container_width=True, config={"displayModeBar": False})
            st.caption("Analyse simple par fréquence de mots (hors mots vides portugais) — pas d'analyse de sentiment avancée."
                       if st.session_state.lang == "FR" else
                       "Simple word-frequency analysis (Portuguese stopwords removed) — not advanced sentiment analysis.")


# ============================================================================
# SECTION: VENDEURS / MARKETPLACE
# ============================================================================
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
    agg = {"orders": ("order_id", "nunique")}
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


# ============================================================================
# SECTION: PAIEMENTS
# ============================================================================
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
                    ))
                    fig.update_xaxes(title="Nombre de versements" if st.session_state.lang == "FR" else "Number of installments")
                    fig.update_yaxes(title="Panier moyen (R$)" if st.session_state.lang == "FR" else "Avg basket (R$)")
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})
                else:
                    missing_data_card(t("no_payments"))
            else:
                missing_data_card(t("no_payments"))


# ============================================================================
# SECTION: CUSTOMERS (RFM business, sans clustering ML)
# ============================================================================
def compute_rfm(valid, reference_date, lang):
    rfm = valid.groupby("customer_unique_id").agg(
        recency=("purchased_at", lambda x: (reference_date - x.max()).days if x.notna().any() else np.nan),
        frequency=("order_id", "nunique"),
        monetary=("price", "sum"),
    ).dropna()

    try:
        rfm["R_score"] = pd.qcut(rfm["recency"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
        rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
        rfm["M_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)
    except (ValueError, IndexError):
        # Pas assez de valeurs distinctes pour découper en quintiles : on retombe sur un score simplifié.
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


def display_customers(df, df_all, reference_date):
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
                textfont=dict(color=theme["text"])
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
        st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: FINANCE
# ============================================================================
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
    n_orders = valid["order_id"].nunique()
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
                    marker=dict(colors=PIE_COLORS),
                    textfont=dict(color=theme["text"])
                ))
                st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# SECTION: PROBLEMES & ACTIONS
# ============================================================================
def _L(lang, fr, en):
    return fr if lang == "FR" else en


def detect_problems(df, reference_date, lang):
    """Détecte des problèmes business à partir de seuils calculés sur les données filtrées.
    Chaque problème détecté est accompagné d'une action recommandée concrète."""
    problems = []
    if df.empty:
        return problems

    valid = df.copy()

    # 1. Retards de livraison
    if "is_late" in valid.columns and valid["is_late"].notna().any():
        late_rate = valid["is_late"].mean() * 100
        sev = "high" if late_rate >= 15 else ("medium" if late_rate >= 8 else None)
        if sev:
            desc = _L(lang, f"{late_rate:.1f}% des commandes sont livrées en retard.",
                      f"{late_rate:.1f}% of orders are delivered late.")
            if "customer_state" in valid.columns:
                by_state = valid.groupby("customer_state")["is_late"].mean().sort_values(ascending=False)
                if not by_state.empty and by_state.iloc[0] > 0:
                    desc += _L(lang,
                                f" L'État le plus touché est {by_state.index[0]} ({by_state.iloc[0]*100:.1f}%).",
                                f" The most affected state is {by_state.index[0]} ({by_state.iloc[0]*100:.1f}%).")
            action = _L(lang,
                        "Renégocier les délais avec les transporteurs sur les zones les plus en retard et afficher "
                        "des délais estimés plus réalistes au moment de l'achat.",
                        "Renegotiate carrier lead times for the most delayed zones and show more realistic "
                        "estimated delivery dates at checkout.")
            problems.append({"title": _L(lang, "Taux de retard de livraison élevé", "High delivery delay rate"),
                              "severity": sev, "description": desc, "action": action})

    # 2. Satisfaction sous la moyenne
    if "avg_review_score" in valid.columns and valid["avg_review_score"].notna().any():
        avg_score = valid["avg_review_score"].mean()
        sev = "high" if avg_score < 3.5 else ("medium" if avg_score < 4.0 else None)
        if sev:
            desc = _L(lang, f"Note moyenne des avis : {avg_score:.2f}/5.",
                      f"Average review score: {avg_score:.2f}/5.")
            if "product_category" in valid.columns:
                by_cat = valid.groupby("product_category")["avg_review_score"].mean().sort_values()
                if not by_cat.empty:
                    desc += _L(lang,
                                f" La catégorie la moins bien notée est '{by_cat.index[0]}' ({by_cat.iloc[0]:.2f}/5).",
                                f" The lowest-rated category is '{by_cat.index[0]}' ({by_cat.iloc[0]:.2f}/5).")
            action = _L(lang,
                        "Investiguer les causes des mauvaises notes sur cette catégorie (qualité produit, description "
                        "trompeuse, emballage) et relancer les vendeurs concernés.",
                        "Investigate the root causes of poor ratings in this category (product quality, misleading "
                        "description, packaging) and follow up with the sellers involved.")
            problems.append({"title": _L(lang, "Satisfaction client sous la moyenne", "Below-average customer satisfaction"),
                              "severity": sev, "description": desc, "action": action})

    # 3. Corrélation délai / note
    if "delivery_days" in valid.columns and "avg_review_score" in valid.columns:
        d = valid[["delivery_days", "avg_review_score"]].dropna()
        if len(d) >= 30:
            corr = d["delivery_days"].corr(d["avg_review_score"])
            if pd.notna(corr) and corr <= -0.2:
                desc = _L(lang,
                          f"Corrélation délai/note : {corr:.2f} — plus la livraison est longue, plus la note baisse.",
                          f"Delay/rating correlation: {corr:.2f} — the longer the delivery, the lower the rating.")
                action = _L(lang,
                            "Prioriser la réduction des délais sur les commandes les plus à risque (au-delà de la "
                            "médiane) pour limiter l'impact sur la satisfaction.",
                            "Prioritize reducing delivery time for at-risk orders (above the median) to limit the "
                            "impact on satisfaction.")
                problems.append({"title": _L(lang, "Les retards dégradent directement la satisfaction",
                                              "Delays directly hurt satisfaction"),
                                  "severity": "medium", "description": desc, "action": action})

    # 4. Fidélisation
    if "customer_unique_id" in valid.columns and "price" in valid.columns:
        base = valid[valid["price"] > 0]
        if not base.empty:
            freq = base.groupby("customer_unique_id")["order_id"].nunique()
            repeat_rate = (freq > 1).mean() * 100
            if repeat_rate < 10:
                desc = _L(lang, f"Seulement {repeat_rate:.1f}% des clients ont recommandé au moins une fois.",
                          f"Only {repeat_rate:.1f}% of customers have ordered more than once.")
                action = _L(lang,
                            "Mettre en place un programme de fidélité ou des relances email post-achat pour "
                            "augmenter le taux de réachat.",
                            "Set up a loyalty program or post-purchase email follow-ups to increase the repeat "
                            "purchase rate.")
                problems.append({"title": _L(lang, "Faible fidélisation client", "Low customer retention"),
                                  "severity": "medium", "description": desc, "action": action})

    # 5. Concentration géographique
    if "customer_state" in valid.columns and "price" in valid.columns:
        base = valid[valid["price"] > 0]
        rev_by_state = base.groupby("customer_state")["price"].sum().sort_values(ascending=False)
        total = rev_by_state.sum()
        if total > 0 and not rev_by_state.empty:
            top_share = rev_by_state.iloc[0] / total * 100
            if top_share >= 35:
                desc = _L(lang, f"{rev_by_state.index[0]} concentre {top_share:.1f}% du chiffre d'affaires total.",
                          f"{rev_by_state.index[0]} accounts for {top_share:.1f}% of total revenue.")
                action = _L(lang,
                            "Diversifier l'acquisition client dans d'autres États pour réduire le risque de "
                            "dépendance géographique.",
                            "Diversify customer acquisition across other states to reduce geographic dependency risk.")
                problems.append({"title": _L(lang, "Forte concentration géographique du CA",
                                              "High geographic revenue concentration"),
                                  "severity": "low", "description": desc, "action": action})

    # 6. Concentration vendeurs
    if "seller_id" in valid.columns and "price" in valid.columns:
        base = valid[valid["price"] > 0]
        rev_by_seller = base.groupby("seller_id")["price"].sum().sort_values(ascending=False)
        total = rev_by_seller.sum()
        n_sellers = rev_by_seller.shape[0]
        if total > 0 and n_sellers > 0:
            top10_n = max(1, int(np.ceil(n_sellers * 0.1)))
            top10_share = rev_by_seller.iloc[:top10_n].sum() / total * 100
            if top10_share >= 60:
                desc = _L(lang,
                          f"Les 10% de vendeurs les plus gros génèrent {top10_share:.1f}% du CA total.",
                          f"The top 10% of sellers generate {top10_share:.1f}% of total revenue.")
                action = _L(lang,
                            "Diversifier le portefeuille vendeurs pour réduire le risque de dépendance à quelques "
                            "gros comptes (perte de vendeur, rupture de stock).",
                            "Diversify the seller portfolio to reduce dependency risk on a few large accounts "
                            "(seller churn, stockouts).")
                problems.append({"title": _L(lang, "Forte concentration du CA sur peu de vendeurs",
                                              "High revenue concentration among few sellers"),
                                  "severity": "low", "description": desc, "action": action})

    # 7. Paiement en plusieurs fois et panier
    installments_col = "max_installments" if "max_installments" in valid.columns else (
        "payment_installments" if "payment_installments" in valid.columns else None)
    if installments_col and "price" in valid.columns:
        v = valid.dropna(subset=[installments_col])
        v = v[v[installments_col] > 0]
        if len(v) >= 30:
            high_installments_share = (v[installments_col] >= 10).mean() * 100
            if high_installments_share >= 15:
                desc = _L(lang,
                          f"{high_installments_share:.1f}% des commandes sont payées en 10 versements ou plus.",
                          f"{high_installments_share:.1f}% of orders are paid in 10+ installments.")
                action = _L(lang,
                            "Surveiller le risque d'impayés sur les paniers à fort nombre de versements et évaluer "
                            "l'intérêt d'un plafond ou de frais de financement adaptés.",
                            "Monitor default risk on baskets with many installments and evaluate a cap or adapted "
                            "financing fees.")
                problems.append({"title": _L(lang, "Forte proportion de paiements longs (10+ versements)",
                                              "High share of long installment plans (10+)"),
                                  "severity": "low", "description": desc, "action": action})

    return problems


def display_problems(df, df_all, lang, reference_date):
    st.markdown(f'<div class="section-header">{t("nav_problems")}</div>', unsafe_allow_html=True)
    st.caption(t("problems_intro"))

    problems = detect_problems(df, reference_date, lang)

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
        st.markdown("""
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

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        with st.expander(t("stats_expander")):
            if not df.empty:
                cols_to_show = [c for c in ["price", "delivery_days", "avg_review_score"] if c in df.columns]
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
            reset_label = "Réinitialiser" if lang == "FR" else "Reset"
            if st.button(reset_label, key="reset_chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        for role, msg in st.session_state.chat_history:
            if role == "user":
                who = "Vous" if lang == "FR" else "You"
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

    reference_date = df_all["purchased_at"].max() if "purchased_at" in df_all.columns else pd.Timestamp.now()

    st.markdown(f'<div class="page-title">{t("app_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{t("app_subtitle")}</div>', unsafe_allow_html=True)

    lang = st.session_state.lang

    nav_map = {
        t('nav_overview'): lambda d, da: display_overview(d, da),
        t('nav_geo'): lambda d, da: display_geo(d, da),
        t('nav_logistics'): lambda d, da: display_logistics(d, da),
        t('nav_satisfaction'): lambda d, da: display_satisfaction(d, da),
        t('nav_sellers'): lambda d, da: display_sellers(d, da),
        t('nav_payments'): lambda d, da: display_payments(d, da),
        t('nav_customers'): lambda d, da: display_customers(d, da, reference_date),
        t('nav_finance'): lambda d, da: display_finance(d, da),
        t('nav_problems'): lambda d, da: display_problems(d, da, lang, reference_date),
        t('nav_synthese'): lambda d, da: display_synthese(d, lang),
        t('nav_chat'): lambda d, da: display_chat(d, lang),
    }

    if nav_selected in nav_map:
        nav_map[nav_selected](df, df_all)

    st.markdown(f"""
    <hr style="border-color:{theme['border']}; margin-top:32px;">
    <div style="text-align:center; color:{theme['muted']}; font-size:0.7rem; padding:12px 0;">
        Olist Analytics · Tableau de bord e-commerce · Données Olist
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
