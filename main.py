import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database
from services.session_manager import SessionManager
from services.otp_forwarder import OTPForwarder
from services.scheduler import BotScheduler
from handlers import user_handlers, admin_handlers
from config import BOT_TOKEN

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main bot function"""
    try:
        # Initialize bot and dispatcher
        bot = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Initialize database
        db = Database()
        await db.init_db()
        logger.info("Database initialized")
        
        # Initialize services
        session_manager = SessionManager()
        otp_forwarder = OTPForwarder(bot, session_manager)
        scheduler = BotScheduler(bot)
        
        # Set services in handlers
        user_handlers.set_services(otp_forwarder, scheduler)
        
        # Include routers
        dp.include_router(user_handlers.router)
        dp.include_router(admin_handlers.router)
        
        # Start scheduler
        scheduler_task = asyncio.create_task(scheduler.start_scheduler())
        
        logger.info("Bot starting...")
        
        # Start polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Cleanup
        if 'scheduler_task' in locals():
            scheduler_task.cancel()
        
        if 'session_manager' in locals():
            await session_manager.cleanup_all_sessions()
        
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
