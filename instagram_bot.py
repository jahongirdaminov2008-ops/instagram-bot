import logging
import os
import re
import tempfile

import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # @BotFather dan olingan token
# ======================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

INSTAGRAM_PATTERN = re.compile(
    r"https?://(www\.)?instagram\.com/(p|reel|tv|stories)/[A-Za-z0-9_\-]+/?(\?[^\s]*)?"
)


def is_instagram_url(text: str) -> bool:
    return bool(INSTAGRAM_PATTERN.search(text))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Salom! Men Instagram video yuklovchi botman.\n\n"
        "📌 Foydalanish:\n"
        "Instagram post, reel yoki video havolasini yuboring — men yuklab beraman!\n\n"
        "Masalan:\n"
        "https://www.instagram.com/reel/ABC123/\n\n"
        "⚠️ Faqat ochiq (public) hisoblar ishlaydi."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🆘 Yordam:\n\n"
        "1️⃣ Instagram video/reel havolasini nusxalang\n"
        "2️⃣ Menga yuboring\n"
        "3️⃣ Video yuklanib, sizga yuboriladi\n\n"
        "✅ Qo'llab-quvvatlanadi: Post, Reel, IGTV\n"
        "❌ Ishlamaydi: Xususiy (private) hisoblar, Stories"
    )


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()

    if not is_instagram_url(url):
        await update.message.reply_text(
            "❌ Bu Instagram havolasi emas.\n"
            "To'g'ri havola misoli:\n"
            "https://www.instagram.com/reel/ABC123/"
        )
        return

    status_msg = await update.message.reply_text("⏳ Video yuklanmoqda, biroz kuting...")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "%(id)s.%(ext)s")

        ydl_opts = {
            "outtmpl": output_path,
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_title = info.get("title", "Instagram Video")

                # Yuklangan faylni topish
                downloaded_file = None
                for fname in os.listdir(tmpdir):
                    if fname.endswith((".mp4", ".mkv", ".webm", ".mov")):
                        downloaded_file = os.path.join(tmpdir, fname)
                        break

                if not downloaded_file:
                    raise FileNotFoundError("Video fayli topilmadi.")

                file_size_mb = os.path.getsize(downloaded_file) / (1024 * 1024)

                # Telegram 50MB limit (bot API)
                if file_size_mb > 50:
                    await status_msg.edit_text(
                        f"⚠️ Video hajmi {file_size_mb:.1f}MB — Telegram limiti 50MB.\n"
                        "Iltimos, qisqaroq video sinab ko'ring."
                    )
                    return

                await status_msg.edit_text("📤 Video yuborilmoqda...")

                with open(downloaded_file, "rb") as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"✅ {video_title[:200]}",
                        supports_streaming=True,
                    )

                await status_msg.delete()

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Download error: {error_msg}")

            if "Private" in error_msg or "private" in error_msg:
                msg = "🔒 Bu xususiy (private) hisob. Faqat ochiq hisoblar ishlaydi."
            elif "login" in error_msg.lower():
                msg = "🔐 Bu video kirish talab qiladi. Faqat ochiq postlar yuklanadi."
            elif "not found" in error_msg.lower() or "404" in error_msg:
                msg = "🚫 Video topilmadi. Havola to'g'riligini tekshiring."
            else:
                msg = f"❌ Yuklab bo'lmadi. Havola yoki video muammosi bo'lishi mumkin."

            await status_msg.edit_text(msg)

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await status_msg.edit_text(
                "⚠️ Xatolik yuz berdi. Iltimos, keyinroq qayta urining."
            )


def main() -> None:
    if BOT_TOKEN == "8628632426:AAEQS7JyjenwymQcu5dE-Dd1MNC12k6RHuo":
        print("❌ Xato: BOT_TOKEN o'rnatilmagan!")
        print("instagram_bot.py faylida BOT_TOKEN ni o'zgartiring.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, download_video)
    )

    print("✅ Bot ishga tushdi! To'xtatish uchun Ctrl+C bosing.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()