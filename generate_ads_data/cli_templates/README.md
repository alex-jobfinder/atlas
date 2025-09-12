# Netflix Ads Data Modeling - Streamlined Templates

This directory contains **streamlined templates** that replace the complex multi-command workflow with simple, template-driven examples for Netflix ads data modeling.

## **Directory Structure**

```
cli_templates/
├── README.md                    # This file - Main overview
├── README-streamlined.md        # Detailed streamlined approach guide
├── examples/                    # Complete example templates
│   ├── README.md               # Examples directory guide
│   └── netflix-ads-examples.yml # Pre-built Netflix ads examples
├── workflows/                   # Workflow templates and guides
│   ├── README.md               # Workflows directory guide
│   ├── workflow-guide.md       # Complete workflow documentation
│   ├── field-testing-template.yml # Field testing workflow
│   ├── database-schema-reference.yml # Database schema reference
│   └── designs.md              # Design approaches and strategies
└── profiles/                    # Campaign profile templates
    ├── README.md               # Profiles directory guide
    └── campaign-profiles.yml   # Pre-built campaign profiles
```

## **What This Solves**

**Old Problem**: Creating realistic Netflix ads data required 4+ CLI commands and manual entity management.

**New Solution**: Single templates that automatically generate complete examples with performance data.

## **Quick Start**

### **1. Create Complete Example**
```bash
python cli.py create-example --template examples/netflix-ads-examples.yml --example luxury_auto_awareness
```

### **2. Test Specific Fields**
```bash
python cli.py test-fields --template workflows/field-testing-template.yml --focus "campaign.target_cpm"
```

### **3. Use Pre-built Profile**
```bash
python cli.py create-profile --name high_cpm_tv_awareness
```

## **Key Features**

✅ **Smart defaults** based on your existing examples
✅ **Automatic faker generation** for missing fields
✅ **Field-specific testing** without rebuilding everything
✅ **Auto-performance generation** when examples are complete
✅ **Template inheritance** for consistent patterns
✅ **Realistic Netflix ads data** for database modeling

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
python cli.py create-example --template examples/netflix-ads-examples.yml --example luxury_auto_awareness
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
