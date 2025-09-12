# Examples Directory

This directory contains **complete example templates** for Netflix ads data generation.

## **What's Here**

### **Netflix Ads Examples** (`netflix-ads-examples.yml`)
Pre-built examples based on your existing `config.yml` with smart defaults and auto-generation.

**Examples included:**
- `luxury_auto_awareness`: High-end TV drama awareness campaign
- `crunchy_snacks_consideration`: Mobile comedy consideration campaign
- `nexbank_conversion`: Mobile banking conversion campaign

## **Usage**

### **Create Complete Example**
```bash
python cli.py create-example --template examples/netflix-ads-examples.yml --example luxury_auto_awareness
```

**What this does:**
1. Creates complete entity hierarchy (advertiser → campaign → line items → creatives)
2. Uses smart defaults for missing fields
3. Generates performance data automatically
4. Returns complete example ready for database modeling

## **Example Structure**

```yaml
examples:
  luxury_auto_awareness:
    description: "High-end TV drama awareness campaign"
    strategy: "Target premium drama/documentaries; 30s cinematic"
    results: "+22% brand consideration; 3.5x engagement"

    advertiser:
      name: "Luxury Auto Co"
      contact_email: "ads@luxauto.com"
      brand: "LuxAuto"
      agency_name: "Vision Media"

    campaign:
      name: "EV Awareness Launch"
      objective: "AWARENESS"
      target_cpm: 15.50
      budget: 120000.00

    line_items:
      - name: "EV Cinematic 30s"
        ad_format: "STANDARD_VIDEO"
        targeting_json: '{"DEVICE": ["TV"], "CONTENT_GENRE": ["DRAMA"]}'

    performance:
      generate: true
      type: "both"
      seed: 42
      hours: 168
```

## **When to Use**

Use these examples when you need to:
- **Generate complete Netflix ads data** for database modeling
- **Test end-to-end workflows** with realistic data
- **Create consistent examples** for documentation
- **Understand entity relationships** in context

## **Customization**

You can customize these examples by:
1. **Modifying values** in the template
2. **Adding new examples** following the same structure
3. **Overriding specific fields** using the field testing workflow
4. **Extending with new entities** as needed

## **Next Steps**

1. **Try the examples**: Start with `luxury_auto_awareness`
2. **Customize values**: Modify CPM, targeting, or creative specs
3. **Add new examples**: Create examples for your specific use cases
4. **Use field testing**: Test specific variations while keeping context
