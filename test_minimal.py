import asyncio
import logging
from pyrogram import Client, filters

from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(BOT_NAME)

app = Client(
    "CosaTestMinimal",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="/app/sessions",
)

@app.on_message(filters.all, group=-1)
async def debug_log_all(client, message):
    logger.info(f"✅ DEBUG: pesan masuk dari chat_id={message.chat.id}, text={message.text!r}")

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    logger.info("✅ /start diterima, mengirim balasan...")
    await message.reply_text("✅ Bot minimal ini BISA membalas. Berarti masalahnya ada di PyTgCalls.")

async def main():
    await app.start()
    logger.info(f"🤖 [TEST MINIMAL] {BOT_NAME} berjalan tanpa PyTgCalls. Kirim /start sekarang.")
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
