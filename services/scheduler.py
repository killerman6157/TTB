import asyncio
from datetime import datetime, time, timedelta
import pytz
from database import Database
import logging

logger = logging.getLogger(__name__)

class BotScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.is_operating = True
        self.watt_timezone = pytz.timezone('Africa/Lagos')  # WAT timezone
    
    async def start_scheduler(self):
        """Start the scheduler"""
        logger.info("Bot scheduler started")
        while True:
            try:
                await self.check_operating_hours()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    async def check_operating_hours(self):
        """Check and update operating hours"""
        now = datetime.now(self.watt_timezone)
        current_hour = now.hour
        
        # Operating hours: 8 AM to 10 PM WAT
        should_be_operating = 8 <= current_hour < 22
        
        if should_be_operating != self.is_operating:
            self.is_operating = should_be_operating
            
            if self.is_operating:
                logger.info("Bot is now OPEN for account receiving (8:00 AM WAT)")
            else:
                logger.info("Bot is now CLOSED for account receiving (10:00 PM WAT)")
    
    def is_operating_hours(self) -> bool:
        """Check if currently in operating hours"""
        return self.is_operating
    
    def get_next_opening_time(self) -> str:
        """Get next opening time message"""
        now = datetime.now(self.watt_timezone)
        
        if now.hour >= 22:
            # After 10 PM, next opening is tomorrow 8 AM
            next_opening = now.replace(hour=8, minute=0, second=0, microsecond=0)
            next_opening += timedelta(days=1)
        else:
            # Before 8 AM, opening is today 8 AM
            next_opening = now.replace(hour=8, minute=0, second=0, microsecond=0)
        
        return next_opening.strftime("gobe karfe 8:00 na safe")
    
    def get_next_closing_time(self) -> str:
        """Get next closing time message"""
        now = datetime.now(self.watt_timezone)
        
        if now.hour < 22:
            next_closing = now.replace(hour=22, minute=0, second=0, microsecond=0)
            return next_closing.strftime("yau karfe 10:00 na dare")
        else:
            return "an riga an rufe"
