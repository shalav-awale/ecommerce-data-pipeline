WITH date_spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2019-01-01' as date)"
    ) }}
),

dates AS (
    SELECT
        date_day::date AS full_date,
        EXTRACT(YEAR FROM date_day)::int AS year,
        EXTRACT(MONTH FROM date_day)::int AS month,
        EXTRACT(QUARTER FROM date_day)::int AS quarter,
        TO_CHAR(date_day, 'Month') AS month_name,
        EXTRACT(DOW FROM date_day)::int AS day_of_week,
        TO_CHAR(date_day, 'Day') AS day_name,
        CASE
            WHEN EXTRACT(DOW FROM date_day)::int IN (0, 6)
            THEN TRUE
            ELSE FALSE
        END AS is_weekend
    FROM date_spine
)

SELECT * FROM dates