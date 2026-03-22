import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "mindmate.db"

def get_db_connection():
    """Get a database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        init_db(conn)  # Ensure tables exist on connection
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

def get_journal_stats(user_id: str = "default_user") -> dict:
    """Get journal statistics including total entries and average mood"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get total entries
            cursor.execute("""
                SELECT COUNT(*) as total_entries, 
                       AVG(mood_score) as avg_mood
                FROM journal_entries
                WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            return {
                "total_entries": result["total_entries"] or 0,
                "avg_mood": result["avg_mood"] or 0
            }
    except Exception as e:
        logger.error(f"Failed to get journal stats: {str(e)}")
        return {"total_entries": 0, "avg_mood": 0}

def get_meditation_stats(user_id: str = "default_user") -> dict:
    """Get meditation statistics including total minutes"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get total minutes
            cursor.execute("""
                SELECT SUM(minutes) as total_minutes
                FROM meditation_sessions
                WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            return {
                "total_minutes": result["total_minutes"] or 0
            }
    except Exception as e:
        logger.error(f"Failed to get meditation stats: {str(e)}")
        return {"total_minutes": 0}

def get_user_data(user_id: str = "default_user") -> tuple:
    """Get comprehensive user wellness data including mood, sleep and meditation stats
    
    Returns:
        tuple: (mood_data, sleep_data, meditation_data)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get mood data
            cursor.execute("""
                SELECT COALESCE(AVG(mood_score), 0) as average,
                       COALESCE(COUNT(*), 0) as count,
                       COALESCE(AVG(mood_score), 0) - (
                           SELECT COALESCE(AVG(mood_score), 0)
                           FROM mood_entries 
                           WHERE user_id = ? 
                           AND timestamp > datetime('now', '-7 days')
                       ) as change,
                       GROUP_CONCAT(DISTINCT tags) as tags,
                       json_group_array(
                           json_object(
                               'date', date(timestamp),
                               'rating', mood_score
                           )
                       ) as history,
                       json_group_array(
                           json_object(
                               'date', date(timestamp),
                               'text', notes
                           )
                       ) as journal_entries
                FROM mood_entries
                WHERE user_id = ?
            """, (user_id, user_id))
            mood_data = dict(cursor.fetchone())
            
            # Get sleep data
            cursor.execute("""
                SELECT COALESCE(AVG(sleep_time), 0) as hours,
                       COALESCE(AVG(sleep_quality), 0) as quality,
                       COALESCE(AVG(sleep_time), 0) - (
                           SELECT COALESCE(AVG(sleep_time), 0)
                           FROM sleep_data
                           WHERE user_id = ?
                           AND date > date('now', '-7 days')
                       ) as change,
                       json_group_array(
                           json_object(
                               'date', date,
                               'hours', sleep_time
                           )
                       ) as history
                FROM sleep_data
                WHERE user_id = ?
            """, (user_id, user_id))
            sleep_data = dict(cursor.fetchone())
            
            # Get meditation data
            cursor.execute("""
                SELECT COALESCE(COUNT(*), 0) as sessions,
                       COALESCE(SUM(minutes), 0) as minutes,
                       json_group_array(
                           json_object(
                               'date', date(timestamp),
                               'minutes', minutes
                           )
                       ) as history
                FROM meditation_sessions
                WHERE user_id = ?
            """, (user_id,))
            meditation_data = dict(cursor.fetchone())
            
            return (mood_data, sleep_data, meditation_data)
            
    except Exception as e:
        logger.error(f"Failed to get user data: {str(e)}")
        return (
            {"average": 0, "count": 0, "change": 0, "tags": "", "history": "[]", "journal_entries": "[]"},
            {"hours": 0, "quality": 0, "change": 0, "history": "[]"},
            {"sessions": 0, "minutes": 0, "history": "[]"}
        )

def init_db(conn=None):
    """Initialize the database with required tables"""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        if conn is None:
            conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create journal entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    entry_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    mood_score REAL NOT NULL,
                    keywords TEXT
                )
            """)
            
        # Create meditation sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meditation_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    session_type TEXT NOT NULL,
                    minutes INTEGER NOT NULL,
                    notes TEXT
                )
            """)
            
        # Create mood entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mood_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    mood_score INTEGER NOT NULL,
                    notes TEXT,
                    tags TEXT
                )
            """)
            
        # Create sleep data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sleep_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date DATE NOT NULL,
                    sleep_time INTEGER NOT NULL,
                    sleep_quality INTEGER NOT NULL,
                    notes TEXT
                )
            """)
            
        # Create goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    created_date DATETIME NOT NULL,
                    target_date DATE NOT NULL,
                    target_value INTEGER NOT NULL,
                    progress INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0
                )
            """)
            
        # Create community posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    likes INTEGER DEFAULT 0
                )
            """)
            
        # Create professional help resources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professional_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    description TEXT,
                    rating REAL
                )
            """)

        # Create professional appointment requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS professional_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    preferred_professional TEXT,
                    appointment_date DATE NOT NULL,
                    appointment_time TEXT NOT NULL,
                    concerns TEXT NOT NULL,
                    status TEXT DEFAULT 'Pending',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

        # Create mood_tracker table (alias for mood_entries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mood_tracker (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    mood_score INTEGER NOT NULL,
                    notes TEXT,
                    tags TEXT
                )
            """)

        # Create chatbot_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chatbot_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    response_helpful INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    is_admin BOOLEAN DEFAULT 0
                )
            """)

        # Create RPG character table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rpg_characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    archetype TEXT NOT NULL,
                    stats TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

        # Create RPG quests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rpg_quests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    quest_name TEXT NOT NULL,
                    xp_earned INTEGER NOT NULL,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

        # Create RPG skills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rpg_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    skill_name TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    progress INTEGER DEFAULT 0,
                    last_practiced TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
        conn.commit()
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
