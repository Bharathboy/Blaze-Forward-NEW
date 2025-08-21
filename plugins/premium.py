import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from config import Config
from database import db

def get_user_id(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    try:
        return int(message.command[1])
    except (IndexError, ValueError):
        return None

def get_rank(message):
    try:
        return message.command[2]
    except IndexError:
        return "bronze" # Default rank

def get_expiry_time(message):
    try:
        duration_str = message.command[3]
        duration_unit = duration_str[-1].lower()
        duration_value = int(duration_str[:-1])

        if duration_unit == 'd':
            return datetime.now() + timedelta(days=duration_value)
        elif duration_unit == 'w':
            return datetime.now() + timedelta(weeks=duration_value)
        elif duration_unit == 'm':
            return datetime.now() + timedelta(days=30 * duration_value) # Approximate month
        else:
            return None # Invalid time unit
    except (IndexError, ValueError):
        return None # No expiry

@Client.on_message(filters.command("add_premium") & filters.user(Config.BOT_OWNER))
async def add_premium(client, message):
    user_id = get_user_id(message)
    if not user_id:
        return await message.reply_text("Please reply to a user or provide a user ID.")

    rank = get_rank(message)
    if rank not in ["gold", "silver", "bronze"]:
        return await message.reply_text("Invalid rank. Please use 'gold', 'silver', or 'bronze'.")

    expiry_time = get_expiry_time(message)
    await db.add_premium_user(user_id, rank, expiry_time)
    
    expiry_text = f"until {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}" if expiry_time else "permanently"
    await message.reply_text(f"User {user_id} has been given {rank} premium status {expiry_text}.")


@Client.on_message(filters.command("remove_premium") & filters.user(Config.BOT_OWNER))
async def remove_premium(client, message):
    user_id = get_user_id(message)
    if not user_id:
        return await message.reply_text("Please reply to a user or provide a user ID.")

    if await db.is_premium_user(user_id):
        await db.remove_premium_user(user_id)
        await message.reply_text(f"Premium status for user {user_id} has been removed.")
    else:
        await message.reply_text("This user does not have premium status.")