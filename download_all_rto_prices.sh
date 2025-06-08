#!/bin/bash

# =============================================================================
# RTO Price Data Download Script - GridStatus.io Integration
# =============================================================================
# 
# This script downloads wholesale electricity price data for all major RTOs
# using the gridstatus.io API and saves them as CSV files compatible with
# existing analysis scripts.
#
# Author: AI Assistant
# Date: $(date +%Y-%m-%d)
# Version: 1.0
#
# =============================================================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
DEFAULT_YEAR=$(date +%Y)
DEFAULT_OUTPUT_DIR="gridstatus_price"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
PYTHON_SCRIPT="${SCRIPT_DIR}/download_rto_prices_gridstatus.py"

# Available RTOs
ALL_RTOS=("caiso" "ercot" "isone" "miso" "nyiso" "pjm" "spp")

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to print section headers
print_header() {
    local message=$1
    echo
    print_color $CYAN "============================================================"
    print_color $CYAN "$message"
    print_color $CYAN "============================================================"
}

# Function to print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Download wholesale electricity price data for RTOs from gridstatus.io

OPTIONS:
    -y, --year YEAR         Year to download data for (default: $DEFAULT_YEAR)
    -o, --output-dir DIR    Output directory for CSV files (default: $DEFAULT_OUTPUT_DIR)
    -r, --rtos RTO_LIST     Comma-separated list of RTOs to download
                           Available: ${ALL_RTOS[*]}
                           (default: all RTOs)
    -k, --api-key KEY       GridStatus.io API key (or set GRIDSTATUS_API_KEY env var)
    -l, --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
    --no-log               Disable logging to file (output only to console)
    -h, --help              Show this help message

EXAMPLES:
    # Download all RTOs for 2024
    $0 --year 2024

    # Download specific RTOs for 2023
    $0 --year 2023 --rtos caiso,ercot,miso

    # Use custom output directory
    $0 --year 2024 --output-dir /path/to/price_data

    # Set API key via command line
    $0 --year 2024 --api-key your_api_key_here

    # Disable logging to file
    $0 --year 2024 --no-log

ENVIRONMENT VARIABLES:
    GRIDSTATUS_API_KEY      Your gridstatus.io API key (recommended for security)

NOTES:
    - Requires Python 3.7+ with gridstatusio library installed
    - Downloads day-ahead LMP/SPP prices for optimal locations in each RTO
    - Creates timestamped log files in ./logs/ directory
    - Files are saved in EIA-compatible CSV format

EOF
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local all_good=true
    
    # Check Python
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_color $GREEN "✓ Python 3 found: $python_version"
    else
        print_color $RED "✗ Python 3 not found"
        all_good=false
    fi
    
    # Check Python script
    if [[ -f "$PYTHON_SCRIPT" ]]; then
        print_color $GREEN "✓ Python download script found: $PYTHON_SCRIPT"
    else
        print_color $RED "✗ Python download script not found: $PYTHON_SCRIPT"
        all_good=false
    fi
    
    # Check API key
    if [[ -n "$GRIDSTATUS_API_KEY" ]]; then
        print_color $GREEN "✓ GridStatus.io API key found in environment"
    elif [[ -n "$API_KEY" ]]; then
        export GRIDSTATUS_API_KEY="$API_KEY"
        print_color $GREEN "✓ GridStatus.io API key provided via command line"
    else
        print_color $RED "✗ GridStatus.io API key not found"
        print_color $YELLOW "  Set GRIDSTATUS_API_KEY environment variable or use --api-key option"
        all_good=false
    fi
    
    if [[ "$all_good" == "false" ]]; then
        print_color $RED "Prerequisites check failed. Please fix the issues above."
        exit 1
    fi
    
    print_color $GREEN "All prerequisites satisfied!"
}

# Function to create log directory
setup_logging() {
    if [[ "$NO_LOG" == "true" ]]; then
        print_color $YELLOW "Logging disabled - output to console only"
        LOG_FILE=""
        return 0
    fi
    
    mkdir -p "$LOG_DIR"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    LOG_FILE="${LOG_DIR}/rto_price_download_${timestamp}.log"
    
    # Start logging
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
    
    print_color $BLUE "Logging to: $LOG_FILE"
}

# Function to download price data
download_price_data() {
    local year=$1
    local output_dir=$2
    local rtos_list=$3
    
    print_header "Starting Price Data Download"
    
    print_color $BLUE "Configuration:"
    print_color $BLUE "  Year: $year"
    print_color $BLUE "  Output Directory: $output_dir"
    print_color $BLUE "  RTOs: $rtos_list"
    print_color $BLUE "  Python Script: $PYTHON_SCRIPT"
    
    # Build command
    local cmd="python3 \"$PYTHON_SCRIPT\" --year $year --output-dir \"$output_dir\""
    
    if [[ -n "$rtos_list" ]]; then
        # Convert comma-separated list to space-separated for Python script
        local rtos_array=(${rtos_list//,/ })
        cmd="$cmd --rtos ${rtos_array[*]}"
    fi
    
    print_color $YELLOW "Executing: $cmd"
    echo
    
    # Execute the command
    if eval $cmd; then
        print_color $GREEN "✓ Price data download completed successfully!"
        return 0
    else
        print_color $RED "✗ Price data download failed!"
        return 1
    fi
}

# Function to generate summary report
generate_summary() {
    local output_dir=$1
    local year=$2
    
    print_header "Download Summary Report"
    
    if [[ ! -d "$output_dir" ]]; then
        print_color $RED "Output directory not found: $output_dir"
        return 1
    fi
    
    local csv_files=("$output_dir"/*_price_*_hr_${year}.csv)
    
    if [[ ${#csv_files[@]} -eq 0 ]] || [[ ! -f "${csv_files[0]}" ]]; then
        print_color $RED "No price CSV files found in $output_dir"
        return 1
    fi
    
    print_color $BLUE "Price files downloaded:"
    echo
    
    local total_size=0
    local total_lines=0
    
    for file in "${csv_files[@]}"; do
        if [[ -f "$file" ]]; then
            local filename=$(basename "$file")
            local size=$(du -h "$file" | cut -f1)
            local lines=$(wc -l < "$file")
            local data_lines=$((lines - 4))  # Subtract header lines
            
            printf "  %-40s %8s %8d lines (%d data rows)\n" "$filename" "$size" "$lines" "$data_lines"
            
            # Add to totals (convert size to bytes for accurate total)
            # Use stat for cross-platform compatibility
            if command -v stat &> /dev/null; then
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    # macOS
                    local size_bytes=$(stat -f%z "$file")
                else
                    # Linux
                    local size_bytes=$(stat -c%s "$file")
                fi
            else
                # Fallback: estimate from KB
                local size_kb=$(du -k "$file" | cut -f1)
                local size_bytes=$((size_kb * 1024))
            fi
            total_size=$((total_size + size_bytes))
            total_lines=$((total_lines + lines))
        fi
    done
    
    echo
    local total_size_mb=$((total_size / 1024 / 1024))
    print_color $GREEN "Total: ${#csv_files[@]} files, ${total_size_mb}MB, $total_lines total lines"
    
    # Check for expected data completeness (8,764 lines = 4 headers + 8,760 data rows)
    local expected_lines=8764
    local complete_files=0
    
    for file in "${csv_files[@]}"; do
        if [[ -f "$file" ]]; then
            local lines=$(wc -l < "$file")
            if [[ $lines -eq $expected_lines ]]; then
                ((complete_files++))
            fi
        fi
    done
    
    if [[ $complete_files -eq ${#csv_files[@]} ]]; then
        print_color $GREEN "✓ All files have complete data (8,760 hourly records + headers)"
    else
        print_color $YELLOW "⚠ Some files may have incomplete data"
    fi
    
    print_color $BLUE "Files saved in: $output_dir"
    if [[ -n "$LOG_FILE" ]]; then
        print_color $BLUE "Log file: $LOG_FILE"
    fi
}

# Parse command line arguments
YEAR="$DEFAULT_YEAR"
OUTPUT_DIR="$DEFAULT_OUTPUT_DIR"
RTOS_LIST=""
API_KEY=""
LOG_LEVEL="INFO"
NO_LOG="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--year)
            YEAR="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -r|--rtos)
            RTOS_LIST="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --no-log)
            NO_LOG="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_color $RED "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate year
if ! [[ "$YEAR" =~ ^[0-9]{4}$ ]] || [[ $YEAR -lt 2015 ]] || [[ $YEAR -gt $(date +%Y) ]]; then
    print_color $RED "Invalid year: $YEAR. Must be between 2015 and $(date +%Y)"
    exit 1
fi

# Validate RTOs if specified
if [[ -n "$RTOS_LIST" ]]; then
    IFS=',' read -ra RTOS_ARRAY <<< "$RTOS_LIST"
    for rto in "${RTOS_ARRAY[@]}"; do
        if [[ ! " ${ALL_RTOS[*]} " =~ " ${rto} " ]]; then
            print_color $RED "Invalid RTO: $rto. Available RTOs: ${ALL_RTOS[*]}"
            exit 1
        fi
    done
fi

# Main execution
main() {
    local start_time=$(date +%s)
    
    print_header "RTO Price Data Download - GridStatus.io"
    print_color $BLUE "Started at: $(date)"
    
    setup_logging
    check_prerequisites
    
    if download_price_data "$YEAR" "$OUTPUT_DIR" "$RTOS_LIST"; then
        generate_summary "$OUTPUT_DIR" "$YEAR"
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local minutes=$((duration / 60))
        local seconds=$((duration % 60))
        
        print_header "Download Complete!"
        print_color $GREEN "Total time: ${minutes}m ${seconds}s"
        print_color $GREEN "Success! Price data ready for analysis."
        
        exit 0
    else
        if [[ -n "$LOG_FILE" ]]; then
            print_color $RED "Download failed. Check the log file for details: $LOG_FILE"
        else
            print_color $RED "Download failed. Check the console output above for details."
        fi
        exit 1
    fi
}

# Run main function
main "$@" 