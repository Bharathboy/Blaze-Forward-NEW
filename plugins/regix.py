import os
import sys
import math
import time, re
import asyncio
import logging
import random
from .utils import STS, progress_bar_tuple
from database import Db, db
from .test import CLIENT, get_client, iter_messages
from config import Config, temp
from script import Script
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from .db import connect_user_db, connect_persistent_db # <-- Import new function
from pyrogram.types import Message

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Script.TEXT

async def get_task_limit(user_id):
    rank = await db.get_premium_user_rank(user_id)
    return Config.TASK_LIMITS.get(rank, Config.TASK_LIMITS["default"])


@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id


    if user not in temp.USER_LOCKS:
        temp.USER_LOCKS[user] = asyncio.Lock()

    client = None
    i = None
    user_db = None # Initialize user_db to None

    async with temp.USER_LOCKS[user]:
        task_limit = await get_task_limit(user)
        active_tasks = len(temp.lock.get(user, []))

        if active_tasks >= task_limit:
            return await message.answer(f"ʏᴏᴜ ʜᴀᴠᴇ ʀᴇᴀᴄʜᴇᴅ ʏᴏᴜʀ ᴍᴀxɪᴍᴜᴍ ʟɪᴍɪᴛ ᴏꜰ {task_limit} ғᴏʀᴡᴀʀᴅ ᴛᴀsᴋs. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ꜰᴏʀ ʏᴏᴜʀ ᴏᴛʜᴇʀ ᴛᴀsᴋs ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴏʀ ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ, sᴇᴇ /plans", show_alert=True)

        frwd_id = message.data.split("_")[2]
        sts = STS(frwd_id)
        if not sts.verify():
            await message.answer("ʏᴏᴜ ᴀʀᴇ ᴄʟɪᴄᴋɪɴɢ ᴏɴ ᴀɴ ᴏʟᴅ ʙᴜᴛᴛᴏɴ.", show_alert=True)
            return await message.message.delete()

        i = sts.get(full=True)

        if user not in temp.lock:
            temp.lock[user] = []
        temp.lock[user].append(i.bot_id)

    try:
        if user not in temp.CANCEL:
            temp.CANCEL[user] = {}
        temp.CANCEL[user][i.bot_id] = False

        if i.TO in temp.IS_FRWD_CHAT:
            await message.answer("ᴀ ᴛᴀsᴋ ɪs ᴀʟʀᴇᴀᴅʏ ɪɴ ᴘʀᴏɢʀᴇss ғᴏʀ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ. ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ.", show_alert=True)
            await stop(client, user, i.bot_id)
            return

        m = await msg_edit(message.message, "<code>ᴠᴇʀɪꜰʏɪɴɢ ʏᴏᴜʀ ᴅᴀᴛᴀ, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</code>")
        temp.ACTIVE_STATUS_MSGS.setdefault(user, {})[i.bot_id] = m
        _bot, caption, forward_tag, datas, protect, button = await sts.get_data(user)

        # Premium Features
        user_rank = await db.get_premium_user_rank(user)
        if user_rank == "default":
            # If user is not premium, disable premium features for this task
            regex_filter = None
            message_replacements = None
            persistent_deduplication = False
            regex_filter_mode = 'exclude'
            custom_cover_url = None
        else:
            custom_cover_url = datas.get('custom_cover')
            regex_filter = datas.get('regex_filter')
            message_replacements = datas.get('message_replacements')
            persistent_deduplication = datas.get('persistent_deduplication', False)
            regex_filter_mode = datas.get('regex_filter_mode', 'exclude')

        forwarding_speed = Config.FORWARDING_SPEED.get(user_rank, Config.FORWARDING_SPEED["default"]) if _bot['is_bot'] else 10
        
        dburi = datas['db_uri']
        if (persistent_deduplication or datas['skip_duplicate']) and not dburi:
            await m.edit_text("You have enabled a deduplication feature, but you haven't set a MongoDB URI in your settings. This feature requires a database to work.\n\nPlease go to /settings -> 🗃 MᴏɴɢᴏDB to add your database URI.", disable_web_page_preview=True)
            await stop(client, user, i.bot_id)
            return

        filter = datas['filters']
        max_size = datas['max_size']
        min_size = datas['min_size']
        keyword = datas['keywords']
        exten = datas['extensions']
        keywords = ""
        extensions = ""
        if keyword:
            for key in keyword:
                keywords += f"{key}|"
            keywords = keywords.rstrip("|")
        else:
            keywords = None
        if exten:
            for ext in exten:
                extensions += f"{ext}|"
            extensions = extensions.rstrip("|")
        else:
            extensions = None
        if not _bot:
            await msg_edit(m, "<code>ʏᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴀᴅᴅᴇᴅ ᴀɴʏ ʙᴏᴛ. ᴘʟᴇᴀsᴇ ᴀᴅᴅ ᴀ ʙᴏᴛ ᴜsɪɴɢ /settings!</code>", wait=True)
            await stop(client, user, i.bot_id)
            return

        data = _bot['token'] if _bot['is_bot'] else _bot['session']
        try:
            client = await get_client(data, is_bot=_bot['is_bot'])
            await client.start()
        except Exception as e:
            await m.edit(f"ᴇʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ᴄʟɪᴇɴᴛ: {e}")
            await stop(client, user, i.bot_id)
            return

        await msg_edit(m, "<code>ᴘʀᴏᴄᴇssɪɴɢ...</code>")
        try:
            from_chat = await client.get_chat(sts.get("FROM"))
            to_chat = await client.get_chat(sts.get("TO"))
        except Exception as e:
            await msg_edit(m, f"**ᴇʀʀᴏʀ:**\n`{e}`\n\n**sᴏᴜʀᴄᴇ/ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ᴍᴀʏ ʙᴇ ᴘʀɪᴠᴀᴛᴇ. ᴜsᴇ ᴀ ᴜsᴇʀʙᴏᴛ ᴏʀ ᴍᴀᴋᴇ ʏᴏᴜʀ ʙᴏᴛ ᴀɴ ᴀᴅᴍɪɴ ᴛʜᴇʀᴇ.**", retry_btn(frwd_id), True)
            await stop(client, user, i.bot_id)
            return
        try:
            k = await client.send_message(i.TO, "ᴛᴇsᴛɪɴɢ")
            await k.delete()
        except:
            await msg_edit(m, f"**ᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ ʏᴏᴜʀ [UserBot/Bot](t.me/{_bot['username']}) ᴀɴ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟ ᴡɪᴛʜ ꜰᴜʟʟ ᴘᴇʀᴍɪssɪᴏɴs.**", retry_btn(frwd_id), True)
            await stop(client, user, i.bot_id)
            return

        user_have_db = False
        if dburi:
            if persistent_deduplication:
                connected, user_db = await connect_persistent_db(user, dburi)
            else:
                connected, user_db = await connect_user_db(user, dburi, i.TO)

            if not connected:
                await msg_edit(m, "<code>ᴄᴏᴜʟᴅ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ʏᴏᴜʀ ᴅʙ. ᴅᴜᴘʟɪᴄᴀᴛᴇ ᴇɴᴛʀɪᴇs ᴍᴀʏ ʙᴇ sᴋɪᴘᴘᴇᴅ ᴀꜰᴛᴇʀ ᴀ ʀᴇsᴛᴀʀᴛ.</code>")
            else:
                user_have_db = True
        
        temp.forwardings += 1
        await db.add_frwd(user, i.bot_id)

        await send(client, user, Script.FORWARD_START_TXT.format(_bot['id'], _bot['name'], from_chat.title, to_chat.title))

        sts.add(time=True)
        sleep = random.uniform(forwarding_speed,1)
        await msg_edit(m, "<code>ᴘʀᴏᴄᴇssɪɴɢ...</code>")
        temp.IS_FRWD_CHAT.append(i.TO)

        try:
            MSG = []
            pling = 0
            await edit(user, i.bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts, _bot, from_chat, to_chat)
            async for message in iter_messages(client, chat_id=sts.get("FROM"), limit=sts.get("limit"), offset=sts.get("skip"), filters=filter, max_size=max_size):
                if await is_cancelled(client, user, sts, i.bot_id, _bot, from_chat, to_chat):
                    if user_have_db and not persistent_deduplication:
                        await user_db.drop_all()
                    if user_db:
                        await user_db.close()
                    return
                if pling % 20 == 0:
                    await edit(user, i.bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts, _bot, from_chat, to_chat)
                pling += 1
                sts.add('fetched')

                if isinstance(message, str):
                    if message == "DUPLICATE":
                        sts.add("duplicate")
                    elif message == "FILTERED":
                        sts.add("filtered")
                    continue
                if message.empty or message.service:
                    sts.add('deleted')
                    continue
                media_obj = fname = fsize = fuid = None
                if message.media:
                    media_obj = getattr(message, message.media.value, None)
                    if not media_obj:
                        continue
                    fname = getattr(media_obj, "file_name", None)
                    fsize = getattr(media_obj, "file_size", None)
                    fuid = getattr(media_obj, "file_unique_id", None)
                
                # Regex Filter
                if regex_filter and fname:
                    if regex_filter_mode == 'exclude' and re.search(regex_filter, fname):
                        sts.add('filtered')
                        continue
                    if regex_filter_mode == 'include' and not re.search(regex_filter, fname):
                        sts.add('filtered')
                        continue

                if media_obj and fname and await extension_filter(extensions, fname):
                    sts.add('filtered')
                    continue
                elif media_obj and fname and await keyword_filter(keywords, fname):
                    sts.add('filtered')
                    continue
                elif media_obj and fsize is not None and await size_filter(max_size, min_size, fsize):
                    sts.add('filtered')
                    continue

                if user_have_db and (datas['skip_duplicate'] or persistent_deduplication) and fuid:
                    if await user_db.is_file_exit(fuid):
                        sts.add('duplicate')
                        continue
                    await user_db.add_file(fuid)

                if forward_tag:
                    MSG.append(message.id)
                    notcompleted = len(MSG)
                    completed = sts.get('total') - sts.get('fetched')
                    if (notcompleted >= 100 or completed <= 100):
                        await forward(user, client, MSG, sts, protect, _bot, from_chat, to_chat)
                        sts.add('total_files', notcompleted)
                        await asyncio.sleep(10)
                        MSG = []
                else:
                    new_caption = custom_caption(message, caption)
                    cover_to_use = custom_cover_url or getattr(getattr(getattr(message, 'video', None), 'cover', None), 'file_id', None)

                    # Message Replacements
                    if new_caption and message_replacements:
                        for find, replace in message_replacements.items():
                            new_caption = new_caption.replace(find, replace)

                    details = {"msg_id": message.id, "media": media(message), "cover": cover_to_use, "caption": new_caption, 'button': button, "protect": protect}
                    await copy(user, client, details, i.bot_id, sts, _bot, from_chat, to_chat)
                    sts.add('total_files')
                    await asyncio.sleep(sleep)
        except Exception as e:
            await edit(user, i.bot_id, 'ᴇʀʀᴏʀ', f'{e}', sts, _bot, from_chat, to_chat)
            logger.error(f"Error In Forwarding {e}")
            if user_have_db and not persistent_deduplication:
                await user_db.drop_all()
            if user_db:
                await user_db.close()
            if sts.TO in temp.IS_FRWD_CHAT:
                temp.IS_FRWD_CHAT.remove(sts.TO)
            await stop(client, user, i.bot_id)
            return

        if sts.TO in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(sts.TO)
        await send(client, user, "<b>🎉 ғᴏʀᴡᴀᴅɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>")
        await edit(user, i.bot_id, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts, _bot, from_chat, to_chat)
        if user_have_db and not persistent_deduplication:
            await user_db.drop_all()
        if user_db:
            await user_db.close()
        await stop(client, user, i.bot_id)

    except Exception as e:
        logger.error(f"A critical error occurred in the forwarding setup: {e}", exc_info=True)
        if i: # Ensure 'i' was defined before the error
            await stop(client, user, i.bot_id)
        if user_db:
            if not persistent_deduplication:
                await user_db.drop_all()
            await user_db.close()
        await message.answer("ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴀɴᴅ ᴛʜᴇ ᴛᴀsᴋ ᴡᴀs ᴄᴀɴᴄᴇʟʟᴇᴅ.", show_alert=True)



async def copy(user_id, bot, msg, bot_id, sts, bot_info, from_chat, to_chat):
   try:
     if msg.get("media") and msg.get("caption"):
        await bot.send_cached_media(
              chat_id=sts.get('TO'),
              file_id=msg.get("media"),
              cover = msg.get("cover"),
              caption=msg.get("caption"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
     else:
        await bot.copy_message(
              chat_id=sts.get('TO'),
              from_chat_id=sts.get('FROM'),
              video_cover = msg.get("cover"),
              caption=msg.get('caption'),
              message_id=msg.get("msg_id"),
              reply_markup=msg.get('button'),
              protect_content=msg.get("protect"))
   except FloodWait as e:
     await edit(user_id, bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', e.value, sts, bot_info, from_chat, to_chat)
     await asyncio.sleep(e.value)
     await edit(user_id, bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts, bot_info, from_chat, to_chat)
     await copy(user_id, bot, msg, bot_id, sts, bot_info, from_chat, to_chat)
   except Exception as e:
     logger.error(f"Error In Copying {e}")
     sts.add('deleted')

async def forward(user_id, bot, msg_ids, sts, protect, bot_info, from_chat, to_chat):
   try:
     await bot.forward_messages(
           chat_id=sts.get('TO'),
           from_chat_id=sts.get('FROM'),
           protect_content=protect,
           message_ids=msg_ids)
   except FloodWait as e:
     bot_id = bot_info['id']
     await edit(user_id, bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', e.value, sts, bot_info, from_chat, to_chat)
     await asyncio.sleep(e.value)
     await edit(user_id, bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts, bot_info, from_chat, to_chat)
     await forward(user_id, bot, msg_ids, sts, protect, bot_info, from_chat, to_chat)


PROGRESS = """
📈 ᴘᴇʀᴄᴇɴᴛᴀɢᴇ : {0} %

⭕ ғᴇᴛᴄʜᴇᴅ : {1}

⚙️ ғᴏʀᴡᴀʀᴅᴇᴅ : {2}

🗞️ ʀᴇᴍᴀɴɪɴɢ : {3}

♻️ sᴛᴀᴛᴜs : {4}

⏳️ ᴇᴛᴄ : {5}
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass
    except FloodWait as e:
        if wait:
           await asyncio.sleep(e.value)
           return await msg_edit(msg, text, button, wait)

async def edit(user_id, bot_id, title, status, sts, bot_info, from_chat, to_chat):
    try:
        msg = temp.ACTIVE_STATUS_MSGS.get(user_id, {}).get(bot_id)
        if not msg:
            logging.warning(f"No active status message for user {user_id}, bot {bot_id}")
            return
            
        i = sts.get(full=True)
        status = 'Forwarding' if status == 5 else f"sleeping {status} s" if str(status).isnumeric() else status
        percentage = "{:.0f}".format(float(i.fetched)*100/float(i.total)) if float(i.total) > 0 else "0"
        client_type = sts.get('client_type')
        await update_forward(user_id=user_id, last_id=None, start_time=i.start, limit=i.limit, chat_id=i.FROM, toid=i.TO, forward_id=None, msg_id=msg.id, fetched=i.fetched, deleted=i.deleted, total=i.total_files, duplicate=i.duplicate, skip=i.skip, filterd=i.filtered, client_type=client_type, bot_id=i.bot_id)
        now = time.time()
        diff = int(now - i.start) if i.start>0 else 0
        speed = sts.divide(i.fetched, diff)
        elapsed_time = round(diff) * 1000
        time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000 if speed > 0 else 0
        estimated_total_time = elapsed_time + time_to_completion
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
        estimated_total_time = estimated_total_time if (estimated_total_time != '' or status not in ["ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"]) else '0 s'
        remaining = i.limit - i.fetched if i.limit > i.fetched else 0
        start_time = sts.get('start')
        uptime = await get_bot_uptime(start_time)
        total = sts.get('limit') - sts.get('fetched')
        time_to_comple = await complete_time(total)
        time_to_comple = time_to_comple if (time_to_comple != '' and status not in ["ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"]) else '0 s'
        progress, percentage = progress_bar_tuple(percentage)
        bar=f"{progress} ​• {percentage}%"
        button =  [[InlineKeyboardButton(bar, f'fwrdstatus#{status}#{percentage}#{i.id}')]]
        text = TEXT.format(i.total, i.fetched, i.total_files, remaining, i.duplicate,
                            i.deleted, i.skip, i.filtered, status, time_to_comple, bot_info['id'], bot_info['name'], from_chat.title, to_chat.title, title)
        if status in ["ᴄᴀɴᴄᴇʟʟᴇᴅ", "ᴄᴏᴍᴘʟᴇᴛᴇᴅ"]:
           button.append([InlineKeyboardButton('• ᴄᴏᴍᴘʟᴇᴛᴇᴅ ​•', url='https://t.me/Blaze_updateZ')])
        else:
           button.append([InlineKeyboardButton('• ᴄᴀɴᴄᴇʟ', f'terminate_frwd_{i.bot_id}')])
        await msg_edit(msg, text, InlineKeyboardMarkup(button))
    except Exception as e:
        logging.error(e, exc_info=True)

async def is_cancelled(client, user_id, sts, bot_id, bot_info, from_chat, to_chat):
   if temp.CANCEL.get(user_id, {}).get(bot_id):
      if sts.TO in temp.IS_FRWD_CHAT:
         temp.IS_FRWD_CHAT.remove(sts.TO)
      await edit(user_id, bot_id, 'ᴄᴀɴᴄᴇʟʟᴇᴅ', "ᴄᴀɴᴄᴇʟʟᴇᴅ", sts, bot_info, from_chat, to_chat)
      await send(client, user_id, Script.FORWARD_CANCEL_TXT.format(bot_info['id'], bot_info['name'], from_chat.title, to_chat.title))
      await stop(client, user_id, bot_id)
      return True
   return False

async def stop(client, user_id, bot_id):
   try:
     if client:
        await client.stop()
   except:
     pass
   await db.rmve_frwd(user_id, bot_id)
   temp.forwardings -= 1
   if user_id in temp.lock and bot_id in temp.lock[user_id]:
       temp.lock[user_id].remove(bot_id)
   if user_id in temp.ACTIVE_STATUS_MSGS and bot_id in temp.ACTIVE_STATUS_MSGS[user_id]:
       del temp.ACTIVE_STATUS_MSGS[user_id][bot_id]

async def send(bot, user, text):
   try:
      await bot.send_message(user, text=text)
   except:
      pass

def custom_caption(msg, caption):
  if msg.media:
    if (msg.video or msg.document or msg.audio or msg.photo):
      media = getattr(msg, msg.media.value, None)
      if media:
        file_name = getattr(media, 'file_name', '')
        file_size = getattr(media, 'file_size', '')
        fcaption = getattr(msg, 'caption', '')
        if fcaption:
          fcaption = fcaption.html
        if caption:
          return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
        return fcaption
  return None

def get_size(size):
  if not size: return "0 B"
  units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
  size = float(size)
  i = 0
  while size >= 1024.0 and i < len(units):
     i += 1
     size /= 1024.0
  return "%.2f %s" % (size, units[i])

async def keyword_filter(keywords, file_name):
    if keywords is None:
        return False
    if re.search(keywords, file_name):
        return False
    else:
        return True

async def extension_filter(extensions, file_name):
    if extensions is None:
        return False
    if not re.search(extensions, file_name):
        return False
    else:
        return True

async def size_filter(max_size, min_size, file_size):
    file_size = file_size / 1024 / 1024
    if max_size and min_size == 0:
        return False
    if max_size == 0:
        return file_size < min_size
    if min_size == 0:
        return file_size > max_size
    if not min_size <= file_size <= max_size:
        return True
    else:
        return False

def media(msg):
  if msg.media:
     media = getattr(msg, msg.media.value, None)
     if media:
        return getattr(media, 'file_id', None)
  return None

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ ʀᴇᴛʀʏ ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd_'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id
    bot_id = int(m.data.split('_')[2])
    if user_id not in temp.CANCEL:
        temp.CANCEL[user_id] = {}
    temp.CANCEL[user_id][bot_id] = True
    await m.answer("ғᴏʀᴡᴀʀᴅɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ !", show_alert=True)

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if not sts.verify():
       fetched, forwarded, remaining = 0, 0, 0
    else:
       fetched, limit, forwarded = sts.get('fetched'), sts.get('limit'), sts.get('total_files')
       remaining = limit - fetched
    start_time = sts.get('start')
    uptime = await get_bot_uptime(start_time)
    total = sts.get('limit') - sts.get('fetched')
    time_to_comple = await complete_time(total)
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, time_to_comple, uptime), show_alert=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()

@Client.on_message(filters.private & filters.command(['stop']))
async def stop_forward(client, message):
    user_id = message.from_user.id
    if not await db.is_forwad_exit(user_id):
        return await message.reply('**ɴᴏ ᴏɴɢᴏɪɴɢ ғᴏʀᴡᴀʀᴅs ᴛᴏ ᴄᴀɴᴄᴇʟ**')

    buttons = []
    for bot_id in temp.lock.get(user_id, []):
        buttons.append([InlineKeyboardButton(f"ғᴏʀᴡᴀʀᴅ ɪᴅ: {bot_id}", callback_data=f"stop_task_{bot_id}")])

    if not buttons:
        return await message.reply('**ɴᴏ ᴏɴɢᴏɪɴɢ ғᴏʀᴡᴀʀᴅs ᴛᴏ ᴄᴀɴᴄᴇʟ**')

    await message.reply("ᴡʜɪᴄʜ ғᴏʀᴡᴀʀᴅɪɴɢ ᴛᴀsᴋ ᴡᴏᴜʟᴅ ʏᴏᴜ ʟɪᴋᴇ ᴛᴏ sᴛᴏᴘ?", reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r'^stop_task_'))
async def stop_task_callback(bot, query):
    user_id = query.from_user.id
    bot_id = int(query.data.split('_')[2])
    if user_id not in temp.CANCEL:
        temp.CANCEL[user_id] = {}
    temp.CANCEL[user_id][bot_id] = True
    await query.message.edit(f"<b>sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴄᴀɴᴄᴇʟᴇᴅ ᴛᴀsᴋ ғᴏʀ ғᴏʀᴡᴀʀᴅ ɪᴅ: {bot_id}</b>")

async def restart_pending_forwads(bot, user):
    user_id = user['user_id']
    bot_id = user['bot_id']
    settings = await db.get_forward_details(user_id, bot_id)
    try:
       skiping = settings['offset']
       fetch = settings['fetched'] - settings['skip']
       temp.forwardings += 1
       forward_id = await store_vars(user_id, bot_id)
       sts = STS(forward_id)
       if settings['chat_id'] is None:
           await db.rmve_frwd(user_id, bot_id)
           temp.forwardings -= 1
           return
       if not sts.verify():
          temp.forwardings -=1
          return
       sts.add('fetched', value=fetch)
       sts.add('duplicate', value=settings['duplicate'])
       sts.add('filtered', value=settings['filtered'])
       sts.add('deleted', value=settings['deleted'])
       sts.add('total_files', value=settings['total'])
       m = await bot.get_messages(user_id, settings['msg_id'])
       temp.ACTIVE_STATUS_MSGS.setdefault(user_id, {})[bot_id] = m
       _bot, caption, forward_tag, datas, protect, button = await sts.get_data(user_id)
       i = sts.get(full=True)
       user_rank = await db.get_premium_user_rank(user_id)
       if user_rank == "default":
            # If user is not premium, disable premium features for this task
            regex_filter = None
            message_replacements = None
            persistent_deduplication = False
            regex_filter_mode = 'exclude'
       else:
            regex_filter = datas.get('regex_filter')
            message_replacements = datas.get('message_replacements')
            persistent_deduplication = datas.get('persistent_deduplication', False)
            regex_filter_mode = datas.get('regex_filter_mode', 'exclude')
       forwarding_speed = Config.FORWARDING_SPEED.get(user_rank, Config.FORWARDING_SPEED["default"]) if _bot['is_bot'] else 10
       filter = datas['filters']
       max_size = datas['max_size']
       min_size = datas['min_size']
       keyword = datas['keywords']
       exten = datas['extensions']
       keywords = ""
       extensions = ""
       if keyword:
           for key in keyword:
               keywords += f"{key}|"
           keywords  = keywords.rstrip("|")
       else:
           keywords = None
       if exten:
           for ext in exten:
               extensions += f"{ext}|"
           extensions = extensions.rstrip("|")
       else:
           extensions = None
       if not _bot:
          await msg_edit(m, "<code>ʏᴏᴜ ᴅɪᴅɴ'ᴛ ᴀᴅᴅ ᴀɴʏ ʙᴏᴛ. ᴘʟᴇᴀsᴇ ᴀᴅᴅ ᴀ ʙᴏᴛ ᴜsɪɴɢ /settings !</code>", wait=True)
          return
       if _bot['is_bot'] == True:
          data = _bot['token']
       else:
          data = _bot['session']
       try:
          il = True if _bot['is_bot'] == True else False
          client = await get_client(data, is_bot=il)
          await client.start()
       except Exception as e:
          await m.edit(e)
          return
       try:
          await msg_edit(m, "<code>ᴘʀᴏᴄᴇssɪɴɢ...</code>")
       except:
          await db.rmve_frwd(user_id, bot_id)
          return
       try:
          from_chat = await client.get_chat(sts.get("FROM"))
          to_chat = await client.get_chat(sts.get("TO"))
       except Exception as e:
          await msg_edit(m, f"**ᴇʀʀᴏʀ:**\n`{e}`\n\n**sᴏᴜʀᴄᴇ/ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ᴍᴀʏ ʙᴇ ᴀ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀɴɴᴇʟ / ɢʀᴏᴜᴘ. ᴜsᴇ ᴀ ᴜsᴇʀʙᴏᴛ (ᴜsᴇʀ ᴍᴜsᴛ ʙᴇ ᴀ ᴍᴇᴍʙᴇʀ) ᴏʀ ᴍᴀᴋᴇ ʏᴏᴜʀ [ʙᴏᴛ](t.me/{_bot['username']}) ᴀɴ ᴀᴅᴍɪɴ ᴛʜᴇʀᴇ**", retry_btn(forward_id), True)
          await stop(client, user_id, bot_id)
          return
       try:
          k = await client.send_message(i.TO, "ᴛᴇsᴛɪɴɢ")
          await k.delete()
       except:
          await msg_edit(m, f"**ᴘʟᴇᴀsᴇ ᴍᴀᴋᴇ ʏᴏᴜʀ [UserBot / Bot](t.me/{_bot['username']}) ᴀᴅᴍɪɴ ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟ ᴡɪᴛʜ ꜰᴜʟʟ ᴘᴇʀᴍɪssɪᴏɴs**", retry_btn(forward_id), True)
          await stop(client, user_id, bot_id)
          return
    except:
       await db.rmve_frwd(user_id, bot_id)
       return
    user_have_db = False
    dburi = datas['db_uri']
    if dburi:
        if persistent_deduplication:
            connected, user_db = await connect_persistent_db(user_id, dburi)
        else:
            connected, user_db = await connect_user_db(user_id, dburi, i.TO)

        if not connected:
            await bot.send_message(user_id, "<code>ᴄᴀɴɴᴏᴛ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ ʏᴏᴜʀ ᴅʙ. ᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇs ᴍᴀʏ ʙᴇ sᴋɪᴘᴘᴇᴅ ᴀꜰᴛᴇʀ ʀᴇsᴛᴀʀᴛ.</code>")
        else:
            user_have_db = True
    try:
        start = settings['start_time']
    except KeyError:
        start = None
    sts.add(time=True, start_time=start)
    sleep = random.uniform(forwarding_speed,1)
    temp.IS_FRWD_CHAT.append(i.TO)

    if user_id not in temp.lock:
        temp.lock[user_id] = []
    temp.lock[user_id].append(bot_id)

    try:
      MSG = []
      pling=0
      await edit(user_id, bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts, _bot, from_chat, to_chat)
      async for message in iter_messages(client, chat_id=sts.get("FROM"), limit=sts.get("limit"), offset=skiping, filters=filter, max_size=max_size):
            if await is_cancelled(client, user_id, sts, bot_id, _bot, from_chat, to_chat):
                if user_have_db:
                   if not persistent_deduplication:
                       await user_db.drop_all()
                   await user_db.close()
                return
            if pling %20 == 0:
               await edit(user_id, bot_id, 'ᴘʀᴏɢʀᴇssɪɴɢ', 5, sts, _bot, from_chat, to_chat)
            pling += 1
            sts.add('fetched')

            if isinstance(message, str):
                if message == "DUPLICATE":
                    sts.add("duplicate")
                elif message == "FILTERED":
                    sts.add("filtered")
                continue
            if message.empty or message.service:
               sts.add('deleted')
               continue
            media_obj = None
            fname = fsize = fuid = None
            if message.media:
                media_obj = getattr(message, message.media.value, None)
                if not media_obj:
                    continue
                fname = getattr(media_obj, "file_name", None)
                fsize = getattr(media_obj, "file_size", None)
                fuid = getattr(media_obj, "file_unique_id", None)
            else:
                media_obj = fname = fsize = fuid = None

            if regex_filter and fname:
                if regex_filter_mode == 'exclude' and re.search(regex_filter, fname):
                    sts.add('filtered')
                    continue
                if regex_filter_mode == 'include' and not re.search(regex_filter, fname):
                    sts.add('filtered')
                    continue

            if media_obj and fname and await extension_filter(extensions, fname):
               sts.add('filtered')
               continue
            elif media_obj and fname and await keyword_filter(keywords, fname):
               sts.add('filtered')
               continue
            elif media_obj and fsize is not None and await size_filter(max_size, min_size, fsize):
               sts.add('filtered')
               continue
            
            if user_have_db and (datas['skip_duplicate'] or persistent_deduplication) and fuid:
                if await user_db.is_file_exit(fuid):
                    sts.add('duplicate')
                    continue
                await user_db.add_file(fuid)

            if forward_tag:
               MSG.append(message.id)
               notcompleted = len(MSG)
               completed = sts.get('total') - sts.get('fetched')
               if ( notcompleted >= 100
                    or completed <= 100):
                  await forward(user_id, client, MSG, sts, protect, _bot, from_chat, to_chat)
                  sts.add('total_files', notcompleted)
                  await asyncio.sleep(10)
                  MSG = []
            else:
               new_caption = custom_caption(message, caption)
               if new_caption and message_replacements:
                   for find, replace in message_replacements.items():
                       new_caption = new_caption.replace(find, replace)
               details = {"msg_id": message.id, "media": media(message), "caption": new_caption, 'button': button, "protect": protect}
               await copy(user_id, client, details, bot_id, sts, _bot, from_chat, to_chat)
               sts.add('total_files')
               await asyncio.sleep(sleep)
    except Exception as e:
        await bot.send_message(user_id, f'<b>ᴇʀʀᴏʀ:</b>\n<code>{e}</code>')
        if user_have_db:
            if not persistent_deduplication:
                await user_db.drop_all()
            await user_db.close()
        if sts.TO in temp.IS_FRWD_CHAT:
            temp.IS_FRWD_CHAT.remove(sts.TO)
        await stop(client, user_id, bot_id)
        return

    if sts.TO in temp.IS_FRWD_CHAT:
        temp.IS_FRWD_CHAT.remove(sts.TO)
    await send(client, user_id, "<b>🎉 ғᴏʀᴡᴀᴅɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b>")
    if user_have_db:
        if not persistent_deduplication:
            await user_db.drop_all()
        await user_db.close()
    await edit(user_id, bot_id, 'ᴄᴏᴍᴘʟᴇᴛᴇᴅ', "ᴄᴏᴍᴘʟᴇᴛᴇᴅ", sts, _bot, from_chat, to_chat)
    await stop(client, user_id, bot_id)



async def store_vars(user_id, bot_id):
    settings = await db.get_forward_details(user_id, bot_id)
    fetch = settings['fetched']
    client_type = settings['client_type']
    forward_id = f'{user_id}-{fetch}'
    STS(id=forward_id).store(settings['chat_id'], settings['toid'], settings['skip'], settings['limit'], client_type, bot_id)
    return forward_id

async def restart_forwards(client):
    users = await db.get_all_frwd()
    count = await db.forwad_count()
    logger.info("successfully restarted %s forwards", count)
    tasks = []
    async for user in users:
        tasks.append(restart_pending_forwads(client, user))
    await asyncio.gather(*tasks)

async def update_forward(user_id, chat_id, start_time, toid, last_id, limit, forward_id, msg_id, fetched, total, duplicate, deleted, skip, filterd, client_type, bot_id):
    details = {
        'chat_id': chat_id,
        'toid': toid,
        'forward_id': forward_id,
        'last_id': last_id,
        'limit': limit,
        'msg_id': msg_id,
        'start_time': start_time,
        'fetched': fetched,
        'offset': fetched,
        'deleted': deleted,
        'total': total,
        'duplicate': duplicate,
        'skip': skip,
        'filtered':filterd,
        'client_type': client_type
    }
    await db.update_forward(user_id, bot_id, details)

async def get_bot_uptime(start_time):
    if start_time == 0: return "0s"
    # Calculate the uptime in seconds
    uptime_seconds = int(time.time() - start_time)
    uptime_minutes = uptime_seconds // 60
    uptime_hours = uptime_minutes // 60
    uptime_days = uptime_hours // 24
    uptime_weeks = uptime_days // 7
    uptime_string = ""
    if uptime_weeks != 0:
        uptime_string += f"{uptime_weeks % 7}w, "
    if uptime_days != 0:
        uptime_string += f"{uptime_days % 24}d, "
    if uptime_hours != 0:
        uptime_string += f"{uptime_hours % 24}h, "
    if uptime_minutes != 0:
        uptime_string += f"{uptime_minutes % 60}m, "
    uptime_string += f"{uptime_seconds % 60}s"
    return uptime_string

async def complete_time(total_files, files_per_minute=30):
    if total_files == 0: return "0s"
    minutes_required = total_files / files_per_minute
    seconds_required = minutes_required * 60
    weeks = seconds_required // (7 * 24 * 60 * 60)
    days = (seconds_required % (7 * 24 * 60 * 60)) // (24 * 60 * 60)
    hours = (seconds_required % (24 * 60 * 60)) // (60 * 60)
    minutes = (seconds_required % (60 * 60)) // 60
    seconds = seconds_required % 60
    time_format = ""
    if weeks > 0:
        time_format += f"{int(weeks)}w, "
    if days > 0:
        time_format += f"{int(days)}d, "
    if hours > 0:
        time_format += f"{int(hours)}h, "
    if minutes > 0:
        time_format += f"{int(minutes)}m, "
    if seconds > 0:
        time_format += f"{int(seconds)}s, "
    return time_format[:-2] if time_format else "0s"