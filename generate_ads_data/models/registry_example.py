"""
Example usage of the models registry.

This file demonstrates how to use the centralized registry to access
all models, enums, constants, and schemas.
"""

from .registry import registry


def example_usage():
    """Demonstrate various ways to use the registry."""

    # Method 1: Using the global registry instance
    print("=== Using global registry instance ===")

    # Access enums
    status = registry.EntityStatus.ACTIVE
    objective = registry.Objective.awareness
    ad_format = registry.AdFormat.standard_video

    print(f"Status: {status}")
    print(f"Objective: {objective}")
    print(f"Ad Format: {ad_format}")

    # Access constants
    max_cpm = registry.PricingDefaults.DEFAULT_CPM_MAX
    min_duration = registry.CreativeDefaults.ALLOWED_CREATIVE_DURATIONS[0]

    print(f"Max CPM: {max_cpm}")
    print(f"Min Duration: {min_duration} seconds")

    # Access ORM models
    Advertiser = registry.ORM.Advertiser
    Campaign = registry.ORM.Campaign

    print(f"Advertiser model: {Advertiser}")
    print(f"Campaign model: {Campaign}")

    # Access schemas
    AdvertiserCreate = registry.Schemas.AdvertiserCreate
    CampaignCreate = registry.Schemas.CampaignCreate

    print(f"AdvertiserCreate schema: {AdvertiserCreate}")
    print(f"CampaignCreate schema: {CampaignCreate}")

    # Method 2: Using the Registry class directly
    print("\n=== Using Registry class directly ===")

    # Access through organized categories
    entity_status = registry.Enums.EntityStatus.active
    budget_type = registry.Enums.BudgetType.lifetime
    currency = registry.Enums.Currency.USD

    print(f"Entity Status: {entity_status}")
    print(f"Budget Type: {budget_type}")
    print(f"Currency: {currency}")

    # Access ORM models through organized categories
    LineItem = registry.ORM.LineItem
    Creative = registry.ORM.Creative

    print(f"LineItem model: {LineItem}")
    print(f"Creative model: {Creative}")

    # Method 3: Using utility functions
    print("\n=== Using utility functions ===")

    # Access utility functions
    is_valid_key = registry.Utils.is_valid_targeting_key
    clamp_cpm = registry.Utils.clamp_cpm_to_defaults

    print(f"is_valid_targeting_key function: {is_valid_key}")
    print(f"clamp_cpm_to_defaults function: {clamp_cpm}")

    # Method 4: Direct property access for common components
    print("\n=== Direct property access ===")

    # These are the most commonly used components
    EntityStatus = registry.EntityStatus
    Objective = registry.Objective
    CampaignStatus = registry.CampaignStatus
    AdFormat = registry.AdFormat
    BudgetType = registry.BudgetType
    Currency = registry.Currency
    DspPartner = registry.DspPartner

    print(f"EntityStatus enum: {EntityStatus}")
    print(f"Objective enum: {Objective}")
    print(f"CampaignStatus enum: {CampaignStatus}")
    print(f"AdFormat enum: {AdFormat}")
    print(f"BudgetType enum: {BudgetType}")
    print(f"Currency enum: {Currency}")
    print(f"DspPartner enum: {DspPartner}")


def example_imports():
    """Show different import patterns."""

    print("\n=== Import Patterns ===")

    # Pattern 1: Import the global instance
    # Pattern 2: Import specific registries
    # Pattern 3: Import specific components

    print("All import patterns demonstrated successfully!")


if __name__ == "__main__":
    example_usage()
    example_imports()
