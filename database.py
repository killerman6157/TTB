import aiosqlite
import asyncio
from datetime import datetime
from config import DB_NAME

class Database:
    def __init__(self):
        self.db_name = DB_NAME
    
    async def init_db(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_name) as db:
            # User accounts table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    phone_number TEXT NOT NULL UNIQUE,
                    status TEXT DEFAULT 'pending',
                    session_file TEXT,
                    buyer_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Withdrawal requests table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS withdrawal_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    bank_details TEXT NOT NULL,
                    account_count INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            ''')
            
            # OTP forwarding table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS otp_forwards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL,
                    buyer_id INTEGER NOT NULL,
                    otp_message TEXT NOT NULL,
                    forwarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # System settings table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    async def add_user_account(self, user_id: int, username: str, phone_number: str):
        """Add a new user account"""
        async with aiosqlite.connect(self.db_name) as db:
            try:
                await db.execute('''
                    INSERT INTO user_accounts (user_id, username, phone_number)
                    VALUES (?, ?, ?)
                ''', (user_id, username, phone_number))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False  # Phone number already exists
    
    async def update_account_status(self, phone_number: str, status: str, session_file: str = None, buyer_id: int = None):
        """Update account status and details"""
        async with aiosqlite.connect(self.db_name) as db:
            query = "UPDATE user_accounts SET status = ?, updated_at = CURRENT_TIMESTAMP"
            params = [status]
            
            if session_file:
                query += ", session_file = ?"
                params.append(session_file)
            
            if buyer_id:
                query += ", buyer_id = ?"
                params.append(buyer_id)
            
            query += " WHERE phone_number = ?"
            params.append(phone_number)
            
            await db.execute(query, params)
            await db.commit()
    
    async def get_user_accounts(self, user_id: int):
        """Get all accounts for a user"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
                SELECT phone_number, status FROM user_accounts 
                WHERE user_id = ?
            ''', (user_id,))
            return await cursor.fetchall()
    
    async def get_pending_accounts(self, user_id: int):
        """Get pending accounts count for a user"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM user_accounts 
                WHERE user_id = ? AND status IN ('accepted', 'verified')
            ''', (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def add_withdrawal_request(self, user_id: int, bank_details: str, account_count: int):
        """Add a withdrawal request"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO withdrawal_requests (user_id, bank_details, account_count)
                VALUES (?, ?, ?)
            ''', (user_id, bank_details, account_count))
            await db.commit()
    
    async def mark_accounts_paid(self, user_id: int, paid_count: int):
        """Mark accounts as paid for a user"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                UPDATE user_accounts 
                SET status = 'paid', updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND status IN ('accepted', 'verified')
                LIMIT ?
            ''', (user_id, paid_count))
            
            await db.execute('''
                UPDATE withdrawal_requests 
                SET status = 'completed', processed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND status = 'pending'
            ''', (user_id,))
            
            await db.commit()
    
    async def get_account_stats(self):
        """Get account statistics"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
                SELECT status, COUNT(*) FROM user_accounts GROUP BY status
            ''')
            return await cursor.fetchall()
    
    async def get_buyer_by_phone(self, phone_number: str):
        """Get buyer ID for a phone number"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
                SELECT buyer_id FROM user_accounts 
                WHERE phone_number = ? AND buyer_id IS NOT NULL
            ''', (phone_number,))
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def log_otp_forward(self, phone_number: str, buyer_id: int, otp_message: str):
        """Log OTP forwarding activity"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute('''
                INSERT INTO otp_forwards (phone_number, buyer_id, otp_message)
                VALUES (?, ?, ?)
            ''', (phone_number, buyer_id, otp_message))
            await db.commit()
    
    async def is_operating_hours(self):
        """Check if bot is in operating hours"""
        current_hour = datetime.now().hour
        return 8 <= current_hour < 22  # 8 AM to 10 PM WAT
    
    async def phone_exists(self, phone_number: str):
        """Check if phone number already exists"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM user_accounts WHERE phone_number = ?
            ''', (phone_number,))
            result = await cursor.fetchone()
            return result[0] > 0
