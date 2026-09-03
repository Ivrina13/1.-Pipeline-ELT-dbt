"""
Olist Analytics — Tableau de bord professionnel.
Couvre : ventes & marche, logistique & satisfaction, vendeurs & paiements, clients (RFM).
Chaque onglet principal dispose de sous-onglets : Vue principale, Problemes & Actions, Synthese IA, Assistant IA.
FR/EN, theme sombre.
Lancer avec : streamlit run app.py
"""
import streamlit as st

from ui.i18n import t
from ui.theme import init_theme_state, get_theme, inject_css
from core.store import load_data, get_reference_date
from core.transform import apply_filters
from sections.ventes import display_sales_market
from sections.logistique import display_logistics_satisfaction
from sections.vendeurs import display_sellers_payments
from sections.clients import display_customers_rfm

# ============================================================================
# CONFIGURATION
# ============================================================================
st.set_page_config(page_title="Olist Analytics", layout="wide",
                   initial_sidebar_state="expanded")

init_theme_state()
inject_css()

theme = get_theme()

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
            if st.button("Francais", use_container_width=True):
                st.session_state.lang = "FR"
                st.rerun()
        with col_lang2:
            if st.button("English", use_container_width=True):
                st.session_state.lang = "EN"
                st.rerun()

        st.markdown("<hr class='brand-separator'>", unsafe_allow_html=True)

        st.markdown('<div class="nav-label">Navigation</div>', unsafe_allow_html=True)
        nav_options = [t('tab_sales'), t('tab_logistics'), t('tab_sellers'), t('tab_customers')]
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
# MAIN
# ============================================================================
def main():
    df_all = load_data()

    if df_all is None:
        st.error("Impossible de charger les donnees. Verifiez que le fichier 'data/fct_orders.parquet' existe.")
        st.stop()

    nav_selected, filters = sidebar(df_all)
    df = apply_filters(df_all, filters)

    reference_date = get_reference_date(df_all)
    lang = st.session_state.lang

    st.markdown(f'<div class="page-title">{t("app_title")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{t("app_subtitle")}</div>', unsafe_allow_html=True)

    # Navigation principale
    if nav_selected == t('tab_sales'):
        display_sales_market(df, df_all, lang, reference_date)
    elif nav_selected == t('tab_logistics'):
        display_logistics_satisfaction(df, df_all, lang, reference_date)
    elif nav_selected == t('tab_sellers'):
        display_sellers_payments(df, df_all, lang, reference_date)
    elif nav_selected == t('tab_customers'):
        display_customers_rfm(df, df_all, lang, reference_date)

    st.markdown(f"""
    <hr style="border-color:{theme['border']}; margin-top:32px;">
    <div style="text-align:center; color:{theme['muted']}; font-size:0.7rem; padding:12px 0;">
        Olist Analytics · Tableau de bord e-commerce · Donnees Olist
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
