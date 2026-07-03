-- tests/assert_order_date_within_range.sql

SELECT
    order_id,
    order_date
FROM {{ ref('fct_orders') }}
WHERE order_date < '2016-01-01'
OR order_date > '2018-12-31'