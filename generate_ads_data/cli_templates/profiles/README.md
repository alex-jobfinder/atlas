# Profiles Directory

This directory contains **pre-built campaign profile templates** for common Netflix ads testing scenarios.

## **What's Here**

### **Campaign Profiles** (`campaign-profiles.yml`)
Pre-built profiles for common Netflix ads testing scenarios with smart defaults and template inheritance.

**Profiles included:**
- `high_cpm_tv_awareness`: Test high CPM TV awareness campaigns
- `mobile_consideration`: Test mobile consideration campaigns
- `conversion_interactive`: Test interactive conversion campaigns
- `multi_device_advanced`: Test advanced multi-device targeting

## **Usage**

### **Use Pre-built Profile**
```bash
python cli.py create-profile --name high_cpm_tv_awareness
```

### **Override Specific Fields**
```bash
python cli.py create-profile --name high_cpm_tv_awareness --test-fields "campaign.target_cpm=2000,campaign.budget=150000"
```

## **Profile Structure**

```yaml
profiles:
  high_cpm_tv_awareness:
    description: "Test high CPM TV awareness campaign performance (Luxury Auto pattern)"
    base_template: "awareness_campaign"
    focus: "campaign.target_cpm, campaign.budget, line_items.targeting_json"

    test_values:
      advertiser:
        name: "Luxury Auto Co"
        brand: "LuxAuto"
        industry: "automotive"

      campaign:
        target_cpm: 20.00              # Test: Very high CPM ($20.00)
        budget: 150000.00              # Test: Large budget ($150k)
        objective: "AWARENESS"

      line_items:
        - targeting_json: '{"DEVICE": ["TV"], "CONTENT_GENRE": ["DRAMA", "DOCUMENTARY"]}'
          ad_format: "STANDARD_VIDEO"
          bid_cpm: 20.00               # Match campaign target

    faker_auto:
      - "campaign.flight_dates"
      - "line_items.duration_seconds"
      - "creatives.video_specs"

    performance:
      generate: true
      type: "both"
      seed: 42
      hours: 168
```

## **Base Templates**

Profiles inherit from base templates that provide common defaults:

### **Awareness Campaign Base**
```yaml
base_templates:
  awareness_campaign:
    campaign:
      objective: "AWARENESS"
      status: "ACTIVE"
      dsp_partner: "DV360"
      budget_type: "LIFETIME"
      currency: "USD"

    line_items:
      - ad_format: "STANDARD_VIDEO"
        pacing_pct: 100
        ad_server_type: "VAST_TAG"
        pixel_vendor: "IAS"

    creatives:
      - mime_type: "VIDEO/MP4"
        qa_status: "APPROVED"
        aspect_ratio: "R16_9"
        frame_rate: "30"
```

## **When to Use**

### **Use Profiles When You Need To:**
- **Test common scenarios** with pre-built configurations
- **Ensure consistency** across similar test cases
- **Leverage smart defaults** for Netflix ads best practices
- **Quickly prototype** different campaign types
- **Maintain standardized** testing patterns

### **Profile Types Available:**

1. **High CPM TV Awareness** - Test premium TV campaign performance
2. **Mobile Consideration** - Test mobile-focused consideration campaigns
3. **Conversion Interactive** - Test interactive conversion campaigns
4. **Multi-Device Advanced** - Test complex multi-device targeting

## **Benefits**

✅ **Pre-built configurations** for common scenarios
✅ **Template inheritance** with smart defaults
✅ **Consistent patterns** across all profiles
✅ **Quick testing** of specific variations
✅ **Netflix ads best practices** built-in
✅ **Easy customization** with field overrides

## **Customization**

You can customize profiles by:
1. **Overriding specific fields** using `--test-fields` parameter
2. **Modifying base templates** for new campaign types
3. **Adding new profiles** following the same structure
4. **Extending with new test scenarios** as needed

## **Next Steps**

1. **Try existing profiles**: Start with `high_cpm_tv_awareness`
2. **Override fields**: Test different CPM or budget values
3. **Create custom profiles**: Build profiles for your specific needs
4. **Extend base templates**: Add new campaign type defaults

This profile approach gives you **standardized testing scenarios** with the flexibility to customize specific fields while maintaining realistic Netflix ads data context.
