import os
import json
import re
import asyncio
import twikit.x_client_transaction.transaction as trans
import twikit.user as tw_user
from twikit import Client
from twikit.x_client_transaction import ClientTransaction
from src.scraper.base_scraper import BaseScraper

# Patch 1: Support updated X bundle regex for ondemand.s
NEW_ON_DEMAND_INDEX_REGEX = re.compile(r""",(\d+):["']ondemand\.s["']""", flags=(re.VERBOSE | re.MULTILINE))

_original_get_indices = trans.ClientTransaction.get_indices

async def _patched_get_indices(self, home_page_response, session, headers):
    key_byte_indices = []
    response = self.validate_response(home_page_response) or self.home_page_response
    page_str = str(response)
    
    on_demand_file = trans.ON_DEMAND_FILE_REGEX.search(page_str)
    if on_demand_file:
        on_demand_file_url = f"https://abs.twimg.com/responsive-web/client-web/ondemand.s.{on_demand_file.group(1)}a.js"
    else:
        m = NEW_ON_DEMAND_INDEX_REGEX.search(page_str)
        if m:
            idx = m.group(1)
            h = re.search(r',%s:"([0-9a-f]+)"' % idx, page_str)
            if h:
                on_demand_file_url = f"https://abs.twimg.com/responsive-web/client-web/ondemand.s.{h.group(1)}a.js"
            else:
                on_demand_file_url = None
        else:
            on_demand_file_url = None

    if on_demand_file_url:
        on_demand_file_response = await session.request(method="GET", url=on_demand_file_url, headers=headers)
        key_byte_indices_match = trans.INDICES_REGEX.finditer(str(on_demand_file_response.text))
        for item in key_byte_indices_match:
            key_byte_indices.append(item.group(2))

    if not key_byte_indices:
        raise Exception("Couldn't get KEY_BYTE indices")
    key_byte_indices = list(map(int, key_byte_indices))
    return key_byte_indices[0], key_byte_indices[1:]

trans.ClientTransaction.get_indices = _patched_get_indices

# Patch 2: Prevent KeyError in twikit User class when user fields (urls, withheld) are missing
_original_user_init = tw_user.User.__init__

def _patched_user_init(self, client, data):
    if isinstance(data, dict):
        legacy = data.get('legacy', {})
        if isinstance(legacy, dict):
            entities = legacy.setdefault('entities', {})
            if isinstance(entities, dict):
                desc = entities.setdefault('description', {})
                if isinstance(desc, dict):
                    desc.setdefault('urls', [])
            legacy.setdefault('withheld_in_countries', [])
    _original_user_init(self, client, data)

tw_user.User.__init__ = _patched_user_init

class TwikitScraper(BaseScraper):
    def __init__(self, cookies_path="config/cookies.json", credentials_path="config/credentials.json"):
        self.cookies_path = cookies_path
        self.credentials_path = credentials_path
        self.client = Client('id-ID') # Set language to Indonesian locale
        
        self.authenticated = False

    async def authenticate_async(self):
        # 1. Try loading cookies first
        if os.path.exists(self.cookies_path):
            try:
                print("Loading X/Twitter session from cookies...")
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    cookies_data = json.load(f)
                
                # Check if it is the browser extension list format
                if isinstance(cookies_data, list):
                    print("Detected browser-exported cookies list. Converting format...")
                    formatted_cookies = {}
                    for cookie in cookies_data:
                        if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                            formatted_cookies[cookie["name"]] = cookie["value"]
                    cookies_data = formatted_cookies
                
                self.client.set_cookies(cookies_data)
                self.authenticated = True
                print("Authentication successful via cookies.")
                return True
            except Exception as e:
                print(f"Failed to load cookies: {e}. Attempting standard login...")
        
        # 2. Try credentials
        if os.path.exists(self.credentials_path):
            try:
                with open(self.credentials_path, "r") as f:
                    creds = json.load(f)
                
                username = creds.get("username")
                email = creds.get("email")
                password = creds.get("password")
                
                if not username or not password:
                    print("Missing username or password in config/credentials.json")
                    return False
                
                print(f"Logging into X as {username}...")
                await self.client.login(
                    auth_info_1=username,
                    auth_info_2=email,
                    password=password
                )
                
                # Save cookies for next time
                os.makedirs(os.path.dirname(self.cookies_path), exist_ok=True)
                self.client.save_cookies(self.cookies_path)
                self.authenticated = True
                print("Authentication successful. Cookies saved.")
                return True
            except Exception as e:
                print(f"Failed to login: {e}")
        else:
            print(f"No credentials file found at {self.credentials_path}. Please create it to run live scraping.")
            
        return False

    def authenticate(self):
        return asyncio.run(self.authenticate_async())

    async def search_tweets_async(self, query, limit=100):
        # Recreate Client to bind connection session to the active event loop
        self.client = Client('id-ID')
        self.authenticated = False
        
        if not self.authenticated:
            print("Client is not authenticated. Attempting login...")
            if not await self.authenticate_async():
                print("Skipping live search due to missing/invalid X credentials. Please use mock scraper instead.")
                return []
                
        tweets = []
        try:
            print(f"Searching X for query: '{query}' (limit: {limit})...")
            # Perform search. twikit search is asynchronous.
            # X intermittently serves a stripped bot-check page instead of the app shell,
            # which makes twikit's transaction-ID bootstrap fail with
            # "Couldn't get KEY_BYTE indices". A failed bootstrap poisons the client
            # (the bad page is cached), so reset it and retry a few times.
            max_attempts = 5
            results = None
            for attempt in range(1, max_attempts + 1):
                try:
                    results = await self.client.search_tweet(query, 'Latest')
                    break
                except Exception as e:
                    if "KEY_BYTE" not in str(e) or attempt == max_attempts:
                        raise
                    print(f"X served a bot-check page (attempt {attempt}/{max_attempts}). Retrying...")
                    self.client.client_transaction = ClientTransaction()
                    # The bot-check response sets its own __cf_bm cookie next to the one
                    # from cookies.json (same name, different domain). Duplicate names make
                    # httpx raise CookieConflict on the next request, so dedupe the jar.
                    deduped = {c.name: c.value for c in self.client.http.cookies.jar}
                    self.client.set_cookies(deduped, clear_cookies=True)
                    await asyncio.sleep(3)

            count = 0
            while results and count < limit:
                for tweet in results:
                    created_at_str = tweet.created_at
                    
                    reply_to = str(tweet.in_reply_to) if getattr(tweet, 'in_reply_to', None) else None
                    tweets.append({
                        'tweet_id': str(tweet.id),
                        'username': tweet.user.screen_name,
                        'created_at': created_at_str,
                        'raw_text': tweet.text,
                        'keyword': query,
                        'reply_to_id': reply_to
                    })
                    count += 1
                    if count >= limit:
                        break
                        
                # Fetch next page if needed
                if count < limit:
                    print(f"Fetched {count} tweets. Loading next page...")
                    await asyncio.sleep(2) # rate limiting protection
                    results = await results.next()
                else:
                    break
                    
            print(f"Successfully scraped {len(tweets)} tweets for query: '{query}'")
        except Exception as e:
            print(f"Error during tweet search: {e}")
            
        return tweets

    def search_tweets(self, query, limit=100):
        return asyncio.run(self.search_tweets_async(query, limit))
