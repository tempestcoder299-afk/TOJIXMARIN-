import os, asyncio, base64, requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8351053283:AAH8y9PgQ7NPym7l-FKSJRlU8JVcNF3leXQ" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = {7426624114}

FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]
START_PIC = "https://graph.org/file/528ff7a62d3c63dc4d030-21c629267007f575ec.jpg"

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael System Active!"
def run(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text):
    return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")

def decode(base64_string):
    padding = '=' * (4 - len(base64_string) % 4)
    return base64.urlsafe_b64decode((base64_string + padding).encode('ascii')).decode('ascii')

async def auto_del(client, chat_id, message_id):
    await asyncio.sleep(600)
    try: await client.delete_messages(chat_id, message_id)
    except: pass

# --- SMART FSUB ---
async def get_fsub_buttons(client, user_id, data):
    btns = []
    for i in range(len(FSUB_CHANNELS)):
        try:
            await client.get_chat_member(FSUB_CHANNELS[i], user_id)
        except:
            btns.append([InlineKeyboardButton(f"Join Channel {i+1}", url=LINKS[i])])
    if btns:
        btns.append([InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")])
        return InlineKeyboardMarkup(btns)
    return None

# --- FORCED BUTTON COPY ENGINE ---
async def send_with_buttons(client, chat_id, m_id):
    # DB se message fetch karke uske buttons nikaalna
    msg = await client.get_messages(DB_CHANNEL_ID, m_id)
    markup = msg.reply_markup.to_json() if msg.reply_markup else None
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage"
    payload = {
        "chat_id": chat_id,
        "from_chat_id": DB_CHANNEL_ID,
        "message_id": m_id,
        "reply_markup": markup # Yahan buttons manually bhej rahe hain
    }
    return requests.post(url, json=payload).json()

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        # FSub Check
        if user_id not in ADMINS:
            fsub_markup = await get_fsub_buttons(client, user_id, data)
            if fsub_markup:
                return await message.reply_text("👋 **Join remaining channels!**", reply_markup=fsub_markup)
        
        try:
            val = decode(data)
            ids = list(range(int(val.split("-")[1]), int(val.split("-")[2]) + 1)) if val.startswith("BATCH-") else [int(val)]
            
            for m_id in ids:
                # Naya function jo buttons ke saath copy karega
                res = await send_with_buttons(client, message.chat.id, m_id)
                if res.get("ok"):
                    sent_id = res["result"]["message_id"]
                    asyncio.create_task(auto_del(client, message.chat.id, sent_id))
            
            await message.reply_text("✅ **Files sent with Buttons! Auto-delete in 10 mins.**")
        except Exception as e:
            print(f"Error: {e}")
    else:
        await message.reply_photo(photo=START_PIC, caption="**Raphael System is Online, Rimiru!**")

@bot.on_message(filters.private & filters.user(list(ADMINS)))
async def save_to_db(client, message):
    if message.text and message.text.startswith('/'): return 
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ **Saved!**\n🔗 `{link}`", quote=True)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.run()
