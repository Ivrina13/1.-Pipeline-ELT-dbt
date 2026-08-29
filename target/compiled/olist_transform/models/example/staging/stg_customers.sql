select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    upper(substr(customer_city, 1, 1)) || lower(substr(customer_city, 2)) as customer_city,
    customer_state
from "dev"."main"."olist_customers_dataset"