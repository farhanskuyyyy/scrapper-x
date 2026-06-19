import os
import argparse
import json
from src.database.db_manager import DBManager
from src.scraper.mock_scraper import MockScraper
from src.scraper.twikit_scraper import TwikitScraper
from src.preprocess.text_cleaner import TextCleaner
from src.preprocess.lexicon_labeler import LexiconLabeler
from src.models.classifier_pipeline import ClassifierPipeline

def load_settings(config_path="config/settings.json"):
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {
        "db_path": "data/database.sqlite",
        "keywords": ["Makan Bergizi Gratis", "MBG"],
        "test_split": 0.2,
        "max_features": 5000
    }

def main():
    parser = argparse.ArgumentParser(description="Twitter Sentiment Analysis Pipeline on Makan Bergizi Gratis (MBG)")
    parser.add_argument("--mode", type=str, required=True, 
                        choices=["scrape", "preprocess", "label", "train", "run-all"],
                        help="Pipeline phase to execute.")
    parser.add_argument("--limit", type=int, default=100,
                        help="Number of tweets to scrape per keyword.")
    parser.add_argument("--live", action="store_true", default=False,
                        help="Scrape live Twitter/X data using twikit. If not set, mock scraper is used.")
    args = parser.parse_args()

    settings = load_settings()
    db_path = settings.get("db_path", "data/database.sqlite")
    keywords = settings.get("keywords", ["Makan Bergizi Gratis", "MBG"])
    test_split = settings.get("test_split", 0.2)
    max_features = settings.get("max_features", 5000)

    # Initialize DB Manager
    db = DBManager(db_path)

    if args.mode == "scrape" or args.mode == "run-all":
        print("\n=== PHASE 1: SCRAPING ===")
        # Decide which scraper to use
        if not args.live:
            print("Using Mock Scraper to generate synthetic data...")
            scraper = MockScraper()
        else:
            print("Using Twikit Live Scraper (requires config/cookies.json or config/credentials.json)...")
            scraper = TwikitScraper()
            
        total_scraped = 0
        for kw in keywords:
            scraped = scraper.search_tweets(kw, limit=args.limit)
            if scraped:
                inserted = db.insert_tweets(scraped)
                total_scraped += inserted
                print(f"Inserted {inserted} new unique tweets for keyword '{kw}' into database.")
        
        print(f"Scraping complete. Total unique tweets stored: {total_scraped}")

    if args.mode == "preprocess" or args.mode == "run-all":
        print("\n=== PHASE 2: PREPROCESSING ===")
        df_uncleaned = db.get_raw_tweets()
        if df_uncleaned.empty:
            print("No new raw tweets to clean.")
        else:
            print(f"Cleaning {len(df_uncleaned)} raw tweets...")
            cleaner = TextCleaner()
            processed_count = 0
            for _, row in df_uncleaned.iterrows():
                tid = row['tweet_id']
                raw_text = row['raw_text']
                # Clean, remove stopwords, stem (slow process)
                cleaned = cleaner.preprocess_pipeline(raw_text)
                db.update_cleaned_text(tid, cleaned)
                processed_count += 1
                if processed_count % 50 == 0:
                    print(f"Processed {processed_count}/{len(df_uncleaned)} tweets...")
            print(f"Preprocessing complete. Cleaned {processed_count} tweets successfully.")

    if args.mode == "label" or args.mode == "run-all":
        print("\n=== PHASE 3: AUTOMATIC LABELING (INSET LEXICON) ===")
        df_unlabeled = db.get_unlabeled_tweets()
        if df_unlabeled.empty:
            print("No new cleaned tweets to label. Make sure you run --mode preprocess first.")
        else:
            print(f"Labeling {len(df_unlabeled)} preprocessed tweets using InSet Lexicon...")
            # Automatically downloads lexicon files if not present
            labeler = LexiconLabeler()
            labeled_count = 0
            for _, row in df_unlabeled.iterrows():
                tid = row['tweet_id']
                cleaned_text = row['cleaned_text']
                
                score, label = labeler.calculate_sentiment(cleaned_text)
                db.update_sentiment(tid, score, label)
                labeled_count += 1
                
            print(f"Labeling complete. Classified {labeled_count} tweets automatically.")

    if args.mode == "train" or args.mode == "run-all":
        print("\n=== PHASE 4: MODEL TRAINING & EVALUATION ===")
        pipeline = ClassifierPipeline(db, test_size=test_split, max_features=max_features)
        pipeline.run_training_pipeline()

if __name__ == "__main__":
    main()
