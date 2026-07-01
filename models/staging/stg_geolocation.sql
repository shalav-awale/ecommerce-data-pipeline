SELECT
    geolocation_zip_code_prefix,
    geolocation_lat,
    geolocation_lng,
    geolocation_city,
    geolocation_state,
    source_file,
    loaded_at::timestamp as loaded_at

FROM {{ source('raw', 'raw_geolocation') }}