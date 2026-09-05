"""
Bloc 5 : Insights — synthese generee a partir des donnees.
Structure : ce qui s'est passe / pourquoi / attention / recommandations.
Chaque domaine (sales, logistics, sellers, customers) a sa propre logique
de calcul, pour que la synthese soit specifique a l'onglet consulte.
Detection automatique de problemes business avec action recommandee.
"""
import numpy as np
import pandas as pd

from utils.helpers import _L


def _ca_trend_contributor(valid: pd.DataFrame) -> tuple:
    """
    Calcule la tendance mensuelle du CA et identifie la categorie (ou a
    defaut l'Etat) qui contribue le plus a la variation du dernier mois.
    Retourne (monthly, texte_pourquoi_ou_None).
    """
    if "purchased_at" not in valid.columns or "price" not in valid.columns:
        return None, None

    monthly = valid.groupby(valid["purchased_at"].dt.to_period("M"))["price"].sum()
    if len(monthly) <= 1:
        return monthly, None

    last_period, prev_period = monthly.index[-1], monthly.index[-2]
    diff = monthly.iloc[-1] - monthly.iloc[-2]
    base = monthly.iloc[-2]
    if not base or abs(diff) / base <= 0.03:  # variation non significative
        return monthly, None

    group_col = "product_category" if "product_category" in valid.columns else (
        "customer_state" if "customer_state" in valid.columns else None)
    if not group_col:
        return monthly, None

    periods = valid["purchased_at"].dt.to_period("M")
    last_by_group = valid[periods == last_period].groupby(group_col)["price"].sum()
    prev_by_group = valid[periods == prev_period].groupby(group_col)["price"].sum()
    delta_by_group = last_by_group.subtract(prev_by_group, fill_value=0).sort_values()
    if delta_by_group.empty:
        return monthly, None

    if diff < 0:
        contributor, contributor_delta = delta_by_group.index[0], delta_by_group.iloc[0]
        text = (f"La baisse du CA s'explique en grande partie par '{contributor}' "
                f"({contributor_delta:,.0f} R$ de variation sur le mois).")
    else:
        contributor, contributor_delta = delta_by_group.index[-1], delta_by_group.iloc[-1]
        text = (f"La hausse du CA est en grande partie tiree par '{contributor}' "
                f"(+{contributor_delta:,.0f} R$ sur le mois).")
    return monthly, text


def _insights_sales(valid: pd.DataFrame, insights: dict) -> None:
    if "price" not in valid.columns or valid.empty:
        return

    total_rev = valid["price"].sum()
    n_orders = valid["order_id"].nunique() if "order_id" in valid.columns else len(valid)
    insights["ce_qui_sest_passe"].append(f"CA total: {total_rev:,.0f} R$ sur {n_orders:,} commandes.")

    if n_orders > 0:
        avg_basket = total_rev / n_orders
        insights["ce_qui_sest_passe"].append(f"Panier moyen: {avg_basket:,.0f} R$.")

    if "customer_unique_id" in valid.columns:
        n_customers = valid["customer_unique_id"].nunique()
        insights["ce_qui_sest_passe"].append(f"Base clients: {n_customers:,} clients uniques.")

    monthly, why_text = _ca_trend_contributor(valid)
    if monthly is not None and len(monthly) > 1:
        trend = "en hausse" if monthly.iloc[-1] > monthly.iloc[-2] else "en baisse"
        insights["ce_qui_sest_passe"].append(f"Tendance mensuelle: CA {trend} par rapport au mois precedent.")
    if why_text:
        insights["pourquoi"].append(why_text)

    if "product_category" in valid.columns:
        rev_by_cat = valid.groupby("product_category")["price"].sum().sort_values(ascending=False)
        if not rev_by_cat.empty and rev_by_cat.iloc[0] / rev_by_cat.sum() > 0.4:
            insights["attention"].append(
                f"Dependance produit: '{rev_by_cat.index[0]}' concentre plus de 40% du CA."
            )
            insights["recommandations"].append(
                "Diversifier le catalogue pour reduire la dependance a une seule categorie."
            )

    if "customer_state" in valid.columns:
        rev_by_state = valid.groupby("customer_state")["price"].sum().sort_values(ascending=False)
        if not rev_by_state.empty and rev_by_state.iloc[0] / rev_by_state.sum() > 0.35:
            insights["attention"].append(
                f"Dependance geographique: {rev_by_state.index[0]} concentre plus de 35% du CA."
            )
            insights["recommandations"].append(
                "Investir dans l'acquisition sur d'autres Etats pour reduire la dependance geographique."
            )

    if monthly is not None and len(monthly) > 1 and monthly.iloc[-1] < monthly.iloc[-2]:
        insights["recommandations"].append(
            "Lancer une action commerciale ciblee (promotion, relance) sur le segment en baisse identifie ci-dessus."
        )


def _insights_logistics(valid: pd.DataFrame, insights: dict) -> None:
    if "delivery_days" in valid.columns:
        avg_delivery = valid["delivery_days"].mean()
        insights["ce_qui_sest_passe"].append(f"Delai de livraison moyen: {avg_delivery:.1f} jours.")

    late_rate = None
    if "is_late" in valid.columns:
        late_rate = valid["is_late"].mean() * 100
        insights["ce_qui_sest_passe"].append(f"Taux de retard: {late_rate:.1f}%.")

    if "avg_review_score" in valid.columns:
        avg_score = valid["avg_review_score"].mean()
        insights["ce_qui_sest_passe"].append(f"Note moyenne des avis: {avg_score:.1f}/5.")

    if late_rate is not None and late_rate > 8 and "customer_state" in valid.columns:
        by_state = valid.groupby("customer_state")["is_late"].mean().sort_values(ascending=False)
        if not by_state.empty and by_state.iloc[0] > 0:
            insights["pourquoi"].append(
                f"Les retards sont concentres dans l'Etat {by_state.index[0]} ({by_state.iloc[0]*100:.1f}%)."
            )
            insights["attention"].append(
                f"{by_state.index[0]} depasse largement la moyenne nationale de retard."
            )

    if "delivery_days" in valid.columns and "avg_review_score" in valid.columns:
        d = valid[["delivery_days", "avg_review_score"]].dropna()
        if len(d) >= 30:
            corr = d["delivery_days"].corr(d["avg_review_score"])
            if pd.notna(corr) and corr < -0.15:
                insights["pourquoi"].append(
                    f"Correlation delai/note: {corr:.2f}  les retards impactent directement la satisfaction."
                )

    if "seller_state" in valid.columns and "customer_state" in valid.columns and "delivery_days" in valid.columns:
        v = valid.dropna(subset=["seller_state", "customer_state", "delivery_days"])
        if not v.empty:
            same_state = v[v["seller_state"] == v["customer_state"]]["delivery_days"].mean()
            diff_state = v[v["seller_state"] != v["customer_state"]]["delivery_days"].mean()
            if pd.notna(same_state) and pd.notna(diff_state) and diff_state > same_state * 1.2:
                insights["attention"].append(
                    f"Les livraisons inter-Etats prennent {diff_state:.1f} jours en moyenne "
                    f"contre {same_state:.1f} jours en intra-Etat."
                )

    if late_rate is not None and late_rate > 8:
        insights["recommandations"].append(
            "Renegocier les delais avec les transporteurs sur les zones les plus en retard."
        )
    if "avg_review_score" in valid.columns and valid["avg_review_score"].mean() < 4.0:
        insights["recommandations"].append(
            "Prioriser la reduction des delais sur les commandes les plus a risque de retard."
        )


def _insights_sellers(valid: pd.DataFrame, insights: dict) -> None:
    if "seller_id" not in valid.columns or "price" not in valid.columns:
        return

    rev_by_seller = valid.groupby("seller_id")["price"].sum().sort_values(ascending=False)
    total = rev_by_seller.sum()
    n_sellers = rev_by_seller.shape[0]
    if total == 0 or n_sellers == 0:
        return

    insights["ce_qui_sest_passe"].append(f"Marketplace: {n_sellers:,} vendeurs actifs.")
    insights["ce_qui_sest_passe"].append(
        f"Vendeur en tete: {str(rev_by_seller.index[0])[:14]} ({rev_by_seller.iloc[0]:,.0f} R$)."
    )

    top10_n = max(1, int(np.ceil(n_sellers * 0.1)))
    top10_share = rev_by_seller.iloc[:top10_n].sum() / total * 100
    insights["ce_qui_sest_passe"].append(f"Les 10% de vendeurs generent {top10_share:.1f}% du CA.")

    if top10_share >= 60:
        insights["attention"].append(
            f"Concentration elevee: les 10% de vendeurs generent {top10_share:.1f}% du CA."
        )
        insights["recommandations"].append(
            "Diversifier le portefeuille vendeurs pour reduire la dependance aux plus gros comptes."
        )

    if "seller_state" in valid.columns:
        by_state = valid.groupby("seller_state")["price"].sum().sort_values(ascending=False)
        if not by_state.empty and by_state.iloc[0] / by_state.sum() > 0.4:
            insights["pourquoi"].append(
                f"La concentration du CA vendeurs s'explique en partie par une forte presence "
                f"de vendeurs dans l'Etat {by_state.index[0]} ({by_state.iloc[0]/by_state.sum()*100:.1f}% du CA)."
            )

    if "delivery_days" in valid.columns:
        top_sellers_ids = rev_by_seller.head(top10_n).index
        top_delay = valid[valid["seller_id"].isin(top_sellers_ids)]["delivery_days"].mean()
        other_delay = valid[~valid["seller_id"].isin(top_sellers_ids)]["delivery_days"].mean()
        if pd.notna(top_delay) and pd.notna(other_delay) and top_delay > other_delay * 1.15:
            insights["pourquoi"].append(
                f"Les vendeurs les plus performants ont aussi des delais plus longs "
                f"({top_delay:.1f}j vs {other_delay:.1f}j pour les autres) — probable effet volume."
            )


def _insights_customers(valid: pd.DataFrame, insights: dict) -> None:
    if "customer_unique_id" not in valid.columns or "order_id" not in valid.columns:
        return

    n_customers = valid["customer_unique_id"].nunique()
    insights["ce_qui_sest_passe"].append(f"Base clients: {n_customers:,} clients uniques.")

    freq = valid.groupby("customer_unique_id")["order_id"].nunique()
    repeat_rate = (freq > 1).mean() * 100
    insights["ce_qui_sest_passe"].append(f"Taux de reachat: {repeat_rate:.1f}% des clients ont commande plus d'une fois.")

    if "price" in valid.columns:
        rev_by_customer = valid.groupby("customer_unique_id")["price"].sum().sort_values(ascending=False)
        total = rev_by_customer.sum()
        top10_n = max(1, int(np.ceil(len(rev_by_customer) * 0.1)))
        top10_share = rev_by_customer.iloc[:top10_n].sum() / total * 100 if total > 0 else 0
        insights["ce_qui_sest_passe"].append(f"Les 10% de clients les plus actifs generent {top10_share:.1f}% du CA.")
        if top10_share >= 50:
            insights["attention"].append(
                f"Forte dependance a une minorite de clients: le top 10% genere {top10_share:.1f}% du CA."
            )

    if repeat_rate < 15:
        insights["attention"].append(f"Faible fidelisation: seulement {repeat_rate:.1f}% des clients reachetent.")
        insights["recommandations"].append("Lancer un programme de fidelite ou des relances post-achat.")

    # Chercher une cause possible au faible reachat
    repeat_customers = freq[freq > 1].index
    if "is_late" in valid.columns and repeat_rate < 15:
        late_repeat = valid[valid["customer_unique_id"].isin(repeat_customers)]["is_late"].mean()
        late_one_time = valid[~valid["customer_unique_id"].isin(repeat_customers)]["is_late"].mean()
        if pd.notna(late_repeat) and pd.notna(late_one_time) and late_one_time > late_repeat * 1.2:
            insights["pourquoi"].append(
                f"Les clients qui ne reachetent pas ont connu davantage de retards "
                f"({late_one_time*100:.1f}% vs {late_repeat*100:.1f}% pour les clients fideles)."
            )
    if "avg_review_score" in valid.columns and repeat_rate < 15:
        score_repeat = valid[valid["customer_unique_id"].isin(repeat_customers)]["avg_review_score"].mean()
        score_one_time = valid[~valid["customer_unique_id"].isin(repeat_customers)]["avg_review_score"].mean()
        if pd.notna(score_repeat) and pd.notna(score_one_time) and score_one_time < score_repeat - 0.2:
            insights["pourquoi"].append(
                f"Les clients non-recurrents ont donne des notes plus basses en moyenne "
                f"({score_one_time:.1f}/5 vs {score_repeat:.1f}/5 pour les clients fideles)."
            )


def generate_insights(df: pd.DataFrame, lang: str, domain: str = "general") -> dict:
    """Genere des insights structures et specifiques au domaine consulte."""
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

    domain_fn = {
        "sales": _insights_sales,
        "logistics": _insights_logistics,
        "sellers": _insights_sellers,
        "customers": _insights_customers,
    }.get(domain)

    if domain_fn:
        domain_fn(valid, insights)
    else:
        # Domaine inconnu: fallback generique (comportement historique)
        _insights_sales(valid, insights)
        _insights_logistics(valid, insights)

    if not insights["pourquoi"] and insights["ce_qui_sest_passe"]:
        insights["pourquoi"].append(
            "Aucune cause majeure identifiee automatiquement sur cette periode."
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
