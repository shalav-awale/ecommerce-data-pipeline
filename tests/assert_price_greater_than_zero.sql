-- tests/assert_price_greater_than_zero.sql

SELECT
    order_id,
    order_item_id,
    price
FROM {{ ref('fct_order_items') }}
WHERE price <= 0