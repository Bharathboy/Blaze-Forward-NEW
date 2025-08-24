

import os
import sys
import asyncio 
from database import Db, db
from config import Config, temp
from script import Script
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument
import psutil
import time as time
from os import environ, execle, system

START_TIME = time.time()



main_buttons = [[
    InlineKeyboardButton('❣️ ᴅᴇᴠᴇʟᴏᴘᴇʀ ❣️', url='https://t.me/bharath_boy')
],[
    InlineKeyboardButton('🔍 ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ ', url='https://t.me/bharathboi_bot'),
    InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/filmztube')
],[
    InlineKeyboardButton('👨‍💻 ʜᴇʟᴘ', callback_data='help'),
    InlineKeyboardButton('💁 ᴀʙᴏᴜᴛ', callback_data='about')
],[
    InlineKeyboardButton('⚙ sᴇᴛᴛɪɴɢs', callback_data='settings#main')
]]



@Client.on_message(filters.private & filters.command(['start']))
async def start(client, message):
    user = message.from_user
    if not await db.is_user_exist(user.id):
        await db.add_user(user.id, user.first_name)
    reply_markup = InlineKeyboardMarkup(main_buttons)
    await client.send_message(
        chat_id=message.chat.id,
        reply_markup=reply_markup,
        text=Script.START_TXT.format(message.from_user.first_name))



@Client.on_message(filters.private & filters.command(['restart']) & filters.user(Config.BOT_OWNER))
async def restart(client, message):
    msg = await message.reply_text(text="<i>Trying to restarting.....</i>")
    await asyncio.sleep(5)
    await msg.edit("<i>Server restarted successfully ✅</i>")
    system("git pull -f && pip3 install --no-cache-dir -r requirements.txt")
    execle(sys.executable, sys.executable, "main.py", environ)



@Client.on_callback_query(filters.regex(r'^help'))
async def helpcb(bot, query):
    buttons = [[
        InlineKeyboardButton('🤔 ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴍᴇ ❓', callback_data='how_to_use')
    ],[
        InlineKeyboardButton('Aʙᴏᴜᴛ ✨️', callback_data='about'),
        InlineKeyboardButton('⚙ Sᴇᴛᴛɪɴɢs', callback_data='settings#main')
    ],[
        InlineKeyboardButton('• back', callback_data='back')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.edit_text(text=Script.HELP_TXT, reply_markup=reply_markup, disable_web_page_preview=True)


@Client.on_callback_query(filters.regex(r'^how_to_use'))
async def how_to_use(bot, query):
    buttons = [[InlineKeyboardButton('• back', callback_data='help')]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.edit_text(
        text=Script.HOW_USE_TXT,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )



@Client.on_callback_query(filters.regex(r'^back'))
async def back(bot, query):
    reply_markup = InlineKeyboardMarkup(main_buttons)
    await query.message.edit_text(
       reply_markup=reply_markup,
       text=Script.START_TXT.format(query.from_user.first_name))



@Client.on_callback_query(filters.regex(r'^about'))
async def about(bot, query):
    buttons = [[
         InlineKeyboardButton('• back', callback_data='help'),
         InlineKeyboardButton('Stats ✨️', callback_data='status')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.edit_text(
        text=Script.ABOUT_TXT,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )



@Client.on_callback_query(filters.regex(r'^status'))
async def status(bot, query):
    users_count, bots_count = await db.total_users_bots_count()
    forwardings = await db.forwad_count()
    upt = await get_bot_uptime(START_TIME)
    buttons = [[
        InlineKeyboardButton('• back', callback_data='help'),
        InlineKeyboardButton('System Stats ✨️', callback_data='systm_sts'),
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.edit_text(
        text=Script.STATUS_TXT.format(upt, users_count, bots_count, forwardings),
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )



@Client.on_callback_query(filters.regex(r'^systm_sts'))
async def sys_status(bot, query):
    buttons = [[InlineKeyboardButton('• back', callback_data='help')]]
    ram = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent()
    disk_usage = psutil.disk_usage('/')
    total_space = disk_usage.total / (1024**3)  # Convert to GB
    used_space = disk_usage.used / (1024**3)    # Convert to GB
    free_space = disk_usage.free / (1024**3)
    text = f"""
╔════❰ sᴇʀᴠᴇʀ sᴛᴀᴛs  ❱═❍⊱❁۪۪
║╭━━━━━━━━━━━━━━━➣
║┣⪼ <b>ᴛᴏᴛᴀʟ ᴅɪsᴋ sᴘᴀᴄᴇ</b>: <code>{total_space:.2f} GB</code>
║┣⪼ <b>ᴜsᴇᴅ</b>: <code>{used_space:.2f} GB</code>
║┣⪼ <b>ꜰʀᴇᴇ</b>: <code>{free_space:.2f} GB</code>
║┣⪼ <b>ᴄᴘᴜ</b>: <code>{cpu}%</code>
║┣⪼ <b>ʀᴀᴍ</b>: <code>{ram}%</code>
║╰━━━━━━━━━━━━━━━➣
╚══════════════════❍⊱❁۪۪
"""
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.edit_text(
        text,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )



async def get_bot_uptime(start_time):
    # Calculate the uptime in seconds
    uptime_seconds = int(time.time() - start_time)
    uptime_minutes = uptime_seconds // 60
    uptime_hours = uptime_minutes // 60
    uptime_days = uptime_hours // 24
    uptime_weeks = uptime_days // 7
    uptime_string = ""
    if uptime_hours != 0:
        uptime_string += f" {uptime_hours % 24}H"
    if uptime_minutes != 0:
        uptime_string += f" {uptime_minutes % 60}M"
    uptime_string += f" {uptime_seconds % 60} Sec"
    return uptime_string   



@Client.on_message(filters.private & filters.command(['ongoing']))
async def ongoing_forwards(client, message):
    user_id = message.from_user.id
    if not await db.is_forwad_exit(user_id):
        return await message.reply('**ɴᴏ ᴏɴɢᴏɪɴɢ ғᴏʀᴡᴀʀᴅs**')

    forwards_cursor = await db.get_all_frwd()
    active_user_forwards = False
    async for forward in forwards_cursor:
        if forward.get('user_id') == user_id:
            active_user_forwards = True
            bot_id = forward.get('bot_id')
            
            # Delete old message object if it exists in memory and on Telegram
            try:
                old_msg = temp.ACTIVE_STATUS_MSGS.get(user_id, {}).get(bot_id)
                if old_msg:
                    await old_msg.delete()
            except Exception:
                pass # Already deleted or other error

            # Send a new status message
            new_sts_msg = await message.reply_text("`Generating new status message...`")
            
            # Update the message object in our global state
            temp.ACTIVE_STATUS_MSGS.setdefault(user_id, {})[bot_id] = new_sts_msg
            
            # Update the message ID in the database for persistence on restart
            details = await db.get_forward_details(user_id, bot_id)
            details['msg_id'] = new_sts_msg.id
            await db.update_forward(user_id, bot_id, details)
    
    if not active_user_forwards:
        await message.reply('**ɴᴏ ᴏɴɢᴏɪɴɢ ғᴏʀᴡᴀʀᴅs**')