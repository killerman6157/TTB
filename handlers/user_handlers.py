import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from services.session_manager import SessionManager
from services.otp_forwarder import OTPForwarder
from services.scheduler import BotScheduler
from utils.validators import validate_phone_number, extract_country_from_phone, validate_bank_details
from config import ADMIN_ID, BUYER_ID
import logging

logger = logging.getLogger(__name__)

class UserStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_otp = State()
    waiting_for_bank_details = State()

router = Router()
db = Database()
session_manager = SessionManager()

# Global variables to be set from main
otp_forwarder = None
scheduler = None

def set_services(forwarder, sched):
    global otp_forwarder, scheduler
    otp_forwarder = forwarder
    scheduler = sched

@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    welcome_text = (
        "Barka da zuwa cibiyar karbar Telegram accounts! 🤖\n\n"
        "Don farawa, turo lambar wayar account din da kake son sayarwa "
        "(misali: +2348167757987).\n\n"
        "⚠️ MUHIMMI: Tabbatar ka cire Two-Factor Authentication (2FA) "
        "kafin ka tura lambar."
    )
    
    # Pin this message
    sent_message = await message.answer(welcome_text)
    try:
        await sent_message.pin()
    except:
        pass  # Ignore if can't pin
    
    await state.set_state(UserStates.waiting_for_phone)

@router.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    """Handle /cancel command"""
    await state.clear()
    await message.answer("An soke aikin cikin nasara.")

@router.message(Command("myaccounts"))
async def my_accounts_command(message: types.Message):
    """Show user's accounts"""
    user_id = message.from_user.id
    accounts = await db.get_user_accounts(user_id)
    
    if not accounts:
        await message.answer("Ba ka da wata lamba da ka tura tukuna.")
        return
    
    response = "📋 Lambar da ka tura:\n\n"
    for phone, status in accounts:
        status_emoji = {
            'pending': '⏳',
            'accepted': '✅',
            'verified': '🔐',
            'paid': '💰',
            'rejected': '❌'
        }.get(status, '❓')
        
        response += f"{status_emoji} `{phone}` — `{status}`\n"
    
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("withdraw"))
async def withdraw_command(message: types.Message, state: FSMContext):
    """Handle withdrawal request"""
    user_id = message.from_user.id
    
    # Check if it's payment hours (same as operating hours for now)
    if not scheduler or not scheduler.is_operating_hours():
        await message.answer(
            "An rufe biyan kuɗi na yau. Za a fara biyan kuɗi gobe "
            "da karfe 8:00 na safe (WAT). Don Allah a jira."
        )
        return
    
    # Check if user has accounts ready for payment
    pending_count = await db.get_pending_accounts(user_id)
    if pending_count == 0:
        await message.answer(
            "Ba ka da accounts da suke shirye don biya. "
            "Ka tura accounts kafin ka yi buƙatar biya."
        )
        return
    
    await message.answer(
        "Maza turo lambar asusun bankinka da sunan mai asusun.\n\n"
        "Misali: 9131085651 OPay Bashir Rabiu\n\n"
        "Za a fara biyan kuɗi daga karfe 8:00 na dare (WAT). "
        "Admin zai tura maka kuɗin ka akan lokaci."
    )
    
    await state.set_state(UserStates.waiting_for_bank_details)

@router.message(UserStates.waiting_for_phone)
async def handle_phone_input(message: types.Message, state: FSMContext):
    """Handle phone number input"""
    phone_number = validate_phone_number(message.text)
    
    if not phone_number:
        await message.answer(
            "Lambar wayar ba daidai ba ce. Don Allah ka tura lambar "
            "mai kamar haka: +2348167757987"
        )
        return
    
    # Check if it's operating hours
    if not scheduler or not scheduler.is_operating_hours():
        next_opening = scheduler.get_next_opening_time() if scheduler else "gobe"
        await message.answer(
            f"An rufe karbar Telegram accounts na yau. An rufe karbar accounts "
            f"da karfe 10:00 na dare (WAT). Za a sake buɗewa {next_opening}. "
            f"Don Allah a gwada gobe."
        )
        await state.clear()
        return
    
    # Check if phone already exists
    if await db.phone_exists(phone_number):
        country = extract_country_from_phone(phone_number)
        await message.answer(
            f"⚠️ Kuskure! An riga an yi rajistar wannan lambar!\n\n"
            f"+{phone_number[1:]}\n"
            f"| {country}\n\n"
            f"Ba za ka iya sake tura wannan lambar ba sai nan da mako ɗaya."
        )
        await state.clear()
        return
    
    # Store phone and ask for OTP
    await state.update_data(phone_number=phone_number)
    
    await message.answer(
        f"Ana sarrafawa... Don Allah a jira.\n\n"
        f"🇳🇬 An tura lambar sirri (OTP) zuwa lambar: {phone_number}. "
        f"Don Allah ka tura lambar sirrin a nan.\n\n"
        f"Ko ka danna /cancel don soke."
    )
    
    await state.set_state(UserStates.waiting_for_otp)

@router.message(UserStates.waiting_for_otp)
async def handle_otp_input(message: types.Message, state: FSMContext):
    """Handle OTP input and login"""
    otp_code = message.text.strip()
    
    # Validate OTP format
    if not otp_code.isdigit() or len(otp_code) not in [5, 6]:
        await message.answer(
            "Lambar sirri ba daidai ba ce. Don Allah ka tura lambar sirri "
            "ta 5 ko 6 lambobi."
        )
        return
    
    state_data = await state.get_data()
    phone_number = state_data.get('phone_number')
    
    if not phone_number:
        await message.answer("Kuskure ya faru. Don Allah ka sake farawa da /start")
        await state.clear()
        return
    
    # Show processing message
    processing_msg = await message.answer("⏳ Ana shiga account... Don Allah a jira.")
    
    try:
        # Create session and login
        success, result_message = await session_manager.create_session(phone_number, otp_code)
        
        if success:
            # Add to database
            user_id = message.from_user.id
            username = message.from_user.username or "Unknown"
            
            await db.add_user_account(user_id, username, phone_number)
            await db.update_account_status(
                phone_number, 
                'accepted', 
                session_manager.get_session_file(phone_number),
                BUYER_ID
            )
            
            # Start OTP forwarding
            if otp_forwarder:
                await otp_forwarder.start_forwarding(phone_number, BUYER_ID)
            
            # Terminate other sessions for security
            client = await session_manager.get_session(phone_number)
            if client:
                await session_manager.terminate_other_sessions(client)
            
            await processing_msg.edit_text(
                "✅ An shiga account din ku cikin nasara ku cire shi daga na'urar ku. "
                "Za a biya ku bisa ga adadin account din da kuka kawo. "
                "Ana biyan kuɗi daga karfe 8:00 na dare (WAT) zuwa gaba. "
                "Don Allah ka shirya tura bukatar biya ta /withdraw."
            )
            
        else:
            await processing_msg.edit_text(f"❌ {result_message}")
    
    except Exception as e:
        logger.error(f"Error during login process: {e}")
        await processing_msg.edit_text(
            "❌ Kuskure ya faru yayin shiga account. Don Allah ka sake gwadawa."
        )
    
    await state.clear()

@router.message(UserStates.waiting_for_bank_details)
async def handle_bank_details(message: types.Message, state: FSMContext):
    """Handle bank details for withdrawal"""
    bank_details = message.text.strip()
    
    if not validate_bank_details(bank_details):
        await message.answer(
            "Bayanin banki ba daidai ba ne. Don Allah ka tura kamar haka:\n"
            "9131085651 OPay Bashir Rabiu"
        )
        return
    
    user_id = message.from_user.id
    account_count = await db.get_pending_accounts(user_id)
    
    if account_count == 0:
        await message.answer("Ba ka da accounts da suke shirye don biya.")
        await state.clear()
        return
    
    # Add withdrawal request
    await db.add_withdrawal_request(user_id, bank_details, account_count)
    
    await message.answer(
        f"✅ An karbi buƙatar biya.\n"
        f"Adadin accounts: {account_count}\n"
        f"Admin zai tura maka kuɗin ka akan lokaci."
    )
    
    # Notify admin
    if ADMIN_ID:
        admin_message = (
            f"🔔 BUKATAR BIYA!\n\n"
            f"User ID: {user_id} (Username: @{message.from_user.username or 'Unknown'})\n"
            f"Bukatar biya don accounts guda: {account_count}\n"
            f"Bayanan Banki: {bank_details}\n\n"
            f"Danna /mark_paid {user_id} {account_count} don tabbatar da biyan."
        )
        
        try:
            await message.bot.send_message(ADMIN_ID, admin_message)
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    await state.clear()
