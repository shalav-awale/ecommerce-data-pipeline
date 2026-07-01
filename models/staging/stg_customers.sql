SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state,
    source_file,
    loaded_at::timestamp as loaded_at

FROM {{ source('raw', 'raw_customers')}}