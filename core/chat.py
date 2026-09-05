"""
Bloc 6 : Chat — assistant IA "Ask your data"
J'utilise DuckDB pour interroger l'ensemble des tables Olist (pas seulement
l'onglet actif), et Claude (Anthropic) pour traduire la question en SQL
puis formuler une réponse en langage naturel.
"""

import duckdb
import pandas as pd
import streamlit as st
from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"

# Adapte ces chemins si ton app.py ne tourne pas depuis la racine du repo
DATA_PATHS = {
    "customers": "data/dim_customers.parquet",
    "products": "data/dim_products.parquet",
    "sellers": "data/dim_sellers.parquet",
    "orders": "data/fct_orders.parquet",
}


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    """Charge les 4 tables Olist dans une connexion DuckDB en memoire."""
    con = duckdb.connect(database=":memory:")
    for table_name, path in DATA_PATHS.items():
        con.execute(
            f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{path}')"
        )
    return con


@st.cache_data
def get_schema_description() -> str:
    """Construit une description du schema (tables + colonnes) pour le prompt systeme."""
    con = get_connection()
    lines = []
    for table_name in DATA_PATHS:
        cols = con.execute(f"DESCRIBE {table_name}").fetchdf()
        col_list = ", ".join(
            f"{row['column_name']} ({row['column_type']})" for _, row in cols.iterrows()
        )
        lines.append(f"- {table_name}: {col_list}")
    return "\n".join(lines)


def _get_client() -> Anthropic:
    return Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def _generate_sql(question: str, schema: str) -> str:
    """Demande a Claude de traduire la question en requete SQL DuckDB."""
    client = _get_client()
    system = f"""Tu es un generateur de requetes SQL pour DuckDB.
Voici les tables disponibles (base de donnees Olist e-commerce) :
{schema}

Regles :
- Reponds UNIQUEMENT avec la requete SQL, sans aucun texte, sans markdown, sans balises.
- Utilise uniquement les tables et colonnes listees ci-dessus.
- La requete doit etre en lecture seule (SELECT uniquement).
- Limite les resultats a 200 lignes maximum (LIMIT 200), sauf si la question
  demande un agregat unique (auquel cas pas de LIMIT necessaire)."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    sql = response.content[0].text.strip().strip("`").strip()
    if sql.lower().startswith("sql"):
        sql = sql[3:].strip()
    if not sql.lower().lstrip().startswith("select"):
        raise ValueError("Requete non autorisee generee par le modele.")
    return sql


def _summarize_result(question: str, sql: str, result_df: pd.DataFrame, lang: str) -> str:
    """Demande a Claude de formuler une reponse en langage naturel a partir du resultat."""
    client = _get_client()
    lang_instruction = "Reponds en francais." if lang == "fr" else "Answer in English."
    preview = result_df.head(50).to_csv(index=False)
    system = f"""Tu es un analyste de donnees e-commerce. {lang_instruction}
On t'a pose une question ; voici la requete SQL executee et un apercu du
resultat (CSV, jusqu'a 50 lignes). Formule une reponse claire, concise et
chiffree. N'invente rien au-dela des donnees fournies."""
    user_msg = (
        f"Question : {question}\n\n"
        f"Requete SQL executee :\n{sql}\n\n"
        f"Resultat (CSV) :\n{preview}"
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text.strip()


def answer_question(q: str, df: pd.DataFrame, lang: str) -> str:
    """
    Repond a une question en langage naturel sur L'ENSEMBLE des donnees
    Olist (customers, products, sellers, orders) via DuckDB + Claude.
    Le parametre df est conserve pour compatibilite avec l'appel existant
    mais n'est plus la seule source de donnees interrogee.
    """
    schema = get_schema_description()
    con = get_connection()

    try:
        sql = _generate_sql(q, schema)
        result_df = con.execute(sql).fetchdf()
    except Exception as e:
        return (
            f"Je n'ai pas reussi a interroger les donnees pour cette question ({e})."
            if lang == "fr"
            else f"I couldn't query the data for this question ({e})."
        )

    if result_df.empty:
        return (
            "Aucun resultat trouve pour cette question."
            if lang == "fr"
            else "No results found for this question."
        )

    return _summarize_result(q, sql, result_df, lang)
