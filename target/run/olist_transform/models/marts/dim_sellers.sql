
  
  create view "dev"."main"."dim_sellers__dbt_tmp" as (
    -- dim_sellers.sql
-- Une ligne = un vendeur unique

with sellers as (
    select * from "dev"."main"."stg_sellers"
),

seller_metrics as (
    select
        oi.seller_id,
        count(distinct oi.order_id) as total_orders,
        sum(oi.price) as total_revenue,
        avg(oi.price) as avg_order_value,
        count(oi.order_item_id) as total_items_sold,
        count(distinct oi.product_id) as unique_products_sold
    from "dev"."main"."stg_order_items" oi
    group by oi.seller_id
),

seller_reviews as (
    select
        oi.seller_id,
        avg(r.review_score) as avg_review_score,
        count(r.review_id) as review_count
    from "dev"."main"."stg_order_items" oi
    left join "dev"."main"."stg_order_reviews" r on oi.order_id = r.order_id
    group by oi.seller_id
),

seller_delivery as (
    select
        oi.seller_id,
        avg(date_diff('day', o.purchased_at, o.delivered_at)) as avg_delivery_days
    from "dev"."main"."stg_order_items" oi
    left join "dev"."main"."stg_orders" o on oi.order_id = o.order_id
    where o.delivered_at is not null
    group by oi.seller_id
)

select
    sellers.seller_id,
    sellers.seller_city as seller_city,
    sellers.seller_state as seller_state,
    sellers.seller_zip_code_prefix as seller_zip_code_prefix,
    
    coalesce(seller_metrics.total_orders, 0) as total_orders,
    coalesce(seller_metrics.total_revenue, 0) as total_revenue,
    coalesce(seller_metrics.avg_order_value, 0) as avg_order_value,
    coalesce(seller_metrics.total_items_sold, 0) as total_items_sold,
    coalesce(seller_metrics.unique_products_sold, 0) as unique_products_sold,
    
    seller_reviews.avg_review_score,
    coalesce(seller_reviews.review_count, 0) as review_count,
    
    seller_delivery.avg_delivery_days,
    
    case 
        when coalesce(seller_metrics.total_orders, 0) = 0 then 'Nouveau vendeur'
        when coalesce(seller_metrics.total_orders, 0) <= 5 then 'Petit vendeur'
        when coalesce(seller_metrics.total_orders, 0) <= 20 then 'Vendeur moyen'
        when coalesce(seller_metrics.total_orders, 0) <= 50 then 'Grand vendeur'
        else 'Top vendeur'
    end as seller_segment,
    
    current_date as dim_created_at

from sellers
left join seller_metrics on sellers.seller_id = seller_metrics.seller_id
left join seller_reviews on sellers.seller_id = seller_reviews.seller_id
left join seller_delivery on sellers.seller_id = seller_delivery.seller_id
  );
