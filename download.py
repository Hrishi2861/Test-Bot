import os
import asyncio
import logging
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import subprocess
from config import user_session_string, UPLOAD_GROUP_ID
from pyrogram import Client

async def download_links(chat_id, links, bot):
    downloads = []
    for index, link in enumerate(links, start=1):
        if link.strip().endswith(".m3u8"):
            # Ask user for quality selection before downloading
            quality_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("144p", callback_data=f"quality|{chat_id}|144p|{index}"),
                 InlineKeyboardButton("240p", callback_data=f"quality|{chat_id}|240p|{index}")],
                [InlineKeyboardButton("360p", callback_data=f"quality|{chat_id}|360p|{index}"),
                 InlineKeyboardButton("480p", callback_data=f"quality|{chat_id}|480p|{index}")],
                [InlineKeyboardButton("720p", callback_data=f"quality|{chat_id}|720p|{index}"),
                 InlineKeyboardButton("1080p", callback_data=f"quality|{chat_id}|1080p|{index}")]
            ])
            await bot.send_message(chat_id, f"Select quality for: {link.strip()}", reply_markup=quality_keyboard)
        else:
            # Use aria2c for direct downloads
            output_path = f"downloads/file_{index}"
            process = await asyncio.create_subprocess_exec("aria2c", "-x16", "-s16", "-d", "downloads", "-o", f"file_{index}", link.strip())
            await process.communicate()
            downloads.append(output_path)
    return downloads

async def handle_quality_selection(chat_id, quality, index, link, bot):
    output_path = f"downloads/video_{index}.mp4"
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best',
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([link])
    return output_path

async def upload_files(chat_id, files, bot):
    upload_client = Client("upload_session", session_string=user_session_string)
    await upload_client.start()
    for file in files:
        file_size = os.path.getsize(file)
        if file_size > 4 * 1024 * 1024 * 1024:
            # Split file into 2GB parts
            split_command = f"split -b 2G {file} {file}_part"
            subprocess.run(split_command, shell=True)
            parts = sorted([f for f in os.listdir("downloads") if f.startswith(os.path.basename(file))])
            for part in parts:
                sent_message = await upload_client.send_document(UPLOAD_GROUP_ID, f"downloads/{part}")
                await bot.forward_messages(chat_id, UPLOAD_GROUP_ID, sent_message.message_id)
                os.remove(f"downloads/{part}")
        else:
            sent_message = await upload_client.send_document(UPLOAD_GROUP_ID, file)
            await bot.forward_messages(chat_id, UPLOAD_GROUP_ID, sent_message.message_id)
            os.remove(file)
    await upload_client.stop()
