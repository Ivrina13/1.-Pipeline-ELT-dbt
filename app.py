import duckdb
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
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
# DESIGN TOKENS
# Palette : fond quasi-noir, cartes ardoise, accent indigo signature + teal
# secondaire pour les deltas positifs. Inspire des dashboards fintech sombres.
# ============================================================================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

THEMES = {
    "dark": {
        "bg_gradient": "radial-gradient(circle at 15% 0%, #14121f 0%, #0a0a0d 45%, #060608 100%)",
        "card_bg": "#131319",
        "card_bg_soft": "#111117",
        "card_border": "rgba(255,255,255,0.06)",
        "sidebar_bg": "#0d0d12",
        "text": "#f2f2f6",
        "muted": "#83839a",
        "accent": "#8B7CFA",
        "accent_soft": "rgba(139,124,250,0.12)",
        "accent2": "#3FD7C4",
        "featured_gradient": "linear-gradient(135deg, #7C6AF0 0%, #4C3FBF 100%)",
        "btn_bg": "rgba(255,255,255,0.06)",
        "btn_border": "rgba(255,255,255,0.14)",
        "btn_text": "#f2f2f6",
        "row_border": "rgba(255,255,255,0.05)",
        "chip_bg": "rgba(255,255,255,0.04)",
        "plotly_template": "plotly_dark",
        "grid": "rgba(255,255,255,0.05)",
        "nav_active_bg": "rgba(139,124,250,0.14)",
        "nav_active_text": "#c9c2fb",
    },
    "light": {
        "bg_gradient": "radial-gradient(circle at 15% 0%, #f1effc 0%, #f8f8fb 45%, #ffffff 100%)",
        "card_bg": "#ffffff",
        "card_bg_soft": "#fafafe",
        "card_border": "#e9e8f2",
        "sidebar_bg": "#ffffff",
        "text": "#14131f",
        "muted": "#6c6b80",
        "accent": "#6E5CE0",
        "accent_soft": "rgba(110,92,224,0.10)",
        "accent2": "#12A28F",
        "featured_gradient": "linear-gradient(135deg, #7C6AF0 0%, #4C3FBF 100%)",
        "btn_bg": "#6E5CE0",
        "btn_border": "#6E5CE0",
        "btn_text": "#ffffff",
        "row_border": "#f0f0f6",
        "chip_bg": "#f4f3fa",
        "plotly_template": "plotly_white",
        "grid": "#ecebf4",
        "nav_active_bg": "rgba(110,92,224,0.10)",
        "nav_active_text": "#4C3FBF",
    },
}
t = THEMES[st.session_state.theme]
PLOTLY_TEMPLATE = t["plotly_template"]
UP_COLOR = "#3FD98A" if st.session_state.theme == "dark" else "#0F9D63"
DOWN_COLOR = "#FF7A7A" if st.session_state.theme == "dark" else "#D6425E"

# ----------------------------------------------------------------------------
# CSS
# ----------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif; color: {t['text']} !important; }}

.stApp {{ background: {t['bg_gradient']}; color: {t['text']}; }}
.block-container {{ padding-top: 2.6rem; padding-bottom: 3rem; }}

.page-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: {t['text']};
    margin-bottom: 2px;
    line-height: 1.1;
    letter-spacing: -0.02em;
}}
.page-subtitle {{
    color: {t['muted']};
    font-size: 0.92rem;
    margin-bottom: 26px;
}}
.data-note {{
    color: {t['muted']};
    font-size: 0.75rem;
    font-style: italic;
    margin-top: -10px;
    margin-bottom: 18px;
}}

section[data-testid="stSidebar"] {{
    background: {t['sidebar_bg']};
    border-right: 1px solid {t['card_border']};
}}
section[data-testid="stSidebar"] * {{ color: {t['text']} !important; }}

.brand-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}}
.brand-mark {{
    width: 30px; height: 30px;
    border-radius: 9px;
    background: {t['featured_gradient']};
    flex-shrink: 0;
}}
.brand-name {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: -0.01em;
}}
.brand-sub {{
    color: {t['muted']};
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 18px;
}}

.card {{
    background: {t['card_bg']};
    border: 1px solid {t['card_border']};
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 16px;
}}
.card-featured {{
    background: {t['featured_gradient']};
    border: none;
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 16px;
}}
.card-title {{
    font-size: 0.72rem;
    color: {t['muted']};
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 8px;
    font-weight: 600;
}}
.card-featured .card-title {{ color: rgba(255,255,255,0.75); }}
.big-number {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.9rem;
    font-weight: 600;
    color: {t['text']};
    letter-spacing: -0.01em;
}}
.card-featured .big-number {{ color: #ffffff; }}
.delta-up {{ color: {UP_COLOR}; font-size: 0.8rem; font-weight: 500; margin-top: 6px; }}
.delta-down {{ color: {DOWN_COLOR}; font-size: 0.8rem; font-weight: 500; margin-top: 6px; }}
.card-featured .delta-up, .card-featured .delta-down {{ color: rgba(255,255,255,0.85); }}
.badge {{ color: {t['accent']}; font-size: 0.76rem; font-weight: 600; margin-top: 2px; }}

.ticker-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 11px 0; border-bottom: 1px solid {t['row_border']};
}}
.ticker-row:last-child {{ border-bottom: none; }}
.ticker-name {{ font-weight: 600; font-size: 0.88rem; color: {t['text']}; }}
.ticker-sub {{ font-size: 0.71rem; color: {t['muted']}; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {t['card_bg']};
    border: 1px solid {t['card_border']} !important;
    border-radius: 16px;
}}

div[data-testid="stMetric"] {{ background: transparent; }}

div.stButton > button {{
    background: {t['btn_bg']};
    color: {t['btn_text']};
    border: 1px solid {t['btn_border']};
    border-radius: 10px;
    font-weight: 500;
    font-size: 0.86rem;
    padding: 7px 18px;
}}

/* Navigation en pills verticales, sans emoji, avec accent actif */
.stRadio > div {{ flex-direction: column; gap: 2px; }}
.stRadio > div > label {{
    padding: 9px 12px !important;
    border-radius: 10px !important;
    margin-bottom: 1px;
}}
.stRadio > div > label:has(input:checked) {{
    background: {t['nav_active_bg']} !important;
}}
.stRadio > div > label:has(input:checked) p {{
    color: {t['nav_active_text']} !important;
    font-weight: 600 !important;
}}

hr {{ border-color: {t['card_border']}; }}
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# HELPERS D'AFFICHAGE
# ============================================================================
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


def list_card(title, rows):
    """rows: liste de tuples (nom, sous-texte, valeur, badge_texte)"""
    body = ""
    for name, sub, value, badge in rows:
        body += f"""
        <div class="ticker-row">
            <div><div class="ticker-name">{name}</div><div class="ticker-sub">{sub}</div></div>
            <div style="text-align:right"><div class="ticker-name">{value}</div><div class="badge">{badge}</div></div>
        </div>"""
    st.markdown(f"""<div class="card"><div class="card-title">{title}</div>{body}</div>""",
                unsafe_allow_html=True)


def card_title(text):
    st.markdown(f'<p class="card-title">{text}</p>', unsafe_allow_html=True)


def style_fig(fig, height=320):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=t["text"], family="Inter, sans-serif"),
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_xaxes(gridcolor=t["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=t["grid"], zeroline=False)
    return fig


def gauge_chart(value, max_value, suffix="", title_font_size=30):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': suffix, 'font': {'color': t["text"], 'size': title_font_size}},
        gauge={
            'axis': {'range': [0, max_value], 'tickcolor': t["muted"], 'tickfont': {'color': t["muted"]}},
            'bar': {'color': t["accent"]},
            'bgcolor': t["chip_bg"],
            'borderwidth': 0,
        }
    ))
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10),
                       paper_bgcolor="rgba(0,0,0,0)", font={'color': t["text"]})
    return fig


ACCENT_SEQ = [t["accent"], t["accent2"], "#B7ACFF", "#6FE3D4", "#5C4FD6", "#8FE0D6", "#A99BFF"]


# ============================================================================
# CHARGEMENT DES DONNEES
# ============================================================================
@st.cache_data
def load_data():
    """Charge fct_orders depuis le fichier Parquet versionne dans le repo
    (data/fct_orders.parquet), via une base DuckDB en memoire (aucune ecriture
    disque, donc compatible avec le mode lecture seule de Streamlit Cloud)."""
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        parquet_path = os.path.join(BASE_DIR, "data", "fct_orders.parquet")

        if not os.path.exists(parquet_path):
            st.error(f"Fichier introuvable : {parquet_path}")
            st.info("Verifie que 'data/fct_orders.parquet' est bien present et commite dans le repo GitHub.")
            return None

        conn = duckdb.connect(database=":memory:")
        conn.execute(f"""
            CREATE TABLE fct_orders AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)

        df = conn.execute("SELECT * FROM fct_orders").df()
        conn.close()

        if df.empty:
            st.warning("La table fct_orders est vide.")
            return None

        # Convertir les colonnes de date
        date_cols = ["purchased_at", "approved_at", "shipped_at", "delivered_at", "estimated_delivery_at"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Creer des colonnes derivees si necessaire
        if "estimated_delivery_at" in df.columns and "estimated_delivery" not in df.columns:
            df["estimated_delivery"] = df["estimated_delivery_at"]

        if "delivered_at" in df.columns and "purchased_at" in df.columns:
            if "delivery_days" not in df.columns:
                df["delivery_days"] = (df["delivered_at"] - df["purchased_at"]).dt.days
            if "is_late" not in df.columns and "estimated_delivery" in df.columns:
                df["is_late"] = df["delivered_at"] > df["estimated_delivery"]

        # Nettoyer les donnees
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
        st.error(f"Erreur lors du chargement des donnees: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None


# ============================================================================
# SIDEBAR - nav, filtres, switch de theme
# ============================================================================
def sidebar(df):
    with st.sidebar:
        st.markdown("""
        <div class="brand-row">
            <div class="brand-mark"></div>
            <div class="brand-name">Olist Analytics</div>
        </div>
        <div class="brand-sub">Business Intelligence</div>
        """, unsafe_allow_html=True)

        nav_selected = st.radio(
            "Navigation",
            ["Vue Globale", "Logistique", "Satisfaction", "Clients", "Finance"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        theme_label = "Mode clair" if st.session_state.theme == "dark" else "Mode sombre"
        if st.button(theme_label, use_container_width=True):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

        st.markdown("---")
        st.markdown("#### Filtres")

        filters = {}

        if "purchased_at" in df.columns and not df["purchased_at"].isna().all():
            min_date = df["purchased_at"].min().date()
            max_date = df["purchased_at"].max().date()
            filters["date_range"] = st.date_input("Periode", [min_date, max_date])

        if "customer_state" in df.columns:
            states = ["Tous"] + sorted(df["customer_state"].dropna().unique().tolist())
            filters["state"] = st.selectbox("Etat", states)

        if "status" in df.columns:
            statuses = sorted(df["status"].dropna().unique().tolist())
            filters["status"] = st.multiselect("Statut", statuses, default=statuses)

        if "product_category" in df.columns:
            categories = ["Toutes"] + sorted(df["product_category"].dropna().unique().tolist())
            filters["category"] = st.selectbox("Categorie", categories)

        if "avg_review_score" in df.columns:
            filters["min_score"] = st.slider("Note minimale", 1.0, 5.0, 1.0, 0.5)

        st.markdown("---")
        if st.button("Reinitialiser", use_container_width=True):
            st.rerun()

        st.markdown("---")
        st.caption(f"{len(df):,} lignes disponibles")

        return nav_selected, filters


def apply_filters(df, filters):
    """Applique les filtres selectionnes"""
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


# ============================================================================
# 1. VUE GLOBALE
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
        metric_card("CA total", f"R$ {total_revenue:,.0f}", featured=True)
    with c2:
        metric_card("Commandes", f"{total_orders:,}")
    with c3:
        metric_card("Clients uniques", f"{unique_customers:,}")
    with c4:
        metric_card("Panier moyen", f"R$ {avg_basket:,.2f}",
                    delta_text=f"R$ {abs(basket_delta):,.2f} vs moyenne globale",
                    delta_up=basket_delta >= 0)

    col_left, col_right = st.columns([1.7, 1])

    with col_left:
        with st.container(border=True):
            card_title("Evolution des ventes")
            if "purchased_at" in valid.columns and not valid.empty:
                daily_sales = valid.groupby("purchased_at")["price"].sum().reset_index()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_sales["purchased_at"], y=daily_sales["price"], mode="lines",
                    line=dict(color=t["accent"], width=3, shape="spline"),
                    fill="tozeroy", fillcolor=t["accent"] + "22",
                ))
                st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Pas de donnees pour cette selection.")

        if "product_category" in valid.columns and not valid.empty:
            top_cats = valid.groupby("product_category")["price"].sum().sort_values(ascending=False).head(5)
            total_cat_rev = valid["price"].sum()
            rows = [
                (cat[:22], "Categorie", f"R$ {val:,.0f}", f"{(val / total_cat_rev * 100):.1f}% du CA")
                for cat, val in top_cats.items()
            ]
            list_card("Top 5 categories", rows)

    with col_right:
        with st.container(border=True):
            card_title("Repartition des statuts")
            if "status" in valid.columns and not valid.empty:
                status_counts = valid["status"].value_counts()
                fig = go.Figure(go.Pie(labels=status_counts.index, values=status_counts.values,
                                        hole=0.6, marker=dict(colors=ACCENT_SEQ),
                                        textfont=dict(color=t["text"])))
                st.plotly_chart(style_fig(fig, height=260), use_container_width=True, config={"displayModeBar": False})

        if "customer_state" in valid.columns and not valid.empty:
            top_states = valid["customer_state"].value_counts().head(5)
            rows = [
                (state, "Etat", f"{n:,}", f"{(n / len(valid) * 100):.1f}% des lignes")
                for state, n in top_states.items()
            ]
            list_card("Top 5 Etats", rows)


# ============================================================================
# 2. LOGISTIQUE
# ============================================================================
def display_logistics(df, df_all):
    if "delivery_days" not in df.columns:
        st.warning("Les donnees de livraison ne sont pas disponibles.")
        return

    valid = df[df["delivery_days"].notna()]
    valid_all = df_all[df_all["delivery_days"].notna()]

    if valid.empty:
        st.warning("Aucune donnee de livraison valide pour cette selection.")
        return

    avg_delivery = valid["delivery_days"].mean()
    median_delivery = valid["delivery_days"].median()
    late_rate = valid["is_late"].mean() * 100 if "is_late" in valid.columns else 0
    late_rate_all = valid_all["is_late"].mean() * 100 if "is_late" in valid_all.columns and not valid_all.empty else late_rate
    late_delta = late_rate - late_rate_all

    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        metric_card("Delai moyen", f"{avg_delivery:.1f} j", featured=True)
    with c2:
        metric_card("Delai median", f"{median_delivery:.1f} j")
    with c3:
        metric_card("Taux de retard", f"{late_rate:.1f}%",
                    delta_text=f"{abs(late_delta):.1f} pts vs moyenne globale",
                    delta_up=late_delta >= 0)

    col_left, col_right = st.columns([1, 1.7])

    with col_left:
        with st.container(border=True):
            card_title("Taux de livraison a temps")
            on_time_rate = 100 - late_rate
            fig = gauge_chart(round(on_time_rate, 1), 100, suffix="%")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        with st.container(border=True):
            card_title("Distribution des delais de livraison")
            fig = px.histogram(valid, x="delivery_days", nbins=30)
            fig.update_traces(marker_color=t["accent"])
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    col_a, col_b = st.columns(2)
    with col_a:
        if "customer_state" in valid.columns:
            with st.container(border=True):
                card_title("Delai par Etat")
                fig = px.box(valid, x="customer_state", y="delivery_days")
                fig.update_traces(marker_color=t["accent2"])
                st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})

    with col_b:
        if "purchased_at" in valid.columns:
            with st.container(border=True):
                card_title("Evolution du taux de retard")
                v = valid.copy()
                v["month_year"] = v["purchased_at"].dt.to_period('M').astype(str)
                late_by_month = v.groupby("month_year")["is_late"].mean().reset_index()
                late_by_month["is_late"] = late_by_month["is_late"] * 100
                fig = go.Figure(go.Scatter(x=late_by_month["month_year"], y=late_by_month["is_late"],
                                            mode="lines", line=dict(color=t["accent2"], width=3)))
                st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# 3. SATISFACTION
# ============================================================================
def display_satisfaction(df, df_all):
    if "avg_review_score" not in df.columns:
        st.warning("Les donnees d'avis ne sont pas disponibles.")
        return

    valid = df[df["avg_review_score"].notna()]
    if valid.empty:
        st.warning("Aucune donnee d'avis valide pour cette selection.")
        return

    avg_score = valid["avg_review_score"].mean()
    good_rate = (valid["avg_review_score"] >= 4).mean() * 100
    bad_rate = (valid["avg_review_score"] <= 2).mean() * 100

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        metric_card("Bonnes notes (4-5)", f"{good_rate:.1f}%", featured=True)
    with c2:
        metric_card("Mauvaises notes (1-2)", f"{bad_rate:.1f}%")
    with c3:
        metric_card("Volume d'avis", f"{len(valid):,}")

    col_left, col_right = st.columns([1, 1.7])

    with col_left:
        with st.container(border=True):
            card_title("Note moyenne")
            fig = gauge_chart(round(avg_score, 2), 5)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_right:
        with st.container(border=True):
            card_title("Distribution des notes")
            v = valid.copy()
            v["review_score_rounded"] = v["avg_review_score"].round()
            fig = px.histogram(v, x="review_score_rounded", nbins=5)
            fig.update_traces(marker_color=t["accent"])
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    col_a, col_b = st.columns(2)
    with col_a:
        if "product_category" in valid.columns:
            with st.container(border=True):
                card_title("Note moyenne par categorie")
                score_by_cat = valid.groupby("product_category")["avg_review_score"].mean().sort_values(ascending=False).head(10)
                fig = px.bar(score_by_cat)
                fig.update_traces(marker_color=t["accent2"])
                st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})

    with col_b:
        if "delivery_days" in valid.columns:
            with st.container(border=True):
                card_title("Delai de livraison vs note")
                d = valid[valid["delivery_days"].notna()]
                if not d.empty:
                    fig = px.scatter(d, x="delivery_days", y="avg_review_score", opacity=0.5,
                                     color_discrete_sequence=[t["accent"]])
                    st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# 4. CLIENTS
# ============================================================================
def display_customers(df, df_all):
    valid = df[df["price"] > 0]

    if "customer_unique_id" not in valid.columns or valid.empty:
        st.warning("Les donnees clients ne sont pas disponibles pour cette selection.")
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
        metric_card("Taux de rechat", f"{repeat_rate:.1f}%", featured=True)
    with c2:
        metric_card("Inactifs (plus d'1 an)", f"{churn_rate:.1f}%")
    with c3:
        metric_card("Total clients", f"{len(rfm):,}")

    col_left, col_right = st.columns([1, 1.4])

    with col_left:
        with st.container(border=True):
            card_title("Segmentation clients")
            seg_counts = rfm["segment"].value_counts()
            fig = go.Figure(go.Pie(labels=seg_counts.index, values=seg_counts.values,
                                    hole=0.6, marker=dict(colors=ACCENT_SEQ)))
            st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

    with col_right:
        with st.container(border=True):
            card_title("Top 10 clients (par CA)")
            top_clients = rfm.nlargest(10, "monetary")
            rows = [
                (cust_id[:15], f"{int(row['frequency'])} commande(s)", f"R$ {row['monetary']:,.0f}", str(row["segment"]))
                for cust_id, row in top_clients.iterrows()
            ]
            list_card("", rows)


# ============================================================================
# 5. FINANCE
# ============================================================================
def display_finance(df, df_all):
    valid = df[df["price"] > 0]
    if valid.empty:
        st.warning("Aucune donnee financiere pour cette selection.")
        return

    total_revenue = valid["price"].sum()
    total_payment = valid["total_payment_value"].sum() if "total_payment_value" in valid.columns else total_revenue
    n_orders = valid["order_id"].nunique()
    avg_installments = valid["max_installments"].mean() if "max_installments" in valid.columns else None

    c1, c2, c3 = st.columns(3)
    with c1:
        metric_card("Chiffre d'affaires", f"R$ {total_revenue:,.0f}", featured=True)
    with c2:
        metric_card("Total encaisse", f"R$ {total_payment:,.0f}")
    with c3:
        if avg_installments is not None:
            metric_card("Versements moyens", f"{avg_installments:.1f}x")
        else:
            metric_card("Commandes", f"{n_orders:,}")

    col_left, col_right = st.columns([1.7, 1])

    with col_left:
        with st.container(border=True):
            card_title("CA cumule dans le temps")
            if "purchased_at" in valid.columns:
                monthly = valid.groupby("month_year")["price"].sum().reset_index().sort_values("month_year")
                monthly["cumulative"] = monthly["price"].cumsum()
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly["month_year"], y=monthly["cumulative"], mode="lines",
                    line=dict(color=t["accent"], width=3, shape="spline"),
                    fill="tozeroy", fillcolor=t["accent"] + "22",
                ))
                st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})

    with col_right:
        if "product_category" in valid.columns:
            with st.container(border=True):
                card_title("CA par categorie")
                cat_rev = valid.groupby("product_category")["price"].sum().sort_values(ascending=False).head(6)
                fig = go.Figure(go.Pie(labels=cat_rev.index, values=cat_rev.values,
                                        hole=0.6, marker=dict(colors=ACCENT_SEQ)))
                st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})


# ============================================================================
# MAIN
# ============================================================================
def main():
    df_all = load_data()

    if df_all is None:
        st.error("Impossible de charger les donnees.")
        st.stop()

    nav_selected, filters = sidebar(df_all)
    df = apply_filters(df_all, filters)

    st.markdown('<p class="page-title">Olist Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Dashboard e-commerce — donnees Olist</p>', unsafe_allow_html=True)

    if nav_selected == "Vue Globale":
        display_overview(df, df_all)
    elif nav_selected == "Logistique":
        display_logistics(df, df_all)
    elif nav_selected == "Satisfaction":
        display_satisfaction(df, df_all)
    elif nav_selected == "Clients":
        display_customers(df, df_all)
    elif nav_selected == "Finance":
        display_finance(df, df_all)


if __name__ == "__main__":
    main()
  
