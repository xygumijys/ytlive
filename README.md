# 🎵 24/7 YouTube Music Live Bot

A powerful, **Free-to-Run** Telegram bot that streams your music/video to YouTube Live 24/7.
Works on **Render (Free)**, **Koyeb**, and **Railway**.

---

## ✨ Features
*   **24/7 Live:** Automatically loops your video and audio forever.
*   **Free to Run:** Optimized for Render Free Tier ($0/month).
*   **Multi-Stream:** Run multiple streams using different Telegram Groups.
*   **Easy Uploads:** Send files directly to Telegram or use Google Drive links.
*   **No PC Needed:** Runs on the cloud, even if your phone/laptop is off.

---

## � How to Deploy (Step-by-Step)

### Option 1: Render (Best for Free 24/7)
**Cost:** $0/month | **Difficulty:** Easy

1.  **Fork Repo:** [Click Here to Fork](https://github.com/new) (Upload these files to your GitHub).
2.  **Deploy:** Click the button below:
    
    [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

3.  **Configure:**
    *   Give it a name (e.g., `my-music-bot`).
    *   Click **Apply**.
4.  **Environment Variables:**
    *   Go to **Environment** tab.
    *   Add `BOT_TOKEN`: Get from [@BotFather](https://t.me/BotFather).
    *   Add `ADMIN_ID`: Get from [@userinfobot](https://t.me/userinfobot) (Your ID).

---

## 💤 How to Keep it Alive 24/7 (Important!)
Render's free plan sleeps after 15 mins. To stop this:

1.  Copy your **Render App URL** (e.g., `https://my-music-bot.onrender.com`).
2.  Go to **[UptimeRobot.com](https://uptimerobot.com/)** and Sign Up (Free).
3.  Click **"Add New Monitor"**.
4.  **Monitor Type:** HTTP(s).
5.  **Friendly Name:** My Bot.
6.  **URL (or IP):** Paste your Render URL here.
7.  **Monitoring Interval:** 5 minutes.
8.  Click **Create Monitor**.

✅ **Done! Now your bot will never sleep.**

---

## 🎮 How to Use (Commands)

### 1. Setup Stream
*   `/start` - Check if bot is alive.
*   `/set_stream <key>` - Set your YouTube Stream Key.
    *   *Example:* `/set_stream abcd-1234-efgh-5678`

### 2. Upload Media (Two Ways)
**Method A: Direct Upload (Easiest)**
*   Just **Send the Video file** to the bot.
*   Just **Send the Audio file** to the bot.

**Method B: Google Drive Links**
*   `/set_video <link>` - Set video from GDrive.
*   `/set_audio <link>` - Set audio from GDrive.
*   *(Make sure GDrive link is "Anyone with the link")*

### 3. Start/Stop
*   `/start_stream` - Start the Magic! 🚀
*   `/stop_stream` - Stop the stream.
*   `/status` - Check if running.
*   `/logs` - See errors if any.

---

## ⚙️ YouTube Settings (For Best Results)
Go to **YouTube Live Dashboard** and set:
*   ✅ **Enable Auto-Start:** ON
*   ❌ **Enable Auto-Stop:** OFF
*   ✅ **Enable DVR:** ON
*   ✅ **Unlist Live Replay:** ON

---

## ❓ Troubleshooting
*   **Stream stops after 15 mins?** You forgot **UptimeRobot** step!
*   **Video not downloading?** Check if GDrive link is Public.
*   **Lagging?** Don't run more than 1 stream on Free Render account.

---
*Made with ❤️ for 24/7 Music Lovers*
