import asyncio
import logging
import random
import re
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

from config import Config, temp
from database import db
# Corrected: Use relative imports to access sibling plugin modules
from ..db import connect_user_db, connect_persistent_db
from ..regix import (
    custom_caption,
    extension_filter,
    keyword_filter,
    media,
    size_filter,
)
from ..test import get_client, parse_buttons

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PROCESSING = set()

async def forward_message_with_retry(message, to_chat_id, configs, new_caption, message_replacements):
    """
    Forwards or copies a message with a retry mechanism for FloodWait errors.
    """
    # Add a random delay between 1 and 3 seconds
    await asyncio.sleep(random.uniform(1, 3))
    
    try:
        if configs.get('forward_tag'):
            await message.forward(to_chat_id, protect_content=configs.get('protect', False))
        else:
            if new_caption and message_replacements:
                for find, replace in message_replacements.items():
                    new_caption = new_caption.replace(find, replace)

            await message.copy(
                chat_id=to_chat_id,
                caption=new_caption if new_caption is not None else (message.caption or ""),
                reply_markup=parse_buttons(configs.get('button') or ''),
                protect_content=configs.get('protect', False)
            )
    except FloodWait as e:
        logger.warning(f"FloodWait error when forwarding message {message.id}. Waiting for {e.value} seconds.")
        await asyncio.sleep(e.value)
        # Retry the action after waiting
        await forward_message_with_retry(message, to_chat_id, configs, new_caption, message_replacements)


async def live_forward_handler(client, message):
    if message.chat.id not in Config.LIVE_FORWARD_CONFIG:
        return

    message_identifier = (message.chat.id, message.id)
    if message_identifier in PROCESSING:
        return
    PROCESSING.add(message_identifier)

    try:
        config = Config.LIVE_FORWARD_CONFIG[message.chat.id]
        user_id = config["user_id"]
        to_chat_id = config["to_chat_id"]
        
        # The listening client is always the forwarding client in this simplified logic
        forwarder_client = client
        
        configs = await db.get_configs(user_id)
        
        # --- Comprehensive Filtering Logic ---
        if (message.text and not configs.get('filters', {}).get('text', True)) or \
           (message.document and not configs.get('filters', {}).get('document', True)) or \
           (message.video and not configs.get('filters', {}).get('video', True)) or \
           (message.photo and not configs.get('filters', {}).get('photo', True)) or \
           (message.audio and not configs.get('filters', {}).get('audio', True)) or \
           (message.voice and not configs.get('filters', {}).get('voice', True)) or \
           (message.animation and not configs.get('filters', {}).get('animation', True)) or \
           (message.sticker and not configs.get('filters', {}).get('sticker', True)) or \
           (message.poll and not configs.get('filters', {}).get('poll', True)):
            return

        media_obj = fname = fsize = fuid = None
        if message.media:
            media_obj = getattr(message, message.media.value, None)
            if media_obj:
                fname = getattr(media_obj, "file_name", None)
                fsize = getattr(media_obj, "file_size", 0)
                fuid = getattr(media_obj, "file_unique_id", None)

        user_rank = await db.get_premium_user_rank(user_id)
        message_replacements = None
        persistent_deduplication = False

        if user_rank != "default":
            regex_filter = configs.get('regex_filter')
            regex_filter_mode = configs.get('regex_filter_mode', 'exclude')
            message_replacements = configs.get('message_replacements')
            persistent_deduplication = configs.get('persistent_deduplication', False)
            
            if regex_filter and fname and (
                (regex_filter_mode == 'exclude' and re.search(regex_filter, fname)) or
                (regex_filter_mode == 'include' and not re.search(regex_filter, fname))
            ):
                return

        keywords = "|".join(configs.get('keywords') or []) or None
        extensions = "|".join(configs.get('extensions') or []) or None
        
        if media_obj and fname and await extension_filter(extensions, fname):
            return
        if media_obj and fname and await keyword_filter(keywords, fname):
            return
        if media_obj and fsize and await size_filter(configs.get('max_size', 0), configs.get('min_size', 0), fsize):
            return

        if (configs.get('duplicate', True) or persistent_deduplication) and fuid:
            db_uri = configs.get('db_uri')
            if db_uri:
                is_persistent = persistent_deduplication
                db_connection = await (connect_persistent_db(user_id, db_uri) if is_persistent else connect_user_db(user_id, db_uri, to_chat_id))
                
                if db_connection[0]:
                    user_db = db_connection[1]
                    if await user_db.is_file_exit(fuid):
                        await user_db.close()
                        return
                    await user_db.add_file(fuid)
                    await user_db.close()
        
        # --- Improved Forwarding Logic with Retry ---
        new_caption = custom_caption(message, configs.get('caption'))
        await forward_message_with_retry(message, to_chat_id, configs, new_caption, message_replacements)

    except Exception as e:
        logging.error(f"Error in live forward handler for message {message.id} in chat {message.chat.id}: {e}", exc_info=True)
    finally:
        if message_identifier in PROCESSING:
            PROCESSING.remove(message_identifier)