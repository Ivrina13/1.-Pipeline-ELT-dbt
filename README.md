# 1.-Pipeline-nettoyage-dashboard-Vente-Stock
[ Pipeline + Dashboard ] ● Objectif : Fournir une vision consolidée des KPIs de vente, satisfaction client et performance logistique à travers un dashboard interactif, afin de guider les décisions stratégiques.

---

# Olist Analytics Platform - Business Intelligence Dashboard

## 1. Description du Projet (Business Vision)

Cette plateforme d'analyse business fournit une vue interactive et en temps réel des performances commerciales d'Olist, la plus grande place de marché du e-commerce brésilien.

**L'outil répond à 3 besoins stratégiques majeurs :**

📊 **Vision consolidée** : Un dashboard unique qui synthétise les KPIs critiques (chiffre d'affaires, satisfaction client, performance logistique) pour une prise de décision rapide.

🔍 **Analyse granulaire** : Possibilité de filtrer par catégorie de produit, région, période ou vendeur pour identifier des opportunités de croissance ou des axes d'amélioration.

📈 **Suivi des tendances** : Visualisation de l'évolution des performances dans le temps pour anticiper les pics d'activité et ajuster les ressources.

**Pour qui ?**
- **Équipes commerciales** : Identification des produits et catégories à fort potentiel
- **Logistique** : Optimisation des délais de livraison et détection des zones à risque
- **Marketing** : Analyse de la satisfaction client et du NPS par région
- **Direction** : Vision panoramique de la santé de l'activité

---

## 2. Architecture Technique

### Pipeline de données

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Données brutes  │────▶│   Staging    │────▶│    Marts        │────▶│   Dashboard     │
│  (CSV Kaggle)    │     │  (dbt models)│     │  (dimensions &  │     │  (Streamlit)    │
│                  │     │              │     │   faits)        │     │                 │
└─────────────────┘     └──────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                      │                      │
    8 fichiers           Nettoyage &            Modélisation          Visualisation
    └─ customers         transformations        └─ dim_customers      └─ KPIs
    └─ orders            └─ stg_orders          └─ dim_products      └─ Graphiques
    └─ products          └─ stg_products        └─ dim_sellers       └─ Filtres
    └─ sellers           └─ stg_sellers         └─ fct_orders        └─ Alertes
    └─ order_items       └─ stg_order_items
    └─ payments          └─ stg_payments
    └─ reviews           └─ stg_reviews
    └─ geolocation       └─ stg_geolocation
```

### Stack Technique

| Couche | Outils |
|--------|--------|
| **Orchestration & Transformation** | dbt (Data Build Tool) |
| **Base de données** | PostgreSQL / DuckDB |
| **Visualisation & Dashboard** | Streamlit + Plotly |
| **Langage** | Python 3.9+, SQL |
| **Contrôle de version** | Git & GitHub |

---

## 3. Installation

### Prérequis
- Python 3.9+
- PostgreSQL 13+ (ou DuckDB pour version légère)
- dbt-core
- Git

### 1. Cloner le projet
```bash
git clone https://github.com/votre-org/olist-analytics.git
cd olist-analytics
```

### 2. Créer l'environnement Python
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

### 3. Configurer dbt
```bash
cd olist_transform
# Créer le fichier profiles.yml (voir exemple ci-dessous)
dbt deps
dbt debug
```

**Exemple de `profiles.yml` :**
```yaml
olist_transform:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: postgres
      password: votre_mdp
      port: 5432
      dbname: olist_db
      schema: public
      threads: 4
```

### 4. Charger les données sources
```bash
# Télécharger les CSV depuis Kaggle et les placer dans data/
dbt seed  # Importe les données de référence
dbt run   # Exécute les transformations
dbt test  # Vérifie l'intégrité des données
```

### 5. Lancer le dashboard
```bash
cd ..
streamlit run app.py
```

---

## 4. Structure du Projet

```
olist-analytics/
├── app.py                      # Dashboard Streamlit
├── olist_transform/            # Projet dbt
│   ├── models/
│   │   ├── staging/            # Nettoyage des données brutes
│   │   │   ├── stg_customers.sql
│   │   │   ├── stg_orders.sql
│   │   │   ├── stg_products.sql
│   │   │   ├── stg_sellers.sql
│   │   │   ├── stg_order_items.sql
│   │   │   ├── stg_order_payments.sql
│   │   │   ├── stg_order_reviews.sql
│   │   │   └── stg_geolocation.sql
│   │   ├── marts/              # Modèles business (dimensions & faits)
│   │   │   ├── dim_customers.sql
│   │   │   ├── dim_products.sql
│   │   │   ├── dim_sellers.sql
│   │   │   └── fct_orders.sql
│   │   └── schema.yml          # Documentation & tests dbt
│   ├── seeds/                  # Données de référence (CSV)
│   ├── snapshots/              # Suivi des historiques
│   └── dbt_project.yml
├── requirements.txt
└── README.md
```

---
### KPIs principaux
- **Total Holding** : Valeur totale des commandes sur la période
- **Taux de satisfaction** : Note moyenne des avis clients
- **Performance logistique** : Délai moyen de livraison vs estimé
- **Portfolio Health Score** : Indicateur composite de santé business

### Analyses disponibles
-  **Performance temporelle** : Évolution des ventes et satisfaction
-  **Par catégorie** : Top produits et marges par catégorie
-  **Par région** : Distribution géographique des ventes
-  **Par vendeur** : Performance individuelle des vendeurs
-  **Avis clients** : Analyse sentimentale des reviews

---

## 5. Questions Business Traitées

| # | Question Business | Source de données | Résultat attendu |
|---|-------------------|-------------------|------------------|
| 1 | Quelles catégories génèrent le plus de CA ? | `fct_orders` + `dim_products` | Top 10 catégories par revenu |
| 2 | Quel est l'impact du délai de livraison sur les notes ? | `fct_orders` + `stg_order_reviews` | Corrélation délai → satisfaction |
| 3 | Où sont les zones à fort potentiel inexploité ? | `dim_customers` + géolocalisation | Carte de densité des ventes |
| 4 | Quels vendeurs sont les plus performants ? | `dim_sellers` + `fct_orders` | Classement des vendeurs par CA et notes |
| 5 | Y a-t-il une saisonnalité des ventes ? | `fct_orders` (date) | Pics identifiés (Black Friday, etc.) |

---

## 6. Exemple de Résultats

**Analyse catégorielle (extrait) :**
```
Top 3 catégories par CA :
1. moveis_decoracao → R$ 1.2M (18% du total)
2. cama_mesa_banho → R$ 850K (13%)
3. beleza_saude → R$ 720K (11%)
```

**Impact logistique :**
- Délai moyen réel : 12.5 jours (vs 10.2 jours estimé)
- Note moyenne : 4.1/5
- **Corrélation** : +2 jours de retard → -0.5 point de note

---

## 7. Licence & Crédits

- **Dataset** : [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) - fourni par Olist
- **Projet** : Développé dans le cadre d'une analyse business par Ivrina Nivarosa

---
## 8. DASHBOARD Streamlit 
