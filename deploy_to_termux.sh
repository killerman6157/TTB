#!/bin/bash
# Telegram Account Trading Bot - Termux Deployment Script

echo "🤖 Telegram Account Trading Bot - Termux Setup"
echo "=============================================="

# Update Termux packages
echo "📦 Updating Termux packages..."
pkg update -y && pkg upgrade -y

# Install required system packages
echo "🔧 Installing system dependencies..."
pkg install -y python git nano

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install aiogram==3.20.0 aiosqlite==0.21.0 telethon==1.40.0 python-dotenv==1.1.1 pytz==2025.2

# Create bot directory structure
echo "📁 Setting up directory structure..."
mkdir -p sessions

# Set proper permissions
chmod +x main.py
chmod +x test_bot.py

# Test the installation
echo "🧪 Testing bot components..."
python test_bot.py

if [ $? -eq 0 ]; then
    echo "✅ Installation successful!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Edit .env file with your real API credentials"
    echo "2. Run: python main.py"
    echo ""
    echo "🔑 Required credentials:"
    echo "- BOT_TOKEN (from @BotFather)"
    echo "- API_ID and API_HASH (from https://my.telegram.org/apps)"
    echo "- ADMIN_ID (your Telegram user ID)"
    echo "- BUYER_ID (buyer's Telegram user ID)"
    echo ""
    echo "📖 Read README.md for complete instructions"
else
    echo "❌ Installation failed. Check the errors above."
    exit 1
fi
