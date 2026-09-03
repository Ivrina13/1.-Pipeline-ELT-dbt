"""
Section : Ventes & Marche (KPIs, evolution, categories, carte geographique).
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from ui.i18n import t
from ui.theme import COLORS, PIE_COLORS, get_theme
from utils.helpers import style_fig, metric_card, missing_data_card, display_subtabs, \
    display_insights_section, display_problems_section, display_chat_section
from utils.geo import load_brazil_geojson, build_choropleth
from core.insights import generate_insights, detect_problems


def display_sales_market(df, df_all, lang, reference_date):
    theme = get_theme()
    tab_main, tab_problems, tab_synthese, tab_chat = display_subtabs()

    with tab_main:
        if "price" not in df.columns:
            st.warning(t("no_finance"))
            return

        valid = df[df["price"] > 0]
        valid_all = df_all[df_all["price"] > 0]

        if valid.empty:
            st.warning(t("no_finance"))
            return

        # KPIs
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

        # Graphiques + Carte
        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            # Evolution des ventes
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

            # Top categories
            if "product_category" in valid.columns:
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

            # CA cumule
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
            # Statuts
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

            # Top Etats
            if "customer_state" in valid.columns:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_states")}</div>', unsafe_allow_html=True)
                    top_states = valid["customer_state"].value_counts().head(5)
                    fig = go.Figure(go.Bar(
                        x=top_states.index,
                        y=top_states.values,
                        marker_color=COLORS["accent2"]
                    ))
                    st.plotly_chart(style_fig(fig, height=200), use_container_width=True, config={"displayModeBar": False})

            # Carte geographique
            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("nav_geo")}</div>', unsafe_allow_html=True)
                if "customer_state" in valid.columns:
                    geo_df = valid.groupby("customer_state").agg(
                        orders=("order_id", "nunique"),
                        revenue=("price", "sum")
                    ).reset_index()
                    geo_df_sorted = geo_df.sort_values("revenue", ascending=False)

                    geojson = load_brazil_geojson()
                    mapbox_style = "carto-darkmatter" if st.session_state.theme == "dark" else "carto-positron"

                    if geojson is not None:
                        try:
                            fig = build_choropleth(
                                geo_df, geojson, "revenue",
                                [theme["surface"], COLORS["accent"]], mapbox_style,
                                labels={"revenue": "CA (R$)"},
                                hover_data={"orders": True, "revenue": ":.0f"},
                            )
                            fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=260,
                                              paper_bgcolor="rgba(0,0,0,0)",
                                              font=dict(color=theme["text"]))
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                        except Exception:
                            fig = px.bar(geo_df_sorted.head(10), x="customer_state", y="revenue")
                            fig.update_traces(marker_color=COLORS["accent"])
                            st.plotly_chart(style_fig(fig, height=240), use_container_width=True,
                                            config={"displayModeBar": False})
                    else:
                        fig = px.bar(geo_df_sorted.head(10), x="customer_state", y="revenue")
                        fig.update_traces(marker_color=COLORS["accent"])
                        st.plotly_chart(style_fig(fig, height=240), use_container_width=True,
                                        config={"displayModeBar": False})
                else:
                    missing_data_card(t("no_geo"))

    with tab_problems:
        problems = detect_problems(df, reference_date, lang)
        problems_filtered = [p for p in problems if any(k in p["title"].lower() for k in ["geographique", "concentration", "fidelisation", "retard"])]
        display_problems_section(problems_filtered, lang)

    with tab_synthese:
        insights = generate_insights(df, lang, domain="sales")
        display_insights_section(insights, lang)
        with st.expander(t("stats_expander")):
            if not df.empty:
                cols_to_show = [c for c in ["price", "delivery_days", "avg_review_score"] if c in df.columns]
                if cols_to_show:
                    stats = df[cols_to_show].describe().round(2)
                    st.dataframe(stats, use_container_width=True)

    with tab_chat:
        display_chat_section(df, lang)
