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
BOT_TOKEN = "8336671886:AAGrAv4g0CEc4X8kO1CFv7R8hucIMck60ac" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = [7426624114] #

# Auto-Button External Links
CHANNEL_INDEX = "https://t.me/tempest_main"
ANIME_INDEX = "https://t.me/+jyN7Ne_wEDExMGU1"
ONGOING_ANIME = "https://t.me/+ANvaArXotyJiNDRl"

# Force Subscription Lists
FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Master System Online!"
def run_flask(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text): 
    return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")

def decode(b64): 
    return base64.urlsafe_b64decode((b64 + '=' * (4 - len(b64) % 4)).encode('ascii')).decode('ascii')

# --- AUTO-DELETE TASK (10 MINUTES) ---
async def delete_after_delay(client, chat_id, message_id):
    await asyncio.sleep(600) #
    try: 
        await client.delete_messages(chat_id, message_id)
    except: 
        pass

# --- SMART PAINTER + 2+1 AUTO BUTTON LOGIC ---
def get_colorful_markup(reply_markup):
    # Case 1: Agar buttons nahi hain toh 2+1 layout add karo
    if not reply_markup:
        return {
            "inline_keyboard": [
                [
                    {"text": "ANIME INDEX", "url": ANIME_INDEX, "style": "success"}, # Green
                    {"text": "CHANNEL INDEX", "url": CHANNEL_INDEX, "style": "primary"} # Blue
                ],
                [
                    {"text": "ONGOING ANIME", "url": ONGOING_ANIME, "style": "danger"} # Red
                ]
            ]
        }
    
    # Case 2: Agar buttons hain toh G-B-B-G-R pattern apply karo
    new_kb = []
    btn_index = 0
    styles = ["success", "primary", "primary", "success", "danger"]
    
    for row in reply_markup.inline_keyboard:
        new_row = []
        for btn in row:
            style = styles[btn_index] if btn_index < len(styles) else "primary"
            b_data = {"text": btn.text, "style": style}
            if btn.url: b_data["url"] = btn.url
            elif btn.callback_data: b_data["callback_data"] = btn.callback_data
            new_row.append(b_data)
            btn_index += 1
        new_kb.append(new_row)
    return {"inline_keyboard": new_kb}

# --- SMART FSUB CHECKER ---
async def get_pending_channels(client, user_id):
    pending = []
    for i, ch_id in enumerate(FSUB_CHANNELS):
        try:
            await client.get_chat_member(ch_id, user_id)
        except:
            pending.append(InlineKeyboardButton(f"Join Channel {i+1}", url=LINKS[i]))
    return pending

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        if user_id not in ADMINS:
            # Check Force Subscription
            pending_btns = await get_pending_channels(client, user_id)
            if pending_btns:
                btns = [[btn] for btn in pending_btns]
                btns.append([InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")])
                return await message.reply_text("👋 Join remaining channels first!", reply_markup=InlineKeyboardMarkup(btns))
        
        try:
            val = decode(data)
            ids = list(range(int(val.split("-")[1]), int(val.split("-")[2]) + 1)) if "BATCH-" in val else [int(val)]

                        # --- PERFECTLY ALIGNED CORE LOGIC ---
            for m_id in ids:
                msg = await client.get_messages(DB_CHANNEL_ID, m_id)
                
                # Auto-Buttons aur 2+1 Layout apply ho raha hai
                payload = {
                    "chat_id": message.chat.id,
                    "from_chat_id": DB_CHANNEL_ID,
                    "message_id": m_id,
                    "reply_markup": json.dumps(get_colorful_markup(msg.reply_markup))
                }
                
                # API request to copy message
                res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage", json=payload).json()
                
                if res.get("ok"):
                    # Auto-Delete Task correctly triggered
                    sent_msg_id = res["result"]["message_id"]
                    asyncio.create_task(delete_after_delay(client, message.chat.id, sent_msg_id))
            
            # Ye line 'for' loop ke bilkul barabar (bahar) honi chahiye
            await message.reply_text("✅ Files sent! Auto-delete in 10 mins.")

        except Exception as e:
            print(f"Error: {e}")

    else:
        await message.reply_text("Raphael Pro Online, Rimiru! Main poori tarah taiyaar hoon.")

@bot.on_message(filters.command(["add", "addchnl"]) & filters.user(ADMINS))
async def add_chnl(client, message):
    try:
        FSUB_CHANNELS.append(int(message.command[1]))
        LINKS.append(message.command[2])
        await message.reply_text("✅ Channel Added!")
    except: await message.reply_text("❌ Usage: `/add [ID] [Link]`")

@bot.on_message(filters.command("vars") & filters.user(ADMINS))
async def show_vars(client, message):
    text = "⚙️ **Settings:**\n\n"
    for i in range(len(FSUB_CHANNELS)):
        text += f"{i+1}. `{FSUB_CHANNELS[i]}` | [Link]({LINKS[i]})\n"
    await message.reply_text(text, disable_web_page_preview=True)
@bot.on_message(filters.command(["remove", "delchnl"]) & filters.user(ADMINS))
async def remove_fsub(client, message):
    try:
        idx = int(message.command[1]) - 1
        rem_id = FSUB_CHANNELS.pop(idx)
        LINKS.pop(idx)
        await message.reply_text(f"🗑️ Removed position {idx+1}\nID: `{rem_id}`")
    except:
        await message.reply_text("❌ Usage: `/remove [Position]`")

@bot.on_message(filters.command("batch") & filters.user(ADMINS))
async def batch_cmd(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ Usage: `/batch [StartID] [EndID]`")
    s, e = message.command[1], message.command[2]
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(f'BATCH-{s}-{e}')}"
    await message.reply_text(f"📂 **Batch Link:**\n`{link}`")

@bot.on_message(filters.private & filters.user(ADMINS))
async def save(client, message):
    if message.text and message.text.startswith('/'): return
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ Saved! ID: `{sent.id}`\n🔗 `{link}`", quote=True)

# --- STARTUP ---
async def set_menu():
    await bot.set_bot_commands([
        BotCommand("start", "Check Status"),
        BotCommand("batch", "Create Batch"),
        BotCommand("add", "Add FSub Channel"),
        BotCommand("vars", "Check Settings"),
        BotCommand("remove", "Remove FSub Channel")
    ])

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.start()
    bot.loop.run_until_complete(set_menu())
    print("Raphael Pro Master System Ready!")
    asyncio.get_event_loop().run_forever()
