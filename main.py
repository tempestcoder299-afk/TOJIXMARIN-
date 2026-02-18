import os, asyncio, base64, requests, json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8226452814:AAG_GZuXu330Inan7i6eJfnoXmczzaddLSY" # File Store Bot Token
DB_CHANNEL_ID = -1003336472608 
ADMINS = [7426624114] 

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Entity Fix Active!"
def run(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- DIRECT API CALL FOR STYLE PRESERVATION ---
def send_with_style(chat_id, from_chat_id, message_id, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    }
    # Agar message mein buttons hain, toh unhe JSON ke roop mein force bhejenge
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return requests.post(url, json=payload).json()

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) > 1:
        # (Yahan aapka FSub aur decoding logic pehle jaisa hi rahega)
        data = message.command[1]
        try:
            # Decoding and ID fetching
            m_id = int(base64.urlsafe_b64decode(data + '=' * (4 - len(data) % 4)).decode('ascii'))
            
            # DB se message uthao aur uske raw buttons check karo
            msg = await client.get_messages(DB_CHANNEL_ID, m_id)
            markup = msg.reply_markup if msg.reply_markup else None
            
            # Force Copy with Styles
            send_with_style(message.chat.id, DB_CHANNEL_ID, m_id, markup)
            
        except: pass
    else:
        await message.reply_text("Raphael Online, Rimiru! Ab colorful buttons try karo.")

@bot.on_message(filters.private & filters.user(ADMINS))
async def save(client, message):
    if message.text and message.text.startswith('/'): return
    
    # Save to DB using Raw API to keep Styles
    markup = message.reply_markup if message.reply_markup else None
    res = send_with_style(DB_CHANNEL_ID, message.chat.id, message.id, markup)
    
    if res.get("ok"):
        new_id = res["result"]["message_id"]
        encoded = base64.urlsafe_b64encode(str(new_id).encode('ascii')).decode('ascii').strip("=")
        await message.reply_text(f"✅ **Saved with Styles!**\n🔗 `https://t.me/{(await client.get_me()).username}?start={encoded}`")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
