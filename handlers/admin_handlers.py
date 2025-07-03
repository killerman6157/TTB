from aiogram import Router, types
from aiogram.filters import Command
from database import Database
from services.session_manager import SessionManager
from config import ADMIN_ID, CHANNEL_ID
import logging

logger = logging.getLogger(__name__)

router = Router()
db = Database()
session_manager = SessionManager()

def admin_only(func):
    """Decorator to restrict commands to admin only"""
    async def wrapper(message: types.Message, *args, **kwargs):
        if message.from_user.id != ADMIN_ID:
            await message.answer("❌ Ba ka da izinin amfani da wannan umarnin.")
            return
        return await func(message, *args, **kwargs)
    return wrapper

@router.message(Command("user_accounts"))
@admin_only
async def user_accounts_command(message: types.Message):
    """Show accounts for a specific user"""
    try:
        # Extract user ID from command
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "Amfani: /user_accounts [User ID]\n"
                "Misali: /user_accounts 123456789"
            )
            return
        
        user_id = int(parts[1])
        accounts = await db.get_user_accounts(user_id)
        pending_count = await db.get_pending_accounts(user_id)
        
        if not accounts:
            await message.answer(f"User ID {user_id} ba shi da accounts.")
            return
        
        response = f"👤 User ID {user_id} Accounts:\n\n"
        response += f"📊 Accounts da suke shirye don biya: {pending_count}\n\n"
        
        for phone, status in accounts:
            status_emoji = {
                'pending': '⏳',
                'accepted': '✅',
                'verified': '🔐',
                'paid': '💰',
                'rejected': '❌'
            }.get(status, '❓')
            
            response += f"{status_emoji} {phone} — {status}\n"
        
        await message.answer(response)
        
    except ValueError:
        await message.answer("User ID dole ya zama lamba.")
    except Exception as e:
        logger.error(f"Error in user_accounts command: {e}")
        await message.answer("Kuskure ya faru.")

@router.message(Command("mark_paid"))
@admin_only
async def mark_paid_command(message: types.Message):
    """Mark accounts as paid for a user"""
    try:
        # Extract user ID and count from command
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer(
                "Amfani: /mark_paid [User ID] [Adadin Accounts]\n"
                "Misali: /mark_paid 123456789 5"
            )
            return
        
        user_id = int(parts[1])
        paid_count = int(parts[2])
        
        # Verify user has enough pending accounts
        pending_count = await db.get_pending_accounts(user_id)
        if pending_count < paid_count:
            await message.answer(
                f"❌ User ID {user_id} yana da accounts {pending_count} kawai "
                f"da suke shirye don biya, ba {paid_count} ba."
            )
            return
        
        # Mark as paid
        await db.mark_accounts_paid(user_id, paid_count)
        
        await message.answer(
            f"✅ An yiwa User ID {user_id} alamar biya don accounts guda {paid_count}. "
            f"An cire su daga jerin biyan da ake jira, an kuma sanya su a matsayin "
            f"wanda aka biya."
        )
        
        # Notify the user
        try:
            await message.bot.send_message(
                user_id,
                f"✅ An biya ku don accounts guda {paid_count}. "
                f"Na gode da kasuwanci!"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
    except ValueError:
        await message.answer("User ID da adadin accounts dole su zama lambobi.")
    except Exception as e:
        logger.error(f"Error in mark_paid command: {e}")
        await message.answer("Kuskure ya faru.")

@router.message(Command("stats"))
@admin_only
async def stats_command(message: types.Message):
    """Show account statistics"""
    try:
        stats = await db.get_account_stats()
        
        if not stats:
            await message.answer("📊 Babu bayani a halin yanzu.")
            return
        
        response = "📊 *Statistics:*\n\n"
        
        total_accounts = 0
        for status, count in stats:
            status_emoji = {
                'pending': '⏳',
                'accepted': '✅',
                'verified': '🔐',
                'paid': '💰',
                'rejected': '❌'
            }.get(status, '❓')
            
            response += f"{status_emoji} {status}: {count}\n"
            total_accounts += count
        
        response += f"\n📈 Jimillar accounts: {total_accounts}"
        
        await message.answer(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.answer("Kuskure ya faru.")

@router.message(Command("completed_today_payment"))
@admin_only
async def completed_payment_command(message: types.Message):
    """Mark today's payments as completed and notify channel"""
    try:
        await message.answer("✅ An kammala biyan kuɗi na yau.")
        
        # Send notification to channel
        if CHANNEL_ID:
            channel_message = (
                "🔔 SANARWA: An biya duk wanda ya nemi biya yau! "
                "Muna maku fatan alheri, sai gobe karfe 8:00 na safe."
            )
            
            try:
                await message.bot.send_message(CHANNEL_ID, channel_message)
                await message.answer("📢 An tura sanarwa zuwa channel.")
            except Exception as e:
                logger.error(f"Failed to send to channel: {e}")
                await message.answer("❌ An gaza tura sanarwa zuwa channel.")
        else:
            await message.answer("⚠️ Channel ID ba a saita ba.")
            
    except Exception as e:
        logger.error(f"Error in completed_payment command: {e}")
        await message.answer("Kuskure ya faru.")

@router.message(Command("accept"))
@admin_only
async def accept_account_command(message: types.Message):
    """Accept and verify an account"""
    try:
        # Extract user ID and phone from command
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer(
                "Amfani: /accept [User ID] [Phone Number]\n"
                "Misali: /accept 123456789 +2348167757987"
            )
            return
        
        user_id = int(parts[1])
        phone_number = parts[2]
        
        # Update account status to verified
        await db.update_account_status(phone_number, 'verified')
        
        await message.answer(
            f"✅ An tabbatar da karɓar account {phone_number} "
            f"daga User ID {user_id}. Yanzu seller yana da damar buƙatar biya."
        )
        
        # Notify the seller
        try:
            await message.bot.send_message(
                user_id,
                f"✅ An tabbatar da account din ku {phone_number}. "
                f"Yanzu kuna iya yin buƙatar biya ta /withdraw."
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
        
    except ValueError:
        await message.answer("User ID dole ya zama lamba.")
    except Exception as e:
        logger.error(f"Error in accept command: {e}")
        await message.answer("Kuskure ya faru.")

@router.message(Command("sessions"))
@admin_only
async def sessions_command(message: types.Message):
    """Show active sessions"""
    try:
        active_sessions = list(session_manager.active_sessions.keys())
        
        if not active_sessions:
            await message.answer("📱 Babu active sessions a halin yanzu.")
            return
        
        response = "📱 Active Sessions:\n\n"
        for i, phone in enumerate(active_sessions, 1):
            response += f"{i}. {phone}\n"
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error in sessions command: {e}")
        await message.answer("Kuskure ya faru.")
