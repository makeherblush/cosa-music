import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls, idle, filters as pytgcalls_filters
from pytgcalls.types import MediaStream as StreamType

from config import API_ID, API_HASH, BOT_TOKEN, BOT_NAME

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(BOT_NAME)

app = Client("CosaMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
call_py = PyTgCalls(app)

queues = {}

def get_audio_url(query: str):
    import yt_dlp
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

async def leave_vc(chat_id: int):
    try:
        await call_py.leave_call(chat_id)
    except Exception:
        pass

async def play_next(chat_id: int):
    if chat_id in queues and len(queues[chat_id]) > 0:
        next_song = queues[chat_id].pop(0)
        url = next_song['url']
        title = next_song['title']

        try:
            await call_py.play(chat_id, StreamType(url))
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⏭️ Skip", callback_data="btn_skip"),
                    InlineKeyboardButton("⏹️ Stop", callback_data="btn_stop")
                ],
                [
                    InlineKeyboardButton("📜 Cek Antrean", callback_data="btn_queue")
                ]
            ])
            
            await app.send_message(
                chat_id, 
                f"🎶 <b>[{BOT_NAME}] Memutar Lagu Berikutnya:</b>\n🎵 <b>{title}</b>",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Gagal memutar lagu berikutnya di {chat_id}: {e}")
            await play_next(chat_id)
    else:
        if chat_id in queues:
            del queues[chat_id]
        
        await leave_vc(chat_id)
        await app.send_message(
            chat_id, 
            f"📭 <b>[{BOT_NAME}]</b> Antrean telah selesai. Bot keluar dari Voice Chat."
        )

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨ Cara Penggunaan", callback_data="help_menu"),
            InlineKeyboardButton("📜 Daftar Perintah", callback_data="cmd_menu")
        ],
        [
            InlineKeyboardButton("➕ Tambahkan Bot ke Grup", url=f"https://t.me/{client.me.username}?startgroup=true")
        ]
    ])
    
    welcome_text = (
        f"🎧 <b>Selamat Datang di {BOT_NAME}!</b>\n\n"
        "Bot pemutar musik Voice Chat dengan sistem antrean otomatis dan kontrol tombol interaktif.\n\n"
        "Gunakan tombol di bawah untuk melihat navigasi lebih lanjut!"
    )
    await message.reply_text(welcome_text, reply_markup=keyboard)

@app.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    if data == "help_menu":
        await callback_query.message.edit_text(
            f"📖 <b>Bantuan {BOT_NAME}</b>\n\n"
            "1. Masukkan bot ke dalam Grup.\n"
            "2. Nyalakan Voice Chat (VC) di grup tersebut.\n"
            "3. Ketik <code>/play [judul lagu]</code> untuk memutar musik.\n"
            "4. Bot akan memutar lagu selanjutnya dari antrean secara otomatis!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]])
        )
    elif data == "cmd_menu":
        await callback_query.message.edit_text(
            f"🛠️ <b>Daftar Perintah {BOT_NAME}:</b>\n\n"
            "• <code>/play [judul]</code> - Putar atau tambahkan ke antrean\n"
            "• <code>/skip</code> - Lewati lagu aktif\n"
            "• <code>/queue</code> - Lihat daftar antrean lagu\n"
            "• <code>/stop</code> - Hentikan pemutaran & keluar VC",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]])
        )
    elif data == "main_menu":
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✨ Cara Penggunaan", callback_data="help_menu"),
                InlineKeyboardButton("📜 Daftar Perintah", callback_data="cmd_menu")
            ],
            [
                InlineKeyboardButton("➕ Tambahkan Bot ke Grup", url=f"https://t.me/{client.me.username}?startgroup=true")
            ]
        ])
        await callback_query.message.edit_text(
            f"🎧 <b>Selamat Datang kembali di {BOT_NAME}!</b>\n\nSilakan pilih menu di bawah:",
            reply_markup=keyboard
        )
    elif data == "btn_skip":
        await callback_query.answer("Melewati lagu...")
        await play_next(chat_id)
    elif data == "btn_stop":
        await callback_query.answer("Menghentikan pemutaran...")
        if chat_id in queues:
            queues[chat_id].clear()
            del queues[chat_id]
        await leave_vc(chat_id)
        await callback_query.message.edit_text(f"⏹️ <b>[{BOT_NAME}] Musik dihentikan & bot keluar dari Voice Chat.</b>")
    elif data == "btn_queue":
        if chat_id not in queues or len(queues[chat_id]) == 0:
            await callback_query.answer("Antrean saat ini kosong!", show_alert=True)
        else:
            text = f"📜 <b>[{BOT_NAME}] DAFTAR ANTREAN:</b>\n\n"
            for idx, song in enumerate(queues[chat_id], 1):
                text += f"<b>{idx}.</b> {song['title']}\n"
            await callback_query.answer("Membuka antrean", show_alert=False)
            await callback_query.message.reply_text(text)

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

        is_active = False
        try:
            calls = getattr(call_py, 'calls', {})
            if chat_id in calls:
                is_active = True
        except Exception:
            is_active = False

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏭️ Skip", callback_data="btn_skip"),
                InlineKeyboardButton("⏹️ Stop", callback_data="btn_stop")
            ],
            [
                InlineKeyboardButton("📜 Cek Antrean", callback_data="btn_queue")
            ]
        ])

        if not is_active:
            await call_py.play(chat_id, StreamType(url))
            await status_msg.edit_text(
                f"▶️ <b>[{BOT_NAME}] Memutar Sekarang:</b>\n🎵 <b>{title}</b>",
                reply_markup=keyboard
            )
        else:
            queues[chat_id].append({"title": title, "url": url})
            pos = len(queues[chat_id])
            await status_msg.edit_text(
                f"➕ <b>[{BOT_NAME}] Ditambahkan ke Antrean (#{pos}):</b>\n🎵 <b>{title}</b>",
                reply_markup=keyboard
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

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⏹️ Hentikan Pemutaran", callback_data="btn_stop")]])
    await message.reply_text(text, reply_markup=keyboard)

@app.on_message(filters.command("stop") & filters.group)
async def stop_cmd(client, message):
    chat_id = message.chat.id
    if chat_id in queues:
        queues[chat_id].clear()
        del queues[chat_id]

    await leave_vc(chat_id)
    await message.reply_text(f"⏹️ <b>[{BOT_NAME}] Musik dihentikan & bot keluar dari Voice Chat.</b>")

# Event Handler pemutaran otomatis lagu berikutnya
@call_py.on_update(pytgcalls_filters.stream_end)
async def stream_end_handler(client, update):
    chat_id = getattr(update, 'chat_id', None)
    if chat_id:
        await play_next(chat_id)

async def main():
    await app.start()
    await call_py.start()
    logger.info(f"🤖 {BOT_NAME} Berhasil Berjalan Sempurna!")
    await idle()

if __name__ == "__main__":
    asyncio.run(main())
