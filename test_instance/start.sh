#!/bin/bash
# Simple startup script for test instance

echo "🧪 Weight Tracker Test Instance Startup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Not in Weight Tracker repository root"
    echo "Please run from: /Users/calummallorie/Repositories/weight-tracker"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  No virtual environment found - using system Python"
fi

# Check Python and dependencies
echo "🐍 Python version:"
python --version

echo "📦 Installing/checking requirements..."
pip install -q -r requirements.txt

echo "🚀 Starting test instance..."
python test_instance/start_test_instance.py