Welcome to your new dbt project!

### Using the starter project

# Instead of: DBT_PROFILES_DIR=. poetry run dbt seed
poetry run dbt seed

# Instead of: DBT_PROFILES_DIR=. poetry run dbt run
poetry run dbt run

# Instead of: DBT_PROFILES_DIR=. poetry run dbt test
poetry run dbt test

### Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices

Seed (campaign_performance)
    ↓
Staging (stg_hourly_campaign_performance)
    ↓
┌─────────────────────────────────────────────────────────┐
│                    MART MODELS                         │
├─────────────────┬─────────────────┬─────────────────────┤
│ Hourly Mart    │ Daily Mart      │ Weekly Mart         │
│ (hour_ts)      │ (date_day)      │ (date_week)         │
│ - Raw metrics  │ - Daily sums    │ - Weekly sums       │
│ - Hour dims    │ - Daily avgs    │ - Weekly avgs       │
│ - All derived  │ - All derived   │ - All derived       │
└─────────────────┴─────────────────┴─────────────────────┘
