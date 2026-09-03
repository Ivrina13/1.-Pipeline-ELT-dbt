"""
Section : Logistique & Satisfaction (delais, notes, mots-cles negatifs).
"""
import re
from collections import Counter

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from ui.i18n import t
from ui.theme import COLORS, get_theme
from utils.helpers import style_fig, metric_card, missing_data_card, display_subtabs, \
    display_insights_section, display_problems_section, display_chat_section, \
    find_review_text_col, STOPWORDS_PT
from core.insights import generate_insights, detect_problems


def display_logistics_satisfaction(df, df_all, lang, reference_date):
    theme = get_theme()
    tab_main, tab_problems, tab_synthese, tab_chat = display_subtabs()

    with tab_main:
        if "delivery_days" not in df.columns and "avg_review_score" not in df.columns:
            st.warning(t("no_delivery") + " " + t("no_reviews"))
            return

        has_delivery = "delivery_days" in df.columns
        has_reviews = "avg_review_score" in df.columns

        if has_delivery:
            valid_del = df[df["delivery_days"].notna()]
            avg_delivery = valid_del["delivery_days"].mean() if not valid_del.empty else 0
            median_delivery = valid_del["delivery_days"].median() if not valid_del.empty else 0
            late_rate = valid_del["is_late"].mean() * 100 if "is_late" in valid_del.columns else 0

            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card(t("kpi_avg_delivery"), f"{avg_delivery:.1f} j", featured=True)
            with c2:
                metric_card(t("kpi_median_delivery"), f"{median_delivery:.1f} j")
            with c3:
                metric_card(t("kpi_late_rate"), f"{late_rate:.1f}%")

        if has_reviews:
            valid_rev = df[df["avg_review_score"].notna()]
            if not valid_rev.empty:
                avg_score = valid_rev["avg_review_score"].mean()
                good_rate = (valid_rev["avg_review_score"] >= 4).mean() * 100
                bad_rate = (valid_rev["avg_review_score"] <= 2).mean() * 100
                c1, c2, c3 = st.columns(3)
                with c1:
                    metric_card(t("kpi_good_reviews"), f"{good_rate:.1f}%", featured=True)
                with c2:
                    metric_card(t("kpi_bad_reviews"), f"{bad_rate:.1f}%")
                with c3:
                    metric_card(t("kpi_review_count"), f"{len(valid_rev):,}")

        col_left, col_right = st.columns([1, 1.6])

        with col_left:
            if has_delivery and not valid_del.empty:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_delivery_dist")}</div>', unsafe_allow_html=True)
                    fig = px.histogram(valid_del, x="delivery_days", nbins=25)
                    fig.update_traces(marker_color=COLORS["accent"])
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

            if has_reviews and not valid_rev.empty:
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
            if has_delivery and "is_late" in valid_del.columns and "purchased_at" in valid_del.columns:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_late_trend")}</div>', unsafe_allow_html=True)
                    v = valid_del.copy()
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

            if has_reviews and not valid_rev.empty:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_score_dist")}</div>', unsafe_allow_html=True)
                    v = valid_rev.copy()
                    v["review_score_rounded"] = v["avg_review_score"].round()
                    fig = px.histogram(v, x="review_score_rounded", nbins=5)
                    fig.update_traces(marker_color=COLORS["accent"])
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

        col_a, col_b = st.columns(2)

        with col_a:
            if has_reviews and "product_category" in valid_rev.columns:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_score_category")}</div>', unsafe_allow_html=True)
                    score_by_cat = valid_rev.groupby("product_category")["avg_review_score"].mean().sort_values(ascending=False).head(8)
                    fig = px.bar(x=score_by_cat.values, y=score_by_cat.index, orientation="h")
                    fig.update_traces(marker_color=COLORS["accent2"])
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

            if "customer_state" in valid_del.columns and has_delivery and not valid_del.empty:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_delivery_state")}</div>', unsafe_allow_html=True)
                    top_states = valid_del["customer_state"].value_counts().head(12).index
                    v = valid_del[valid_del["customer_state"].isin(top_states)]
                    fig = px.box(v, x="customer_state", y="delivery_days")
                    fig.update_traces(marker_color=COLORS["accent2"])
                    st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

        with col_b:
            if has_reviews and has_delivery:
                with st.container(border=True):
                    st.markdown(f'<div class="card-title">{t("chart_delivery_score")}</div>', unsafe_allow_html=True)
                    d = df[df["delivery_days"].notna() & df["avg_review_score"].notna()]
                    if not d.empty:
                        fig = px.scatter(d, x="delivery_days", y="avg_review_score", opacity=0.4)
                        fig.update_traces(marker_color=COLORS["accent"], marker_size=5)
                        st.plotly_chart(style_fig(fig, height=280), use_container_width=True, config={"displayModeBar": False})

            with st.container(border=True):
                st.markdown(f'<div class="card-title">{t("chart_negative_keywords")}</div>', unsafe_allow_html=True)
                text_col = find_review_text_col(df)
                if text_col is None or "avg_review_score" not in df.columns:
                    missing_data_card(t("no_review_text"))
                else:
                    neg = df.loc[df["avg_review_score"] <= 2, text_col].dropna().astype(str)
                    if neg.empty:
                        st.info("Aucun avis negatif dans cette selection.")
                    else:
                        words = []
                        for txt in neg:
                            tokens = re.findall(r"[a-zà-úA-ZÀ-Ú]+", txt.lower())
                            words.extend(w for w in tokens if len(w) > 3 and w not in STOPWORDS_PT)
                        if not words:
                            st.info("Aucun mot significatif extrait.")
                        else:
                            counter = Counter(words).most_common(15)
                            words_list, counts = zip(*counter)
                            fig = go.Figure(go.Bar(
                                x=list(counts), y=list(words_list), orientation="h",
                                marker_color=COLORS["negative"],
                            ))
                            fig.update_yaxes(autorange="reversed")
                            st.plotly_chart(style_fig(fig, height=380), use_container_width=True,
                                            config={"displayModeBar": False})

    with tab_problems:
        problems = detect_problems(df, reference_date, lang)
        problems_filtered = [p for p in problems if any(k in p["title"].lower() for k in ["retard", "satisfaction", "delivery", "note"])]
        display_problems_section(problems_filtered, lang)

    with tab_synthese:
        insights = generate_insights(df, lang, domain="logistics")
        display_insights_section(insights, lang)
        with st.expander(t("stats_expander")):
            if not df.empty:
                cols_to_show = [c for c in ["delivery_days", "avg_review_score"] if c in df.columns]
                if cols_to_show:
                    stats = df[cols_to_show].describe().round(2)
                    st.dataframe(stats, use_container_width=True)

    with tab_chat:
        display_chat_section(df, lang)
