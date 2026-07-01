SELECT
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state,
    source_file,
    loaded_at::timestamp as loaded_at
    
FROM {{ source('raw', 'raw_sellers')}}