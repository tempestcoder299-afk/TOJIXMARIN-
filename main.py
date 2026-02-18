import os, asyncio, base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from pyrogram.errors import UserNotParticipant
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8351053283:AAH8y9PgQ7NPym7l-FKSJRlU8JVcNF3leXQ" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = {7426624114} # Set for dynamic admin support

# FSub Setup
FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]
START_PIC = "https://graph.org/file/528ff7a62d3c63dc4d030-21c629267007f575ec.jpg"

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael System is Online!"
def run(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text):
    return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")

def decode(base64_string):
    padding = '=' * (4 - len(base64_string) % 4)
    return base64.urlsafe_b64decode((base64_string + padding).encode('ascii')).decode('ascii')

async def auto_del(client, chat_id, message_id):
    await asyncio.sleep(600) # 10 Minutes
    try: await client.delete_messages(chat_id, message_id)
    except: pass

async def is_admin(_, __, m):
    return m.from_user.id in ADMINS
admin_filter = filters.create(is_admin)

# --- SMART FSUB LOGIC ---
async def get_fsub_buttons(client, user_id, data):
    btns = []
    for i in range(len(FSUB_CHANNELS)):
        try:
            await client.get_chat_member(FSUB_CHANNELS[i], user_id)
        except UserNotParticipant:
            btns.append([InlineKeyboardButton(f"Join Channel {i+1}", url=LINKS[i])])
        except: continue
    
    if btns:
        btns.append([InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")])
        return InlineKeyboardMarkup(btns)
    return None

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        # Smart FSub Check
        if user_id not in ADMINS:
            fsub_markup = await get_fsub_buttons(client, user_id, data)
            if fsub_markup:
                return await message.reply_text("👋 **Join remaining channels to access the file!**", reply_markup=fsub_markup)
        
        try:
            val = decode(data)
            ids = list(range(int(val.split("-")[1]), int(val.split("-")[2]) + 1)) if val.startswith("BATCH-") else [int(val)]
            
            for m_id in ids:
                # Naya Pyrogram dev branch colors ko preserve karega
                sent_msg = await client.copy_message(message.chat.id, DB_CHANNEL_ID, m_id)
                asyncio.create_task(auto_del(client, message.chat.id, sent_msg.id))
            
            await message.reply_text("⚠️ **Files sent! Auto-delete in 10 mins.**")
        except: pass
    else:
        # Admin Start Menu
        if user_id in ADMINS:
            await message.reply_photo(photo=START_PIC, caption="**Welcome back Rimiru!**\nSystem is active with Color Button support.")
        else:
            await message.reply_photo(photo=START_PIC, caption="**Hello! Send me a file link to get started.**")

@bot.on_message(filters.private & admin_filter)
async def save_to_db(client, message):
    if message.text and message.text.startswith('/'): return 
    
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ **Saved!**\n🔗 `{link}`", quote=True)

# --- ADMIN MGMT ---
@bot.on_message(filters.command("add_admin") & filters.user(7426624114))
async def add_adm(client, message):
    try:
        new_id = int(message.command[1])
        ADMINS.add(new_id)
        await message.reply_text(f"✅ `{new_id}` added to Admin List.")
    except: await message.reply_text("Usage: `/add_admin [ID]`")

if __name__ == "__main__":
    Thread(target=run).start()
    bot.start()
    print("Raphael System Started, Rimiru!")
    asyncio.get_event_loop().run_forever()

