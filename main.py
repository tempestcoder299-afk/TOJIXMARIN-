import os, asyncio, base64, requests, json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8226452814:AAG_GZuXu330Inan7i6eJfnoXmczzaddLSY" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = [7426624114] 

FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Painter is Live!"
def run_flask(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text): return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")
def decode(b64): return base64.urlsafe_b64decode((b64 + '=' * (4 - len(b64) % 4)).encode('ascii')).decode('ascii')

# --- BUTTON COLOR INJECTION ---
def colorize_markup(reply_markup):
    """Buttons ko Success (Green) style mein convert karta hai"""
    if not reply_markup: return None
    new_kb = []
    for row in reply_markup.inline_keyboard:
        new_row = []
        for btn in row:
            # Style "success" add kar rahe hain (Green color ke liye)
            b_data = {"text": btn.text, "style": "success"}
            if btn.url: b_data["url"] = btn.url
            elif btn.callback_data: b_data["callback_data"] = btn.callback_data
            new_row.append(b_data)
        new_kb.append(new_row)
    return {"inline_keyboard": new_kb}

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        # Admin Bypass
        if user_id not in ADMINS:
            for ch in FSUB_CHANNELS:
                try: await client.get_chat_member(ch, user_id)
                except:
                    btns = [[InlineKeyboardButton("Join Channel", url=LINKS[0])],
                           [InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")]]
                    return await message.reply_text("👋 **Join Channels first!**", reply_markup=InlineKeyboardMarkup(btns))
        
        try:
            val = decode(data)
            m_id = int(val.split("-")[1]) if "BATCH-" in val else int(val)
            
            # DB se message fetch karo
            msg = await client.get_messages(DB_CHANNEL_ID, m_id)
            
            # Colorful buttons ke saath bhejien (Direct API Call)
            payload = {
                "chat_id": message.chat.id,
                "from_chat_id": DB_CHANNEL_ID,
                "message_id": m_id,
                "reply_markup": json.dumps(colorize_markup(msg.reply_markup)) if msg.reply_markup else None
            }
            res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage", json=payload).json()
            
            if res.get("ok"):
                # 10 min auto-delete logic
                async def del_msg(chat_id, msg_id):
                    await asyncio.sleep(600)
                    try: await client.delete_messages(chat_id, msg_id)
                    except: pass
                asyncio.create_task(del_msg(message.chat.id, res["result"]["message_id"]))
                await message.reply_text("✅ **Files sent! Auto-delete in 10 mins.**")
        except: pass
    else:
        await message.reply_text("Raphael System Online, Rimiru! Bot khud hi buttons rang dega.")

@bot.on_message(filters.private & filters.user(ADMINS))
async def save(client, message):
    if message.text and message.text.startswith('/'): return
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ **Saved! Bot will auto-color this.**\n🔗 `{link}`", quote=True)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.run()
