WITH source AS (
    SELECT * FROM {{ ref('stg_products') }}
),

translation AS (
    SELECT * FROM {{ ref('stg_product_category_name_translation') }}
),

deduplicated AS (
    SELECT
        p.product_id,
        p.product_category_name,
        t.product_category_name_english,
        p.product_name_length,
        p.product_description_length,
        p.product_photos_qty,
        p.product_weight_g,
        p.product_length_cm,
        p.product_height_cm,
        p.product_width_cm,
        ROW_NUMBER() OVER (
            PARTITION BY p.product_id
            ORDER BY p.loaded_at DESC
        ) AS rn
    FROM source p
    LEFT JOIN translation t
        ON p.product_category_name = t.product_category_name
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} AS product_key,
    product_id,
    product_category_name,
    product_category_name_english,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
FROM deduplicated
WHERE rn = 1