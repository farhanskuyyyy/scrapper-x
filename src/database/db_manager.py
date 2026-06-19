import sqlite3
import os
import pandas as pd

class DBManager:
    def __init__(self, db_path="data/database.sqlite"):
        self.db_path = db_path
        # Ensure data directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        query = """
        CREATE TABLE IF NOT EXISTS tweets (
            tweet_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            cleaned_text TEXT,
            sentiment_score INTEGER DEFAULT 0,
            label TEXT CHECK(label IN ('positive', 'negative', 'neutral')),
            keyword TEXT NOT NULL,
            tweet_url TEXT,
            reply_to_id TEXT,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self.get_connection() as conn:
            conn.execute(query)
            
            # Check if columns exist (for migration of existing databases)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(tweets)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'tweet_url' not in columns:
                conn.execute("ALTER TABLE tweets ADD COLUMN tweet_url TEXT")
                # Backfill URLs for existing records
                conn.execute("UPDATE tweets SET tweet_url = 'https://x.com/' || username || '/status/' || tweet_id WHERE tweet_url IS NULL")
                
            if 'reply_to_id' not in columns:
                conn.execute("ALTER TABLE tweets ADD COLUMN reply_to_id TEXT")
                
            # Hapus tweet duplikat berdasarkan raw_text sebelum membuat unique index
            conn.execute("""
            DELETE FROM tweets 
            WHERE rowid NOT IN (
                SELECT MIN(rowid) 
                FROM tweets 
                GROUP BY raw_text
            )
            """)
            
            # Buat indeks unik pada kolom raw_text untuk memfilter buzzer/spammer
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tweets_raw_text ON tweets(raw_text)")
            
            conn.commit()

    def insert_tweets(self, tweets_list):
        """
        tweets_list: list of dicts with keys: 
        ['tweet_id', 'username', 'created_at', 'raw_text', 'keyword']
        Optional keys: ['tweet_url', 'reply_to_id']
        """
        query = """
        INSERT OR IGNORE INTO tweets (tweet_id, username, created_at, raw_text, keyword, tweet_url, reply_to_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        inserted_count = 0
        with self.get_connection() as conn:
            for t in tweets_list:
                url = t.get('tweet_url') or f"https://x.com/{t['username']}/status/{t['tweet_id']}"
                cursor = conn.execute(query, (
                    t['tweet_id'],
                    t['username'],
                    t['created_at'],
                    t['raw_text'],
                    t['keyword'],
                    url,
                    t.get('reply_to_id')
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1
            conn.commit()
        return inserted_count

    def get_raw_tweets(self):
        """Fetch tweets that haven't been cleaned yet."""
        query = "SELECT tweet_id, raw_text FROM tweets WHERE cleaned_text IS NULL"
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        return df

    def update_cleaned_text(self, tweet_id, cleaned_text):
        query = "UPDATE tweets SET cleaned_text = ? WHERE tweet_id = ?"
        with self.get_connection() as conn:
            conn.execute(query, (cleaned_text, tweet_id))
            conn.commit()

    def get_unlabeled_tweets(self):
        """Fetch cleaned tweets that haven't been labeled yet."""
        query = "SELECT tweet_id, cleaned_text FROM tweets WHERE label IS NULL AND cleaned_text IS NOT NULL"
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        return df

    def update_sentiment(self, tweet_id, score, label):
        query = "UPDATE tweets SET sentiment_score = ?, label = ? WHERE tweet_id = ?"
        with self.get_connection() as conn:
            conn.execute(query, (score, label, tweet_id))
            conn.commit()

    def get_all_data(self):
        query = "SELECT * FROM tweets"
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        return df

    def get_ml_dataset(self, exclude_neutral=True):
        """
        Get dataset for Machine Learning training.
        By default, it excludes 'neutral' tweets as done in the JATI research.
        """
        if exclude_neutral:
            query = "SELECT cleaned_text, label FROM tweets WHERE cleaned_text IS NOT NULL AND label IN ('positive', 'negative')"
        else:
            query = "SELECT cleaned_text, label FROM tweets WHERE cleaned_text IS NOT NULL AND label IS NOT NULL"
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn)
        return df
