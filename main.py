import os, asyncio, base64, requests, json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8351053283:AAH8y9PgQ7NPym7l-FKSJRlU8JVcNF3leXQ" #
DB_CHANNEL_ID = -1003336472608 
ADMINS = [7426624114] #

# FSub Lists (Memory based)
FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Master System Online!"
def run_flask(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text): return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")
def decode(b64): return base64.urlsafe_b64decode((b64 + '=' * (4 - len(b64) % 4)).encode('ascii')).decode('ascii')

# --- AUTO-DELETE TASK ---
async def delete_after_delay(client, chat_id, message_id):
    await asyncio.sleep(600) # 10 Minutes
    try: await client.delete_messages(chat_id, message_id)
    except: pass

# --- SMART G-B-B-G-R PAINTER ---
def get_colorful_markup(reply_markup):
    if not reply_markup: return None
    all_btns = []
    for row in reply_markup.inline_keyboard:
        for btn in row: all_btns.append(btn)
            
    # Pattern: Green, Blue, Blue, Green, Red
    styles = ["success", "primary", "primary", "success", "danger"]
    new_kb, temp_row = [], []
    
    for i, btn in enumerate(all_btns):
        style = styles[i] if i < len(styles) else "primary"
        b_data = {"text": btn.text, "style": style}
        if btn.url: b_data["url"] = btn.url
        elif btn.callback_data: b_data["callback_data"] = btn.callback_data
        
        temp_row.append(b_data)
        if len(temp_row) == 2 or i == len(all_btns) - 1:
            new_kb.append(temp_row)
            temp_row = []
    return {"inline_keyboard": new_kb}

# --- SMART FSUB CHECKER ---
async def get_pending_channels(client, user_id):
    pending = []
    for i, ch_id in enumerate(FSUB_CHANNELS):
        try:
            await client.get_chat_member(ch_id, user_id)
        except:
            # User has not joined
            pending.append(InlineKeyboardButton(f"Join Channel {i+1}", url=LINKS[i]))
    return pending

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        if user_id not in ADMINS:
            pending_btns = await get_pending_channels(client, user_id)
            if pending_btns:
                btns = [[btn] for btn in pending_btns]
                btns.append([InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")])
                return await message.reply_text("👋 **Join remaining channels to get the file!**", reply_markup=InlineKeyboardMarkup(btns))
        
        try:
            val = decode(data)
            if "BATCH-" in val:
                _, s_id, e_id = val.split("-")
                msg_ids = list(range(int(s_id), int(e_id) + 1))
            else:
                msg_ids = [int(val)]

            for m_id in msg_ids:
                msg = await client.get_messages(DB_CHANNEL_ID, m_id)
                payload = {
                    "chat_id": message.chat.id, "from_chat_id": DB_CHANNEL_ID, "message_id": m_id,
                    "reply_markup": json.dumps(get_colorful_markup(msg.reply_markup)) if msg.reply_markup else None
                }
                res = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage", json=payload).json()
                if res.get("ok"):
                    asyncio.create_task(delete_after_delay(client, message.chat.id, res["result"]["message_id"]))
            
            await message.reply_text("✅ **Files sent! Auto-delete in 10 mins.**")
        except: pass
    else:
        await message.reply_text("Raphael Pro Online, Rimiru! Main poori tarah taiyaar hoon.")

# --- ADMIN COMMANDS ---

@bot.on_message(filters.command(["addchnl", "add"]) & filters.user(ADMINS))
async def add_chnl(client, message):
    try:
        new_id = int(message.command[1])
        new_link = message.command[2]
        FSUB_CHANNELS.append(new_id)
        LINKS.append(new_link)
        await message.reply_text(f"✅ **Added!**\nID: `{new_id}`\nLink: {new_link}")
    except:
        await message.reply_text("❌ Usage: `/addchnl [ID] [Link]`")

@bot.on_message(filters.command(["delchnl", "remove"]) & filters.user(ADMINS))
async def del_chnl(client, message):
    try:
        index = int(message.command[1]) - 1
        rem_id = FSUB_CHANNELS.pop(index)
        LINKS.pop(index)
        await message.reply_text(f"🗑️ **Removed position {index+1}**\nID: `{rem_id}`")
    except:
        await message.reply_text("❌ Usage: `/remove [Position Number]`")

@bot.on_message(filters.command("vars") & filters.user(ADMINS))
async def show_vars(client, message):
    if not FSUB_CHANNELS: return await message.reply_text("❌ FSub List Khali Hai!")
    text = "⚙️ **Raphael Current Settings:**\n\n"
    for i in range(len(FSUB_CHANNELS)):
        ch_link = LINKS[i] if i < len(LINKS) else "No Link"
        text += f"**{i+1}.** ID: `{FSUB_CHANNELS[i]}`\n🔗 [Join Link]({ch_link})\n\n"
    await message.reply_text(text, disable_web_page_preview=True)

@bot.on_message(filters.command("batch") & filters.user(ADMINS))
async def batch_cmd(client, message):
    if len(message.command) < 3: return await message.reply_text("❌ Usage: `/batch [StartID] [EndID]`")
    s, e = message.command[1], message.command[2]
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(f'BATCH-{s}-{e}')}"
    await message.reply_text(f"📂 **Batch Link:**\n`{link}`")

@bot.on_message(filters.private & filters.user(ADMINS))
async def save(client, message):
    if message.text and message.text.startswith('/'): return
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ **Saved!**\n🆔 **ID:** `{sent.id}`\n🔗 **Link:** `{link}`", quote=True)

# --- STARTUP ---
async def set_menu():
    await bot.set_bot_commands([
        BotCommand("start", "Check Status"),
        BotCommand("batch", "Create Batch"),
        BotCommand("addchnl", "Add FSub Channel"),
        BotCommand("remove", "Remove FSub Channel"),
        BotCommand("vars", "Check Settings")
    ])

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.start()
    bot.loop.run_until_complete(set_menu())
    print("Raphael Pro System Fully Fixed, Rimiru!")
    asyncio.get_event_loop().run_forever()

# --- STARTUP ---
async def set_menu():
    await bot.set_bot_commands([
        BotCommand("start", "Check Status"),
        BotCommand("batch", "Create Batch"),
        BotCommand("addchnl", "Add FSub"),
        BotCommand("vars", "Check Settings")
    ])

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.start()
    bot.loop.run_until_complete(set_menu())
    print("Raphael Pro is Ready, Rimiru!")
    asyncio.get_event_loop().run_forever()
