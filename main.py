import os, asyncio, base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from pyrogram.errors import UserNotParticipant
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_ID = 37197223
API_HASH = "3a43ae287a696ee9a6a82fb79f605b75"
BOT_TOKEN = "8226452814:AAG_GZuXu330Inan7i6eJfnoXmczzaddLSY" 
DB_CHANNEL_ID = -1003336472608 
ADMINS = [7426624114] 

# Default FSub Setup
FSUB_CHANNELS = [-1003641267601, -1003625900383]
LINKS = ["https://t.me/+mr5SZGOlW0U4YmQ1", "https://t.me/+BsibgbLhN48xNDdl"]

START_PIC = "https://graph.org/file/528ff7a62d3c63dc4d030-21c629267007f575ec.jpg"

app = Flask(__name__)
@app.route('/')
def home(): return "Tempest Bot is Alive!"
def run(): app.run(host="0.0.0.0", port=8080)

bot = Client("TempestBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---
def encode(text):
    return base64.urlsafe_b64encode(str(text).encode('ascii')).decode('ascii').strip("=")

def decode(base64_string):
    padding = '=' * (4 - len(base64_string) % 4)
    return base64.urlsafe_b64decode((base64_string + padding).encode('ascii')).decode('ascii')

async def check_fsub(client, user_id):
    for ch_id in FSUB_CHANNELS:
        try:
            member = await client.get_chat_member(ch_id, user_id)
            if member.status in ["kicked", "left"]: return False
        except UserNotParticipant: return False
        except: continue 
    return True

async def auto_del(m):
    await asyncio.sleep(600) # 10 Minutes
    try: await m.delete()
    except: pass

# --- ADMIN COMMANDS ---

@bot.on_message(filters.command("vars") & filters.user(ADMINS))
async def show_vars(client, message):
    text = "📊 **Current Bot Configuration:**\n\n"
    text += f"**API ID:** `{API_ID}`\n"
    text += f"**API Hash:** `{API_HASH}`\n"
    text += f"**Token:** `{BOT_TOKEN}`\n\n"
    text += "📢 **FSub Channels:**\n"
    if not FSUB_CHANNELS:
        text += "❌ Empty!"
    else:
        for i in range(len(FSUB_CHANNELS)):
            text += f"**{i+1}.** ID: `{FSUB_CHANNELS[i]}` | [Link]({LINKS[i]})\n"
    await message.reply_text(text, disable_web_page_preview=True)

@bot.on_message(filters.command("add") & filters.user(ADMINS))
async def add_fsub(client, message):
    global FSUB_CHANNELS, LINKS
    try:
        new_id = int(message.command[1])
        new_link = message.command[2]
        FSUB_CHANNELS.append(new_id)
        LINKS.append(new_link)
        await message.reply_text(f"✅ **Added!**\nID: `{new_id}`\nLink: {new_link}")
    except:
        await message.reply_text("❌ Usage: `/add [ID] [Link]`")

@bot.on_message(filters.command("remove") & filters.user(ADMINS))
async def remove_fsub(client, message):
    global FSUB_CHANNELS, LINKS
    try:
        index = int(message.command[1]) - 1
        rem_id = FSUB_CHANNELS.pop(index)
        LINKS.pop(index)
        await message.reply_text(f"🗑️ Removed position {index+1}\nID: `{rem_id}`")
    except:
        await message.reply_text("❌ Usage: `/remove [Number]`")

@bot.on_message(filters.command("replaceall") & filters.user(ADMINS))
async def replace_all(client, message):
    global FSUB_CHANNELS, LINKS
    try:
        index = int(message.command[1]) - 1
        FSUB_CHANNELS[index] = int(message.command[2])
        LINKS[index] = message.command[3]
        await message.reply_text(f"✅ Position {index+1} replaced!")
    except:
        await message.reply_text("❌ Usage: `/replaceall [Number] [ID] [Link]`")

@bot.on_message(filters.command("batch") & filters.user(ADMINS))
async def batch(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ Usage: `/batch [Start_ID] [End_ID]`")
    s, e = message.command[1], message.command[2]
    me = await client.get_me()
    link = f"https://t.me/{me.username}?start={encode(f'BATCH-{s}-{e}')}"
    await message.reply_text(f"✅ **Batch Link:**\n`{link}`")

# --- START & FILE LOGIC ---

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if len(message.command) > 1:
        data = message.command[1]
        if user_id not in ADMINS and not await check_fsub(client, user_id):
            btns = [[InlineKeyboardButton(f"Join Channel {i+1}", url=LINKS[i])] for i in range(len(LINKS))]
            btns.append([InlineKeyboardButton("✅ Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={data}")])
            return await message.reply_text("👋 **Join Channels to access the file!**", reply_markup=InlineKeyboardMarkup(btns))
        
        try:
            val = decode(data)
            ids = list(range(int(val.split("-")[1]), int(val.split("-")[2]) + 1)) if val.startswith("BATCH-") else [int(val)]
            for m_id in ids:
                msg = await client.get_messages(DB_CHANNEL_ID, m_id)
                f_msg = await client.copy_message(message.chat.id, DB_CHANNEL_ID, m_id, reply_markup=msg.reply_markup)
                asyncio.create_task(auto_del(f_msg))
            await message.reply_text("⚠️ **Auto-delete in 10 mins.**")
        except: pass
    else:
        await message.reply_photo(photo=START_PIC, caption="**Welcome Rimiru! Bot is active.**")

# --- FILE SAVE (No Commands) ---
@bot.on_message(filters.private & filters.user(ADMINS))
async def save_to_db(client, message):
    # Command Filter
    if message.text and message.text.startswith('/'): return 
    
    sent = await message.copy(chat_id=DB_CHANNEL_ID)
    link = f"https://t.me/{(await client.get_me()).username}?start={encode(sent.id)}"
    await message.reply_text(f"✅ **Saved!**\n🔗 `{link}`", quote=True)

# --- MENU COMMAND SETUP ---
async def set_menu():
    await bot.set_bot_commands([
        BotCommand("start", "Bot status"),
        BotCommand("vars", "Settings check"),
        BotCommand("add", "Add FSub"),
        BotCommand("remove", "Remove FSub"),
        BotCommand("replaceall", "Replace FSub"),
        BotCommand("batch", "Create batch link")
    ])

if __name__ == "__main__":
    Thread(target=run).start()
    bot.start()
    bot.loop.run_until_complete(set_menu())
    print("Bot Started, Rimiru!")
    asyncio.get_event_loop().run_forever()
