import duckdb

conn = duckdb.connect("olist.duckdb")
print("Chargement des fichiers CSV dans DuckDB...")

conn.execute("CREATE OR REPLACE TABLE orders AS SELECT * FROM read_csv_auto('olist_orders_dataset.csv');")
conn.execute("CREATE OR REPLACE TABLE order_items AS SELECT * FROM read_csv_auto('olist_order_items_dataset.csv');")
conn.execute("CREATE OR REPLACE TABLE customers AS SELECT * FROM read_csv_auto('olist_customers_dataset.csv');")

print("Base de données créée avec succès !")
result = conn.execute("SELECT COUNT(*) FROM orders;").fetchone()
print(f"Nombre total de commandes : {result[0]}")
conn.close()
