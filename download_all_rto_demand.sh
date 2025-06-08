#!/bin/bash

# Download All RTO Demand Data from GridStatus.io
# This script downloads demand data for all major RTOs using the gridstatus.io API

# Configuration
YEAR=2024
API_KEY="${GRIDSTATUS_API_KEY:-}"  # Read from environment variable
OUTPUT_DIR="gridstatus_demand"
SCRIPT_NAME="download_rto_demand_gridstatus.py"
LOG_FILE="download_rtos_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required files exist
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if API key is set
    if [ -z "$API_KEY" ]; then
        print_error "GridStatus.io API key not found!"
        print_error "Please set the GRIDSTATUS_API_KEY environment variable:"
        print_error "  export GRIDSTATUS_API_KEY='your_api_key_here'"
        print_error "Or use the -k option to specify the API key"
        exit 1
    fi
    
    # Check if Python script exists
    if [ ! -f "$SCRIPT_NAME" ]; then
        print_error "Python script '$SCRIPT_NAME' not found in current directory"
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python &> /dev/null; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Function to download data for all RTOs
download_all_rtos() {
    print_status "Starting download for all RTOs for year $YEAR"
    print_status "Output directory: $OUTPUT_DIR"
    print_status "Log file: $LOG_FILE"
    
    # Create log file
    echo "RTO Download Log - $(date)" > "$LOG_FILE"
    echo "Year: $YEAR" >> "$LOG_FILE"
    echo "Output Directory: $OUTPUT_DIR" >> "$LOG_FILE"
    echo "----------------------------------------" >> "$LOG_FILE"
    
    # Run the Python script for all RTOs
    print_status "Executing: python $SCRIPT_NAME --year $YEAR --api-key [HIDDEN] --output-dir $OUTPUT_DIR"
    
    python "$SCRIPT_NAME" --year "$YEAR" --api-key "$API_KEY" --output-dir "$OUTPUT_DIR" 2>&1 | tee -a "$LOG_FILE"
    
    # Check the exit status
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "Download completed successfully"
    else
        print_error "Download failed. Check log file: $LOG_FILE"
        return 1
    fi
}

# Function to download specific RTOs
download_specific_rtos() {
    local rtos=("$@")
    print_status "Starting download for specific RTOs: ${rtos[*]}"
    print_status "Year: $YEAR"
    print_status "Output directory: $OUTPUT_DIR"
    
    # Create log file
    echo "RTO Download Log - $(date)" > "$LOG_FILE"
    echo "Year: $YEAR" >> "$LOG_FILE"
    echo "RTOs: ${rtos[*]}" >> "$LOG_FILE"
    echo "Output Directory: $OUTPUT_DIR" >> "$LOG_FILE"
    echo "----------------------------------------" >> "$LOG_FILE"
    
    # Run the Python script for specific RTOs
    print_status "Executing: python $SCRIPT_NAME --year $YEAR --api-key [HIDDEN] --output-dir $OUTPUT_DIR --rtos ${rtos[*]}"
    
    python "$SCRIPT_NAME" --year "$YEAR" --api-key "$API_KEY" --output-dir "$OUTPUT_DIR" --rtos "${rtos[@]}" 2>&1 | tee -a "$LOG_FILE"
    
    # Check the exit status
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "Download completed successfully"
    else
        print_error "Download failed. Check log file: $LOG_FILE"
        return 1
    fi
}

# Function to show download summary
show_summary() {
    print_status "Download Summary:"
    
    if [ -d "$OUTPUT_DIR" ]; then
        echo ""
        echo "Files created in $OUTPUT_DIR:"
        ls -lh "$OUTPUT_DIR"/*.csv 2>/dev/null | while read -r line; do
            echo "  $line"
        done
        
        echo ""
        echo "File count by RTO:"
        for rto in caiso ercot isone miso nyiso pjm spp; do
            file="$OUTPUT_DIR/${rto}_load_act_hr_${YEAR}.csv"
            if [ -f "$file" ]; then
                lines=$(wc -l < "$file")
                size=$(ls -lh "$file" | awk '{print $5}')
                print_success "$rto: $lines lines, $size"
            else
                print_warning "$rto: File not found"
            fi
        done
    else
        print_warning "Output directory '$OUTPUT_DIR' not found"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [RTOs...]"
    echo ""
    echo "Download RTO demand data from gridstatus.io"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -y, --year     Year to download (default: $YEAR)"
    echo "  -k, --api-key  GridStatus.io API key (default: from GRIDSTATUS_API_KEY env var)"
    echo "  -o, --output   Output directory (default: $OUTPUT_DIR)"
    echo "  -l, --list     List available RTOs"
    echo ""
    echo "RTOs (if specified, only these will be downloaded):"
    echo "  caiso ercot isone miso nyiso pjm spp"
    echo ""
    echo "Environment Variables:"
    echo "  GRIDSTATUS_API_KEY          GridStatus.io API key (recommended)"
    echo ""
    echo "Examples:"
    echo "  export GRIDSTATUS_API_KEY='your_key_here'"
    echo "  $0                          # Download all RTOs"
    echo "  $0 caiso ercot              # Download only CAISO and ERCOT"
    echo "  $0 -y 2023                  # Download all RTOs for 2023"
    echo "  $0 -y 2023 caiso pjm        # Download CAISO and PJM for 2023"
    echo "  $0 -k your_key caiso        # Use specific API key for CAISO"
}

# Function to list available RTOs
list_rtos() {
    echo "Available RTOs:"
    echo "  caiso  - California Independent System Operator"
    echo "  ercot  - Electric Reliability Council of Texas"
    echo "  isone  - ISO New England"
    echo "  miso   - Midcontinent Independent System Operator"
    echo "  nyiso  - New York Independent System Operator"
    echo "  pjm    - PJM Interconnection"
    echo "  spp    - Southwest Power Pool"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -y|--year)
            YEAR="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -l|--list)
            list_rtos
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            # Remaining arguments are RTOs
            SPECIFIC_RTOS+=("$1")
            shift
            ;;
    esac
done

# Main execution
main() {
    echo "=================================================="
    echo "  RTO Demand Data Download Script"
    echo "  GridStatus.io API"
    echo "=================================================="
    echo ""
    
    # Check prerequisites
    check_prerequisites
    echo ""
    
    # Download data
    if [ ${#SPECIFIC_RTOS[@]} -eq 0 ]; then
        # Download all RTOs
        download_all_rtos
    else
        # Download specific RTOs
        download_specific_rtos "${SPECIFIC_RTOS[@]}"
    fi
    
    echo ""
    
    # Show summary
    show_summary
    
    print_status "Script completed. Log saved to: $LOG_FILE"
}

# Run main function
main 