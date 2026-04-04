#!/bin/bash
# Setup script for BTC trading autoresearch on Mac Mini M4

set -e

echo "================================================"
echo "BTC Trading Autoresearch Setup"
echo "Mac Mini M4 - Ichimoku Cloud Optimization"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check Python version
print_info "Checking Python version..."
python3 --version | grep -q "3.1[0-9]" && print_success "Python 3.10+ found" || print_error "Python 3.10+ required"

# Create virtual environment
print_info "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_info "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements_trading.txt
print_success "Dependencies installed"

# Test data pipeline
print_info "Testing data pipeline..."
python3 -c "
import sys
sys.path.insert(0, '.')
from prepare_trading import download_btc_data, calculate_all_indicators
import pandas as pd

print('Testing with small dataset...')
data = download_btc_data(
    start_date='2024-01-01',
    end_date='2024-01-10',
    interval='1d',
    force_download=False
)
print(f'Downloaded {len(data)} rows')

data_with_indicators = calculate_all_indicators(data)
ichimoku_cols = [col for col in data_with_indicators.columns if 'ichimoku' in col]
print(f'Calculated {len(ichimoku_cols)} Ichimoku indicators')
print('✅ Data pipeline test passed')
"

# Create cache directory
print_info "Setting up cache directories..."
mkdir -p ~/.cache/autoresearch-trading/data
mkdir -p ~/.cache/autoresearch-trading/indicators
print_success "Cache directories created"

# Test strategy
print_info "Testing strategy template..."
python3 -c "
import sys
sys.path.insert(0, '.')
from strategy import test_strategy
test_strategy()
"
print_success "Strategy test passed"

# Create gitignore for cache
if [ ! -f ".gitignore" ]; then
    print_info "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Virtual environment
venv/
__pycache__/
*.py[cod]
*$py.class

# Cache directories
.cache/
*.pkl
*.pickle

# Results
results_*.tsv

# IDE
.vscode/
.idea/
*.swp
*.swo

# System
.DS_Store
Thumbs.db
EOF
    print_success ".gitignore created"
fi

# Make scripts executable
print_info "Making scripts executable..."
chmod +x setup_trading.sh 2>/dev/null || true

echo ""
echo "================================================"
echo "SETUP COMPLETE!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Prepare full data:"
echo "   ${YELLOW}python prepare_trading.py${NC}"
echo ""
echo "2. Run test backtest:"
echo "   ${YELLOW}python -c \"import sys; sys.path.insert(0, '.'); from backtest import BacktestEngine; print('Backtest engine ready')\"${NC}"
echo ""
echo "3. Read the program:"
echo "   ${YELLOW}cat program_trading.md | head -50${NC}"
echo ""
echo "4. Start autonomous research:"
echo "   ${YELLOW}# Point your AI agent at program_trading.md${NC}"
echo ""
echo "Cache directory: ${YELLOW}~/.cache/autoresearch-trading/${NC}"
echo "Virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo "================================================"