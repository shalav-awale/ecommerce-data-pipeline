-- tests/assert_days_to_delivery_not_negative.sql
-- Tests that delivered orders don't have negative delivery days
-- Returns rows where this rule is violated
-- Zero rows = test passes

SELECT
    order_id,
    days_to_delivery,
    delivery_status
FROM {{ ref('fct_orders') }}
WHERE days_to_delivery < 0