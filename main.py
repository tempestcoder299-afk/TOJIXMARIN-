import os, asyncio, base64, requests, json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8351053283:AAH8y9PgQ7NPym7l-FKSJRlU8JVcNF3leXQ" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = {7426624114}

FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Style-Lock Online!"
def run(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def encode(text): return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")
def decode(b64): return base64.urlsafe_b64decode((b64 + '=' * (4 - len(b64) % 4)).encode('ascii')).decode('ascii')

# --- SAVE WITH FORCE BUTTONS ---
async def force_save_to_db(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"
    payload = {
        "chat_id": DB_CHANNEL_ID,
        "from_chat_id": message.chat.id,
        "message_id": message.id
    }
    # Agar message mein blue/colorful buttons hain, toh unhe force copy karo
    if message.reply_markup:
        markup_dict = json.loads(str(message.reply_markup))
        payload["reply_markup"] = json.dumps(markup_dict)
    
    return requests.post(url, json=payload).json()

# --- START WITH FORCE BUTTONS ---
async def force_send_to_user(chat_id, m_id):
    # DB se original colorful message uthao
    msg = await bot.get_messages(DB_CHANNEL_ID, m_id)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"
    payload = {
        "chat_id": chat_id,
        "from_chat_id": DB_CHANNEL_ID,
        "message_id": m_id
    }
    if msg.reply_markup:
        markup_dict = json.loads(str(msg.reply_markup))
        payload["reply_markup"] = json.dumps(markup_dict)
        
    return requests.post(url, json=payload).json()

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        # FSub Check
        for ch in FSUB_CHANNELS:
            try:
                await client.get_chat_member(ch, user_id)
            except:
                btn = [[InlineKeyboardButton("Join Channel", url=LINKS[0])],
                       [InlineKeyboardButton("Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")]]
                return await message.reply_text("👋 Join channels first!", reply_markup=InlineKeyboardMarkup(btn))

        try:
            val = decode(data)
            m_id = int(val)
            # Force send with styles
            res = await force_send_to_user(message.chat.id, m_id)
            if res.get("ok"):
                sent_id = res["result"]["message_id"]
                asyncio.create_task((lambda m: asyncio.sleep(600) and client.delete_messages(message.chat.id, m))(sent_id))
        except: pass
    else:
        await message.reply_text("Raphael System Online, Rimiru!")

@bot.on_message(filters.private & filters.user(list(ADMINS)))
async def save(client, message):
    if message.text and message.text.startswith('/'): return
    
    # DB mein force save karo styles ke saath
    res = await force_save_to_db(message)
    
    if res.get("ok"):
        m_id = res["result"]["message_id"]
        link = f"https://t.me/{(await client.get_me()).username}?start={encode(m_id)}"
        await message.reply_text(f"✅ **Saved with Blue/Color Buttons!**\n🔗 `{link}`", quote=True)
    else:
        await message.reply_text(f"❌ Error: {res.get('description')}")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
