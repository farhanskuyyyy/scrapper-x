"""
Diagnostic script for the 'Couldn't get KEY_BYTE indices' twikit error.
Replicates twikit's transaction-ID bootstrap step by step to show exactly
where it breaks on this machine.

Run with the SAME python you use for main.py:
    python debug_twikit.py
"""
import os
import re
import sys
import json
import asyncio
import traceback

print(f"Python     : {sys.version}")
print(f"Executable : {sys.executable}")

try:
    import twikit
    print(f"twikit     : {twikit.__version__}")
except ImportError as e:
    print(f"twikit     : NOT INSTALLED in this interpreter ({e})")
    print("\nFix: python -m pip install -U twikit")
    sys.exit(1)

if tuple(map(int, twikit.__version__.split(".")[:2])) < (2, 3):
    print("\ntwikit is OUTDATED -> this exact error. Fix: python -m pip install -U twikit")
    print("If pip refuses to install >=2.3, your Python is too old -> install Python 3.10+")
    sys.exit(1)

from twikit import Client
from twikit.x_client_transaction.utils import handle_x_migration

ON_DEMAND_FILE_REGEX = re.compile(r""",(\d+):["']ondemand\.s["']""", flags=(re.VERBOSE | re.MULTILINE))
INDICES_REGEX = re.compile(r"\[(\d+)\],\s*16")


async def main():
    client = Client('id-ID')

    # Load cookies the same way TwikitScraper does
    cookies_path = "config/cookies.json"
    if os.path.exists(cookies_path):
        with open(cookies_path, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        if isinstance(cookies_data, list):
            cookies_data = {c["name"]: c["value"] for c in cookies_data
                            if isinstance(c, dict) and "name" in c and "value" in c}
        client.set_cookies(cookies_data)
        print(f"Cookies    : loaded ({len(cookies_data)} entries)")
    else:
        print("Cookies    : config/cookies.json NOT FOUND (continuing without)")

    ct_headers = {
        'Accept-Language': 'id-ID,id;q=0.9',
        'Cache-Control': 'no-cache',
        'Referer': 'https://x.com',
        'User-Agent': client._user_agent
    }

    print("\n[1] Fetching x.com home page (with migration handling, twikit's own code)...")
    try:
        home_page = await handle_x_migration(client.http, ct_headers)
    except Exception:
        print("    FAILED to reach x.com:")
        traceback.print_exc()
        print("    -> Check firewall/antivirus/proxy/ISP block on x.com")
        return

    page_str = str(home_page)
    print(f"    page length={len(page_str)}")

    m = ON_DEMAND_FILE_REGEX.search(page_str)
    if not m:
        title = home_page.title.get_text(strip=True) if home_page.title else "(no title)"
        print(f"    -> 'ondemand.s' NOT found. Page title: {title!r}")
        print("    -> X served a challenge/blocked/login page instead of the app shell.")
        print("       Causes: expired/invalid cookies, IP flagged, ISP/DNS interference.")
        print("       Try: re-export fresh cookies.json, different network/VPN.")
        return

    idx = m.group(1)
    h = re.search(r',%s:"([0-9a-f]+)"' % idx, page_str)
    if not h:
        print("    -> ondemand hash not found; page format unexpected.")
        return
    url = f"https://abs.twimg.com/responsive-web/client-web/ondemand.s.{h.group(1)}a.js"
    print(f"    OK. ondemand file: {url}")

    print("\n[2] Fetching ondemand.s JS from abs.twimg.com...")
    try:
        r = await client.http.request(method="GET", url=url, headers=ct_headers)
    except Exception:
        print("    FAILED to reach abs.twimg.com:")
        traceback.print_exc()
        print("    -> CDN blocked. Check firewall/antivirus/DNS/ISP block on abs.twimg.com")
        return

    indices = INDICES_REGEX.findall(str(r.text))
    print(f"    status={r.status_code}, length={len(r.text)}, indices found={indices}")
    if not indices:
        print("    -> Indices NOT found: X changed frontend, twikit needs update, or CDN response corrupted.")
        return

    print("\n[3] Running a real search_tweet('MBG')...")
    try:
        tweets = await client.search_tweet("MBG", "Latest", count=5)
        print(f"    OK. Got {len(tweets)} tweets. Everything works on this machine.")
    except Exception:
        print("    Search FAILED with full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
