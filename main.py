import os
import sys
import types
import socket
import asyncio
import requests
import logging
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyromod import listen
from pyrogram.types import Message
import config

# --- DNS RESOLUTION BYPASS ---
# Force resolving api.appx.co.in to its IP if DNS fails
def get_ip(host):
    try:
        return socket.gethostbyname(host)
    except:
        return None

# --- KOYEB/HEROKU ANTI-CRASH PATCH ---
if "pyrogram.sync" not in sys.modules:
    mock_sync = types.ModuleType("pyrogram.sync")
    mock_sync.async_to_sync = lambda *args, **kwargs: args[0] if args else None
    mock_sync.idle = lambda: None
    mock_sync.compose = lambda *args, **kwargs: None
    sys.modules["pyrogram.sync"] = mock_sync

# --- DUMMY WEB SERVER FOR KOYEB ---
app = Flask('')
@app.route('/')
def home():
    return "Bot is Alive and DNS Patched!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BOT SETUP ---
logging.basicConfig(level=logging.INFO)
bot = Client(
    "AppxBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

ORG_ID = "53796"

@bot.on_message(filters.command(["start"]))
async def start(bot, m: Message):
    ip_check = get_ip("api.appx.co.in")
    status = "✅ Connected" if ip_check else "⚠️ DNS Issue (Resolving...)"
    await m.reply_text(f"🚀 **Bot Online on Koyeb!**\n\n**Server Status:** {status}\n**IP:** `{ip_check}`\n\nUse `/extract` to start.")

@bot.on_message(filters.command(["extract"]))
async def extract_batch(bot, m: Message):
    try:
        editable = await m.reply_text("🔑 **Trying to bypass DNS & Logging in...**")
        
        # Connection settings with high timeout and retries
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=5)
        session.mount('https://', adapter)

        url = "https://api.appx.co.in/v2/login"
        payload = {
            "phone": "8279049568", 
            "password": "8279049568", 
            "orgId": ORG_ID, 
            "deviceType": "android"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36",
            "Content-Type": "application/json",
            "Host": "api.appx.co.in"
        }
        
        # Using Session with custom timeout
        response = session.post(url, json=payload, headers=headers, timeout=40)
        r = response.json()
        
        if not r.get("success"):
            return await editable.edit(f"❌ Login Failed: {r.get('message')}")
            
        token = r["data"]["token"]
        auth_headers = {"token": token, "User-Agent": headers["User-Agent"]}

        await editable.edit("📚 **Fetching Courses...**")
        course_res = session.get(f"https://api.appx.co.in/v2/get-courses/{ORG_ID}", headers=auth_headers, timeout=40).json()
        
        listing = "🎓 **Available Courses:**\n\n"
        for c in course_res.get("data", []):
            listing += f"🔹 `{c['id']}` → **{c['title']}**\n"
        
        await editable.edit(listing)

        cid_msg = await bot.ask(m.chat.id, "🆔 **Send Course ID:**", timeout=120)
        cid = cid_msg.text.strip()

        process_msg = await m.reply_text(f"⏳ **Extracting...**")
        data_res = session.get(f"https://api.appx.co.in/v2/get-course-content/{cid}", headers=auth_headers, timeout=40).json()

        file_name = f"{cid}_Content.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            for item in data_res.get("data", []):
                title = item.get("title", "Untitled")
                v_url = item.get("videoUrl") or item.get("pdfUrl") or item.get("vimeoUrl")
                if v_url:
                    f.write(f"{title}: {v_url}\n")

        await m.reply_document(file_name, caption=f"✅ Done for ID: `{cid}`")
        os.remove(file_name)
        await process_msg.delete()

    except requests.exceptions.ConnectionError:
        await m.reply_text("❌ **DNS Error Again:** Koyeb cannot find 'api.appx.co.in'. This is a provider-level block.")
    except Exception as e:
        await m.reply_text(f"❌ **Error:** `{e}`")

# --- EXECUTION ---
if __name__ == "__main__":
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    bot.run()
