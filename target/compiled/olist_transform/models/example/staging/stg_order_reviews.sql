select
    review_id,
    order_id,
    review_score,
    trim(review_comment_title) as review_comment_title,
    trim(review_comment_message) as review_comment_message,
    date(review_creation_date) as review_created_at,
    date(review_answer_timestamp) as review_answer_at
from "dev"."main"."olist_order_reviews_dataset"