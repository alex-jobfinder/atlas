"""
Streamlined processor for Netflix ads data generation.
Implements template-driven workflows with smart defaults and auto-generation.
"""

from typing import Any, Dict, List

import yaml

from db_utils import generate_hourly_performance, get_logger, persist_advertiser, persist_campaign
from factories.faker_providers import seed_all
from models.registry import registry


class StreamlinedProcessor:
    """Processes streamlined templates to create Netflix ads data examples."""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.faker_seed = None

    def create_example_from_template(
        self, template_path: str, example_name: str, performance_only: bool = False
    ) -> Dict[str, Any]:
        """Create complete example from template with auto-performance generation."""
        try:
            # Load template
            template = self._load_template(template_path)

            if example_name not in template.get("examples", {}):
                raise ValueError(f"Example '{example_name}' not found in template")

            example = template["examples"][example_name]

            if performance_only:
                return self._generate_performance_only(example)
            else:
                return self._create_complete_example(example, template)

        except Exception as e:
            self.logger.error(f"Failed to create example: {e}")
            raise

    def test_specific_fields(
        self, template_path: str, focus_fields: List[str], auto_performance: bool = True
    ) -> Dict[str, Any]:
        """Test specific fields while auto-generating realistic context."""
        try:
            # Load template
            template = self._load_template(template_path)

            # Extract test fields
            test_fields = template.get("test_fields", {})

            # Create example with test fields and auto-generated context
            result = self._create_example_with_test_fields(test_fields, focus_fields, template)

            # Auto-generate performance if requested
            if auto_performance and result.get("campaign_id"):
                self._auto_generate_performance(result["campaign_id"], template.get("performance", {}))

            return result

        except Exception as e:
            self.logger.error(f"Failed to test fields: {e}")
            raise

    def create_campaign_from_profile(
        self, profile_name: str, override_fields: Dict[str, str], performance_only: bool = False
    ) -> Dict[str, Any]:
        """Create campaign from pre-built profile with smart defaults."""
        try:
            # Load profiles template
            template_path = "cli_templates/profiles/campaign-profiles.yml"
            template = self._load_template(template_path)

            if profile_name not in template.get("profiles", {}):
                raise ValueError(f"Profile '{profile_name}' not found in template")

            profile = template["profiles"][profile_name]

            # Apply base template
            base_template_name = profile.get("base_template")
            if base_template_name:
                base_template = template.get("base_templates", {}).get(base_template_name, {})
                profile = self._merge_templates(base_template, profile)

            # Apply test values
            test_values = profile.get("test_values", {})
            profile = self._merge_templates(profile, {"test_values": test_values})

            # Apply field overrides
            if override_fields:
                profile = self._apply_field_overrides(profile, override_fields)

            if performance_only:
                return self._generate_performance_only(profile)
            else:
                return self._create_complete_example(profile, template)

        except Exception as e:
            self.logger.error(f"Failed to create profile: {e}")
            raise

    def test_prebuilt_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Test pre-built scenario with one command."""
        try:
            # Load scenarios template
            template_path = "cli_templates/testing-scenarios.yml"
            template = self._load_template(template_path)

            if scenario_name not in template.get("scenarios", {}):
                raise ValueError(f"Scenario '{scenario_name}' not found in template")

            scenario = template["scenarios"][scenario_name]

            # Create example from scenario
            return self._create_example_from_scenario(scenario, template)

        except Exception as e:
            self.logger.error(f"Failed to test scenario: {e}")
            raise

    def _load_template(self, template_path: str) -> Dict[str, Any]:
        """Load and parse YAML template."""
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found: {template_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in template: {e}")

    def _create_complete_example(self, example: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """Create complete example with all entities."""
        try:
            # Set faker seed if specified
            if self.faker_seed is not None:
                seed_all(self.faker_seed)

            # Create advertiser
            advertiser_data = example.get("advertiser", {})
            advertiser_id = self._create_advertiser(advertiser_data)

            # Create campaign
            campaign_data = example.get("campaign", {})
            campaign_id = self._create_campaign(advertiser_id, campaign_data)

            # Create line items and creatives
            line_items_data = example.get("line_items", [])
            line_item_ids = self._create_line_items(campaign_id, line_items_data)

            # Auto-generate performance if configured
            performance_config = example.get("performance", {})
            if performance_config.get("generate", False):
                self._auto_generate_performance(campaign_id, performance_config)

            return {
                "advertiser_id": advertiser_id,
                "campaign_id": campaign_id,
                "line_item_ids": line_item_ids,
                "status": "created",
                "message": "Complete example created successfully",
            }

        except Exception as e:
            self.logger.error(f"Failed to create complete example: {e}")
            raise

    def _create_advertiser(self, advertiser_data: Dict[str, Any]) -> int:
        """Create advertiser from data."""
        try:
            # Use faker to fill missing fields
            advertiser_data = self._fill_missing_advertiser_fields(advertiser_data)

            # Create advertiser
            payload = registry.AdvertiserCreate(**advertiser_data)
            advertiser_id = persist_advertiser(payload)

            self.logger.info(f"Created advertiser: {advertiser_data.get('name')} (ID: {advertiser_id})")
            return advertiser_id

        except Exception as e:
            self.logger.error(f"Failed to create advertiser: {e}")
            raise

    def _create_campaign(self, advertiser_id: int, campaign_data: Dict[str, Any]) -> int:
        """Create campaign from data."""
        try:
            # Use faker to fill missing fields
            campaign_data = self._fill_missing_campaign_fields(campaign_data)

            # Create campaign using existing logic
            from db_utils import build_auto_campaign

            campaign = build_auto_campaign(advertiser_id, campaign_data.get("objective"))

            # Override with template data
            if "name" in campaign_data:
                campaign.name = campaign_data["name"]

            # Handle CPM conversion properly
            if "target_cpm" in campaign_data:
                # Values are already in USD, just ensure it's a Decimal
                from decimal import Decimal

                campaign.target_cpm = Decimal(str(campaign_data["target_cpm"]))

            # Persist campaign
            result = persist_campaign(advertiser_id, campaign, return_ids=True)
            campaign_id = result.get("campaign_id")

            self.logger.info(f"Created campaign: {campaign_data.get('name')} (ID: {campaign_id})")
            return campaign_id

        except Exception as e:
            self.logger.error(f"Failed to create campaign: {e}")
            raise

    def _create_line_items(self, campaign_id: int, line_items_data: List[Dict[str, Any]]) -> List[int]:
        """Create line items and creatives from data."""
        line_item_ids = []

        try:
            for line_item_data in line_items_data:
                # Use faker to fill missing fields
                line_item_data = self._fill_missing_line_item_fields(line_item_data)

                # Create line item (simplified - would need full implementation)
                line_item_id = self._create_single_line_item(campaign_id, line_item_data)
                line_item_ids.append(line_item_id)

                # Create creatives
                creatives_data = line_item_data.get("creatives", [])
                for creative_data in creatives_data:
                    creative_data = self._fill_missing_creative_fields(creative_data)
                    self._create_single_creative(line_item_id, creative_data)

            return line_item_ids

        except Exception as e:
            self.logger.error(f"Failed to create line items: {e}")
            raise

    def _create_single_line_item(self, campaign_id: int, line_item_data: Dict[str, Any]) -> int:
        """Create a single line item (placeholder implementation)."""
        # This would need to be implemented with proper line item creation logic
        # For now, return a placeholder ID
        self.logger.info(f"Creating line item: {line_item_data.get('name')}")
        return 1  # Placeholder

    def _create_single_creative(self, line_item_id: int, creative_data: Dict[str, Any]) -> int:
        """Create a single creative (placeholder implementation)."""
        # This would need to be implemented with proper creative creation logic
        # For now, just log
        self.logger.info(f"Creating creative: {creative_data.get('name')}")
        return 1  # Placeholder

    def _auto_generate_performance(self, campaign_id: int, performance_config: Dict[str, Any]) -> None:
        """Auto-generate performance data for campaign."""
        try:
            performance_type = performance_config.get("type", "normal")
            seed = performance_config.get("seed", self.faker_seed)
            # Default: 1 week (168 hours)

            if performance_type in ["normal", "both"]:
                rows = generate_hourly_performance(campaign_id, seed=seed, replace=True)
                self.logger.info(f"Generated {rows} normal performance rows for campaign {campaign_id}")

            if performance_type in ["extended", "both"]:
                from services.performance_ext import generate_hourly_performance_ext

                rows = generate_hourly_performance_ext(campaign_id, seed=seed, replace=True)
                self.logger.info(f"Generated {rows} extended performance rows for campaign {campaign_id}")

        except Exception as e:
            self.logger.error(f"Failed to generate performance: {e}")
            # Don't raise - performance generation failure shouldn't fail the whole process

    def _fill_missing_advertiser_fields(self, advertiser_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing advertiser fields with faker data."""
        from factories.faker_providers import fake_advertiser

        if not advertiser_data.get("name"):
            name, email, brand, agency = fake_advertiser()
            advertiser_data.setdefault("name", name)
            advertiser_data.setdefault("contact_email", email)
            advertiser_data.setdefault("brand", brand)
            advertiser_data.setdefault("agency_name", agency)

        return advertiser_data

    def _fill_missing_campaign_fields(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing campaign fields with defaults."""
        campaign_data.setdefault("status", "ACTIVE")
        campaign_data.setdefault("dsp_partner", "DV360")
        campaign_data.setdefault("currency", "USD")
        campaign_data.setdefault("budget_type", "LIFETIME")

        return campaign_data

    def _fill_missing_line_item_fields(self, line_item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing line item fields with defaults."""
        line_item_data.setdefault("ad_format", "STANDARD_VIDEO")
        line_item_data.setdefault("pacing_pct", 100)
        line_item_data.setdefault("ad_server_type", "VAST_TAG")
        line_item_data.setdefault("pixel_vendor", "IAS")

        return line_item_data

    def _fill_missing_creative_fields(self, creative_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing creative fields with defaults."""
        creative_data.setdefault("mime_type", "VIDEO/MP4")
        creative_data.setdefault("qa_status", "APPROVED")
        creative_data.setdefault("placement", "MID_ROLL")
        creative_data.setdefault("aspect_ratio", "R16_9")
        creative_data.setdefault("frame_rate", "30")

        return creative_data

    def _merge_templates(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge override template into base template."""
        result = base.copy()
        result.update(override)
        return result

    def _apply_field_overrides(self, template: Dict[str, Any], overrides: Dict[str, str]) -> Dict[str, Any]:
        """Apply field overrides to template."""
        # This would need more sophisticated field path resolution
        # For now, just update top-level fields
        result = template.copy()
        result.update(overrides)
        return result

    def _create_example_with_test_fields(
        self, test_fields: Dict[str, Any], focus_fields: List[str], template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create example focusing on test fields with auto-generated context."""
        # Implementation would combine test fields with auto-generated context
        # For now, return a placeholder
        return {
            "status": "test_fields_processed",
            "focus_fields": focus_fields,
            "message": "Field testing template processed (implementation needed)",
        }

    def _create_example_from_scenario(self, scenario: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
        """Create example from pre-built scenario."""
        # Implementation would process scenario template
        # For now, return a placeholder
        return {
            "status": "scenario_processed",
            "scenario": scenario.get("description", "Unknown scenario"),
            "message": "Scenario template processed (implementation needed)",
        }

    def _generate_performance_only(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """Generate only performance data for existing entities."""
        # Implementation would find existing entities and generate performance
        # For now, return a placeholder
        return {
            "status": "performance_only",
            "message": "Performance-only generation requested (implementation needed)",
        }


# Convenience functions for CLI commands
def create_example_from_template(
    template_path: str, example_name: str, performance_only: bool = False
) -> Dict[str, Any]:
    """Create complete example from template."""
    processor = StreamlinedProcessor()
    return processor.create_example_from_template(template_path, example_name, performance_only)


def test_specific_fields(template_path: str, focus_fields: List[str], auto_performance: bool = True) -> Dict[str, Any]:
    """Test specific fields while auto-generating realistic context."""
    processor = StreamlinedProcessor()
    return processor.test_specific_fields(template_path, focus_fields, auto_performance)


def create_campaign_from_profile(
    profile_name: str, override_fields: Dict[str, str], performance_only: bool = False
) -> Dict[str, Any]:
    """Create campaign from pre-built profile."""
    processor = StreamlinedProcessor()
    return processor.create_campaign_from_profile(profile_name, override_fields, performance_only)


def test_prebuilt_scenario(scenario_name: str) -> Dict[str, Any]:
    """Test pre-built scenario."""
    processor = StreamlinedProcessor()
    return processor.test_prebuilt_scenario(scenario_name)
