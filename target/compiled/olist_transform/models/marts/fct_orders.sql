-- Grain : une ligne = une commande

with order_items_agg as (
    select
        order_id,
        count(*) as item_count,
        sum(price) as price,
        sum(freight_value) as freight_value
    from "dev"."main"."stg_order_items"
    group by order_id
),

payments_agg as (
    select
        order_id,
        sum(payment_value) as total_payment_value,
        count(*) as payment_count,
        max(payment_installments) as max_installments
    from "dev"."main"."stg_order_payments"
    group by order_id
),

reviews_agg as (
    select
        order_id,
        avg(review_score) as avg_review_score,  -- ← review_score (pas score)
        count(*) as review_count
    from "dev"."main"."stg_order_reviews"
    group by order_id
),

orders as (
    select * from "dev"."main"."stg_orders"
),

customers as (
    select * from "dev"."main"."stg_customers"
),

order_items as (
    select * from "dev"."main"."stg_order_items"
),

products as (
    select * from "dev"."main"."stg_products"
)

select
    orders.order_id,
    orders.customer_id,
    customers.customer_unique_id,
    customers.customer_city,
    customers.customer_state,
    orders.purchased_at,
    orders.approved_at,
    orders.shipped_at,
    orders.delivered_at,
    orders.estimated_delivery_at,
    orders.estimated_delivery_at AS estimated_delivery,
    orders.status,
    products.product_category_name AS product_category,
    coalesce(order_items_agg.item_count, 0) as item_count,
    coalesce(order_items_agg.price, 0) as price,
    coalesce(order_items_agg.freight_value, 0) as freight_value,
    coalesce(payments_agg.total_payment_value, 0) as total_payment_value,
    payments_agg.payment_count,
    payments_agg.max_installments,
    reviews_agg.avg_review_score,
    reviews_agg.review_count,
    date_diff('day', orders.purchased_at, orders.delivered_at) AS delivery_days,
    CASE 
        WHEN orders.delivered_at > orders.estimated_delivery_at THEN TRUE
        ELSE FALSE
    END AS is_late,
    date_diff('day', orders.estimated_delivery_at, orders.delivered_at) AS delivery_delay_days

from orders
left join customers on orders.customer_id = customers.customer_id
left join order_items_agg on orders.order_id = order_items_agg.order_id
left join payments_agg on orders.order_id = payments_agg.order_id
left join reviews_agg on orders.order_id = reviews_agg.order_id
left join order_items on orders.order_id = order_items.order_id
left join products on order_items.product_id = products.product_id
group by
    orders.order_id,
    orders.customer_id,
    customers.customer_unique_id,
    customers.customer_city,
    customers.customer_state,
    orders.purchased_at,
    orders.approved_at,
    orders.shipped_at,
    orders.delivered_at,
    orders.estimated_delivery_at,
    orders.status,
    products.product_category_name,
    order_items_agg.item_count,
    order_items_agg.price,
    order_items_agg.freight_value,
    payments_agg.total_payment_value,
    payments_agg.payment_count,
    payments_agg.max_installments,
    reviews_agg.avg_review_score,
    reviews_agg.review_count