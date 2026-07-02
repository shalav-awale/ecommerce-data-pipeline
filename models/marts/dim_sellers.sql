with source as (
    select * from {{ ref('stg_sellers')}}
),
deduplication as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state,
        row_number() over (partition by seller_id order by loaded_at desc) as rn
    from source
)
select
    {{ dbt_utils.generate_surrogate_key(['seller_id']) }} as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
from deduplication
where rn = 1