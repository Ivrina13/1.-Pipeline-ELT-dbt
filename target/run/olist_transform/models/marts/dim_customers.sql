
  
  create view "dev"."main"."dim_customers__dbt_tmp" as (
    -- dim_customers.sql
-- Une ligne = un client unique

with customers as (
    select * from "dev"."main"."stg_customers"
),

orders as (
    select 
        order_id,
        customer_id,
        purchased_at
    from "dev"."main"."stg_orders"
),

order_items as (
    select
        order_id,
        price
    from "dev"."main"."stg_order_items"
),

customer_metrics as (
    select
        o.customer_id,
        count(distinct o.order_id) as total_orders,
        sum(oi.price) as total_spent,
        min(o.purchased_at) as first_purchase_date,
        max(o.purchased_at) as last_purchase_date,
        date_diff('day', max(o.purchased_at), current_date) as recency_days
    from orders o
    left join order_items oi on o.order_id = oi.order_id
    group by o.customer_id
)

select
    customers.customer_id,
    customers.customer_unique_id,
    customers.customer_city as customer_city,
    customers.customer_state as customer_state,
    customers.customer_zip_code_prefix as customer_zip_code_prefix,
    
    coalesce(customer_metrics.total_orders, 0) as total_orders,
    coalesce(customer_metrics.total_spent, 0) as total_spent,
    customer_metrics.first_purchase_date,
    customer_metrics.last_purchase_date,
    customer_metrics.recency_days,
    
    case 
        when customer_metrics.total_orders = 0 then 'Aucun achat'
        when customer_metrics.total_orders = 1 then 'Nouveau client'
        when customer_metrics.total_orders <= 3 then 'Client régulier'
        when customer_metrics.total_orders <= 6 then 'Client fidèle'
        else 'Client VIP'
    end as customer_segment,
    
    current_date as dim_created_at

from customers
left join customer_metrics on customers.customer_id = customer_metrics.customer_id
  );
