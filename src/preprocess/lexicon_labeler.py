import os
import requests
import pandas as pd

class LexiconLabeler:
    def __init__(self, positive_url=None, negative_url=None, save_dir="data"):
        self.save_dir = save_dir
        self.pos_path = os.path.join(save_dir, "positive.tsv")
        self.neg_path = os.path.join(save_dir, "negative.tsv")
        
        self.positive_url = positive_url or "https://raw.githubusercontent.com/fajri91/InSet/master/positive.tsv"
        self.negative_url = negative_url or "https://raw.githubusercontent.com/fajri91/InSet/master/negative.tsv"
        
        # Dictionary mapping word -> weight (int)
        self.pos_lexicon = {}
        self.neg_lexicon = {}
        
        self.setup_lexicon()

    def download_file(self, url, dest_path):
        print(f"Downloading lexicon from {url} to {dest_path}...")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        response = requests.get(url)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(response.content)

    def load_lexicon_file(self, path, dest_dict):
        # Read TSV files (usually columns: word, weight)
        try:
            df = pd.read_csv(path, sep="\t", header=None, names=["word", "weight"])
            # Create dictionary
            for _, row in df.iterrows():
                word = str(row["word"]).strip().lower()
                try:
                    weight = int(row["weight"])
                    # Store weight in lexicon dictionary
                    dest_dict[word] = weight
                except ValueError:
                    continue
        except Exception as e:
            print(f"Error reading lexicon file {path}: {e}")

    def setup_lexicon(self):
        # Download files if they do not exist
        if not os.path.exists(self.pos_path):
            self.download_file(self.positive_url, self.pos_path)
        if not os.path.exists(self.neg_path):
            self.download_file(self.negative_url, self.neg_path)
            
        # Load files
        self.load_lexicon_file(self.pos_path, self.pos_lexicon)
        self.load_lexicon_file(self.neg_path, self.neg_lexicon)
        print(f"Loaded InSet Lexicon. Positive words: {len(self.pos_lexicon)}, Negative words: {len(self.neg_lexicon)}")

    def calculate_sentiment(self, text):
        """
        Calculate sentiment score for Indonesian text.
        Returns:
            score (int), label (str)
        """
        if not text:
            return 0, "neutral"
            
        words = text.split()
        score = 0
        
        for word in words:
            if word in self.pos_lexicon:
                score += self.pos_lexicon[word]
            if word in self.neg_lexicon:
                score += self.neg_lexicon[word]
                
        if score > 0:
            label = "positive"
        elif score < 0:
            label = "negative"
        else:
            label = "neutral"
            
        return score, label
