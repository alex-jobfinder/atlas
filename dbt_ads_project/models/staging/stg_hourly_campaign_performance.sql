{{ config(materialized='view') }}

-- Staging model for hourly campaign performance
-- This model references the seed data and can be extended with transformations as needed

-- This staging model references the campaign_performance seed data
-- The seed file contains all the semantic metadata and column definitions

select * from {{ ref('campaign_performance') }}

-- Add any staging-level transformations here if needed
-- Examples:
-- - Column renaming
-- - Data type casting
-- - Basic filtering
-- - Simple calculations
