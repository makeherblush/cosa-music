# Cosa Music 🎵

Bot Telegram untuk *streaming* audio berkuaiitas tinggi langsung ke Voice Chat (Group Call) dengan sistem antrean (*queue*) dan *auto-play*.

## 🚀 Fitur
- Pemutaran musik via YouTube (`yt-dlp`)
- Antrean lagu otomatis (FIFO: First-In, First-Out)
- Perintah `/play`, `/skip`, `/queue`, dan `/stop`
- Support Docker Deployment di Railway

## 🛠️ Variables di Railway
Pastikan menambahkan variabel berikut di Railway Dashboard:
- `API_ID` : API ID dari my.telegram.org
- `API_HASH` : API Hash dari my.telegram.org
- `BOT_TOKEN` : Bot Token dari @BotFather