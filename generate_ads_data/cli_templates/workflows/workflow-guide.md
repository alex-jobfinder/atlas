# Netflix Ads Data Modeling - Complete Workflow Guide

This directory contains **workflow templates and guides** for the streamlined Netflix ads data generation system.

## **What's Here**

### **Core Workflows**
- `field-testing-template.yml` - Test specific fields with auto-generated context
- `database-schema-reference.yml` - Complete database schema with DDL and constraints

### **Documentation**
- `workflow-guide.md` - **This file** - Complete workflow documentation
- `designs.md` - Design approaches and implementation strategies

## **🚀 Enhanced Features**

### **🛡️ Automatic Constraint Handling**
The system now automatically satisfies all database constraints during data generation:
- **Supply funnel constraints**: responses ≥ 90% of requests, eligible ≥ 80% of responses
- **Video progression constraints**: q25 ≥ q50 ≥ q75 ≥ q100
- **Performance bounds**: viewable ≤ impressions, audible ≤ impressions

### **🔒 Safe Division Protection**
All computed fields use the `safe_div()` utility for robust error handling:
- **Zero protection**: No more division by zero errors
- **Consistent defaults**: Returns 0.0 for invalid calculations
- **Runtime safety**: Robust calculation of rates and percentages

## **Workflow Types**

### **1. Complete Examples Workflow**
```bash
# Generate complete Netflix ads example with performance data
python cli.py create-example --template examples/netflix-ads-examples.yml --example luxury_auto_awareness
```

**What it does:**
- Creates complete entity hierarchy (advertiser → campaign → line items → creatives)
- Uses smart defaults for missing fields
- Generates performance data automatically
- **Automatically satisfies all database constraints** ✅
- **Uses safe division for all calculated fields** ✅
- Returns complete example ready for database modeling

### **2. Field Testing Workflow**
```bash
# Test specific fields while auto-generating realistic context
python cli.py test-fields --template workflows/field-testing-template.yml --focus "campaign.target_cpm,line_items.targeting_json"
```

**What it does:**
- Uses your test field values
- Generates realistic context with faker
- Creates complete Netflix ads example
- Generates performance data
- **Ensures constraint compliance** with new field values ✅
- Focuses on your specific test fields

### **3. Profile-Based Workflow**
```bash
# Use pre-built profiles for common testing scenarios
python cli.py create-profile --name high_cpm_tv_awareness --test-fields "campaign.target_cpm=2000"
```

**What it does:**
- Uses pre-built profile with smart defaults
- Applies your test field overrides
- Auto-generates missing data with faker
- Creates complete example with performance data
- **Maintains constraint relationships** across all generated data ✅

## **Template Structure**

### **Examples Template** (`examples/netflix-ads-examples.yml`)
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

    # New: Constraint-aware generation
    constraint_handling:
      supply_funnel: true
      video_progression: true
      performance_bounds: true
```

### **Field Testing Template** (`workflows/field-testing-template.yml`)
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

# New: Enhanced constraint handling
constraint_handling:
  supply_funnel: true                    # Ensure supply funnel constraints
  video_progression: true                # Ensure video quartile ordering
  performance_bounds: true               # Ensure performance metric bounds
  safe_division: true                    # Use safe division for all calculations
```

### **Campaign Profiles Template** (`profiles/campaign-profiles.yml`)
```yaml
profiles:
  [profile_name]:
    description: "Profile description"
    base_template: "base_template_name"
    focus: "Fields this profile focuses on"

    test_values: {...}
    faker_auto: [...]
    performance: {...}

    # New: Constraint-aware generation
    constraints:
      supply_funnel: true
      video_progression: true
      performance_bounds: true

base_templates:
  [base_name]: {...}
```

## **🛡️ Constraint Handling Examples**

### **Supply Funnel Constraints**
```python
# Automatically satisfied during data generation
requests = 1000
responses = max(900, int(1000 * random_factor))      # ≥ 90% of requests
eligible = max(720, int(responses * random_factor))   # ≥ 80% of responses
auctions = max(576, int(eligible * random_factor))   # ≥ 80% of eligible
```

### **Video Progression Constraints**
```python
# Automatically ordered during generation
video_starts = 800
video_q25 = min(700, int(video_starts * random_factor))    # ≤ video_starts
video_q50 = min(600, video_q25)                            # ≤ q25
video_q75 = min(500, video_q50)                            # ≤ q50
video_q100 = min(400, video_q75)                           # ≤ q75
```

### **Safe Division Examples**
```python
# All computed fields use safe division
@computed_field
@property
def viewability_rate(self) -> float:
    return safe_div(self.viewable_impressions, self.impressions)

@computed_field
@property
def completion_rate(self) -> float:
    return safe_div(self.video_q100, self.video_starts)

@computed_field
@property
def effective_cpm(self) -> int:
    return int(safe_div(self.spend * 1000, self.impressions))
```

## **🚀 Complete Data Generation**

### **Run All Examples and Profiles**
```bash
# Generate everything in one command
./run_all.sh

# This creates:
# ✅ 3 Complete Examples (Luxury Auto, Crunchy Snacks, NexBank)
# ✅ 4 Campaign Profiles (High CPM, Mobile, Interactive, Multi-device)
# ✅ Performance data for all campaigns (basic + extended)
# ✅ All database constraints automatically satisfied
# ✅ Safe division handling for all calculations
# ✅ ~34MB SQLite database with realistic Netflix ads data
```

### **Individual Example Generation**
```bash
# Create specific examples
python cli.py create-example --template examples/netflix-ads-examples.yml --example luxury_auto_awareness
python cli.py create-example --template examples/netflix-ads-examples.yml --example crunchy_snacks_consideration
python cli.py create-example --template examples/netflix-ads-examples.yml --example nexbank_conversion

# Create specific profiles
python cli.py create-profile --name high_cpm_tv_awareness
python cli.py create-profile --name mobile_consideration
python cli.py create-profile --name conversion_interactive
python cli.py create-profile --name multi_device_advanced
```

## **🔧 Development Workflows**

### **Testing and Validation**
```bash
# Run all tests
make test

# Run specific test file
make test-one FILE=tests/test_flows_v1.py

# Test specific functionality
python -c "from services.performance_ext import ExtendedPerformanceMetrics; print('Import successful')"
```

### **Database Management**
```bash
# Initialize database
make init-db

# Clean artifacts
make clean

# Setup dependencies
make deps
```

## **📊 Performance Data Generation**

### **Smart Architecture**
- **Single data generation point** - All performance data generated in one place
- **Zero duplication** - Shared utilities and smart calculation
- **Constraint-aware** - All database constraints automatically satisfied
- **Safe calculation** - Robust error handling for all computed fields

### **Data Quality Features**
- **Realistic ranges** - Performance metrics follow Netflix ads patterns
- **Temporal factors** - Hour-of-day, day-of-week, seasonal variations
- **Supply funnel** - Realistic ad serving pipeline simulation
- **Video progression** - Proper quartile ordering and completion tracking

## **🎯 Best Practices**

### **When Testing Fields**
1. **Use constraint-aware generation** - Ensure new values maintain relationships
2. **Leverage safe division** - All calculated fields handle edge cases automatically
3. **Test realistic scenarios** - Use values within expected ranges
4. **Validate constraints** - Check that generated data satisfies all relationships

### **When Creating Profiles**
1. **Follow naming conventions** - Use descriptive profile names
2. **Include constraint handling** - Enable automatic constraint satisfaction
3. **Test performance generation** - Ensure realistic data generation
4. **Document use cases** - Clear description of when to use each profile

### **When Extending Examples**
1. **Maintain relationships** - Keep entity hierarchies consistent
2. **Use registry pattern** - Access all components through centralized registry
3. **Leverage utilities** - Use shared functions for common operations
4. **Test constraints** - Verify that new examples satisfy all database constraints

## **🚀 Next Steps**

1. **Try complete generation** - Run `./run_all.sh` to see the full system in action
2. **Test field variations** - Use field testing workflow for specific scenarios
3. **Create custom profiles** - Build profiles for your specific use cases
4. **Extend examples** - Add new examples following the established patterns
5. **Leverage constraints** - Use automatic constraint handling for complex scenarios

This workflow approach gives you **comprehensive testing capabilities** while maintaining realistic Netflix ads data context. The enhanced constraint handling and safe division features ensure robust, production-ready data generation for effective database modeling and development.
