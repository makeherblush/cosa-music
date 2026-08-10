import asyncio
import logging
from pyrogram import Client, filters

from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(BOT_NAME)

app = Client("CosaMusicBotTest", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

@app.on_message(filters.all)
async def debug_log_all(client, message):
    logger.info(f"DEBUG: pesan masuk dari chat_id={message.chat.id}, text={message.text!r}")

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("Bot minimal ini HIDUP dan bisa membalas pesan.")

async def main():
    await app.start()
    logger.info(f"🤖 {BOT_NAME} (MINIMAL TEST) Berhasil Berjalan!")
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
