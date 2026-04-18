import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# Cloud Run sets K_SERVICE environment variable
if os.environ.get("K_SERVICE"):
    DB_PATH = "/tmp/system.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "system.db")

def init_db():
    """Initializes the database schema if it doesn't exist."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Tasks Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    due_date TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Calendar Events Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calendar_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    meet_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Notes Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Generic Action Logs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_name TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully at %s", DB_PATH)
    except sqlite3.Error as e:
        logger.error("Failed to initialize database: %s", e)

def get_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

# Ensure DB is initialized when this module is run or imported
init_db()

def get_full_state():
    """Fetches the state from tasks, calendar_events, notes, and action_logs."""
    try:
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            tasks = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM calendar_events ORDER BY created_at DESC")
            events = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM notes ORDER BY created_at DESC")
            notes = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM action_logs ORDER BY created_at DESC")
            logs = [dict(row) for row in cursor.fetchall()]
            
            return {
                "tasks": tasks,
                "calendar_events": events,
                "notes": notes,
                "action_logs": logs
            }
    except Exception as e:
        logger.error(f"Error fetching full state: {e}")
        return {"tasks": [], "calendar_events": [], "notes": [], "action_logs": []}
