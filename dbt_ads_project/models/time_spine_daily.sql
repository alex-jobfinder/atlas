-- Daily time spine model required by dbt semantic layer
-- Must have granularity DAY or smaller
{{
    config(
        materialized='table',
    )
}}

with days as (
    {{
        dbt.date_spine(
            'day',
            "date '2024-01-01'",
            "date '2026-01-01'"
        )
    }}
),

final as (
    select cast(date_day as date) as date_day
    from days
    where date_day > date '2022-01-01'
    and date_day < date '2026-01-01'
)

select * from final
order by 1
