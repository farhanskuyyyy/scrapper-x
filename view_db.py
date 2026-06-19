import argparse
import sqlite3
import pandas as pd
from src.database.db_manager import DBManager

def main():
    parser = argparse.ArgumentParser(description="View SQLite Database Content")
    parser.add_argument("--label", type=str, choices=["positive", "negative", "neutral", "all"], default="all",
                        help="Filter tweets by sentiment label.")
    parser.add_argument("--limit", type=int, default=5,
                        help="Number of tweets to display.")
    parser.add_argument("--only-replies", action="store_true", default=False,
                        help="Only show reply tweets (tweets replying to another tweet).")
    args = parser.parse_args()

    db_path = "data/database.sqlite"
    try:
        db_mgr = DBManager(db_path)
        conn = db_mgr.get_connection()
        
        # 1. Tampilkan total baris data
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM tweets")
        total_rows = cur.fetchone()[0]
        print(f"==========================================")
        print(f"DATABASE SUMMARY ({db_path})")
        print(f"==========================================")
        print(f"Total data terkumpul: {total_rows} tweet\n")
        
        # 2. Tampilkan distribusi sentimen
        print("=== Distribusi Sentimen ===")
        query_dist = "SELECT label, COUNT(*) as jumlah FROM tweets GROUP BY label"
        df_dist = pd.read_sql_query(query_dist, conn)
        print(df_dist.to_markdown(index=False))
        print()
        
        # 3. Tampilkan pratinjau data dengan filter
        where_clauses = []
        if args.label != "all":
            where_clauses.append(f"label = '{args.label}'")
        if args.only_replies:
            where_clauses.append("reply_to_id IS NOT NULL")
            
        where_str = ""
        if where_clauses:
            where_str = "WHERE " + " AND ".join(where_clauses)
            
        label_title = args.label.upper() if args.label != "all" else "ALL"
        reply_title = " (REPLIES ONLY)" if args.only_replies else ""
        print(f"=== Pratinjau {args.limit} Data Terakhir (Filter: {label_title}{reply_title}) ===")
        
        query_preview = f"""
        SELECT username, raw_text, label, reply_to_id, tweet_url 
        FROM tweets 
        {where_str}
        ORDER BY scraped_at DESC 
        LIMIT {args.limit}
        """
        df_preview = pd.read_sql_query(query_preview, conn)
        
        # Setting pandas output agar rapi dan tidak terpotong
        pd.set_option('display.max_colwidth', 50)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        
        if df_preview.empty:
            print("Tidak ada data yang cocok dengan kriteria filter.")
        else:
            print(df_preview.to_string(index=False))
        print(f"==========================================\n")
        
        conn.close()
    except sqlite3.OperationalError:
        print(f"Error: File database tidak ditemukan di '{db_path}'.")
        print("Silakan jalankan scraper terlebih dahulu dengan perintah:")
        print("python main.py --mode scrape")

if __name__ == "__main__":
    main()
