#!/bin/bash

# QAS AI Medical System - Setup Script
# This script automates the initial setup process

set -e

echo "🏥 QAS AI Medical System - Setup Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Tesseract is installed
echo -e "${YELLOW}Checking Tesseract OCR installation...${NC}"
if ! command -v tesseract &> /dev/null; then
    echo -e "${RED}❌ Tesseract OCR is not installed!${NC}"
    echo "Please install Tesseract:"
    echo "  macOS: brew install tesseract"
    echo "  Ubuntu: sudo apt-get install tesseract-ocr"
    exit 1
else
    echo -e "${GREEN}✅ Tesseract OCR is installed${NC}"
    tesseract --version | head -n 1
fi

# Check if Python is installed
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python is installed${NC}"
    python3 --version
fi

# Check if Node.js is installed
echo -e "${YELLOW}Checking Node.js installation...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Node.js is installed${NC}"
    node --version
fi

# Check if PostgreSQL is installed
echo -e "${YELLOW}Checking PostgreSQL installation...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL CLI not found. You may need to install PostgreSQL or Docker.${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL is installed${NC}"
    psql --version
fi

echo ""
echo -e "${GREEN}=== Backend Setup ===${NC}"

# Setup backend
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Python dependencies installed${NC}"

cd ..

echo ""
echo -e "${GREEN}=== Frontend Setup ===${NC}"

# Setup frontend
cd frontend

echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
npm install
echo -e "${GREEN}✅ Node.js dependencies installed${NC}"

cd ..

echo ""
echo -e "${GREEN}=== Database Setup ===${NC}"

# Check if database exists
echo -e "${YELLOW}Checking database setup...${NC}"
if command -v psql &> /dev/null; then
    # Try to create database
    if psql -U postgres -lqt | cut -d \| -f 1 | grep -qw medical_db; then
        echo -e "${GREEN}✅ Database 'medical_db' already exists${NC}"
    else
        echo -e "${YELLOW}Creating database 'medical_db'...${NC}"
        createdb -U postgres medical_db 2>/dev/null || echo -e "${YELLOW}⚠️  Could not create database. Please create it manually or use Docker.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  PostgreSQL not found. Consider using Docker Compose:${NC}"
    echo "   docker-compose up -d postgres"
fi

echo ""
echo -e "${GREEN}=== Configuration Check ===${NC}"

# Check .env file
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: Update the following in .env:${NC}"
    echo "  1. JWT_SECRET_KEY - Run: openssl rand -hex 32"
    echo "  2. DB_PASSWORD - Set a secure database password"
    echo "  3. Verify AWS credentials are correct"
else
    echo -e "${RED}❌ .env file not found!${NC}"
fi

echo ""
echo -e "${GREEN}=== AWS S3 Check ===${NC}"

# Check AWS credentials
if command -v aws &> /dev/null; then
    echo -e "${GREEN}✅ AWS CLI is installed${NC}"
    echo -e "${YELLOW}Testing S3 access...${NC}"
    if aws s3 ls 2>/dev/null; then
        echo -e "${GREEN}✅ AWS credentials are configured${NC}"
    else
        echo -e "${YELLOW}⚠️  AWS credentials may not be configured correctly${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  AWS CLI not installed. S3 access will be handled by boto3.${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✨ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update .env file with secure values:"
echo "   - Generate JWT secret: openssl rand -hex 32"
echo "   - Set database password"
echo ""
echo "2. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload"
echo ""
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. Or use Docker Compose:"
echo "   docker-compose up -d"
echo ""
echo "5. Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo -e "${YELLOW}📚 Read the README.md for detailed instructions!${NC}"
