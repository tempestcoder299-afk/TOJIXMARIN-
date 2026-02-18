import os, asyncio, base64, requests, json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from flask import Flask
from threading import Thread

# --- CONFIG ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8351053283:AAH8y9PgQ7NPym7l-FKSJRlU8JVcNF3leXQ" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = {7426624114} 

# Ye lists memory mein rahengi (For permanent use, connect MongoDB)
FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]

app = Flask(__name__)
@app.route('/')
def home(): return "Raphael Pro Max Online!"
def run(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text): return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")
def decode(b64): return base64.urlsafe_b64decode((b64 + '=' * (4 - len(b64) % 4)).encode('ascii')).decode('ascii')

# --- HANDLERS ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        
        # OWNER BYPASS
        if user_id not in ADMINS:
            for ch in FSUB_CHANNELS:
                try:
                    await client.get_chat_member(ch, user_id)
                except:
                    btn = [[InlineKeyboardButton("Join Channel", url=LINKS[0])],
                           [InlineKeyboardButton("Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")]]
                    return await message.reply_text("👋 **Join channels first!**", reply_markup=InlineKeyboardMarkup(btn))

        try:
            val = decode(data)
            # Batch support
            if "BATCH-" in val:
                _, start_id, end_id = val.split("-")
                msg_ids = list(range(int(start_id), int(end_id) + 1))
            else:
                msg_ids = [int(val)]

            for m_id in msg_ids:
                # copy_message automatically takes whatever is in DB (Colorful or Normal)
                sent = await client.copy_message(chat_id=message.chat.id, from_chat_id=DB_CHANNEL_ID, message_id=m_id)
                asyncio.create_task((lambda m: asyncio.sleep(600) and client.delete_messages(message.chat.id, m))(sent.id))
            
            await message.reply_text("✅ **Files sent! Auto-delete in 10 mins.**")
        except: pass
    else:
        await message.reply_text("Raphael System Online, Rimiru! Main poori tarah taiyaar hoon.")

# --- ADMIN COMMANDS ---

@bot.on_message(filters.command("batch") & filters.user(list(ADMINS)))
async def batch_cmd(client, message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: `/batch [Start_ID] [End_ID]`")
    s, e = message.command[1], message.command[2]
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(f'BATCH-{s}-{e}')}"
    await message.reply_text(f"📂 **Batch Link Generated:**\n`{link}`")

@bot.on_message(filters.command("addchnl") & filters.user(list(ADMINS)))
async def add_chnl(client, message):
    try:
        cid = int(message.command[1])
        link = message.command[2]
        FSUB_CHANNELS.append(cid)
        LINKS.append(link)
        await message.reply_text(f"✅ Channel added to FSub: `{cid}`")
    except:
        await message.reply_text("Usage: `/addchnl -100xxx link`")

@bot.on_message(filters.command("delchnl") & filters.user(list(ADMINS)))
async def del_chnl(client, message):
    try:
        cid = int(message.command[1])
        if cid in FSUB_CHANNELS:
            idx = FSUB_CHANNELS.index(cid)
            FSUB_CHANNELS.pop(idx)
            LINKS.pop(idx)
            await message.reply_text("🗑️ Channel removed.")
    except:
        await message.reply_text("Usage: `/delchnl -100xxx`")

@bot.on_message(filters.command("vars") & filters.user(list(ADMINS)))
async def show_vars(client, message):
    text = f"⚙️ **System Variables (Rimiru):**\n\n"
    text += f"Admin ID: `{7426624114}`\n"
    text += f"DB ID: `{DB_CHANNEL_ID}`\n"
    text += f"FSub Channels: {len(FSUB_CHANNELS)}\n"
    for i, ch in enumerate(FSUB_CHANNELS):
        text += f"🔗 `{ch}` -> [Link]({LINKS[i]})\n"
    await message.reply_text(text, disable_web_page_preview=True)

@bot.on_message(filters.private & filters.user(list(ADMINS)))
async def auto_save(client, message):
    if message.text and message.text.startswith('/'): return
    # Copy to DB with whatever buttons/styles exist
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ **Saved!**\n🔗 `{link}`", quote=True)

# --- STARTUP ---
async def startup(client):
    await client.set_bot_commands([
        BotCommand("start", "Check if bot is alive"),
        BotCommand("batch", "Create batch link"),
        BotCommand("vars", "Check all settings"),
        BotCommand("addchnl", "Add FSub channel"),
        BotCommand("delchnl", "Remove FSub channel")
    ])

if __name__ == "__main__":
    Thread(target=run).start()
    bot.start()
    bot.loop.run_until_complete(startup(bot))
    print("Raphael System Fully Operational, Rimiru!")
    asyncio.get_event_loop().run_forever()

