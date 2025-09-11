-- Hourly time spine model required by dbt semantic layer
-- Must have granularity HOUR or smaller
{{
    config(
        materialized='table',
    )
}}

with hours as (
    {{
        dbt.date_spine(
            'hour',
            "date '2024-01-01'",
            "date '2026-01-01'"
        )
    }}
),

final as (
    select cast(date_hour as datetime) as date_hour
    from hours
    where date_hour > datetime '2022-01-01 00:00:00'
    and date_hour < datetime '2026-01-01 00:00:00'
)

select * from final
order by 1
