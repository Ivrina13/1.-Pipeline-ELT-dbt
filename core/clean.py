"""
Bloc 2 : Clean — nettoyage des donnees brutes.
Parsing des dates, gestion des valeurs manquantes, normalisation des etats.
"""
import pandas as pd

from utils.geo import BR_STATES

DATE_COLS = ["purchased_at", "approved_at", "shipped_at", "delivered_at", "estimated_delivery_at"]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Applique le nettoyage complet sur le DataFrame brut et retourne un DataFrame pret a l'emploi."""
    df = df.copy()

    for col in DATE_COLS:
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
