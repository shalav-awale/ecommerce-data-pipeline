SELECT
    product_category_name,
    product_category_name_english,
    source_file,
    loaded_at::timestamp as loaded_at

FROM {{ source('raw', 'raw_product_category_name_translation') }}