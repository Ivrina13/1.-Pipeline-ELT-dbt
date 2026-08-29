
  
  create view "dev"."main"."dim_products__dbt_tmp" as (
    -- dim_products.sql
-- Une ligne = un produit unique

with products as (
    select * from "dev"."main"."stg_products"
),

translation as (
    select * from "dev"."main"."stg_category_name_translation"
),

-- Métriques produits (ventes)
product_sales as (
    select
        oi.product_id,
        count(distinct oi.order_id) as total_orders,
        sum(oi.price) as total_revenue,
        avg(oi.price) as avg_price,
        count(oi.order_item_id) as total_items_sold
    from "dev"."main"."stg_order_items" oi
    group by oi.product_id
),

-- Notes moyennes par produit
product_reviews as (
    select
        oi.product_id,
        avg(r.review_score) as avg_review_score,
        count(r.review_id) as review_count
    from "dev"."main"."stg_order_items" oi
    left join "dev"."main"."stg_order_reviews" r on oi.order_id = r.order_id
    group by oi.product_id
)

select
    products.product_id,
    products.product_category_name,
    coalesce(translation.product_category_name_english, products.product_category_name) as product_category_english,
    products.weight_g,
    products.length_cm,
    products.height_cm,
    products.width_cm,
    
    -- Métriques de vente
    coalesce(product_sales.total_orders, 0) as total_orders,
    coalesce(product_sales.total_revenue, 0) as total_revenue,
    coalesce(product_sales.avg_price, 0) as avg_price,
    coalesce(product_sales.total_items_sold, 0) as total_items_sold,
    
    -- Métriques d'avis
    product_reviews.avg_review_score,
    coalesce(product_reviews.review_count, 0) as review_count,
    
    current_date as dim_created_at

from products
left join translation on products.product_category_name = translation.product_category_name
left join product_sales on products.product_id = product_sales.product_id
left join product_reviews on products.product_id = product_reviews.product_id
  );
