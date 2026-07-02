-- models/marts/fact_orders.sql
--
-- Orders fact table (Kimball star schema).
-- Grain: one row per order_id.
-- Joins to dim_customers for customer_key.
-- Joins to dim_dates for order date attributes.

WITH
    int_orders AS (
        SELECT * FROM {{ ref('int_orders_enriched') }}
    ),
    dim_customers AS (
        SELECT * FROM {{ ref('dim_customers') }}
    ),
    dim_dates AS (
        SELECT * FROM {{ ref('dim_dates') }}
    )

SELECT
    -- Surrogate key for this fact table
    {{ dbt_utils.generate_surrogate_key(['order_id']) }} AS order_key,

    -- Natural key — kept for traceability
    o.order_id,

    -- Foreign keys to dimensions
    c.customer_key,
    d.full_date AS order_date,

    -- Order attributes
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    -- Calculated metrics from intermediate layer
    o.days_to_delivery,
    o.days_to_estimated_delivery,
    o.is_late_delivery,
    o.delivery_status

FROM int_orders o

LEFT JOIN dim_customers c
    ON o.customer_id = c.customer_id

LEFT JOIN dim_dates d
    ON o.order_purchase_timestamp::date = d.full_date