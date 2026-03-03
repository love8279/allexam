import os
import sys
import types
import asyncio
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import pyrogram
from pyrogram import Client, filters
from pyromod import listen
import config

# --- ANTI-CRASH PATCH ---
if "pyrogram.sync" not in sys.modules:
    mock_sync = types.ModuleType("pyrogram.sync")
    mock_sync.async_to_sync = lambda *args, **kwargs: args[0] if args else None
    mock_sync.idle = lambda: None
    mock_sync.compose = lambda *args, **kwargs: None
    sys.modules["pyrogram.sync"] = mock_sync

logging.basicConfig(level=logging.INFO)

bot = Client(
    "AppxBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

ORG_ID = "53796"

# Connection issues ke liye Session setup
def get_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

@bot.on_message(filters.command("extract") & filters.private)
async def extract_handler(bot, m):
    editable = await m.reply_text("⏳ **Connecting to Appx Server...**")
    session = get_session()
    
    try:
        # Step 1: Login
        login_url = "https://api.appx.co.in/v2/login"
        payload = {
            "phone": "8279049568", 
            "password": "8279049568", 
            "orgId": ORG_ID, 
            "deviceType": "android"
        }
        
        # User-Agent add karna zaroori hai taki server block na kare
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
            "Content-Type": "application/json"
        }

        response = session.post(login_url, json=payload, headers=headers, timeout=15)
        res_data = response.json()

        if not res_data.get("success"):
            return await editable.edit(f"❌ Login Failed: {res_data.get('message')}")

        token = res_data["data"]["token"]
        auth_headers = {"token": token, "User-Agent": headers["User-Agent"]}

        # Step 2: Get Courses
        await editable.edit("📚 **Fetching Courses...**")
        course_res = session.get(f"https://api.appx.co.in/v2/get-courses/{ORG_ID}", headers=auth_headers, timeout=15).json()
        
        listing = "🎓 **Available Courses:**\n\n"
        for c in course_res.get("data", []):
            listing += f"🔹 `{c['id']}` → **{c['title']}**\n"
        
        await editable.edit(listing)

        # Step 3: Input ID
        cid_msg = await bot.ask(m.chat.id, "🆔 **Enter Course ID:**", timeout=60)
        cid = cid_msg.text.strip()
        
        # Aage ka extraction logic...
        await m.reply_text(f"✅ Extraction started for ID: {cid}")

    except requests.exceptions.ConnectionError:
        await editable.edit("❌ **Network Error:** Appx server is not responding. Heroku might be blocked or DNS is down. Try again in 5 minutes.")
    except Exception as e:
        await editable.edit(f"❌ **Error:** `{str(e)}`")

if __name__ == "__main__":
    bot.run()
    
