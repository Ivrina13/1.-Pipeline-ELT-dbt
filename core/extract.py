"""
Bloc 1 : Extract — lecture brute des donnees.
Ici : lecture du fichier data/fct_orders.parquet via DuckDB.
(A terme, remplacable par un appel API sans changer le reste du pipeline.)
"""
import os

import duckdb
import pandas as pd


def read_raw_data(parquet_path: str = None) -> pd.DataFrame | None:
    """Lit le fichier parquet brut et retourne un DataFrame, ou None si absent/erreur."""
    try:
        if parquet_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            parquet_path = os.path.join(base_dir, "data", "fct_orders.parquet")

        if not os.path.exists(parquet_path):
            return None

        conn = duckdb.connect(database=":memory:")
        conn.execute(f"""
            CREATE TABLE fct_orders AS
            SELECT * FROM read_parquet('{parquet_path}')
        """)
        df = conn.execute("SELECT * FROM fct_orders").df()
        conn.close()

        if df.empty:
            return None

        return df

    except Exception:
        return None
