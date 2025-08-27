import sqlite3
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class StorageHandler:
    def __init__(self, db_path: str = "data/captures.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._init_db()
        
    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    char_count INTEGER NOT NULL,
                    word_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_app_name ON captures(app_name);
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON captures(created_at);
            """)
            
            conn.commit()
            conn.close()
            
    def save_capture(self, buffer_info: Dict) -> bool:
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO captures 
                    (app_name, content, start_time, end_time, char_count, word_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    buffer_info["app_name"],
                    buffer_info["content"],
                    buffer_info["start_time"].isoformat(),
                    buffer_info["end_time"].isoformat(),
                    buffer_info["char_count"],
                    buffer_info["word_count"],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                conn.close()
                return True
                
        except Exception as e:
            print(f"Error saving capture: {e}")
            return False
            
    def save_multiple_captures(self, captures: Dict[str, Dict]) -> int:
        saved_count = 0
        
        for app_name, buffer_info in captures.items():
            if self.save_capture(buffer_info):
                saved_count += 1
                
        return saved_count
        
    def get_recent_captures(self, limit: int = 50) -> List[Dict]:
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, app_name, content, start_time, end_time, 
                           char_count, word_count, created_at
                    FROM captures 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    results.append({
                        "id": row[0],
                        "app_name": row[1],
                        "content": row[2],
                        "start_time": row[3],
                        "end_time": row[4],
                        "char_count": row[5],
                        "word_count": row[6],
                        "created_at": row[7]
                    })
                    
                return results
                
        except Exception as e:
            print(f"Error retrieving captures: {e}")
            return []
            
    def get_captures_by_app(self, app_name: str, limit: int = 20) -> List[Dict]:
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, app_name, content, start_time, end_time, 
                           char_count, word_count, created_at
                    FROM captures 
                    WHERE app_name = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (app_name, limit))
                
                rows = cursor.fetchall()
                conn.close()
                
                results = []
                for row in rows:
                    results.append({
                        "id": row[0],
                        "app_name": row[1],
                        "content": row[2],
                        "start_time": row[3],
                        "end_time": row[4],
                        "char_count": row[5],
                        "word_count": row[6],
                        "created_at": row[7]
                    })
                    
                return results
                
        except Exception as e:
            print(f"Error retrieving captures for {app_name}: {e}")
            return []
            
    def get_statistics(self) -> Dict:
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM captures")
                total_captures = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT app_name) FROM captures")
                unique_apps = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(char_count) FROM captures")
                total_chars = cursor.fetchone()[0] or 0
                
                cursor.execute("SELECT SUM(word_count) FROM captures")
                total_words = cursor.fetchone()[0] or 0
                
                cursor.execute("""
                    SELECT app_name, COUNT(*) as count
                    FROM captures 
                    GROUP BY app_name 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_apps = cursor.fetchall()
                
                conn.close()
                
                return {
                    "total_captures": total_captures,
                    "unique_apps": unique_apps,
                    "total_characters": total_chars,
                    "total_words": total_words,
                    "top_apps": [{"app": app, "captures": count} for app, count in top_apps]
                }
                
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}