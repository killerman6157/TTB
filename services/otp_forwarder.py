import asyncio
from telethon import events
from telethon.tl.types import User
from database import Database
from utils.validators import is_otp_message
from config import BUYER_ID
import logging

logger = logging.getLogger(__name__)

class OTPForwarder:
    def __init__(self, bot, session_manager):
        self.bot = bot
        self.session_manager = session_manager
        self.db = Database()
        self.forwarding_active = {}
    
    async def start_forwarding(self, phone_number: str, buyer_id: int = None):
        """Start OTP forwarding for a phone number"""
        if not buyer_id:
            buyer_id = BUYER_ID
        
        client = await self.session_manager.get_session(phone_number)
        if not client:
            logger.error(f"No session found for {phone_number}")
            return False
        
        # Add event handler for new messages
        @client.on(events.NewMessage(from_users=777000))  # Telegram system bot
        async def handle_system_message(event):
            try:
                message_text = event.message.message
                
                # Check if it's an OTP message
                if is_otp_message(message_text):
                    # Forward to buyer
                    await self.bot.send_message(
                        buyer_id,
                        f"📨 OTP daga Telegram account {phone_number}:\n\n{message_text}"
                    )
                    
                    # Log the forward
                    await self.db.log_otp_forward(phone_number, buyer_id, message_text)
                    logger.info(f"OTP forwarded from {phone_number} to buyer {buyer_id}")
                
            except Exception as e:
                logger.error(f"Error forwarding OTP from {phone_number}: {e}")
        
        # Add handler for any incoming messages that might be OTP
        @client.on(events.NewMessage)
        async def handle_all_messages(event):
            try:
                # Skip if sender is the account owner
                if event.sender_id == await client.get_me():
                    return
                
                message_text = event.message.message
                sender = await event.get_sender()
                
                # Check for Telegram official messages
                if isinstance(sender, User) and (
                    sender.bot and sender.verified or 
                    sender.id == 777000 or  # Telegram system
                    'telegram' in (sender.username or '').lower()
                ):
                    if is_otp_message(message_text):
                        await self.bot.send_message(
                            buyer_id,
                            f"🔐 OTP daga Telegram system ({phone_number}):\n\n{message_text}"
                        )
                        
                        await self.db.log_otp_forward(phone_number, buyer_id, message_text)
                        logger.info(f"System OTP forwarded from {phone_number}")
                
            except Exception as e:
                logger.error(f"Error handling message from {phone_number}: {e}")
        
        self.forwarding_active[phone_number] = True
        logger.info(f"OTP forwarding started for {phone_number}")
        return True
    
    async def stop_forwarding(self, phone_number: str):
        """Stop OTP forwarding for a phone number"""
        if phone_number in self.forwarding_active:
            self.forwarding_active[phone_number] = False
            logger.info(f"OTP forwarding stopped for {phone_number}")
    
    async def is_forwarding_active(self, phone_number: str) -> bool:
        """Check if forwarding is active for phone number"""
        return self.forwarding_active.get(phone_number, False)
