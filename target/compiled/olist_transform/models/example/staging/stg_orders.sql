select
    order_id,
    customer_id,
    lower(trim(order_status)) as status,
    
    -- Date seule
    date(order_purchase_timestamp) as purchased_date,
    date(order_approved_at) as approved_date,
    date(order_delivered_carrier_date) as shipped_date,
    date(order_delivered_customer_date) as delivered_date,
    date(order_estimated_delivery_date) as estimated_delivery_date,
    
    -- Heure seule
    extract(hour from order_purchase_timestamp) as purchased_hour,
    extract(hour from order_approved_at) as approved_hour,
    extract(hour from order_delivered_carrier_date) as shipped_hour,
    extract(hour from order_delivered_customer_date) as delivered_hour,
    
    -- Timestamp complet (si besoin)
    order_purchase_timestamp as purchased_at,
    order_approved_at as approved_at,
    order_delivered_carrier_date as shipped_at,
    order_delivered_customer_date as delivered_at,
    order_estimated_delivery_date as estimated_delivery_at

from "dev"."main"."olist_orders_dataset"