import os
import signal
import logging
import asyncio
import subprocess
import json
import html
from collections import deque
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
import gdown

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Configuration
STORAGE_DIR = Path("storage")
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
ALLOWED_VIDEO_EXT = {".mp4", ".mkv", ".mov"}
ALLOWED_AUDIO_EXT = {".mp3", ".wav", ".aac", ".m4a"}

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global State: {chat_id: subprocess.Popen}
ACTIVE_STREAMS = {}

def get_chat_dir(chat_id: int) -> Path:
    """Get or create the storage directory for a specific chat."""
    path = STORAGE_DIR / str(chat_id)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config_path(chat_id: int) -> Path:
    return get_chat_dir(chat_id) / "config.json"

def load_config(chat_id: int) -> dict:
    path = get_config_path(chat_id)
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(chat_id: int, config: dict):
    with open(get_config_path(chat_id), "w") as f:
        json.dump(config, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Railway RTMP Bot**\n\n"
        "**Commands:**\n"
        "🔑 `/set_stream <key>` - Set YouTube Stream Key\n"
        "📹 `/set_video <link>` - Upload video or set GDrive link\n"
        "🎵 `/set_audio <link>` - Upload audio or set GDrive link\n"
        "▶️ `/start_stream` - Start Live Stream\n"
        "⏹ `/stop_stream` - Stop Live Stream\n"
        "ℹ️ `/status` - Check stream status\n"
        "📜 `/logs` - View ffmpeg logs\n\n"
        "**Note:** Max file size 200MB."
    )

async def set_stream_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("❌ Usage: `/set_stream <your_key>`")
        return

    stream_key = context.args[0]
    config = load_config(chat_id)
    config["stream_key"] = stream_key
    save_config(chat_id, config)
    
    masked_key = stream_key[:4] + "*" * (len(stream_key) - 8) + stream_key[-4:]
    await update.message.reply_text(f"✅ Stream Key Saved: `{masked_key}`")

async def download_gdrive(url: str, output_path: Path) -> bool:
    try:
        # Remove existing file to ensure overwrite
        if output_path.exists():
            output_path.unlink()
            
        # Run gdown in a separate thread
        await asyncio.to_thread(gdown.download, url, str(output_path), quiet=True, fuzzy=True)
        return output_path.exists()
    except Exception as e:
        logger.error(f"GDrive download failed: {e}")
        return False

async def set_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_dir = get_chat_dir(chat_id)
    target_path = chat_dir / "video.mp4"

    # Check if link provided
    if context.args:
        link = context.args[0]
        status_msg = await update.message.reply_text("⬇️ Downloading Video from GDrive...")
        if await download_gdrive(link, target_path):
            await status_msg.edit_text("✅ **Video Set!** (from GDrive)")
        else:
            await status_msg.edit_text("❌ GDrive Download Failed. Check link.")
        return

    await update.message.reply_text("📹 Please upload a video file or use `/set_video <gdrive_link>`.")

async def set_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_dir = get_chat_dir(chat_id)
    target_path = chat_dir / "audio.mp3"

    # Check if link provided
    if context.args:
        link = context.args[0]
        status_msg = await update.message.reply_text("⬇️ Downloading Audio from GDrive...")
        if await download_gdrive(link, target_path):
            await status_msg.edit_text("✅ **Audio Set!** (from GDrive)")
        else:
            await status_msg.edit_text("❌ GDrive Download Failed. Check link.")
        return

    await update.message.reply_text("🎵 Please upload an audio file or use `/set_audio <gdrive_link>`.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message
    
    file_obj = None
    file_name = ""
    
    if message.video:
        file_obj = message.video
        file_name = message.video.file_name or "video.mp4"
    elif message.audio:
        file_obj = message.audio
        file_name = message.audio.file_name or "audio.mp3"
    elif message.document:
        file_obj = message.document
        file_name = message.document.file_name or "file"
    else:
        return

    ext = Path(file_name).suffix.lower()
    
    if file_obj.file_size > MAX_FILE_SIZE:
        await message.reply_text("❌ File too large! Max 200MB.")
        return

    chat_dir = get_chat_dir(chat_id)
    target_path = None
    file_type = ""

    if ext in ALLOWED_VIDEO_EXT:
        target_path = chat_dir / "video.mp4"
        file_type = "Video"
    elif ext in ALLOWED_AUDIO_EXT:
        target_path = chat_dir / "audio.mp3"
        file_type = "Audio"
    else:
        await message.reply_text(f"❌ Unsupported file extension: {ext}")
        return

    status_msg = await message.reply_text(f"⬇️ Downloading {file_type}...")
    
    try:
        new_file = await file_obj.get_file()
        await new_file.download_to_drive(custom_path=target_path)
        await status_msg.edit_text(f"✅ **{file_type} Set!**\nReady for streaming.")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await status_msg.edit_text(f"❌ Download Error: {e}")

async def start_stream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id in ACTIVE_STREAMS:
        if ACTIVE_STREAMS[chat_id].poll() is None:
            await update.message.reply_text("⚠️ Stream is already running!")
            return
        else:
            del ACTIVE_STREAMS[chat_id]

    chat_dir = get_chat_dir(chat_id)
    config = load_config(chat_id)
    stream_key = config.get("stream_key")
    
    if not stream_key:
        await update.message.reply_text("❌ Stream Key not set! Use `/set_stream`.")
        return

    video_path = chat_dir / "video.mp4"
    if not video_path.exists():
        await update.message.reply_text("❌ Video file not found! Use `/set_video`.")
        return

    await update.message.reply_text("🚀 Starting Stream...")

    # FFmpeg command
    command = [
        "ffmpeg",
        "-re",
        "-stream_loop", "-1",
        "-i", str(video_path),
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-b:v", "1000k", "-maxrate", "1000k", "-bufsize", "2000k",
        "-pix_fmt", "yuv420p", "-g", "50",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv",
        f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    ]

    try:
        log_file = open(chat_dir / "ffmpeg.log", "w")
        preexec = os.setsid if os.name != 'nt' else None
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=log_file,
            preexec_fn=preexec
        )
        ACTIVE_STREAMS[chat_id] = process
        await update.message.reply_text(f"✅ *Stream Started!* (PID: {process.pid})")
    except Exception as e:
        logger.error(f"Stream start failed: {e}")
        await update.message.reply_text(f"❌ Failed to start stream: {e}")

async def stop_stream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in ACTIVE_STREAMS:
        await update.message.reply_text("⚠️ No active stream found.")
        return

    process = ACTIVE_STREAMS[chat_id]
    
    try:
        if os.name != 'nt':
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=5)
    except Exception as e:
        logger.warning(f"Kill failed: {e}")
    
    if chat_id in ACTIVE_STREAMS:
        del ACTIVE_STREAMS[chat_id]
        
    await update.message.reply_text("⏹ *Stream Stopped.*")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in ACTIVE_STREAMS:
        proc = ACTIVE_STREAMS[chat_id]
        if proc.poll() is None:
            await update.message.reply_text(f"✅ *Stream is LIVE* (PID: {proc.pid})")
        else:
            del ACTIVE_STREAMS[chat_id]
            await update.message.reply_text("❌ Stream process died unexpectedly.")
    else:
        await update.message.reply_text("💤 No stream running.")

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    log_path = get_chat_dir(chat_id) / "ffmpeg.log"
    
    if not log_path.exists():
        await update.message.reply_text("❌ No logs found.")
        return

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = deque(f, maxlen=200)
            content = "".join(lines)
            
        if not content:
            content = "Log file is empty."
            
        safe_content = html.escape(content[-3000:])
        await update.message.reply_text(f"<pre>{safe_content}</pre>", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error reading logs: {e}")

# Web Server for Render/Koyeb
from aiohttp import web

async def health_check(request):
    return web.Response(text="Bot is alive!")

async def start_web_server(application):
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    app.router.add_get("/healthz", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server started on port {port}")

def main():
    print("🚀 Starting Bot...")
    
    # Debug Environment
    print(f"📝 Checking Environment Variables...")
    if not BOT_TOKEN:
        print("❌ FATAL: BOT_TOKEN is missing! The bot cannot start.")
        print("👉 Please go to Render Dashboard -> Environment and add BOT_TOKEN.")
        # Sleep to allow logs to be flushed/read before exit
        import time
        time.sleep(10)
        return
    else:
        print("✅ BOT_TOKEN found.")

    if not ADMIN_ID:
        print("⚠️ WARNING: ADMIN_ID is missing.")
    else:
        print("✅ ADMIN_ID found.")

    # Use post_init to start web server before bot starts polling
    application = ApplicationBuilder().token(BOT_TOKEN).post_init(start_web_server).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_stream", set_stream_key))
    application.add_handler(CommandHandler("start_stream", start_stream))
    application.add_handler(CommandHandler("stop_stream", stop_stream))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("logs", logs))
    application.add_handler(CommandHandler("set_video", set_video))
    application.add_handler(CommandHandler("set_audio", set_audio))
    application.add_handler(MessageHandler(filters.VIDEO | filters.AUDIO | filters.Document.ALL, handle_document))

    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
