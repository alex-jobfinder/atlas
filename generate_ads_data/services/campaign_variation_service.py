# services/campaign_variation_service.py
"""
Enhanced template-based campaign variation service that leverages existing
Netflix Ads patterns and provides intelligent variation generation.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from decimal import Decimal
import json
import random
from datetime import date, timedelta

from models.registry import registry
from services.validators import validate_campaign_v1
from factories.faker_providers import (
    fake_campaign_dates,
    profile_tuned_cpm,
    profile_tuned_budget,
    profile_tuned_duration,
    profile_tuned_targeting
)

@dataclass
class VariationRule:
    """Enhanced variation rule with Netflix Ads domain knowledge."""
    field_path: str  # e.g., "line_items.0.ad_format" or "targeting.device"
    variation_type: str  # "enum_rotation", "range", "profile_based", "smart_combo"
    values: List[Any]
    constraints: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self):
        if not self.description:
            self.description = f"Vary {self.field_path} using {self.variation_type}"

@dataclass
class CampaignTemplate:
    """Enhanced campaign template with Netflix Ads best practices."""
    name: str
    description: str
    profile: str  # AWARENESS, CONSIDERATION, CONVERSION
    base_config: Dict[str, Any]
    variation_rules: List[VariationRule]
    target_variation_count: int
    business_constraints: Dict[str, Any] = field(default_factory=dict)
    performance_goals: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Auto-populate profile-based defaults if not provided
        if not self.base_config.get('target_cpm'):
            cpm = profile_tuned_cpm(self.profile)
            self.base_config['target_cpm'] = float(cpm) if isinstance(cpm, Decimal) else cpm
        if not self.base_config.get('budget'):
            budget = profile_tuned_budget(self.profile)
            # Store budget as a dictionary, not as a float
            self.base_config['budget'] = {
                'amount': float(budget) if isinstance(budget, Decimal) else budget,
                'type': 'LIFETIME',
                'currency': 'USD'
            }

class EnhancedCampaignVariationService:
    """Enhanced service leveraging existing Netflix Ads patterns."""

    def __init__(self):
        self.templates = self._load_enhanced_templates()
        self.variation_counter = 0

    def create_variations_from_template(
        self,
        template_name: str,
        custom_rules: Optional[List[VariationRule]] = None,
        seed: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate campaign variations with enhanced validation."""
        if seed:
            random.seed(seed)

        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        variations = []
        base_config = self._deep_copy_config(template.base_config)

        # Apply variation rules
        rules = custom_rules or template.variation_rules
        for rule in rules:
            new_variations = self._apply_enhanced_variation_rule(base_config, rule, template)
            variations.extend(new_variations)

        # Ensure we don't exceed target count
        variations = variations[:template.target_variation_count]

        # Validate and finalize variations
        validated_variations = []
        for i, variation in enumerate(variations):
            try:
                final_variation = self._finalize_variation(variation, template, i)
                validated_variations.append(final_variation)
            except Exception as e:
                print(f"Warning: Variation {i} failed validation: {e}")
                continue

        return validated_variations

    def _apply_enhanced_variation_rule(
        self,
        base_config: Dict,
        rule: VariationRule,
        template: CampaignTemplate
    ) -> List[Dict]:
        """Apply enhanced variation rules with Netflix Ads domain logic."""
        variations = []

        if rule.variation_type == "enum_rotation":
            variations = self._apply_enum_rotation(base_config, rule)

        elif rule.variation_type == "range":
            variations = self._apply_range_variation(base_config, rule)

        elif rule.variation_type == "profile_based":
            variations = self._apply_profile_based_variation(base_config, rule, template.profile)

        elif rule.variation_type == "smart_combo":
            variations = self._apply_smart_combo_variation(base_config, rule)

        # Apply constraints
        for variation in variations:
            self._apply_rule_constraints(variation, rule.constraints)

        return variations

    def _apply_enum_rotation(self, base_config: Dict, rule: VariationRule) -> List[Dict]:
        """Apply enum rotation variation rule."""
        variations = []
        for value in rule.values:
            variation = self._deep_copy_config(base_config)
            self._set_nested_field(variation, rule.field_path, value)
            variations.append(variation)
        return variations

    def _apply_range_variation(self, base_config: Dict, rule: VariationRule) -> List[Dict]:
        """Apply range-based variation rule."""
        variations = []
        min_val, max_val = rule.values

        # Convert Decimal to float if needed
        if isinstance(min_val, Decimal):
            min_val = float(min_val)
        if isinstance(max_val, Decimal):
            max_val = float(max_val)

        # Generate 3 variations across the range
        for i in range(3):
            variation = self._deep_copy_config(base_config)
            value = min_val + (i * (max_val - min_val) / 2)
            self._set_nested_field(variation, rule.field_path, value)
            variations.append(variation)

        return variations

    def _apply_smart_combo_variation(self, base_config: Dict, rule: VariationRule) -> List[Dict]:
        """Apply smart combination variation rule."""
        variations = []

        # Generate combinations of multiple field values
        import itertools
        field_combinations = list(itertools.product(*rule.values))

        for combo in field_combinations:
            variation = self._deep_copy_config(base_config)
            # Assuming rule.field_path contains comma-separated field paths
            field_paths = rule.field_path.split(',')
            for field_path, value in zip(field_paths, combo):
                self._set_nested_field(variation, field_path.strip(), value)
            variations.append(variation)

        return variations

    def _apply_profile_based_variation(
        self,
        base_config: Dict,
        rule: VariationRule,
        profile: str
    ) -> List[Dict]:
        """Apply profile-based variations using existing Netflix Ads logic."""
        variations = []

        if rule.field_path == "targeting.device":
            # Use existing profile_tuned_targeting logic
            for device_combo in rule.values:
                variation = self._deep_copy_config(base_config)
                self._set_nested_field(variation, rule.field_path, device_combo)
                variations.append(variation)

        elif rule.field_path == "line_items.0.duration_seconds":
            # Use existing profile_tuned_duration logic
            duration = profile_tuned_duration(profile)
            variation = self._deep_copy_config(base_config)
            self._set_nested_field(variation, rule.field_path, duration)
            variations.append(variation)

        return variations

    def _apply_rule_constraints(self, variation: Dict[str, Any], constraints: Dict[str, Any]) -> None:
        """Apply constraints to a variation."""
        for constraint_type, constraint_value in constraints.items():
            if constraint_type == "forbidden":
                # Ensure forbidden values are not used
                pass  # This would need more complex logic to implement
            elif constraint_type == "required":
                # Ensure required values are present
                pass  # This would need more complex logic to implement
            elif constraint_type == "min":
                # Ensure minimum values
                pass  # This would need more complex logic to implement
            elif constraint_type == "max":
                # Ensure maximum values
                pass  # This would need more complex logic to implement

    def _finalize_variation(
        self,
        variation: Dict[str, Any],
        template: CampaignTemplate,
        index: int
    ) -> Dict[str, Any]:
        """Finalize variation with proper naming and validation."""
        # Generate unique name
        variation['name'] = f"{template.name} - Variation {index + 1}"

        # Ensure required fields are present
        if 'advertiser_id' not in variation:
            variation['advertiser_id'] = 1  # Default advertiser

        # Generate flight dates if not present
        if 'flight' not in variation:
            start_date, end_date = fake_campaign_dates()
            variation['flight'] = {
                'start_date': start_date,
                'end_date': end_date
            }

        # Add budget if not present
        if 'budget' not in variation:
            budget_amount = profile_tuned_budget(template.profile)
            variation['budget'] = {
                'amount': float(budget_amount) if isinstance(budget_amount, Decimal) else budget_amount,
                'type': 'LIFETIME',
                'currency': 'USD'
            }
        else:
            # Ensure budget amount is a float if it exists
            if isinstance(variation['budget'], dict) and 'amount' in variation['budget']:
                if isinstance(variation['budget']['amount'], Decimal):
                    variation['budget']['amount'] = float(variation['budget']['amount'])

        # Add frequency cap if not present
        if 'frequency_cap' not in variation:
            variation['frequency_cap'] = {
                'count': 3,
                'unit': 'DAY',
                'scope': 'USER'
            }

        # Convert all Decimal values to float for JSON serialization
        variation = self._convert_decimals_to_floats(variation)

        # Validate using existing Netflix Ads validators
        try:
            # Convert to Pydantic schema for validation
            campaign_create = registry.CampaignCreate(**variation)
            validate_campaign_v1(campaign_create)
        except Exception as e:
            raise ValueError(f"Variation validation failed: {e}")

        return variation

    def _convert_decimals_to_floats(self, obj: Any) -> Any:
        """Recursively convert Decimal objects to floats and dates to strings for JSON serialization."""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._convert_decimals_to_floats(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals_to_floats(item) for item in obj]
        else:
            return obj

    def _load_enhanced_templates(self) -> Dict[str, CampaignTemplate]:
        """Load enhanced templates with Netflix Ads best practices."""
        return {
            "awareness_multi_device": CampaignTemplate(
                name="Awareness Multi-Device",
                description="Awareness campaign optimized for multi-device reach",
                profile="AWARENESS",
                base_config={
                    "objective": "AWARENESS",
                    "status": "DRAFT",
                    "currency": "USD",
                    "dsp_partner": "GOOGLE_DV360",
                    "programmatic_buy_type": "PROGRAMMATIC_GUARANTEED",
                    "content_adjacency_tier": "TIER_1",
                    "brand_lift_enabled": True,
                    "targeting": {},  # Add targeting at campaign level
                    "line_items": [{
                        "name": "Awareness Multi-Device LI",
                        "ad_format": "STANDARD_VIDEO",
                        "bid_cpm": 25.0,  # Use float instead of Decimal
                        "pacing_pct": 100,
                        "targeting": {},
                        "creatives": []
                    }]
                },
                variation_rules=[
                    VariationRule(
                        "line_items.0.ad_format",
                        "enum_rotation",
                        ["STANDARD_VIDEO", "INTERACTIVE_OVERLAY"],
                        {"forbidden": ["PAUSE_ADS"]},
                        "Test different ad formats for awareness"
                    ),
                    VariationRule(
                        "targeting.device",
                        "profile_based",
                        [["DESKTOP"], ["MOBILE"], ["CTV"], ["DESKTOP", "MOBILE"]],
                        {},
                        "Test device targeting combinations"
                    ),
                    VariationRule(
                        "line_items.0.bid_cpm",
                        "range",
                        [20.0, 30.0],  # Use float instead of Decimal
                        {"min": 15.0, "max": 35.0},  # Use float instead of Decimal
                        "Test CPM ranges for optimal awareness"
                    )
                ],
                target_variation_count=6,
                business_constraints={
                    "max_budget": 150000,
                    "min_impressions": 1000000,
                    "required_measurement": ["NIELSEN"]
                },
                performance_goals={
                    "target_ctr": 0.02,
                    "target_completion_rate": 0.75,
                    "target_frequency": 3.5
                }
            ),

            "conversion_mobile_optimized": CampaignTemplate(
                name="Conversion Mobile Optimized",
                description="Conversion campaign optimized for mobile performance",
                profile="CONVERSION",
                base_config={
                    "objective": "CONVERSION",
                    "status": "DRAFT",
                    "currency": "USD",
                    "dsp_partner": "THE_TRADE_DESK",
                    "programmatic_buy_type": "PRIVATE_MARKETPLACE",
                    "content_adjacency_tier": "TIER_2",
                    "attention_metrics_enabled": True,
                    "targeting": {},  # Add targeting at campaign level
                    "line_items": [{
                        "name": "Conversion Mobile LI",
                        "ad_format": "STANDARD_VIDEO",
                        "bid_cpm": 45.0,  # Use float instead of Decimal
                        "pacing_pct": 80,
                        "targeting": {},
                        "creatives": []
                    }]
                },
                variation_rules=[
                    VariationRule(
                        "targeting.device",
                        "enum_rotation",
                        [["MOBILE"], ["MOBILE", "DESKTOP"]],
                        {"required": ["MOBILE"]},
                        "Focus on mobile with optional desktop"
                    ),
                    VariationRule(
                        "line_items.0.bid_cpm",
                        "range",
                        [40.0, 50.0],  # Use float instead of Decimal
                        {"min": 35.0, "max": 55.0},  # Use float instead of Decimal
                        "Test CPM ranges for conversion optimization"
                    ),
                    VariationRule(
                        "line_items.0.pacing_pct",
                        "enum_rotation",
                        [70, 80, 90],
                        {"min": 60, "max": 100},
                        "Test pacing strategies"
                    )
                ],
                target_variation_count=4,
                business_constraints={
                    "max_budget": 75000,
                    "min_impressions": 500000,
                    "required_measurement": ["EDO", "AFFINITY_SOLUTIONS"]
                },
                performance_goals={
                    "target_ctr": 0.05,
                    "target_completion_rate": 0.85,
                    "target_frequency": 2.5
                }
            ),

            "consideration_balanced": CampaignTemplate(
                name="Consideration Balanced",
                description="Balanced consideration campaign with moderate risk",
                profile="CONSIDERATION",
                base_config={
                    "objective": "CONSIDERATION",
                    "status": "DRAFT",
                    "currency": "USD",
                    "dsp_partner": "GOOGLE_DV360",
                    "programmatic_buy_type": "PROGRAMMATIC_PREFERRED",
                    "content_adjacency_tier": "TIER_2",
                    "attention_metrics_enabled": True,
                    "targeting": {},  # Add targeting at campaign level
                    "line_items": [{
                        "name": "Consideration Balanced LI",
                        "ad_format": "STANDARD_VIDEO",
                        "bid_cpm": 35.0,  # Use float instead of Decimal
                        "pacing_pct": 90,
                        "targeting": {},
                        "creatives": []
                    }]
                },
                variation_rules=[
                    VariationRule(
                        "line_items.0.ad_format",
                        "enum_rotation",
                        ["STANDARD_VIDEO", "PAUSE_ADS"],
                        {},
                        "Test video and pause ad formats"
                    ),
                    VariationRule(
                        "targeting.age_range",
                        "enum_rotation",
                        [[25, 34], [35, 44], [45, 54]],
                        {},
                        "Test different age demographics"
                    ),
                    VariationRule(
                        "line_items.0.bid_cpm",
                        "range",
                        [30.0, 40.0],  # Use float instead of Decimal
                        {"min": 25.0, "max": 45.0},  # Use float instead of Decimal
                        "Test moderate CPM ranges"
                    )
                ],
                target_variation_count=5,
                business_constraints={
                    "max_budget": 100000,
                    "min_impressions": 750000,
                    "required_measurement": ["KANTAR"]
                },
                performance_goals={
                    "target_ctr": 0.035,
                    "target_completion_rate": 0.80,
                    "target_frequency": 3.0
                }
            )
        }

    def get_template_metadata(self) -> List[Dict[str, Any]]:
        """Get enhanced template metadata with business context."""
        return [
            {
                "name": template.name,
                "description": template.description,
                "profile": template.profile,
                "variation_count": template.target_variation_count,
                "fields_that_vary": [rule.field_path for rule in template.variation_rules],
                "business_constraints": template.business_constraints,
                "performance_goals": template.performance_goals,
                "estimated_budget_range": self._estimate_budget_range(template)
            }
            for template in self.templates.values()
        ]

    def _estimate_budget_range(self, template: CampaignTemplate) -> Dict[str, float]:
        """Estimate budget range based on template configuration."""
        base_budget = template.base_config.get('budget', 50000)
        variation_count = template.target_variation_count

        # Convert Decimal to float for calculations
        if isinstance(base_budget, Decimal):
            base_budget = float(base_budget)

        return {
            "min": base_budget * 0.8,
            "max": base_budget * variation_count * 1.2,
            "recommended": base_budget * variation_count
        }

    def _deep_copy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deep copy configuration to avoid mutation."""
        return json.loads(json.dumps(config))

    def _set_nested_field(self, obj: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set nested field using dot notation."""
        parts = field_path.split('.')
        current = obj

        # Handle the case where we're setting a top-level field
        if len(parts) == 1:
            obj[parts[0]] = value
            return

        for part in parts[:-1]:
            if part.isdigit():
                if isinstance(current, list) and int(part) < len(current):
                    current = current[int(part)]
                else:
                    # Create the list if it doesn't exist
                    if not isinstance(current, list):
                        current = []
                    while len(current) <= int(part):
                        current.append({})
                    current = current[int(part)]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

        if parts[-1].isdigit():
            if isinstance(current, list):
                while len(current) <= int(parts[-1]):
                    current.append({})
                current[int(parts[-1])] = value
            else:
                current[int(parts[-1])] = value
        else:
            current[parts[-1]] = value
