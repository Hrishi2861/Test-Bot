import os
import logging
import subprocess
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import UPLOAD_GROUP_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def upload_files(chat_id, files, bot, user):
    upload_buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Upload to Destination 1", callback_data=f"upload|{chat_id}|dest1"),
         InlineKeyboardButton("Upload to Destination 2", callback_data=f"upload|{chat_id}|dest2")]
    ])
    
    await bot.send_message(chat_id, "Select upload destination:", reply_markup=upload_buttons)

async def handle_upload_selection(chat_id, destination, files, bot, user):
    for file in files:
        file_size = os.path.getsize(file)
        if file_size > 4 * 1024 * 1024 * 1024:
            # Split file into 2GB parts
            split_command = f"split -b 2G {file} {file}_part"
            subprocess.run(split_command, shell=True)
            parts = sorted([f for f in os.listdir("downloads") if f.startswith(os.path.basename(file))])
            for part in parts:
                sent_message = await user.send_document(UPLOAD_GROUP_ID, f"downloads/{part}")
                await bot.forward_messages(chat_id, UPLOAD_GROUP_ID, sent_message.message_id)
                os.remove(f"downloads/{part}")
        else:
            sent_message = await user.send_document(UPLOAD_GROUP_ID, file)
            await bot.forward_messages(chat_id, UPLOAD_GROUP_ID, sent_message.message_id)
            os.remove(file)
    logger.info(f"Upload completed for chat_id {chat_id} to {destination}.")
