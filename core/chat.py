"""
Bloc 6 : Chat — assistant IA base sur des regles.
Repond aux questions sur les donnees par mots-cles.
(A terme, remplacable par un appel a une API type Sonar/LLM sans changer l'UI.)
"""
import pandas as pd


def answer_question(q: str, df: pd.DataFrame, lang: str) -> str:
    """Repond aux questions sur les donnees."""
    q_lower = q.lower()

    if any(w in q_lower for w in ["chiffre", "ca", "revenue", "vente", "sales"]):
        if "price" in df.columns:
            total = df["price"].sum()
            return f"Le chiffre d'affaires total est de {total:,.0f} R$."
        return "Donnees de CA non disponibles."

    if any(w in q_lower for w in ["livraison", "delivery", "retard", "late"]):
        if "delivery_days" in df.columns:
            avg = df["delivery_days"].mean()
            late = (df["is_late"].mean() * 100) if "is_late" in df.columns else 0
            return f"Delai moyen: {avg:.1f} jours. Taux de retard: {late:.1f}%."
        return "Donnees de livraison non disponibles."

    if any(w in q_lower for w in ["note", "avis", "review", "satisfaction"]):
        if "avg_review_score" in df.columns:
            avg = df["avg_review_score"].mean()
            return f"Note moyenne des avis: {avg:.1f}/5."
        return "Donnees d'avis non disponibles."

    if any(w in q_lower for w in ["client", "customer"]):
        if "customer_unique_id" in df.columns:
            n = df["customer_unique_id"].nunique()
            return f"La base clients compte {n:,} clients uniques."
        return "Donnees clients non disponibles."

    if any(w in q_lower for w in ["etat", "state", "region"]):
        if "customer_state" in df.columns and "price" in df.columns:
            top = df.groupby("customer_state")["price"].sum().sort_values(ascending=False)
            if not top.empty:
                return f"L'Etat generant le plus de CA est {top.index[0]} avec {top.iloc[0]:,.0f} R$."
        return "Donnees geographiques non disponibles."

    if any(w in q_lower for w in ["vendeur", "seller"]):
        if "seller_id" in df.columns:
            n = df["seller_id"].nunique()
            return f"La marketplace compte {n:,} vendeurs actifs."
        return "Donnees vendeurs non disponibles."

    if any(w in q_lower for w in ["paiement", "payment"]):
        if "payment_type" in df.columns:
            top = df["payment_type"].value_counts()
            return f"Le moyen de paiement le plus utilise est '{top.index[0]}' ({top.iloc[0]:,} commandes)."
        return "Donnees de paiement non disponibles."

    return ("Je peux vous renseigner sur: CA, livraisons, avis clients, geographie, vendeurs, paiements "
            "et statistiques generales.")
