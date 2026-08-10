import asyncio
import logging
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio
import yt_dlp

from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(BOT_NAME)

# Inisialisasi Pyrogram & PyTgCalls
app = Client("CosaMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

# Memori Antrean Lagu per Chat ID
# Format: { chat_id: [ {"title": "Judul", "url": "Link_Stream"}, ... ] }
queues = {}

def get_audio_url(query: str):
    """Mencari audio di YouTube menggunakan yt-dlp."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)
        if 'entries' in info and len(info['entries']) > 0:
            track = info['entries'][0]
            return track['url'], track['title']
        else:
            raise Exception("Lagu tidak ditemukan.")

async def play_next(chat_id: int):
    """Memutar lagu berikutnya dari antrean."""
    if chat_id in queues and len(queues[chat_id]) > 0:
        next_song = queues[chat_id].pop(0)
        url = next_song['url']
        title = next_song['title']

        try:
            await call_py.play(
                chat_id,
                AudioPiped(url, high_quality_audio=HighQualityAudio())
            )
            await app.send_message(
                chat_id, 
                f"🎶 <b>[{BOT_NAME}] Memutar Lagu Berikutnya:</b>\n🎵 <b>{title}</b>"
            )
        except Exception as e:
            logger.error(f"Gagal memutar lagu berikutnya di {chat_id}: {e}")
            await play_next(chat_id)
    else:
        # Kosongkan antrean jika habis
        if chat_id in queues:
            del queues[chat_id]
        try:
            await call_py.leave_group_call(chat_id)
            await app.send_message(
                chat_id, 
                f"📭 <b>[{BOT_NAME}]</b> Antrean telah selesai. Bot keluar dari Voice Chat."
            )
        except Exception:
            pass

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        f"🎧 <b>Selamat Datang di {BOT_NAME}!</b>\n\n"
        "Bot pemutar musik Voice Chat dengan sistem antrean otomatis.\n\n"
        "<b>Perintah di Grup:</b>\n"
        "• <code>/play [judul lagu]</code> - Putar lagu atau masukkan ke antrean\n"
        "• <code>/skip</code> - Lewati lagu yang sedang berputar\n"
        "• <code>/queue</code> - Lihat daftar antrean lagu\n"
        "• <code>/stop</code> - Hentikan musik & keluarkan bot dari VC"
    )

@app.on_message(filters.command("play") & filters.group)
async def play_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ <b>Format salah!</b>\nContoh: <code>/play Perfect - Ed Sheeran</code>")

    query = " ".join(message.command[1:])
    chat_id = message.chat.id
    status_msg = await message.reply_text(f"🔍 <i>[{BOT_NAME}] Mencari dan memproses lagu...</i>")

    try:
        url, title = get_audio_url(query)

        if chat_id not in queues:
            queues[chat_id] = []

        try:
            current_call = call_py.get_call(chat_id)
            is_active = current_call is not None
        except Exception:
            is_active = False

        if not is_active:
            # Langsung putar lagu jika VC belum aktif
            await call_py.play(
                chat_id,
                AudioPiped(url, high_quality_audio=HighQualityAudio())
            )
            await status_msg.edit_text(
                f"▶️ <b>[{BOT_NAME}] Memutar Sekarang:</b>\n🎵 <b>{title}</b>"
            )
        else:
            # Tambahkan ke antrean jika sedang ada lagu yang berputar
            queues[chat_id].append({"title": title, "url": url})
            pos = len(queues[chat_id])
            await status_msg.edit_text(
                f"➕ <b>[{BOT_NAME}] Ditambahkan ke Antrean (#{pos}):</b>\n🎵 <b>{title}</b>"
            )

    except Exception as e:
        await status_msg.edit_text(f"❌ <b>[{BOT_NAME}] Gagal memutar lagu:</b> {e}")

@app.on_message(filters.command("skip") & filters.group)
async def skip_cmd(client, message):
    chat_id = message.chat.id
    await message.reply_text(f"⏭️ <i>[{BOT_NAME}] Melewati lagu saat ini...</i>")
    await play_next(chat_id)

@app.on_message(filters.command("queue") & filters.group)
async def queue_cmd(client, message):
    chat_id = message.chat.id
    if chat_id not in queues or len(queues[chat_id]) == 0:
        return await message.reply_text(f"📭 <b>[{BOT_NAME}] Antrean lagu saat ini kosong.</b>")

    text = f"📜 <b>[{BOT_NAME}] DAFTAR ANTREAN LAGU:</b>\n\n"
    for idx, song in enumerate(queues[chat_id], 1):
        text += f"<b>{idx}.</b> {song['title']}\n"

    await message.reply_text(text)

@app.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client, message):
    chat_id = message.chat.id
    if chat_id in queues:
        queues[chat_id].clear()
        del queues[chat_id]

    try:
        await call_py.leave_group_call(chat_id)
        await message.reply_text(f"⏹️ <b>[{BOT_NAME}] Musik dihentikan & bot keluar dari Voice Chat.</b>")
    except Exception:
        await message.reply_text(f"❌ <b>[{BOT_NAME}]</b> Bot tidak sedang berada di Voice Chat.")

# Event Handler saat lagu selesai
@call_py.on_stream_end()
async def stream_end_handler(client, update):
    chat_id = update.chat_id
    await play_next(chat_id)

async def main():
    await app.start()
    await call_py.start()
    logger.info(f"🤖 {BOT_NAME} Berhasil Berjalan Sempurna!")
    await asyncio.gather()

if __name__ == "__main__":
    asyncio.run(main())