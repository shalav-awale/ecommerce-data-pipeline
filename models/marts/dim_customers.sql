with source as (
    select * from {{ ref('stg_customers')}}
),
deduplication as (
    select
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        row_number() over (partition by customer_id order by loaded_at desc) as rn
    from source
)
select
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
from deduplication
where rn = 1