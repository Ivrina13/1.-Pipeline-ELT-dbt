
  
  create view "dev"."main"."stg_category_name_translation__dbt_tmp" as (
    select
    product_category_name,
    product_category_name_english
from "dev"."main"."product_category_name_translation"
  );
