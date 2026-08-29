select
    order_id,
    payment_sequential,
    lower(trim(payment_type)) as payment_type,
    cast(payment_installments as integer) as payment_installments,
    cast(payment_value as numeric(10,2)) as payment_value
from "dev"."main"."olist_order_payments_dataset"