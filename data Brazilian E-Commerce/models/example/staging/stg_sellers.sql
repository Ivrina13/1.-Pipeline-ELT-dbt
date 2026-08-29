select
    seller_id,
    seller_zip_code_prefix,
    upper(substr(seller_city, 1, 1)) || lower(substr(seller_city, 2)) as seller_city,
    seller_state
from {{ ref('olist_sellers_dataset') }}