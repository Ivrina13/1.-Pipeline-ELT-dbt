"""
Section : Clients (RFM).
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from ui.i18n import t
from ui.theme import COLORS, PIE_COLORS
from utils.helpers import style_fig, metric_card, display_subtabs, \
    display_insights_section, display_problems_section, display_chat_section
from core.insights import generate_insights, detect_problems
from core.transform import compute_rfm


def display_customers_rfm(df, df_all, lang, reference_date):
    tab_main, tab_problems, tab_synthese, tab_chat = display_subtabs()
    rfm = None

    with tab_main:
        if "price" not in df.columns:
            st.warning(t("no_customers"))
            return

        valid = df[df["price"] > 0]
        if "customer_unique_id" not in valid.columns or valid.empty:
            st.warning(t("no_customers"))
            return

        rfm = compute_rfm(valid, reference_date, lang)
        if rfm.empty:
            st.warning(t("no_customers"))
            return

        # KPIs
        repeat_rate = (rfm["frequency"] > 1).mean() * 100
        churn_rate = (rfm["recency"] > 365).mean() * 100

        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card(t("kpi_repeat_rate"), f"{repeat_rate:.1f}%", featured=True)
        with c2:
            metric_card(t("kpi_churn_rate"), f"{churn_rate:.1f}%")
        with c3:
            metric_card(t("kpi_total_customers"), f"{len(rfm):,}")

        # Graphiques
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
            st.markdown('<div class="card-title">R x F x M (echantillon)</div>', unsafe_allow_html=True)
            fig = px.scatter(
                rfm.reset_index(), x="frequency", y="monetary", color="segment",
                size="recency", size_max=18, opacity=0.6,
                color_discrete_sequence=PIE_COLORS,
            )
            st.plotly_chart(style_fig(fig, height=300), use_container_width=True, config={"displayModeBar": False})

    with tab_problems:
        problems = detect_problems(df, reference_date, lang)
        problems_filtered = [p for p in problems if any(k in p["title"].lower() for k in ["fidelisation", "client", "customer", "retention", "churn"])]
        display_problems_section(problems_filtered, lang)

    with tab_synthese:
        insights = generate_insights(df, lang, domain="customers")
        display_insights_section(insights, lang)
        with st.expander(t("stats_expander")):
            if rfm is not None and not rfm.empty:
                stats = rfm[["recency", "frequency", "monetary"]].describe().round(2)
                st.dataframe(stats, use_container_width=True)

    with tab_chat:
        display_chat_section(df, lang)
