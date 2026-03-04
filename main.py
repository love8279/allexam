import os
import sys
import logging
import asyncio
import requests
from pyrogram import Client, filters
from pyromod import listen

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fetching Credentials from GitHub Secrets
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client(
    "AppxBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command(["start"]))
async def start(bot, m):
    await m.reply_text("🚀 **Bot is Online on GitHub Actions!**\nSend `/extract` to begin.")

@bot.on_message(filters.command(["extract"]))
async def extract(bot, m):
    await m.reply_text("✅ Extracting feature is active. Please send Course ID.")

if __name__ == "__main__":
    logger.info("Bot starting...")
    bot.run()
