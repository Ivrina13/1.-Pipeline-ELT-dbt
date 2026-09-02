"""
Bloc 3 : Transform — calculs, filtres et agregations.
Filtrage des donnees selon la sidebar, et calcul du RFM clients.
"""
import numpy as np
import pandas as pd

from ui.i18n import TRANSLATIONS


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Applique les filtres de la sidebar (periode, etat, statut, categorie, note min)."""
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


def compute_rfm(valid: pd.DataFrame, reference_date, lang: str) -> pd.DataFrame:
    """Calcule les scores RFM (Recence, Frequence, Montant) et segmente les clients."""
    if valid.empty:
        return pd.DataFrame()

    rfm = valid.groupby("customer_unique_id").agg(
        recency=("purchased_at", lambda x: (reference_date - x.max()).days if x.notna().any() else np.nan),
        frequency=("order_id", "nunique"),
        monetary=("price", "sum"),
    ).dropna()

    if rfm.empty:
        return rfm

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
