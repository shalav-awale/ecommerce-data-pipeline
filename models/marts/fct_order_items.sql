-- models/marts/fact_order_items.sql
--
-- Order items fact table (Kimball star schema).
-- Grain: one row per order_id + order_item_id combination.
-- Joins to dim_products and dim_sellers for surrogate keys.

WITH
    int_order_items AS (
        SELECT * FROM {{ ref('int_order_items_enriched') }}
    ),
    dim_products AS (
        SELECT * FROM {{ ref('dim_products') }}
    ),
    dim_sellers AS (
        SELECT * FROM {{ ref('dim_sellers') }}
    )

SELECT
    -- Surrogate key — composite because neither column alone is unique
    {{ dbt_utils.generate_surrogate_key(['order_id', 'order_item_id']) }}
        AS order_item_key,

    -- Foreign keys to dimensions
    p.product_key,
    s.seller_key,

    -- Natural keys — kept for traceability
    o.order_id,
    o.order_item_id,
    o.product_id,
    o.seller_id,

    -- Order item attributes
    o.shipping_limit_date,
    o.price,
    o.freight_value,

    -- Calculated metrics from intermediate layer
    o.total_item_revenue,
    o.item_rank_by_price

FROM int_order_items o

LEFT JOIN dim_products p
    ON o.product_id = p.product_id

LEFT JOIN dim_sellers s
    ON o.seller_id = s.seller_id