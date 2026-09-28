import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

app = Client(
    "restricted_saver_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=2,
    in_memory=True
)

DOWNLOAD_DIR = "temp/"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

LINK_REGEX = re.compile(r"(?:https?://)?t\.me/(?:c/)?([a-zA-Z0-9_]+|[\-]+?\d+)/(\d+)")

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "Save-Restricted Bot Active.\nSend a restricted post link from a channel."
    )

@app.on_message(filters.text & filters.private)
async def handle_link(client: Client, message: Message):
    text = message.text.strip()
    match = LINK_REGEX.search(text)
    
    if not match:
        return

    chat_identifier = match.group(1)
    msg_id = int(match.group(2))
    
    if chat_identifier.isdigit():
        chat_id = int(f"-100{chat_identifier}")
    else:
        chat_id = chat_identifier

    status_msg = await message.reply_text("Fetching post...")

    try:
        target_msg = await client.get_messages(chat_id, msg_id)
        
        if not target_msg or target_msg.empty:
            await status_msg.edit_text("Error: Message not found or access restricted.")
            return

        if target_msg.media:
            await status_msg.edit_text("Downloading media (streaming)...")
            file_path = await target_msg.download(file_name=DOWNLOAD_DIR)
            
            await status_msg.edit_text("Uploading media...")
            await client.send_cached_media(
                chat_id=message.chat.id,
                file_id=target_msg.media.file_id if hasattr(target_msg.media, "file_id") else file_path,
                caption=target_msg.caption or ""
            )
            
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=target_msg.text or "Empty message."
            )

        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)[:100]}")

if __name__ == "__main__":
    app.run()
