import os
import asyncio
import base64
import requests
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8351053283:AAH8y9PgQ7NPym7l-FKSJRlU8JVcNF3leXQ" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = [7426624114]

# Global Variables
FSUB_CHANNELS = []
LINKS = []
DATA_MSG_ID = 0 

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Master System Online!"
def run_flask(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- TG DB HELPERS ---
async def sync_db():
    global DATA_MSG_ID
    data = {"channels": FSUB_CHANNELS, "links": LINKS}
    content = f"#RAPHAEL_DB\n\n```json\n{json.dumps(data, indent=2)}\n```"
    try:
        if DATA_MSG_ID:
            await bot.edit_message_text(DB_CHANNEL_ID, DATA_MSG_ID, content)
        else:
            sent = await bot.send_message(DB_CHANNEL_ID, content)
            DATA_MSG_ID = sent.id
    except Exception as e:
        # Agar edit fail ho (msg delete ho gaya ho), toh naya bhejo
        sent = await bot.send_message(DB_CHANNEL_ID, content)
        DATA_MSG_ID = sent.id
        print(f"DB Synced (New Message): {DATA_MSG_ID}")

# --- UTILS ---
def encode(text): return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")
def decode(b64): return base64.urlsafe_b64decode((b64 + '=' * (4 - len(b64) % 4)).encode('ascii')).decode('ascii')

async def delete_after_delay(client, chat_id, message_id):
    await asyncio.sleep(600)
    try: await client.delete_messages(chat_id, message_id)
    except: pass

def get_colorful_markup(reply_markup):
    if not reply_markup:
        return {
            "inline_keyboard": [
                [{"text": "ANIME INDEX", "url": "https://t.me/tempest_main"}, {"text": "CHANNEL INDEX", "url": "https://t.me/+jyN7Ne_wEDExMGU1"}],
                [{"text": "ONGOING ANIME", "url": "https://t.me/+ANvaArXotyJiNDRl"}]
            ]
        }
    new_kb = []
    btn_index = 0
    styles = ["success", "primary", "primary", "success", "danger"]
    for row in reply_markup.inline_keyboard:
        new_row = []
        for btn in row:
            style = styles[btn_index % 5]
            b_data = {"text": btn.text, "style": style}
            if btn.url: b_data["url"] = btn.url
            elif btn.callback_data: b_data["callback_data"] = btn.callback_data
            new_row.append(b_data)
            btn_index += 1
        new_kb.append(new_row)
    return {"inline_keyboard": new_kb}

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        pending = []
        for i, ch_id in enumerate(FSUB_CHANNELS):
            try:
                await client.get_chat_member(ch_id, user_id)
            except Exception:
                pending.append([InlineKeyboardButton(f"Join Channel {i+1}", url=LINKS[i])])
        
        if pending and user_id not in ADMINS:
            pending.append([InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")])
            return await message.reply_text("👋 Join remaining channels first!", reply_markup=InlineKeyboardMarkup(pending))

        try:
            val = decode(data)
            ids = list(range(int(val.split("-")[1]), int(val.split("-")[2]) + 1)) if "BATCH-" in val else [int(val)]
            for m_id in ids:
                msg = await client.get_messages(DB_CHANNEL_ID, m_id)
                payload = {
                    "chat_id": message.chat.id, "from_chat_id": DB_CHANNEL_ID, "message_id": m_id,
                    "reply_markup": json.dumps(get_colorful_markup(msg.reply_markup))
                }
                res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage", json=payload).json()
                if res.get("ok"):
                    asyncio.create_task(delete_after_delay(client, message.chat.id, res["result"]["message_id"]))
            await message.reply_text("✅ Files sent! Auto-delete in 10 mins.")
        except Exception as e: print(f"Error: {e}")
    else:
        await message.reply_text("Raphael Pro Online, Rimiru! Main taiyaar hoon.")

@bot.on_message(filters.command("add") & filters.user(ADMINS))
async def add_chnl(client, message):
    try:
        new_id, new_link = int(message.command[1]), message.command[2]
        if new_id in FSUB_CHANNELS: return await message.reply_text("❌ Pehle se added hai!")
        FSUB_CHANNELS.append(new_id)
        LINKS.append(new_link)
        await sync_db()
        await message.reply_text(f"✅ Synced with DB Channel!\nID: `{new_id}`")
    except Exception: await message.reply_text("❌ Usage: `/add [ID] [Link]`")

@bot.on_message(filters.command("remove") & filters.user(ADMINS))
async def remove_fsub(client, message):
    try:
        idx = int(message.command[1]) - 1
        FSUB_CHANNELS.pop(idx)
        LINKS.pop(idx)
        await sync_db()
        await message.reply_text("🗑️ Database Updated!")
    except Exception: await message.reply_text("❌ Usage: `/remove [Index]`")

@bot.on_message(filters.command("vars") & filters.user(ADMINS))
async def show_vars(client, message):
    if not FSUB_CHANNELS: return await message.reply_text("📭 FSub list khali hai.")
    text = "⚙️ **Live FSub Config:**\n\n"
    for i, (cid, lnk) in enumerate(zip(FSUB_CHANNELS, LINKS)):
        text += f"{i+1}. `{cid}` | [Join]({lnk})\n"
    await message.reply_text(text, disable_web_page_preview=True)

@bot.on_message(filters.command("batch") & filters.user(ADMINS))
async def batch_cmd(client, message):
    try:
        s, e = message.command[1], message.command[2]
        link = f"https://t.me/{(await client.get_me()).username}?start={encode(f'BATCH-{s}-{e}')}"
        await message.reply_text(f"📂 **Batch Link:**\n`{link}`")
    except Exception: await message.reply_text("❌ `/batch [StartID] [EndID]`")

@bot.on_message(filters.private & filters.user(ADMINS))
async def save(client, message):
    if message.text and message.text.startswith('/'): return
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ Saved! ID: `{sent.id}`\n🔗 `{link}`", quote=True)

# --- STARTUP SYNC (FIXED LOGIC) ---
async def startup():
    await bot.set_bot_commands([
        BotCommand("start", "Check Status"),
        BotCommand("batch", "Create Batch"),
        BotCommand("add", "Add FSub"),
        BotCommand("vars", "Check Settings"),
        BotCommand("remove", "Remove FSub")
    ])
    
    global DATA_MSG_ID, FSUB_CHANNELS, LINKS
    print("Syncing Database from Telegram...")
    
    try:
        # Peer ID resolve karne ke liye pehle chat fetch karo
        await bot.get_chat(DB_CHANNEL_ID)
        
        async for msg in bot.search_messages(DB_CHANNEL_ID, query="#RAPHAEL_DB", limit=1):
            try:
                DATA_MSG_ID = msg.id
                raw_data = msg.text.split("```json")[1].split("```")[0].strip()
                db = json.loads(raw_data)
                FSUB_CHANNELS = db.get("channels", [])
                LINKS = db.get("links", [])
                print(f"Successfully loaded {len(FSUB_CHANNELS)} channels.")
            except Exception:
                print("Found DB tag but format was wrong.")
    except Exception as e:
        print(f"Startup Sync Failed: {e}. Bot will create new DB on first /add.")

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.start()
    bot.loop.run_until_complete(startup())
    print("Raphael Pro Master System Ready!")
    asyncio.get_event_loop().run_forever()
