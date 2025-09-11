{{ config(materialized='table') }}

-- Mart model for hourly campaign performance
-- This model builds upon the staging data and adds business logic, aggregations,
-- and derived metrics for analysis and reporting

with staging as (
    select * from {{ ref('stg_hourly_campaign_performance') }}
),

enriched as (
    select
        -- Primary keys and identifiers
        id,
        campaign_id,

        -- Time dimensions
        hour_ts,
        date_trunc('day', cast(hour_ts as timestamp)) as date_day,
        date_trunc('week', cast(hour_ts as timestamp)) as date_week,
        date_trunc('month', cast(hour_ts as timestamp)) as date_month,
        hour_of_day,
        day_of_week,
        is_business_hour,

        -- Core performance metrics
        impressions,
        clicks,
        spend,
        video_start,
        video_q25,
        video_q50,
        video_q75,
        video_q100,

        -- Engagement metrics
        frequency,
        reach,
        skips,
        qr_scans,
        interactive_engagements,

        -- Quality and efficiency metrics
        requests,
        responses,
        eligible_impressions,
        auctions_won,
        viewable_impressions,
        audible_impressions,

        -- Error tracking
        error_count,
        timeout_count,

        -- Derived business metrics
        case
            when impressions > 0 then round(cast(clicks as float) / impressions, 4)
            else 0
        end as calculated_ctr,

        case
            when eligible_impressions > 0 then round(cast(auctions_won as float) / eligible_impressions, 4)
            else 0
        end as win_rate,

        case
            when impressions > 0 then round(cast(viewable_impressions as float) / impressions, 4)
            else 0
        end as viewability_rate,

        case
            when impressions > 0 then round(cast(audible_impressions as float) / impressions, 4)
            else 0
        end as audible_rate,

        case
            when spend > 0 and impressions > 0 then round(cast(spend as float) / impressions, 2)
            else 0
        end as cpm,

        case
            when spend > 0 and clicks > 0 then round(cast(spend as float) / clicks, 2)
            else 0
        end as cpc,

        case
            when spend > 0 and video_start > 0 then round(cast(spend as float) / video_start, 2)
            else 0
        end as cpv,

        -- Video completion and engagement rates
        case
            when video_start > 0 then round(cast(video_q100 as float) / video_start, 4)
            else 0
        end as video_completion_rate,

        case
            when video_start > 0 then round(cast(skips as float) / video_start, 4)
            else 0
        end as video_skip_rate,

        case
            when impressions > 0 then round(cast(video_start as float) / impressions, 4)
            else 0
        end as video_start_rate,

        -- Supply funnel efficiency
        case
            when requests > 0 then round(cast(eligible_impressions as float) / requests, 4)
            else 0
        end as supply_funnel_efficiency,

        case
            when eligible_impressions > 0 then round(cast(auctions_won as float) / eligible_impressions, 4)
            else 0
        end as fill_rate,

        -- Response and error rates
        case
            when requests > 0 then round(cast(responses as float) / requests, 4)
            else 0
        end as response_rate,

        case
            when requests > 0 then round(cast(error_count as float) / requests, 4)
            else 0
        end as error_rate,

        case
            when requests > 0 then round(cast(timeout_count as float) / requests, 4)
            else 0
        end as timeout_rate,

        -- Engagement rates
        case
            when impressions > 0 then round(cast(qr_scans as float) / impressions, 4)
            else 0
        end as qr_scan_rate,

        case
            when impressions > 0 then round(cast(interactive_engagements as float) / impressions, 4)
            else 0
        end as interactive_rate,

        -- Effective CPM (in cents)
        case
            when impressions > 0 then round(cast(spend as float) * 1000 / impressions, 0)
            else 0
        end as effective_cpm,

        -- Average watch time (estimated from quartiles)
        case
            when video_start > 0 then
                round(
                    (
                        -- 0-25% segment
                        (video_start - video_q25) * 3.75 +
                        -- 25-50% segment
                        (video_q25 - video_q50) * 11.25 +
                        -- 50-75% segment
                        (video_q50 - video_q75) * 18.75 +
                        -- 75-100% segment
                        (video_q75 - video_q100) * 26.25 +
                        -- 100% completion
                        video_q100 * 30.0
                    ) / video_start, 1
                )
            else 0
        end as avg_watch_time_seconds,

        -- Performance flags
        case when calculated_ctr >= 0.02 then 1 else 0 end as high_ctr_flag,
        case when viewability_rate >= 0.7 then 1 else 0 end as high_viewability_flag,

        -- Metadata
        human_readable,
        audience_json

    from staging
)

select * from enriched
