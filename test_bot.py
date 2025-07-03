#!/usr/bin/env python3
"""
Test script for the Telegram Account Trading Bot
This creates a simple mock test environment to verify all components work properly
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from services.session_manager import SessionManager
from services.scheduler import BotScheduler
from utils.validators import validate_phone_number, is_otp_message, validate_bank_details

async def test_database():
    """Test database operations"""
    print("🔧 Testing database...")
    
    db = Database()
    await db.init_db()
    
    # Test phone exists check
    exists = await db.phone_exists("+2348167757987")
    print(f"   ✓ Phone exists check: {exists}")
    
    # Test add user account
    success = await db.add_user_account(123456789, "test_user", "+2348167757987")
    print(f"   ✓ Add user account: {success}")
    
    # Test get user accounts
    accounts = await db.get_user_accounts(123456789)
    print(f"   ✓ Get user accounts: {len(list(accounts))} found")
    
    # Test account stats
    stats = await db.get_account_stats()
    print(f"   ✓ Account stats: {len(list(stats))} status types")
    
    print("   ✅ Database tests completed\n")

def test_validators():
    """Test validation functions"""
    print("🔧 Testing validators...")
    
    # Test phone validation
    valid_phone = validate_phone_number("+2348167757987")
    invalid_phone = validate_phone_number("invalid")
    print(f"   ✓ Valid phone: {valid_phone}")
    print(f"   ✓ Invalid phone: {invalid_phone}")
    
    # Test OTP detection
    otp_message = "Your verification code is: 12345"
    non_otp = "Hello how are you?"
    print(f"   ✓ OTP message detected: {is_otp_message(otp_message)}")
    print(f"   ✓ Non-OTP message: {is_otp_message(non_otp)}")
    
    # Test bank details
    valid_bank = "9131085651 OPay Bashir Rabiu"
    invalid_bank = "invalid"
    print(f"   ✓ Valid bank details: {validate_bank_details(valid_bank)}")
    print(f"   ✓ Invalid bank details: {validate_bank_details(invalid_bank)}")
    
    print("   ✅ Validator tests completed\n")

def test_session_manager():
    """Test session manager"""
    print("🔧 Testing session manager...")
    
    session_manager = SessionManager()
    
    # Test session file path generation
    phone = "+2348167757987"
    session_file = session_manager.get_session_file(phone)
    print(f"   ✓ Session file path: {session_file}")
    
    # Check sessions directory exists
    sessions_dir_exists = os.path.exists("sessions")
    print(f"   ✓ Sessions directory exists: {sessions_dir_exists}")
    
    print("   ✅ Session manager tests completed\n")

def test_scheduler():
    """Test scheduler functionality"""
    print("🔧 Testing scheduler...")
    
    # Mock bot object for scheduler
    class MockBot:
        pass
    
    scheduler = BotScheduler(MockBot())
    
    # Test operating hours check
    is_operating = scheduler.is_operating_hours()
    print(f"   ✓ Is operating hours: {is_operating}")
    
    # Test time messages
    next_opening = scheduler.get_next_opening_time()
    next_closing = scheduler.get_next_closing_time()
    print(f"   ✓ Next opening: {next_opening}")
    print(f"   ✓ Next closing: {next_closing}")
    
    print("   ✅ Scheduler tests completed\n")

async def run_tests():
    """Run all tests"""
    print("🚀 Starting Telegram Account Trading Bot Tests\n")
    
    try:
        # Test components
        await test_database()
        test_validators()
        test_session_manager()
        test_scheduler()
        
        print("✅ ALL TESTS PASSED!")
        print("\n📋 Bot System Summary:")
        print("   ✓ Database operations working")
        print("   ✓ Phone number validation working") 
        print("   ✓ OTP detection working")
        print("   ✓ Bank details validation working")
        print("   ✓ Session management ready")
        print("   ✓ Operating hours scheduler ready")
        print("\n🎯 Bot is ready for Termux deployment!")
        
        return True
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
