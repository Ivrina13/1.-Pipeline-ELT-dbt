
  
  create view "dev"."main"."stg_products__dbt_tmp" as (
    select
    product_id,
    product_category_name,
    cast(product_weight_g as float) as weight_g,
    cast(product_length_cm as float) as length_cm,
    cast(product_height_cm as float) as height_cm,
    cast(product_width_cm as float) as width_cm
from "dev"."main"."olist_products_dataset"
  );
