#!/bin/bash

# SentinelHire Setup Script
# This script sets up the development environment for the resume fraud detection system

set -e

echo "🚀 Setting up SentinelHire - AI-Powered Resume Fraud Detection System"
echo "=================================================================="

# Check if required tools are installed
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. Please install it first."
        exit 1
    else
        echo "✅ $1 is installed"
    fi
}

echo "📋 Checking prerequisites..."
check_command "node"
check_command "pnpm"
check_command "python3"
check_command "git"

# Get Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node --version)"
    exit 1
fi
echo "✅ Node.js version $(node --version) is compatible"

# Get Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(echo "$PYTHON_VERSION < 3.9" | bc -l)" -eq 1 ]; then
    echo "❌ Python 3.9+ is required. Current version: $(python3 --version)"
    exit 1
fi
echo "✅ Python version $(python3 --version) is compatible"

echo ""
echo "📦 Installing frontend dependencies..."
pnpm install

echo ""
echo "📦 Setting up Python backend..."
cd python_backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Go back to root
cd ..

echo ""
echo "🔧 Setting up environment files..."

# Create .env.local for Next.js if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "Creating .env.local for Next.js..."
    cat > .env.local << EOF
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Python API URL (default: http://localhost:8000)
PYTHON_API_URL=http://localhost:8000
EOF
    echo "⚠️  Please update .env.local with your Supabase credentials"
fi

# Create .env for Python backend if it doesn't exist
if [ ! -f "python_backend/.env" ]; then
    echo "Creating .env for Python backend..."
    cp python_backend/env.example python_backend/.env
    echo "⚠️  Please update python_backend/.env with your API credentials"
fi

echo ""
echo "🗄️  Setting up database..."

# Check if Supabase CLI is installed
if command -v supabase &> /dev/null; then
    echo "Supabase CLI found. You can run 'npx supabase start' to start local development"
else
    echo "Supabase CLI not found. Install it with: npm install -g supabase"
fi

echo ""
echo "🧪 Running tests..."

# Run Python tests
cd python_backend
source venv/bin/activate
echo "Running Python backend tests..."
python3 run_tests.py --type unit
cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "1. Update your environment files with real credentials:"
echo "   - .env.local (Supabase credentials)"
echo "   - python_backend/.env (AWS and other API credentials)"
echo ""
echo "2. Start the Python backend:"
echo "   cd python_backend && source venv/bin/activate && python3 main.py"
echo ""
echo "3. Start the Next.js frontend (in another terminal):"
echo "   pnpm dev"
echo ""
echo "4. Access the application:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📚 For more information, see the README.md file"
