"""Database models and operations for persistent storage."""

from datetime import datetime
from typing import List, Optional
import json
import sqlite3
from pathlib import Path

# Database file location
DB_PATH = Path(__file__).parent / "jobshop.db"


class Database:
    """Simple SQLite database for storing instances and solutions."""
    
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Custom instances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Solutions history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS solutions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instance_name TEXT NOT NULL,
                status TEXT NOT NULL,
                makespan INTEGER,
                operations TEXT,
                solver_statistics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instance_name) REFERENCES instances(name)
            )
        ''')
        
        # Webhooks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                event TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_instance(self, name: str, description: str, data: dict) -> int:
        """Save or update a custom instance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        data_json = json.dumps(data)
        
        cursor.execute('''
            INSERT INTO instances (name, description, data, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                description = excluded.description,
                data = excluded.data,
                updated_at = CURRENT_TIMESTAMP
        ''', (name, description, data_json))
        
        instance_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return instance_id
    
    def get_instance(self, name: str) -> Optional[dict]:
        """Retrieve an instance by name."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT data FROM instances WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def get_all_instances(self) -> List[dict]:
        """Get all custom instances."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, description, created_at, updated_at
            FROM instances
            ORDER BY updated_at DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "name": row[0],
                "description": row[1],
                "created_at": row[2],
                "updated_at": row[3]
            }
            for row in rows
        ]
    
    def delete_instance(self, name: str) -> bool:
        """Delete an instance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM instances WHERE name = ?', (name,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def save_solution(self, instance_name: str, status: str, makespan: Optional[int],
                     operations: list, solver_stats: dict) -> int:
        """Save a solution to history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO solutions (instance_name, status, makespan, operations, solver_statistics)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            instance_name,
            status,
            makespan,
            json.dumps(operations),
            json.dumps(solver_stats)
        ))
        
        solution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return solution_id
    
    def get_solution_history(self, instance_name: str, limit: int = 10) -> List[dict]:
        """Get solution history for an instance."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, status, makespan, created_at
            FROM solutions
            WHERE instance_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (instance_name, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "status": row[1],
                "makespan": row[2],
                "created_at": row[3]
            }
            for row in rows
        ]
    
    def register_webhook(self, url: str, event: str) -> int:
        """Register a webhook."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO webhooks (url, event)
            VALUES (?, ?)
        ''', (url, event))
        
        webhook_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return webhook_id
    
    def get_webhooks(self, event: Optional[str] = None) -> List[dict]:
        """Get active webhooks."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if event:
            cursor.execute('SELECT id, url, event FROM webhooks WHERE active = 1 AND event = ?', (event,))
        else:
            cursor.execute('SELECT id, url, event FROM webhooks WHERE active = 1')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{"id": row[0], "url": row[1], "event": row[2]} for row in rows]
    
    def create_notification(self, type_: str, message: str, data: Optional[dict] = None) -> int:
        """Create a notification."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (type, message, data)
            VALUES (?, ?, ?)
        ''', (type_, message, json.dumps(data) if data else None))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return notification_id
    
    def get_notifications(self, unread_only: bool = False, limit: int = 50) -> List[dict]:
        """Get notifications."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if unread_only:
            cursor.execute('''
                SELECT id, type, message, data, read, created_at
                FROM notifications
                WHERE read = 0
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT id, type, message, data, read, created_at
                FROM notifications
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "type": row[1],
                "message": row[2],
                "data": json.loads(row[3]) if row[3] else None,
                "read": bool(row[4]),
                "created_at": row[5]
            }
            for row in rows
        ]
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark a notification as read."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE notifications SET read = 1 WHERE id = ?', (notification_id,))
        updated = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return updated


# Global database instance
db = Database()
