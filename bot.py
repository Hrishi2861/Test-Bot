import os
import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from download import download_links
from upload import upload_files
from database import store_rclone_config, get_rclone_config
from config import BOT_TOKEN, MONGO_URI, USER_SESSION_STRING, TELEGRAM_API, TELEGRAM_HASH, UPLOAD_GROUP_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Client("txt_bot", api_id=TELEGRAM_API, api_hash=TELEGRAM_HASH, bot_token=BOT_TOKEN)

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["txt_bot"]

# User session client
try:
    user = Client('user', TELEGRAM_API, TELEGRAM_HASH, session_string=USER_SESSION_STRING,
                  workers=1000, parse_mode=enums.ParseMode.HTML, no_updates=True).start()
    IS_PREMIUM_USER = user.me.is_premium  # type: ignore
    logger.info(f"Successfully logged into @{user.me.username} DC: {user.session.dc_id}.")  # type: ignore
    if user.me.is_bot:  # type: ignore
        logger.error("You added bot string in USER_SESSION_STRING which is not allowed!")
        user.stop()  # type: ignore
        IS_PREMIUM_USER = False
        user = None
except:
    logger.error("Failed to create client from USER_SESSION_STRING")
    IS_PREMIUM_USER = False
    user = None

@bot.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    logger.info(f"User {message.chat.id} started the bot.")
    await message.reply_text("Send a .txt file containing download links.")

@bot.on_message(filters.document & filters.private)
async def handle_txt_file(client: Client, message: Message):
    if message.document.file_name.endswith(".txt"):
        logger.info(f"Received .txt file from {message.chat.id}")
        file_path = await message.download()
        with open(file_path, "r") as f:
            links = f.readlines()
        os.remove(file_path)
        
        await message.reply_text("Select the line range to download:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Download", callback_data=f"download|{message.chat.id}")]
        ]))
    else:
        await message.reply_text("Please send a valid .txt file.")

@bot.on_callback_query()
async def callback_handler(client, callback_query):
    data = callback_query.data.split("|")
    if data[0] == "download":
        chat_id = int(data[1])
        logger.info(f"Starting download for {chat_id}")
        await download_links(chat_id)
        await callback_query.message.reply_text("Download completed! Use /leech or /mirror.")
    elif data[0] == "mirror":
        chat_id = int(data[1])
        logger.info(f"Starting mirror for {chat_id}")
        rclone_config = await get_rclone_config(chat_id)
        if not rclone_config:
            await callback_query.message.reply_text("No Rclone config found. Send a new one.")
            return
        
        await upload_files(chat_id, rclone_config)
        await callback_query.message.reply_text("Upload completed!")

@bot.on_message(filters.command("leech"))
async def leech_command(client: Client, message: Message):
    chat_id = message.chat.id
    logger.info(f"Leech command received from {chat_id}")
    await message.reply_text("Leeching files to Telegram...")
    files = await download_links(chat_id)
    for file in files:
        await client.send_document(chat_id, file)
        os.remove(file)
    await message.reply_text("Leeching completed!")

@bot.on_message(filters.command("mirror"))
async def mirror_command(client: Client, message: Message):
    chat_id = message.chat.id
    logger.info(f"Mirror command received from {chat_id}")
    rclone_config = await get_rclone_config(chat_id)
    if not rclone_config:
        await message.reply_text("No Rclone config found. Send a new one.")
        return
    
    await upload_files(message.chat.id, rclone_config)
    await message.reply_text("Upload completed!")

@bot.on_message(filters.command("rclone"))
async def rclone_command(client: Client, message: Message):
    if not message.document or not message.document.file_name.endswith(".conf"):
        await message.reply_text("Please send a valid Rclone config file.")
        return
    
    file_path = await message.download()
    logger.info(f"Received Rclone config from {message.chat.id}")
    await store_rclone_config(message.chat.id, file_path)
    os.remove(file_path)
    await message.reply_text("Rclone config saved successfully!")

dc_id = bot.storage.dc_id  # Get the data center ID
logger.info(f"{bot.name} started in DC{dc_id}.")
bot.run()