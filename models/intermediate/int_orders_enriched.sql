SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    (order_delivered_customer_date::date - order_purchase_timestamp::date) as days_to_delivery,
    (order_estimated_delivery_date::date - order_purchase_timestamp::date) as days_to_estimated_delivery,
    case
	    when order_delivered_customer_date is null then false
	    when (order_estimated_delivery_date::date < order_delivered_customer_date::date) then true
	    else false
    end as is_late_delivery,
    case
    	when order_delivered_customer_date is null then 'NOT_YET_DELIVERED'
    	when order_delivered_customer_date::date > order_estimated_delivery_date::date then 'LATE'
    	when order_delivered_customer_date::date <= order_estimated_delivery_date::date then 'ON-TIME' 
    end as delivery_status,
    source_file,
    loaded_at
FROM {{ ref('stg_orders')}}