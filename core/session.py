"""
Session Manager - Manages user sessions and state

Handles user data, current pattern info, step progress, and color edits.
Uses SQLite for persistence.
"""

import sqlite3
import json
import os
from datetime import datetime

class SessionManager:
    """Manages user sessions and pattern state"""
    
    def __init__(self, db_path="data/sessions.db"):
        """
        Initialize session manager.
        
        Args:
            db_path (str): Path to SQLite database
        """
        self.db_path = db_path
        self._ensure_database()
    
    def _ensure_database(self):
        """Create database and tables if they don't exist"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                language_code TEXT DEFAULT 'ar',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                image_path TEXT,
                original_image_path TEXT,
                pattern_size INTEGER,
                colors_json TEXT,
                grid_path TEXT,
                palette_path TEXT,
                current_step INTEGER DEFAULT 1,
                total_steps INTEGER,
                color_edits_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, user_id, username=None, first_name=None, language_code='ar'):
        """Register or update user info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, language_code, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, language_code, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def create_session(self, user_id, image_path, original_image_path):
        """
        Create new session for user.
        
        Returns:
            str: Session ID
        """
        session_id = f"{user_id}_{int(datetime.now().timestamp())}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (session_id, user_id, image_path, original_image_path)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, image_path, original_image_path))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def update_session(self, session_id, **kwargs):
        """
        Update session data.
        
        Kwargs can include:
            pattern_size, colors_json, grid_path, palette_path,
            current_step, total_steps, color_edits_json
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build update query dynamically
        updates = []
        values = []
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            values.append(value)
        
        values.append(session_id)
        
        query = f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def get_session(self, session_id):
        """Get session data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_user_latest_session(self, user_id):
        """Get user's most recent session"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sessions 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def save_color_edits(self, session_id, color_edits):
        """
        Save color edits for session.
        
        Args:
            session_id (str): Session ID
            color_edits (dict): Dictionary of step edits
        """
        edits_json = json.dumps(color_edits, ensure_ascii=False)
        self.update_session(session_id, color_edits_json=edits_json)
    
    def get_color_edits(self, session_id):
        """Get color edits for session"""
        session = self.get_session(session_id)
        if session and session.get('color_edits_json'):
            return json.loads(session['color_edits_json'])
        return {}
    
    def set_current_step(self, session_id, step_number):
        """Update current step number"""
        self.update_session(session_id, current_step=step_number)
    
    def get_current_step(self, session_id):
        """Get current step number"""
        session = self.get_session(session_id)
        return session.get('current_step', 1) if session else 1


# Testing
if __name__ == "__main__":
    print("🔧 Testing SessionManager...")
    
    # Clean test database
    import tempfile
    test_db = os.path.join(tempfile.gettempdir(), "test_sessions.db")
    if os.path.exists(test_db):
        os.remove(test_db)
    
    mgr = SessionManager(test_db)
    
    print("✅ Database created")
    
    # Test user registration
    mgr.register_user(12345, "test_user", "Test User")
    print("✅ User registered")
    
    # Test session creation
    session_id = mgr.create_session(12345, "/path/to/image.jpg", "/path/to/original.jpg")
    print(f"✅ Session created: {session_id}")
    
    # Test session update
    mgr.update_session(session_id, pattern_size=150, total_steps=100)
    print("✅ Session updated")
    
    # Test retrieval
    session = mgr.get_session(session_id)
    print(f"✅ Session retrieved: {session['pattern_size']} stitches, {session['total_steps']} steps")
    
    # Test color edits
    color_edits = {'step_5': {'new_color': 'أبيض'}}
    mgr.save_color_edits(session_id, color_edits)
    retrieved_edits = mgr.get_color_edits(session_id)
    print(f"✅ Color edits saved and retrieved: {retrieved_edits}")
    
    print("\n🎉 All tests passed!")
