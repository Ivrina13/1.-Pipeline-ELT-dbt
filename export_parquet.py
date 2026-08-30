import duckdb
import os

db_path = os.path.join("data Brazilian E-Commerce", "olist_transform", "dev.duckdb")

print(f"Connexion a : {db_path}")
con = duckdb.connect(db_path, read_only=True)

os.makedirs("data", exist_ok=True)

tables = ["fct_orders", "dim_customers", "dim_products", "dim_sellers"]

for table in tables:
    try:
        con.execute(f"COPY {table} TO 'data/{table}.parquet' (FORMAT PARQUET)")
        print(f"OK : {table} exporte dans data/{table}.parquet")
    except Exception as e:
        print(f"ERREUR sur {table} : {e}")

con.close()
print("Termine. Verifie le contenu du dossier data.")
