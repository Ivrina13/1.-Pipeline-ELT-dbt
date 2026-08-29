
  
  create view "dev"."main"."stg_geolocation__dbt_tmp" as (
    select
    geolocation_zip_code_prefix as zip_code_prefix,
    avg(geolocation_lat) as latitude,
    avg(geolocation_lng) as longitude,
    max(geolocation_city) as city,
    max(geolocation_state) as state
from "dev"."main"."olist_geolocation_dataset"
group by geolocation_zip_code_prefix
  );
