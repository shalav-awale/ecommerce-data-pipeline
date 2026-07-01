SELECT
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value,
    source_file,
    loaded_at::timestamp as loaded_at

FROM {{ source('raw', 'raw_order_payments')}}