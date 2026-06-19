import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

class TextCleaner:
    def __init__(self):
        # Initialize Sastrawi components
        print("Initializing Stemmer and StopWordRemover from Sastrawi...")
        stemmer_factory = StemmerFactory()
        self.stemmer = stemmer_factory.create_stemmer()
        
        stopword_factory = StopWordRemoverFactory()
        # Default stopword list
        self.stopword_remover = stopword_factory.create_stop_word_remover()
        
        # We can also add custom stopwords if needed
        self.custom_stopwords = set([
            "yg", "dg", "rt", "dgn", "ny", "bgt", "dr", "kalo", "amp", "x", "twitter",
            "makan", "bergizi", "gratis", "mbg" # Optional: remove keywords if they skew TF-IDF, but usually we keep them or filter.
        ])

    def clean_text(self, text):
        if not text:
            return ""
        
        # 1. Lowercase (Case Folding)
        text = text.lower()
        
        # 2. Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # 3. Remove Mentions (@username) and Hashtags (#hashtag)
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # 4. Remove emojis and special characters (keep only text and spaces)
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        
        # 5. Remove extra whitespace/newlines
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def remove_stopwords(self, text):
        # Sastrawi default stopword removal
        cleaned = self.stopword_remover.remove(text)
        # Custom slang stopword removal
        words = cleaned.split()
        filtered_words = [w for w in words if w not in self.custom_stopwords]
        return " ".join(filtered_words)

    def stem_text(self, text):
        # Sastrawi Stemmer returns lowercase stemmed text
        return self.stemmer.stem(text)

    def preprocess_pipeline(self, text):
        """Runs the entire pipeline: clean -> remove stopwords -> stem"""
        cleaned = self.clean_text(text)
        no_stopwords = self.remove_stopwords(cleaned)
        stemmed = self.stem_text(no_stopwords)
        return stemmed
