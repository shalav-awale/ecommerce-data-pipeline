SELECT
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date::timestamp as review_creation_date,
    review_answer_timestamp::timestamp as review_answer_timestamp,
    source_file,
    loaded_at::timestamp as loaded_at

FROM {{ source('raw', 'raw_order_reviews') }}