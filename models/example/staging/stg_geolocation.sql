select
    geolocation_zip_code_prefix as zip_code_prefix,
    avg(geolocation_lat) as latitude,
    avg(geolocation_lng) as longitude,
    max(geolocation_city) as city,
    max(geolocation_state) as state
from {{ ref('olist_geolocation_dataset') }}
group by geolocation_zip_code_prefix