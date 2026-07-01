SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value,
    (price + freight_value) AS total_item_revenue,
    ROW_NUMBER() OVER (
        PARTITION BY order_id
        ORDER BY price DESC
    ) AS item_rank_by_price
FROM {{ ref('stg_order_items') }}