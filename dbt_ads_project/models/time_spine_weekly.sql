-- Weekly time spine model required by dbt semantic layer
-- Must have granularity WEEK or smaller
{{
    config(
        materialized='table',
    )
}}

with weeks as (
    {{
        dbt.date_spine(
            'week',
            "date '2024-01-01'",
            "date '2026-01-01'"
        )
    }}
),

final as (
    select cast(date_week as date) as date_week
    from weeks
    where date_week > date '2022-01-01'
    and date_week < date '2026-01-01'
)

select * from final
order by 1
