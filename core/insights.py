"""
Bloc 5 : Insights — synthese generee a partir des donnees.
Structure : ce qui s'est passe / pourquoi / attention / recommandations.
Detection automatique de problemes business avec action recommandee.
"""
import numpy as np
import pandas as pd

from utils.helpers import _L


def generate_insights(df: pd.DataFrame, lang: str, domain: str = "general") -> dict:
    """Genere des insights structures : ce qui s'est passe, pourquoi, attention, recommandations."""
    insights = {
        "ce_qui_sest_passe": [],
        "pourquoi": [],
        "attention": [],
        "recommandations": []
    }

    if df.empty:
        return {"ce_qui_sest_passe": ["Aucune donnee disponible."]}

    df = df.copy()
    valid = df[df["price"] > 0] if "price" in df.columns else df

    # --- CE QUI S'EST PASSE ---
    if "price" in valid.columns and not valid.empty:
        total_rev = valid["price"].sum()
        n_orders = valid["order_id"].nunique()
        insights["ce_qui_sest_passe"].append(
            f"CA total: {total_rev:,.0f} R$ sur {n_orders:,} commandes."
        )
        if "customer_unique_id" in valid.columns:
            n_customers = valid["customer_unique_id"].nunique()
            insights["ce_qui_sest_passe"].append(
                f"Base clients: {n_customers:,} clients uniques."
            )

        if "purchased_at" in valid.columns:
            monthly = valid.groupby(valid["purchased_at"].dt.to_period("M"))["price"].sum()
            if len(monthly) > 1:
                trend = "en hausse" if monthly.iloc[-1] > monthly.iloc[-2] else "en baisse"
                insights["ce_qui_sest_passe"].append(
                    f"Tendance mensuelle: CA {trend} par rapport au mois precedent."
                )

    if "delivery_days" in valid.columns:
        avg_delivery = valid["delivery_days"].mean()
        insights["ce_qui_sest_passe"].append(
            f"Delai de livraison moyen: {avg_delivery:.1f} jours."
        )
        if "is_late" in valid.columns:
            late_rate = valid["is_late"].mean() * 100
            insights["ce_qui_sest_passe"].append(
                f"Taux de retard: {late_rate:.1f}%."
            )

    if "avg_review_score" in valid.columns:
        avg_score = valid["avg_review_score"].mean()
        insights["ce_qui_sest_passe"].append(
            f"Note moyenne des avis: {avg_score:.1f}/5."
        )

    # --- POURQUOI (causes) ---
    if "is_late" in valid.columns and valid["is_late"].mean() > 0.1:
        if "customer_state" in valid.columns:
            by_state = valid.groupby("customer_state")["is_late"].mean().sort_values(ascending=False)
            if not by_state.empty and by_state.iloc[0] > 0:
                insights["pourquoi"].append(
                    f"Les retards sont concentres dans l'Etat {by_state.index[0]} ({by_state.iloc[0]*100:.1f}%)."
                )
        if "delivery_days" in valid.columns and "avg_review_score" in valid.columns:
            corr = valid[["delivery_days", "avg_review_score"]].dropna().corr().iloc[0, 1]
            if pd.notna(corr) and corr < -0.15:
                insights["pourquoi"].append(
                    f"Correlation delai/note: {corr:.2f}  les retards impactent directement la satisfaction."
                )

    if "avg_review_score" in valid.columns:
        if valid["avg_review_score"].mean() < 4.0 and "product_category" in valid.columns:
            by_cat = valid.groupby("product_category")["avg_review_score"].mean().sort_values()
            if not by_cat.empty and by_cat.iloc[0] < 3.5:
                insights["pourquoi"].append(
                    f"La categorie '{by_cat.index[0]}' a la note la plus basse ({by_cat.iloc[0]:.2f}/5)."
                )

    # --- ATTENTION (anomalies, risques, opportunites) ---
    if "seller_id" in valid.columns and "price" in valid.columns:
        rev_by_seller = valid.groupby("seller_id")["price"].sum().sort_values(ascending=False)
        total = rev_by_seller.sum()
        n_sellers = rev_by_seller.shape[0]
        if total > 0 and n_sellers > 0:
            top10_n = max(1, int(np.ceil(n_sellers * 0.1)))
            top10_share = rev_by_seller.iloc[:top10_n].sum() / total * 100
            if top10_share >= 60:
                insights["attention"].append(
                    f"Concentration elevee: les 10% de vendeurs generent {top10_share:.1f}% du CA."
                )

    if "customer_state" in valid.columns and "price" in valid.columns:
        rev_by_state = valid.groupby("customer_state")["price"].sum().sort_values(ascending=False)
        if not rev_by_state.empty and rev_by_state.iloc[0] / rev_by_state.sum() > 0.35:
            insights["attention"].append(
                f"Dependance geographique: {rev_by_state.index[0]} concentre plus de 35% du CA."
            )

    if "customer_unique_id" in valid.columns:
        freq = valid.groupby("customer_unique_id")["order_id"].nunique()
        repeat_rate = (freq > 1).mean() * 100
        if repeat_rate < 15:
            insights["attention"].append(
                f"Faible fidelisation: seulement {repeat_rate:.1f}% des clients reachetent."
            )

    # --- RECOMMANDATIONS ---
    if "is_late" in valid.columns and valid["is_late"].mean() > 0.1:
        insights["recommandations"].append(
            "Renegocier les delais avec les transporteurs sur les zones les plus en retard."
        )
    if "avg_review_score" in valid.columns and valid["avg_review_score"].mean() < 4.0:
        insights["recommandations"].append(
            "Auditer les produits des categories les moins bien notees avec les vendeurs concernes."
        )
    if "customer_unique_id" in valid.columns:
        repeat_rate = (valid.groupby("customer_unique_id")["order_id"].nunique() > 1).mean() * 100
        if repeat_rate < 15:
            insights["recommandations"].append(
                "Lancer un programme de fidelite ou des relances post-achat."
            )
    if "seller_id" in valid.columns and "price" in valid.columns:
        rev_by_seller = valid.groupby("seller_id")["price"].sum().sort_values(ascending=False)
        total = rev_by_seller.sum()
        n_sellers = rev_by_seller.shape[0]
        if total > 0 and n_sellers > 0:
            top10_n = max(1, int(np.ceil(n_sellers * 0.1)))
            top10_share = rev_by_seller.iloc[:top10_n].sum() / total * 100
            if top10_share >= 60:
                insights["recommandations"].append(
                    "Diversifier le portefeuille vendeurs pour reduire la dependance."
                )

    if not insights["ce_qui_sest_passe"]:
        insights["ce_qui_sest_passe"].append("Donnees insuffisantes pour l'analyse.")

    return insights


def detect_problems(df: pd.DataFrame, reference_date, lang: str) -> list:
    """Detecte des problemes business a partir de seuils calcules."""
    problems = []
    if df.empty:
        return problems

    valid = df.copy()

    # 1. Retards de livraison
    if "is_late" in valid.columns and valid["is_late"].notna().any():
        late_rate = valid["is_late"].mean() * 100
        sev = "high" if late_rate >= 15 else ("medium" if late_rate >= 8 else None)
        if sev:
            desc = _L(lang, f"{late_rate:.1f}% des commandes sont livrees en retard.",
                      f"{late_rate:.1f}% of orders are delivered late.")
            if "customer_state" in valid.columns:
                by_state = valid.groupby("customer_state")["is_late"].mean().sort_values(ascending=False)
                if not by_state.empty and by_state.iloc[0] > 0:
                    desc += _L(lang,
                               f" L'Etat le plus touche est {by_state.index[0]} ({by_state.iloc[0]*100:.1f}%).",
                               f" The most affected state is {by_state.index[0]} ({by_state.iloc[0]*100:.1f}%).")
            action = _L(lang,
                        "Renegocier les delais avec les transporteurs sur les zones les plus en retard.",
                        "Renegotiate carrier lead times for the most delayed zones.")
            problems.append({"title": _L(lang, "Taux de retard de livraison eleve", "High delivery delay rate"),
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
                               f" La categorie la moins bien notee est '{by_cat.index[0]}' ({by_cat.iloc[0]:.2f}/5).",
                               f" The lowest-rated category is '{by_cat.index[0]}' ({by_cat.iloc[0]:.2f}/5).")
            action = _L(lang,
                        "Auditer les produits des categories les moins bien notees avec les vendeurs.",
                        "Audit products in the lowest-rated categories with the sellers.")
            problems.append({"title": _L(lang, "Satisfaction client sous la moyenne", "Below-average satisfaction"),
                             "severity": sev, "description": desc, "action": action})

    # 3. Correlation delai / note
    if "delivery_days" in valid.columns and "avg_review_score" in valid.columns:
        d = valid[["delivery_days", "avg_review_score"]].dropna()
        if len(d) >= 30:
            corr = d["delivery_days"].corr(d["avg_review_score"])
            if pd.notna(corr) and corr <= -0.2:
                desc = _L(lang,
                          f"Correlation delai/note : {corr:.2f}  plus la livraison est longue, plus la note baisse.",
                          f"Delay/rating correlation: {corr:.2f}  the longer the delivery, the lower the rating.")
                action = _L(lang,
                            "Prioriser la reduction des delais sur les commandes les plus a risque.",
                            "Prioritize reducing delivery time for at-risk orders.")
                problems.append({"title": _L(lang, "Les retards degradent la satisfaction",
                                             "Delays hurt satisfaction"),
                                 "severity": "medium", "description": desc, "action": action})

    # 4. Fidelisation
    if "customer_unique_id" in valid.columns and "price" in valid.columns:
        base = valid[valid["price"] > 0]
        if not base.empty:
            freq = base.groupby("customer_unique_id")["order_id"].nunique()
            repeat_rate = (freq > 1).mean() * 100
            if repeat_rate < 10:
                desc = _L(lang, f"Seulement {repeat_rate:.1f}% des clients ont recommande au moins une fois.",
                          f"Only {repeat_rate:.1f}% of customers have ordered more than once.")
                action = _L(lang,
                            "Mettre en place un programme de fidelite ou des relances post-achat.",
                            "Set up a loyalty program or post-purchase follow-ups.")
                problems.append({"title": _L(lang, "Faible fidelisation client", "Low customer retention"),
                                 "severity": "medium", "description": desc, "action": action})

    return problems
