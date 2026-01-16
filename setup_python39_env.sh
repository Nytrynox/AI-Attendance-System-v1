#!/bin/bash

# Setup Python 3.9.23 Virtual Environment for Face Attendance System

echo "🚀 Setting up Python 3.9.23 virtual environment..."

# Check if Python 3.9 is available
if ! command -v python3.9 &> /dev/null; then
    echo "❌ Python 3.9 is not installed. Please install Python 3.9.23 first."
    echo "   You can install it using:"
    echo "   brew install python@3.9"
    exit 1
fi

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment with Python 3.9
echo "📦 Creating new virtual environment with Python 3.9..."
python3.9 -m venv venv

# Activate the virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Verify Python version
echo "🐍 Python version:"
python --version

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install essential build tools first
echo "🔨 Installing build tools..."
pip install setuptools wheel

# Install packages one by one to catch any issues
echo "📚 Installing core packages..."

echo "  Installing numpy..."
pip install "numpy>=1.20.0,<1.25.0"

echo "  Installing opencv-python..."
pip install opencv-python==4.8.1.78

echo "  Installing Pillow..."
pip install "Pillow>=8.0.0,<10.0.0"

echo "  Installing dlib..."
pip install dlib==19.24.2

echo "  Installing face-recognition..."
pip install face-recognition==1.3.0

echo "  Installing requests..."
pip install "requests>=2.25.0,<3.0.0"

echo "  Installing scipy..."
pip install "scipy>=1.7.0,<1.10.0"

echo "  Installing scikit-learn..."
pip install "scikit-learn>=1.0.0,<1.3.0"

echo "  Installing pandas..."
pip install "pandas>=1.3.0,<1.6.0"

echo "  Installing matplotlib..."
pip install "matplotlib>=3.4.0,<3.6.0"

echo "  Installing utility libraries..."
pip install "python-dateutil>=2.8.0,<3.0.0"

# Try to install TensorFlow (may not work on all systems)
echo "  Installing TensorFlow (this may take a while or fail on some systems)..."
pip install "tensorflow>=2.13.0,<2.16.0" || echo "⚠️  TensorFlow installation failed - you can continue without it for basic functionality"

echo "✅ Setup complete!"
echo ""
echo "To activate this environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
