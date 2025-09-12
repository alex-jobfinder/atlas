# Netflix Ads Data Modeling - Streamlined Templates

This directory contains **streamlined templates** that replace the complex multi-command workflow with simple, template-driven examples for Netflix ads data modeling.

## **What This Solves**

**Old Problem**: Creating realistic Netflix ads data required 4+ CLI commands and manual entity management.

**New Solution**: Single templates that automatically generate complete examples with performance data.

## **Template Types**

### **1. Complete Examples** (`netflix-ads-examples.yml`)
Pre-built examples based on your existing `config.yml` with smart defaults and auto-generation.

**Examples included:**
- `luxury_auto_awareness`: High-end TV drama awareness campaign
- `crunchy_snacks_consideration`: Mobile comedy consideration campaign
- `nexbank_conversion`: Mobile banking conversion campaign

**Usage:**
```bash
python cli.py create-example --template netflix-ads-examples.yml --example luxury_auto_awareness
```

### **2. Field Testing** (`field-testing-template.yml`)
Test specific fields while automatically generating realistic context around them.

**Perfect for:**
- Testing different CPM values
- Testing targeting variations
- Testing creative specifications
- Testing budget scenarios

**Usage:**
```bash
python cli.py test-fields --template field-testing-template.yml --focus "campaign.target_cpm,line_items.targeting_json"
```

### **3. Campaign Profiles** (`campaign-profiles.yml`)
Pre-built profiles for common Netflix ads testing scenarios.

**Profiles included:**
- `high_cpm_tv_awareness`: Test high CPM TV campaigns
- `mobile_consideration`: Test mobile consideration campaigns
- `conversion_interactive`: Test interactive conversion campaigns
- `multi_device_advanced`: Test advanced multi-device targeting

**Usage:**
```bash
python cli.py create-profile --name high_cpm_tv_awareness
```

## **Key Features**

### **Smart Defaults**
- **Realistic values** that work together
- **Netflix ads best practices** built-in
- **Industry-specific patterns** (auto, tech, consumer goods)

### **Automatic Faker Generation**
- **Missing fields** automatically filled with realistic data
- **Consistent relationships** between entities
- **Reproducible generation** with seed control

### **Field-Specific Testing**
- **Override only what you want to test**
- **Everything else auto-generated**
- **Realistic context** around your test fields

### **Auto-Performance Generation**
- **Performance data** automatically created when examples are complete
- **Both normal and extended** metrics
- **Configurable time periods** and seeds

## **Quick Start**

### **1. Create Complete Example**
```bash
# Generate luxury auto example with performance data
python cli.py create-example --template netflix-ads-examples.yml --example luxury_auto_awareness
```

### **2. Test Specific Fields**
```bash
# Test higher CPM while keeping everything else realistic
python cli.py test-fields --template field-testing-template.yml --focus "campaign.target_cpm"
```

### **3. Use Pre-built Profile**
```bash
# Use high CPM profile for testing
python cli.py create-profile --name high_cpm_tv_awareness
```

## **Template Structure**

### **Examples Template**
```yaml
examples:
  [example_name]:
    description: "What this example demonstrates"
    strategy: "Campaign strategy notes"
    results: "Expected results"

    advertiser: {...}
    campaign: {...}
    line_items: [...]
    performance: {...}
```

### **Field Testing Template**
```yaml
test_scenario: "Description of what you're testing"

test_fields:
  campaign: {...}
  line_items: [...]
  creatives: [...]

auto_generate: {...}
smart_defaults: {...}
faker_config: {...}
performance: {...}
```

### **Campaign Profiles Template**
```yaml
profiles:
  [profile_name]:
    description: "Profile description"
    base_template: "base_template_name"
    focus: "Fields this profile focuses on"

    test_values: {...}
    faker_auto: [...]
    performance: {...}

base_templates:
  [base_name]: {...}
```

## **Migration from Old Commands**

### **Old Workflow (4+ commands):**
```bash
# 1. Create advertiser
python cli.py create-advertiser --auto

# 2. Create campaign
python cli.py create-campaign --advertiser-id 1 --auto --profile AWARENESS

# 3. Generate performance
python cli.py generate-performance --campaign-id 1 --replace

# 4. Generate extended performance
python cli.py generate-performance-ext --campaign-id 1 --replace
```

### **New Workflow (1 command):**
```bash
# Single command creates everything
python cli.py create-example --template netflix-ads-examples.yml --example luxury_auto_awareness

# Or test specific fields
python cli.py test-fields --template field-testing-template.yml --focus "campaign.target_cpm"
```

## **Benefits**

1. **Single command** instead of 4+ commands
2. **Smart defaults** ensure realistic Netflix ads data
3. **Automatic faker generation** fills in missing pieces
4. **Field-specific testing** without rebuilding everything
5. **Template-driven** for consistency and reusability
6. **Auto-performance** generation when examples are complete
7. **Realistic context** around your test fields

## **Use Cases**

### **Database Modeling**
- Generate realistic Netflix ads data examples
- Test different campaign configurations
- Understand entity relationships
- Model performance patterns

### **Testing & Development**
- Test specific field variations
- Validate data constraints
- Test performance generation
- Debug entity relationships

### **Documentation & Examples**
- Create consistent examples
- Document best practices
- Share campaign patterns
- Train team members

## **Next Steps**

1. **Try the examples**: Start with `luxury_auto_awareness`
2. **Test specific fields**: Use field testing template
3. **Create custom profiles**: Build your own testing scenarios
4. **Extend templates**: Add more examples and patterns

This streamlined approach gives you **realistic Netflix ads data examples** quickly for database modeling, with the ability to test specific fields while everything else is automatically generated with smart defaults and faker data.
