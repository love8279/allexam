import os
import sys
import types

# --- ANTI-CRASH PATCH ---
if "pyrogram.sync" not in sys.modules:
    mock_sync = types.ModuleType("pyrogram.sync")
    mock_sync.async_to_sync = lambda x: x
    mock_sync.idle = lambda: None
    mock_sync.compose = lambda x: None
    sys.modules["pyrogram.sync"] = mock_sync
# ------------------------

import re
import asyncio
import requests
import logging
from pyrogram import Client, filters
from pyromod import listen
from pyrogram.types import Message
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Client(
    "AppxBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

ORG_ID = "53796"

@bot.on_message(filters.command(["start"]))
async def start(bot, m: Message):
    await m.reply_text("✅ **Bot is Active!**\nUse `/extract` to get content.")

@bot.on_message(filters.command(["extract"]))
async def extract_batch(bot, m: Message):
    try:
        editable = await m.reply_text("🔑 **Logging in...**")
        
        # Login Logic
        url = "https://api.appx.co.in/v2/login"
        payload = {"phone": "8279049568", "password": "8279049568", "orgId": ORG_ID, "deviceType": "android"}
        r = requests.post(url, json=payload).json()
        
        if not r.get("success"):
            return await editable.edit(f"❌ Login Failed: {r.get('message')}")
            
        token = r["data"]["token"]
        headers = {"token": token}

        await editable.edit("📚 **Fetching Courses...**")
        course_res = requests.get(f"https://api.appx.co.in/v2/get-courses/{ORG_ID}", headers=headers).json()
        
        listing = "🎓 **Available Courses:**\n\n"
        for c in course_res.get("data", []):
            listing += f"🔹 `{c['id']}` → **{c['title']}**\n"
        
        await editable.edit(listing)

        cid_msg = await bot.ask(m.chat.id, "🆔 **Send Course ID:**", timeout=120)
        cid = cid_msg.text.strip()

        process_msg = await m.reply_text(f"⏳ **Extracting...**")
        data_res = requests.get(f"https://api.appx.co.in/v2/get-course-content/{cid}", headers=headers).json()

        file_name = f"{cid}_Content.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            for item in data_res.get("data", []):
                title = item.get("title", "Untitled")
                url = item.get("videoUrl") or item.get("pdfUrl") or item.get("vimeoUrl")
                if url:
                    f.write(f"{title}: {url}\n")

        await m.reply_document(file_name, caption=f"✅ Done for ID: `{cid}`")
        os.remove(file_name)
        await process_msg.delete()

    except Exception as e:
        await m.reply_text(f"❌ **Error:** `{e}`")

async def main():
    await bot.start()
    logger.info("Bot Started!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
        
