SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date::timestamp as shipping_limit_date,
    price,
    freight_value,
    source_file,
    loaded_at::timestamp as loaded_at
    
FROM {{ source('raw', 'raw_order_items')}}