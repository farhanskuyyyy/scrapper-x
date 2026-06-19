from abc import ABC, abstractmethod

class BaseScraper(ABC):
    @abstractmethod
    def search_tweets(self, query, limit=100):
        """
        Search tweets matching a query.
        Returns:
            list of dicts, where each dict has:
            ['tweet_id', 'username', 'created_at', 'raw_text', 'keyword']
        """
        pass
