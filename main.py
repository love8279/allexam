import os
import sys
import logging
import asyncio
from pyrogram import Client, filters

# Logging setup
logging.basicConfig(level=logging.INFO)

# Fetching from Secrets
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Bot Client
bot = Client(
    "AppxBot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ Bot is now running on GitHub Actions!")

if __name__ == "__main__":
    print("Bot starting...")
    bot.run()
    
