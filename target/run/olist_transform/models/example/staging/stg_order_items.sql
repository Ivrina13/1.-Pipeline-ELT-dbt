
  
  create view "dev"."main"."stg_order_items__dbt_tmp" as (
    select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    cast(shipping_limit_date as timestamp) as shipping_limit_date,
    cast(price as numeric(10,2)) as price,
    cast(freight_value as numeric(10,2)) as freight_value
from "dev"."main"."olist_order_items_dataset"
  );
