import os, asyncio, base64, requests, json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8351053283:AAH8y9PgQ7NPym7l-FKSJRlU8JVcNF3leXQ" # Naya Token Updated
DB_CHANNEL_ID = -1003336472608 
ADMINS = [7426624114] 

FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael 5-Color System Live!"
def run_flask(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text): return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")
def decode(b64): return base64.urlsafe_b64decode((b64 + '=' * (4 - len(b64) % 4)).encode('ascii')).decode('ascii')

# --- 5-COLOR SYSTEM LOGIC ---
def get_colorful_markup(reply_markup):
    if not reply_markup: return None
    all_btns = []
    for row in reply_markup.inline_keyboard:
        for btn in row: all_btns.append(btn)
            
    # Position based styling
    styles = ["success", "primary", "primary", "warning", "danger"]
    new_kb, temp_row = [], []
    
    for i, btn in enumerate(all_btns):
        # 5 buttons ke liye predefined colors, baki sab default primary
        style = styles[i] if i < len(styles) else "primary"
        b_data = {"text": btn.text, "style": style}
        if btn.url: b_data["url"] = btn.url
        elif btn.callback_data: b_data["callback_data"] = btn.callback_data
        
        temp_row.append(b_data)
        # 2 buttons per row grid setup
        if len(temp_row) == 2 or i == len(all_btns) - 1:
            new_kb.append(temp_row)
            temp_row = []
    return {"inline_keyboard": new_kb}

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        # Admin Bypass
        if user_id not in ADMINS:
            for ch_id in FSUB_CHANNELS:
                try: await client.get_chat_member(ch_id, user_id)
                except:
                    btns = [[InlineKeyboardButton("Join Channel", url=LINKS[0])],
                           [InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")]]
                    return await message.reply_text("👋 **Join Channels first!**", reply_markup=InlineKeyboardMarkup(btns))
        
        try:
            val = decode(data)
            m_id = int(val)
            msg = await client.get_messages(DB_CHANNEL_ID, m_id)
            
            payload = {
                "chat_id": message.chat.id,
                "from_chat_id": DB_CHANNEL_ID,
                "message_id": m_id,
                "reply_markup": json.dumps(get_colorful_markup(msg.reply_markup)) if msg.reply_markup else None
            }
            # Stability on Render via direct HTTP
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage", json=payload)
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        await message.reply_text("Raphael System Online, Rimiru! 5-Color Logic is active.")

@bot.on_message(filters.private & filters.user(ADMINS))
async def save(client, message):
    if message.text and message.text.startswith('/'): return
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ **Saved! Bot will auto-style 5 buttons.**\n🔗 `{link}`", quote=True)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run()
