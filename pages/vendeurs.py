"""
Section : Vendeurs & Paiements.
"""
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from ui.i18n import t
from ui.theme import COLORS, PIE_COLORS, get_theme
from utils.helpers import style_fig, metric_card, missing_data_card, display_subtabs, \
    display_insights_section, display_problems_section, display_chat_section
from core.insights import generate_insights, detect_problems


def display_sellers_payments(df, df_all, lang, reference_date):
    theme = get_theme()
    tab_main, tab_problems, tab_synthese, tab_chat = display_subtabs()

    with tab_main:
        has_seller = "seller_id" in df.columns
        has_payment = "payment_type" in df.columns or "max_installments" in df.columns

        if not has_seller and not has_payment:
            st.warning(t("no_sellers") + " " + t("no_payments"))
            return

        valid = df
        rev_by_seller = None
        total_rev = 0

        if has_seller:
            valid = df[df["price"] > 0] if "price" in df.columns else df
            valid = valid[valid["seller_id"].notna()]
            n_sellers = valid["seller_id"].nunique() if not valid.empty else 0

            if not valid.empty and "price" in valid.columns:
                rev_by_seller = valid.groupby("seller_id")["price"].sum().sort_values(ascending=False)
                total_rev = rev_by_seller.sum()
                top10_n = max(1, int(np.ceil(n_sellers * 0.1)))
                top10_share = rev_by_seller.iloc[:top10_n].sum() / total_rev * 100 if total_rev > 0 else 0
                top_seller = str(rev_by_seller.index[0]) if n_sellers > 0 else "—"

                c1, c2, c3 = st.columns(3)
                with c1:
                    metric_card(t("kpi_seller_count"), f"{n_sellers:,}", featured=True)
                with c2:
                    metric_card(t("kpi_top_seller"), top_seller[:14],
                                delta_text=f"R$ {rev_by_seller.iloc[0]:,.0f}" if n_sellers > 0 else "—")
                with c3:
                    metric_card(t("kpi_seller_concentration"), f"{top10_share:.1f}%")
            else:
                c1, c2, c3 = st.columns(3)
                with c1:
                    metric_card(t("kpi_seller_count"), f"{n_sellers:,}", featured=True)

        if has_payment:
            valid = df[df["price"] > 0] if "price" in df.columns else df
            if "payment_type" in valid.columns:
                payment_types = valid["payment_type"].nunique()
                c1, c2 = st.columns(2)
                with c1:
                    metric_card(t("kpi_payment_types"), f"{payment_types}", featured=True)
                with c2:
                    if "max_installments" in valid.columns:
                        avg_install = valid["max_installments"].mean()
                        metric_card(t("kpi_avg_installments"), f"{avg_install:.1f}x")
                    else:
                        metric_card(t("kpi_avg_installments"), "—")

        col_left, col_right = st.columns([1, 1])

        with col_left:
            if has_seller and rev_by_seller is not None and not valid.empty:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_seller_revenue")}</div>', unsafe_allow_html=True)
                    top10 = rev_by_seller.head(10).reset_index()
                    top10.columns = ["seller_id", "revenue"]
                    labels = top10["seller_id"].astype(str).str.slice(0, 10)
                    fig = go.Figure(go.Bar(
                        x=labels, y=top10["revenue"], marker_color=COLORS["accent"],
                    ))
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_seller_pareto")}</div>', unsafe_allow_html=True)
                    pareto = rev_by_seller.reset_index()
                    pareto.columns = ["seller_id", "revenue"]
                    pareto["cum_pct"] = pareto["revenue"].cumsum() / total_rev * 100
                    pareto["seller_rank_pct"] = (np.arange(1, len(pareto) + 1)) / len(pareto) * 100
                    fig = go.Figure(go.Scatter(
                        x=pareto["seller_rank_pct"], y=pareto["cum_pct"], mode="lines",
                        line=dict(color=COLORS["accent2"], width=2.5), fill="tozeroy",
                        fillcolor=COLORS["accent2"] + "22",
                    ))
                    fig.update_xaxes(title="% des vendeurs" if lang == "FR" else "% of sellers")
                    fig.update_yaxes(title="% du CA cumule" if lang == "FR" else "% cumulative revenue")
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

        with col_right:
            if has_payment:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_payment_type")}</div>', unsafe_allow_html=True)
                    if "payment_type" in valid.columns and not valid.empty:
                        counts = valid["payment_type"].value_counts()
                        fig = go.Figure(go.Pie(
                            labels=counts.index, values=counts.values, hole=0.5,
                            marker=dict(colors=PIE_COLORS), textfont=dict(color=theme["text"]),
                        ))
                        st.plotly_chart(style_fig(fig, height=280), use_container_width=True,
                                        config={"displayModeBar": False})
                    else:
                        missing_data_card(t("no_payments"))

                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_installments_basket")}</div>', unsafe_allow_html=True)
                    install_col = "max_installments" if "max_installments" in valid.columns else "payment_installments"
                    if install_col in valid.columns and "price" in valid.columns:
                        v = valid.dropna(subset=[install_col])
                        v = v[v[install_col] > 0]
                        if not v.empty:
                            by_installment = v.groupby(install_col)["price"].mean().reset_index()
                            by_installment = by_installment[by_installment[install_col] <= 18]
                            fig = go.Figure(go.Bar(
                                x=by_installment[install_col], y=by_installment["price"],
                                marker_color=COLORS["accent2"],
                            ))
                            fig.update_xaxes(title="Nombre de versements" if lang == "FR" else "Number of installments")
                            fig.update_yaxes(title="Panier moyen (R$)" if lang == "FR" else "Avg basket (R$)")
                            st.plotly_chart(style_fig(fig, height=280), use_container_width=True,
                                            config={"displayModeBar": False})
                        else:
                            missing_data_card(t("no_payments"))
                    else:
                        missing_data_card(t("no_payments"))

            if has_seller and "seller_state" in valid.columns and "customer_state" in valid.columns and "delivery_days" in valid.columns:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_seller_distance")}</div>', unsafe_allow_html=True)
                    v = valid.dropna(subset=["seller_state", "customer_state", "delivery_days"]).copy()
                    if not v.empty:
                        v["origin"] = np.where(v["seller_state"] == v["customer_state"], t("same_state"), t("diff_state"))
                        fig = px.box(v, x="origin", y="delivery_days", color="origin",
                                     color_discrete_sequence=[COLORS["positive"], COLORS["negative"]])
                        st.plotly_chart(style_fig(fig, height=260), use_container_width=True,
                                        config={"displayModeBar": False})

    with tab_problems:
        problems = detect_problems(df, reference_date, lang)
        problems_filtered = [p for p in problems if any(k in p["title"].lower() for k in ["vendeur", "seller", "paiement", "payment", "concentration", "versement"])]
        display_problems_section(problems_filtered, lang)

    with tab_synthese:
        insights = generate_insights(df, lang, domain="sellers")
        display_insights_section(insights, lang)
        with st.expander(t("stats_expander")):
            if not df.empty:
                cols_to_show = [c for c in ["price", "delivery_days"] if c in df.columns]
                if cols_to_show:
                    stats = df[cols_to_show].describe().round(2)
                    st.dataframe(stats, use_container_width=True)

    with tab_chat:
        display_chat_section(df, lang)
