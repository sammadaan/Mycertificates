import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import hashlib
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LegalText:
    """Data class for legal text entries"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    source: str = ""
    url: str = ""
    category: str = ""
    date_published: Optional[datetime] = None
    date_scraped: datetime = None
    content_hash: str = ""
    word_count: int = 0
    quality_score: float = 0.0
    is_processed: bool = False
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.date_scraped is None:
            self.date_scraped = datetime.now()
        if self.content and not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()
        if self.content and not self.word_count:
            self.word_count = len(self.content.split())

class LegalTextDatabase:
    """Database manager for legal text data"""
    
    def __init__(self, db_path: str = "legal_texts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create legal_texts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS legal_texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                category TEXT,
                date_published DATETIME,
                date_scraped DATETIME NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                word_count INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0.0,
                is_processed BOOLEAN DEFAULT FALSE,
                tags TEXT DEFAULT '[]'
            )
        ''')
        
        # Create scraping_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                status TEXT NOT NULL,
                items_scraped INTEGER DEFAULT 0,
                items_saved INTEGER DEFAULT 0,
                errors TEXT,
                details TEXT
            )
        ''')
        
        # Create data_quality_metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_calculated DATETIME NOT NULL,
                total_documents INTEGER DEFAULT 0,
                avg_word_count REAL DEFAULT 0.0,
                avg_quality_score REAL DEFAULT 0.0,
                sources_active INTEGER DEFAULT 0,
                duplicates_found INTEGER DEFAULT 0,
                processed_documents INTEGER DEFAULT 0
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_hash ON legal_texts(content_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_url ON legal_texts(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON legal_texts(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_scraped ON legal_texts(date_scraped)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON legal_texts(category)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def save_legal_text(self, legal_text: LegalText) -> bool:
        """Save a legal text entry to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO legal_texts 
                (title, content, source, url, category, date_published, date_scraped, 
                 content_hash, word_count, quality_score, is_processed, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                legal_text.title,
                legal_text.content,
                legal_text.source,
                legal_text.url,
                legal_text.category,
                legal_text.date_published,
                legal_text.date_scraped,
                legal_text.content_hash,
                legal_text.word_count,
                legal_text.quality_score,
                legal_text.is_processed,
                json.dumps(legal_text.tags)
            ))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Saved legal text: {legal_text.title[:50]}...")
            else:
                logger.warning(f"Duplicate content not saved: {legal_text.title[:50]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving legal text: {e}")
            return False
    
    def get_latest_texts(self, limit: int = 100) -> List[LegalText]:
        """Get the latest legal texts from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM legal_texts 
                ORDER BY date_scraped DESC 
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            texts = []
            for row in rows:
                legal_text = LegalText(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    source=row[3],
                    url=row[4],
                    category=row[5],
                    date_published=datetime.fromisoformat(row[6]) if row[6] else None,
                    date_scraped=datetime.fromisoformat(row[7]),
                    content_hash=row[8],
                    word_count=row[9],
                    quality_score=row[10],
                    is_processed=bool(row[11]),
                    tags=json.loads(row[12])
                )
                texts.append(legal_text)
            
            return texts
            
        except Exception as e:
            logger.error(f"Error retrieving legal texts: {e}")
            return []
    
    def get_texts_by_source(self, source: str, days_back: int = 7) -> List[LegalText]:
        """Get texts from a specific source within the last N days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            cursor.execute('''
                SELECT * FROM legal_texts 
                WHERE source = ? AND date_scraped >= ?
                ORDER BY date_scraped DESC
            ''', (source, cutoff_date.isoformat()))
            
            rows = cursor.fetchall()
            conn.close()
            
            texts = []
            for row in rows:
                legal_text = LegalText(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    source=row[3],
                    url=row[4],
                    category=row[5],
                    date_published=datetime.fromisoformat(row[6]) if row[6] else None,
                    date_scraped=datetime.fromisoformat(row[7]),
                    content_hash=row[8],
                    word_count=row[9],
                    quality_score=row[10],
                    is_processed=bool(row[11]),
                    tags=json.loads(row[12])
                )
                texts.append(legal_text)
            
            return texts
            
        except Exception as e:
            logger.error(f"Error retrieving texts by source: {e}")
            return []
    
    def log_scraping_session(self, source: str, start_time: datetime, 
                           end_time: datetime = None, status: str = "running",
                           items_scraped: int = 0, items_saved: int = 0,
                           errors: List[str] = None, details: str = "") -> int:
        """Log a scraping session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if end_time is None:
                end_time = datetime.now()
            
            error_text = json.dumps(errors) if errors else None
            
            cursor.execute('''
                INSERT INTO scraping_logs 
                (source, start_time, end_time, status, items_scraped, items_saved, errors, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (source, start_time.isoformat(), end_time.isoformat(), 
                  status, items_scraped, items_saved, error_text, details))
            
            log_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return log_id
            
        except Exception as e:
            logger.error(f"Error logging scraping session: {e}")
            return 0
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total documents
            cursor.execute('SELECT COUNT(*) FROM legal_texts')
            total_docs = cursor.fetchone()[0]
            
            # Documents by source
            cursor.execute('SELECT source, COUNT(*) FROM legal_texts GROUP BY source')
            by_source = dict(cursor.fetchall())
            
            # Recent documents (last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            cursor.execute('SELECT COUNT(*) FROM legal_texts WHERE date_scraped >= ?', 
                         (cutoff_date.isoformat(),))
            recent_docs = cursor.fetchone()[0]
            
            # Average word count
            cursor.execute('SELECT AVG(word_count) FROM legal_texts WHERE word_count > 0')
            avg_words = cursor.fetchone()[0] or 0
            
            # Quality score distribution
            cursor.execute('SELECT AVG(quality_score) FROM legal_texts WHERE quality_score > 0')
            avg_quality = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_documents': total_docs,
                'documents_by_source': by_source,
                'recent_documents': recent_docs,
                'average_word_count': round(avg_words, 2),
                'average_quality_score': round(avg_quality, 2),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Remove old data beyond specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            cursor.execute('DELETE FROM legal_texts WHERE date_scraped < ?', 
                         (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def search_texts(self, query: str, limit: int = 50) -> List[LegalText]:
        """Search legal texts by content or title"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_query = f"%{query}%"
            cursor.execute('''
                SELECT * FROM legal_texts 
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY date_scraped DESC 
                LIMIT ?
            ''', (search_query, search_query, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            texts = []
            for row in rows:
                legal_text = LegalText(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    source=row[3],
                    url=row[4],
                    category=row[5],
                    date_published=datetime.fromisoformat(row[6]) if row[6] else None,
                    date_scraped=datetime.fromisoformat(row[7]),
                    content_hash=row[8],
                    word_count=row[9],
                    quality_score=row[10],
                    is_processed=bool(row[11]),
                    tags=json.loads(row[12])
                )
                texts.append(legal_text)
            
            return texts
            
        except Exception as e:
            logger.error(f"Error searching texts: {e}")
            return []