import sqlite3
import json
import threading
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from difflib import SequenceMatcher


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
            
            # Create full-text search index for content
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS captures_fts USING fts5(
                    id UNINDEXED, app_name, content, created_at UNINDEXED,
                    content='captures', content_rowid='id'
                );
            """)
            
            # Check if FTS table needs to be populated
            cursor.execute("SELECT COUNT(*) FROM captures_fts")
            fts_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM captures")
            captures_count = cursor.fetchone()[0]
            
            # If FTS table is empty or out of sync, rebuild it
            if fts_count != captures_count:
                cursor.execute("DELETE FROM captures_fts")
                cursor.execute("""
                    INSERT INTO captures_fts(id, app_name, content, created_at)
                    SELECT id, app_name, content, created_at FROM captures;
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
                
                # Also insert into FTS table
                capture_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO captures_fts(id, app_name, content, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    capture_id,
                    buffer_info["app_name"],
                    buffer_info["content"],
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
    
    def fuzzy_search(self, query: str, limit: int = 50, app_filter: Optional[str] = None, min_score: float = 0.3) -> List[Dict]:
        """
        Perform fuzzy search across captured content
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            app_filter: Filter results by specific app name
            min_score: Minimum relevance score threshold (0.0 to 1.0)
            
        Returns:
            List of captures with relevance scores and snippets
        """
        if not query.strip():
            return []
            
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # First try FTS5 search for exact/prefix matches
                fts_results = self._fts_search(cursor, query, limit, app_filter)
                
                # If FTS doesn't return enough results, do fuzzy matching
                if len(fts_results) < limit:
                    remaining_limit = limit - len(fts_results)
                    fuzzy_results = self._fuzzy_search_fallback(cursor, query, remaining_limit, app_filter, min_score)
                    
                    # Combine results, removing duplicates
                    seen_ids = {result['id'] for result in fts_results}
                    for result in fuzzy_results:
                        if result['id'] not in seen_ids:
                            fts_results.append(result)
                
                conn.close()
                
                # Sort by relevance score (descending) and recency
                results = sorted(fts_results, key=lambda x: (x['relevance_score'], x['created_at']), reverse=True)
                
                return results[:limit]
                
        except Exception as e:
            print(f"Error performing fuzzy search: {e}")
            return []
    
    def _fts_search(self, cursor, query: str, limit: int, app_filter: Optional[str]) -> List[Dict]:
        """Use SQLite FTS5 for fast full-text search"""
        
        # Prepare FTS5 query - escape special characters and add fuzzy matching
        fts_query = self._prepare_fts_query(query)
        
        sql = """
            SELECT c.id, c.app_name, c.content, c.start_time, c.end_time, 
                   c.char_count, c.word_count, c.created_at,
                   fts.rank as fts_rank
            FROM captures_fts fts
            JOIN captures c ON c.id = fts.id
            WHERE captures_fts MATCH ?
        """
        params = [fts_query]
        
        if app_filter:
            sql += " AND c.app_name = ?"
            params.append(app_filter)
            
        sql += " ORDER BY fts.rank, c.created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            snippet = self._extract_snippet(row[2], query)
            relevance_score = self._calculate_fts_score(row[2], query, row[8])
            
            results.append({
                "id": row[0],
                "app_name": row[1],
                "content": row[2],
                "start_time": row[3],
                "end_time": row[4],
                "char_count": row[5],
                "word_count": row[6],
                "created_at": row[7],
                "relevance_score": relevance_score,
                "snippet": snippet
            })
        
        return results
    
    def _fuzzy_search_fallback(self, cursor, query: str, limit: int, app_filter: Optional[str], min_score: float) -> List[Dict]:
        """Fallback fuzzy search using string similarity"""
        
        sql = """
            SELECT id, app_name, content, start_time, end_time, 
                   char_count, word_count, created_at
            FROM captures
        """
        params = []
        
        if app_filter:
            sql += " WHERE app_name = ?"
            params.append(app_filter)
            
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit * 3)  # Get more candidates for fuzzy matching
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for row in rows:
            content_lower = row[2].lower()
            
            # Calculate fuzzy similarity
            similarity_score = self._calculate_fuzzy_score(content_lower, query_lower, query_words)
            
            if similarity_score >= min_score:
                snippet = self._extract_snippet(row[2], query)
                
                results.append({
                    "id": row[0],
                    "app_name": row[1],
                    "content": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "char_count": row[5],
                    "word_count": row[6],
                    "created_at": row[7],
                    "relevance_score": similarity_score,
                    "snippet": snippet
                })
        
        return sorted(results, key=lambda x: x['relevance_score'], reverse=True)[:limit]
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for FTS5 search"""
        # Remove special FTS5 characters and add prefix matching
        cleaned = re.sub(r'[^\w\s]', ' ', query)
        words = cleaned.split()
        
        # Add prefix matching with *
        fts_words = [f'"{word}"*' for word in words if len(word) >= 2]
        
        return ' OR '.join(fts_words) if fts_words else query
    
    def _calculate_fts_score(self, content: str, query: str, fts_rank: float) -> float:
        """Calculate relevance score for FTS results"""
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Count exact matches
        exact_matches = content_lower.count(query_lower)
        
        # Count word matches
        query_words = query_lower.split()
        word_matches = sum(1 for word in query_words if word in content_lower)
        
        # Calculate base score
        base_score = 0.8  # High score for FTS matches
        
        # Boost for exact matches
        exact_boost = min(exact_matches * 0.1, 0.2)
        
        # Boost for word coverage
        word_coverage = word_matches / len(query_words) if query_words else 0
        word_boost = word_coverage * 0.1
        
        return min(base_score + exact_boost + word_boost, 1.0)
    
    def _calculate_fuzzy_score(self, content: str, query: str, query_words: set) -> float:
        """Calculate fuzzy similarity score"""
        
        # String similarity using SequenceMatcher
        sequence_similarity = SequenceMatcher(None, content, query).ratio()
        
        # Word overlap score
        content_words = set(content.split())
        word_overlap = len(query_words.intersection(content_words)) / len(query_words) if query_words else 0
        
        # Partial word matches (substring matching)
        partial_matches = 0
        for query_word in query_words:
            for content_word in content_words:
                if len(query_word) >= 3 and query_word in content_word:
                    partial_matches += 1
                    break
        
        partial_score = partial_matches / len(query_words) if query_words else 0
        
        # Combined score with weights
        combined_score = (
            sequence_similarity * 0.3 +
            word_overlap * 0.5 +
            partial_score * 0.2
        )
        
        return combined_score
    
    def _extract_snippet(self, content: str, query: str, snippet_length: int = 200) -> str:
        """Extract relevant snippet around the query match"""
        if not query.strip():
            return content[:snippet_length] + ("..." if len(content) > snippet_length else "")
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Find the best match position
        best_pos = content_lower.find(query_lower)
        
        # If no exact match, try first word
        if best_pos == -1:
            query_words = query_lower.split()
            if query_words:
                best_pos = content_lower.find(query_words[0])
        
        # If still no match, return beginning
        if best_pos == -1:
            return content[:snippet_length] + ("..." if len(content) > snippet_length else "")
        
        # Calculate snippet boundaries
        start = max(0, best_pos - snippet_length // 3)
        end = min(len(content), start + snippet_length)
        
        # Adjust start if we're at the end
        if end - start < snippet_length:
            start = max(0, end - snippet_length)
        
        snippet = content[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def rebuild_fts_index(self):
        """Rebuild the FTS index from scratch"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Drop and recreate FTS table
                cursor.execute("DROP TABLE IF EXISTS captures_fts")
                cursor.execute("""
                    CREATE VIRTUAL TABLE captures_fts USING fts5(
                        id UNINDEXED, app_name, content, created_at UNINDEXED
                    );
                """)
                
                # Populate with all existing data
                cursor.execute("""
                    INSERT INTO captures_fts(id, app_name, content, created_at)
                    SELECT id, app_name, content, created_at FROM captures;
                """)
                
                conn.commit()
                conn.close()
                print("FTS index rebuilt successfully")
                
        except Exception as e:
            print(f"Error rebuilding FTS index: {e}")