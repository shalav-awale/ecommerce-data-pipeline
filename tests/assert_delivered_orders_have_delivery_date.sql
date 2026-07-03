-- tests/assert_delivered_orders_have_delivery_date.sql
--
-- Tests that orders marked as 'delivered' have a delivery timestamp.
-- 
-- KNOWN ISSUE: 8 orders in the Olist dataset are marked 'delivered'
-- but have NULL delivery timestamps. This appears to be an upstream
-- data quality issue in the source system — likely orders where the
-- delivery confirmation was recorded but the timestamp was not
-- captured. These 8 orders are concentrated in June-July 2018.
--
-- This test intentionally FAILS to surface this known issue
-- and prevent it from silently corrupting delivery time analytics.
-- In production, these records would be flagged for investigation
-- with the source system owner.
--
-- Returns rows where this rule is violated.
-- Zero rows = test passes.

SELECT
    order_id,
    order_status,
    order_delivered_customer_date
FROM {{ ref('fct_orders') }}
WHERE order_status = 'delivered'
AND order_delivered_customer_date IS NULL