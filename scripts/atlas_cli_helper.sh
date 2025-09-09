#!/bin/bash
# Atlas CLI Helper Script - Complete Documentation and Examples
# Usage: ./scripts/atlas_cli_helper.sh [command] [options]
#
# =============================================================================
# ATLAS CLI HELPER SCRIPT
# =============================================================================
#
# This script provides comprehensive documentation and examples for using
# Atlas CLI tools directly instead of templates.
#
# COMMANDS:
#   help          - Show this help message
#   graph         - Show LocalGraphRunner examples
#   alert         - Show LocalAlertRunner examples
#   run-graph     - Run LocalGraphRunner with provided options
#   run-alert     - Run LocalAlertRunner with provided options
#   list-templates - List available templates
#   show-template - Show template content
#
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Print colored output
print_header() {
    echo -e "${WHITE}==============================================================================${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${WHITE}==============================================================================${NC}"
}

print_section() {
    echo -e "${CYAN}$1${NC}"
}

print_example() {
    echo -e "${GREEN}$1${NC}"
}

print_note() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Show help
show_help() {
    print_header "ATLAS CLI HELPER SCRIPT"
    echo ""
    echo "This script provides comprehensive documentation and examples for using"
    echo "Atlas CLI tools directly instead of templates."
    echo ""
    echo "COMMANDS:"
    echo "  help          - Show this help message"
    echo "  graph         - Show LocalGraphRunner examples and options"
    echo "  alert         - Show LocalAlertRunner examples and options"
    echo "  run-graph     - Run LocalGraphRunner with provided options"
    echo "  run-alert     - Run LocalAlertRunner with provided options"
    echo "  list-templates - List available templates"
    echo "  show-template - Show template content"
    echo ""
    echo "EXAMPLES:"
    echo "  ./scripts/atlas_cli_helper.sh help"
    echo "  ./scripts/atlas_cli_helper.sh graph"
    echo "  ./scripts/atlas_cli_helper.sh alert"
    echo "  ./scripts/atlas_cli_helper.sh list-templates"
    echo "  ./scripts/atlas_cli_helper.sh show-template line"
    echo ""
}

# Show LocalGraphRunner documentation
show_graph_docs() {
    print_header "LOCALGRAPH RUNNER CLI DOCUMENTATION"
    
    print_section "🎯 Basic Command Structure:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalGraphRunner [OPTIONS]\""
    echo ""
    
    print_section "📋 Available Options:"
    echo "--preset <name>           # Database preset (sps, alert, etc.)"
    echo "--q \"<aql_expression>\"    # Atlas Query Language expression"
    echo "--style <style>           # Graph style (line, area, stack, etc.)"
    echo "--s <start_time>          # Start time (e.g., e-1w)"
    echo "--e <end_time>            # End time (e.g., 2012-01-01T00:00)"
    echo "--tz <timezone>           # Timezone (e.g., UTC)"
    echo "--theme <theme>           # Theme (light, dark)"
    echo "--w <width>               # Chart width (e.g., 700)"
    echo "--h <height>              # Chart height (e.g., 300)"
    echo "--out <file>              # Output PNG file"
    echo "--emit-v2 <file>          # Export V2 JSON (optional)"
    echo "--save-template <file>    # Save args template (optional)"
    echo ""
    
    print_section "🎨 Graph Styles Available:"
    echo "• line        - Basic line chart"
    echo "• area        - Filled area chart"
    echo "• stack       - Stacked area chart"
    echo "• heatmap     - Heatmap visualization"
    echo "• vspan       - Vertical span highlighting"
    echo "• combination - Combined styles"
    echo "• layering    - Layered visualizations"
    echo ""
    
    print_section "📊 Example Commands:"
    
    print_example "1. Basic Line Chart:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalGraphRunner --preset sps --q 'name,sps,:eq,(,nf.cluster,),:by' --style line --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/my_chart.png\""
    echo ""
    
    print_example "2. Area Chart with Alert Visualization:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalGraphRunner --preset sps --q 'name,sps,:eq,(,nf.cluster,),:by,:sum,50e3,:2over,:gt,:vspan,40,:alpha,triggered,:legend,:rot,name,sps,:eq,(,nf.cluster,),:by,:area,input,:legend,:rot,50e3,:const,threshold,:legend,:rot' --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/my_area_with_alert.png\""
    echo ""
    
    print_example "3. Stack Chart:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalGraphRunner --preset sps --q 'name,sps,:eq,(,nf.cluster,),:by,:stack' --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/my_stack.png\""
    echo ""
    
    print_example "4. Heatmap:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalGraphRunner --preset sps --q 'name,sps,:eq,(,nf.cluster,),:by,:heatmap' --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/my_heatmap.png\""
    echo ""
    
    print_section "🔧 AQL Expression Examples:"
    echo "• Basic query: name,sps,:eq,(,nf.cluster,),:by"
    echo "• With sum: name,sps,:eq,(,nf.cluster,),:by,:sum"
    echo "• With alert: name,sps,:eq,(,nf.cluster,),:by,:sum,50e3,:2over,:gt,:vspan"
    echo "• Multiple series: name,sps,:eq,(,nf.cluster,),:by,:line,input,:legend,:rot"
    echo ""
}

# Show LocalAlertRunner documentation
show_alert_docs() {
    print_header "LOCALALERT RUNNER CLI DOCUMENTATION"
    
    print_section "🎯 Basic Command Structure:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalAlertRunner [OPTIONS]\""
    echo ""
    
    print_section "📋 Available Options:"
    echo "--preset <name>           # Database preset"
    echo "--alert \"<aql_expression>\" # Alert query expression"
    echo "--threshold <value>       # Alert threshold"
    echo "--operator <op>           # Comparison operator (gt, lt, ge, le)"
    echo "--severity <level>        # Alert severity (INFO, WARN, ERROR)"
    echo "--s <start_time>          # Start time"
    echo "--e <end_time>            # End time"
    echo "--tz <timezone>           # Timezone"
    echo "--theme <theme>           # Theme"
    echo "--w <width>               # Chart width"
    echo "--h <height>              # Chart height"
    echo "--out <file>              # Output PNG file"
    echo "--alert-output <file>     # Alert report JSON"
    echo "--emit-v2 <file>          # Export V2 JSON"
    echo "--generate-chart          # Generate chart"
    echo "--generate-report         # Generate alert report"
    echo "--show-visual-alert       # Show visual alert overlay"
    echo ""
    
    print_section "⚡ Alert Operators:"
    echo "• gt  - Greater than"
    echo "• lt  - Less than"
    echo "• ge  - Greater than or equal"
    echo "• le  - Less than or equal"
    echo ""
    
    print_section "🚨 Alert Severity Levels:"
    echo "• INFO  - Informational alerts"
    echo "• WARN  - Warning alerts"
    echo "• ERROR - Error alerts"
    echo ""
    
    print_section "📊 Example Commands:"
    
    print_example "1. Basic Alert Evaluation:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalAlertRunner --preset sps --alert 'name,sps,:eq,(,nf.cluster,),:by' --threshold 1000 --operator lt --severity INFO --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/throughput_alert.png --alert-output target/manual/throughput_alert_report.json\""
    echo ""
    
    print_example "2. Alert with Visual Overlay:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalAlertRunner --preset sps --alert 'name,sps,:eq,(,nf.cluster,),:by' --threshold 50000 --operator gt --severity WARN --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/cpu_alert.png --alert-output target/manual/cpu_alert_report.json --show-visual-alert\""
    echo ""
    
    print_example "3. High CPU Alert:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalAlertRunner --preset sps --alert 'name,sps,:eq,(,nf.cluster,),:by' --threshold 80000 --operator gt --severity ERROR --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/high_cpu_alert.png --alert-output target/manual/high_cpu_alert_report.json\""
    echo ""
    
    print_section "🔧 Alert Expression Examples:"
    echo "• Basic alert: name,sps,:eq,(,nf.cluster,),:by"
    echo "• With sum: name,sps,:eq,(,nf.cluster,),:by,:sum"
    echo "• With threshold: name,sps,:eq,(,nf.cluster,),:by,:sum,50e3,:2over,:gt"
    echo "• With visual: name,sps,:eq,(,nf.cluster,),:by,:sum,50e3,:2over,:gt,:vspan"
    echo ""
}

# List available templates
list_templates() {
    print_header "AVAILABLE TEMPLATES"
    
    print_section "📁 Graph Style Templates (scripts/styles_with_signal_line/):"
    if [ -d "scripts/styles_with_signal_line" ]; then
        for template in scripts/styles_with_signal_line/*.args; do
            if [ -f "$template" ]; then
                template_name=$(basename "$template" .args)
                echo "• $template_name"
            fi
        done
    else
        print_error "Templates directory not found: scripts/styles_with_signal_line/"
    fi
    echo ""
    
    print_section "📁 Alert Templates (scripts/alerts/):"
    if [ -d "scripts/alerts" ]; then
        for template in scripts/alerts/*.args; do
            if [ -f "$template" ]; then
                template_name=$(basename "$template" .args)
                echo "• $template_name"
            fi
        done
    else
        print_error "Alert templates directory not found: scripts/alerts/"
    fi
    echo ""
    
    print_section "📁 Visual Alert Templates (scripts/visual_alerts/):"
    if [ -d "scripts/visual_alerts" ]; then
        for template in scripts/visual_alerts/*.args; do
            if [ -f "$template" ]; then
                template_name=$(basename "$template" .args)
                echo "• $template_name"
            fi
        done
    else
        print_error "Visual alert templates directory not found: scripts/visual_alerts/"
    fi
    echo ""
}

# Show template content
show_template() {
    if [ -z "$1" ]; then
        print_error "Please specify a template name"
        echo "Usage: ./scripts/atlas_cli_helper.sh show-template <template_name>"
        echo ""
        echo "Available templates:"
        list_templates
        return 1
    fi
    
    template_name="$1"
    template_file=""
    
    # Search for template in different directories
    if [ -f "scripts/styles_with_signal_line/${template_name}.args" ]; then
        template_file="scripts/styles_with_signal_line/${template_name}.args"
    elif [ -f "scripts/alerts/${template_name}.args" ]; then
        template_file="scripts/alerts/${template_name}.args"
    elif [ -f "scripts/visual_alerts/${template_name}.args" ]; then
        template_file="scripts/visual_alerts/${template_name}.args"
    else
        print_error "Template not found: $template_name"
        echo ""
        echo "Available templates:"
        list_templates
        return 1
    fi
    
    print_header "TEMPLATE CONTENT: $template_name"
    echo ""
    print_section "📄 Template File: $template_file"
    echo ""
    print_section "📋 Content:"
    cat "$template_file"
    echo ""
    
    print_section "🚀 To run this template:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalGraphRunner \$(cat $template_file)\""
    echo ""
}

# Run LocalGraphRunner
run_graph() {
    if [ -z "$1" ]; then
        print_error "Please provide arguments for LocalGraphRunner"
        echo "Usage: ./scripts/atlas_cli_helper.sh run-graph \"[OPTIONS]\""
        echo ""
        echo "Example:"
        echo "./scripts/atlas_cli_helper.sh run-graph \"--preset sps --q 'name,sps,:eq,(,nf.cluster,),:by' --style line --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/my_chart.png\""
        return 1
    fi
    
    args="$1"
    print_header "RUNNING LOCALGRAPH RUNNER"
    echo ""
    print_section "🚀 Command:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalGraphRunner $args\""
    echo ""
    
    sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $args"
}

# Run LocalAlertRunner
run_alert() {
    if [ -z "$1" ]; then
        print_error "Please provide arguments for LocalAlertRunner"
        echo "Usage: ./scripts/atlas_cli_helper.sh run-alert \"[OPTIONS]\""
        echo ""
        echo "Example:"
        echo "./scripts/atlas_cli_helper.sh run-alert \"--preset sps --alert 'name,sps,:eq,(,nf.cluster,),:by' --threshold 1000 --operator lt --severity INFO --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/throughput_alert.png --alert-output target/manual/throughput_alert_report.json\""
        return 1
    fi
    
    args="$1"
    print_header "RUNNING LOCALALERT RUNNER"
    echo ""
    print_section "🚀 Command:"
    echo "sbt \"project atlas-eval\" \"runMain com.netflix.atlas.eval.tools.LocalAlertRunner $args\""
    echo ""
    
    sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.LocalAlertRunner $args"
}

# Main script logic
case "$1" in
    "help"|"")
        show_help
        ;;
    "graph")
        show_graph_docs
        ;;
    "alert")
        show_alert_docs
        ;;
    "list-templates")
        list_templates
        ;;
    "show-template")
        show_template "$2"
        ;;
    "run-graph")
        run_graph "$2"
        ;;
    "run-alert")
        run_alert "$2"
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

# chmod +x scripts/atlas_cli_helper.sh
# # Show help
# ./scripts/atlas_cli_helper.sh help

# # Show graph documentation
# ./scripts/atlas_cli_helper.sh graph

# # Show alert documentation
# ./scripts/atlas_cli_helper.sh alert

# # List all templates
# ./scripts/atlas_cli_helper.sh list-templates

# # Show specific template content
# ./scripts/atlas_cli_helper.sh show-template line

# # Run graph directly
# ./scripts/atlas_cli_helper.sh run-graph "--preset sps --q 'name,sps,:eq,(,nf.cluster,),:by' --style line --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/my_chart.png"

# # Run alert directly
# ./scripts/atlas_cli_helper.sh run-alert "--preset sps --alert 'name,sps,:eq,(,nf.cluster,),:by' --threshold 1000 --operator lt --severity INFO --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out target/manual/throughput_alert.png --alert-output target/manual/throughput_alert_report.json"