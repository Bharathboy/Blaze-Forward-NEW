import asyncio
import logging
from typing import Union, Optional, AsyncGenerator

from pyrogram import Client as VJ, idle, types, filters
from pyrogram.handlers import MessageHandler

from config import Config, temp
from database import db
from plugins.regix import restart_forwards
from liveforward.handler import live_forward_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s ",
    force=True
)

pyro_log = logging.getLogger("pyrogram")
pyro_log.setLevel(logging.WARNING)

async def check_expired_premiums(client):
    """Periodically checks for and removes expired premium plans, notifying users."""
    while True:
        try:
            expired_user_ids = await db.get_and_remove_expired_users()
            for user_id in expired_user_ids:
                try:
                    await asyncio.sleep(1)
                    await client.send_message(
                        user_id,
                        "😢 **Your premium plan has expired.** 😢\n\n"
                        "You have been reverted to the **Free** plan. To upgrade again, please contact the bot owner."
                    )
                    logging.info(f"Sent expiration notice to user {user_id}")
                except Exception as e:
                    logging.warning(f"Could not send expiration notice to user {user_id}: {e}")
            
            await asyncio.sleep(3600)  # Sleep for 1 hour
        except Exception as e:
            logging.error(f"Error in background premium check: {e}", exc_info=True)
            await asyncio.sleep(300)  # Sleep for 5 minutes on error

# This dictionary will hold the running userbot clients for live forwarding
# Key: user_id, Value: pyrogram.Client instance
temp.LIVE_FORWARD_CLIENTS = {}

async def start_live_forwarder_for_user(user_id):
    """Starts a userbot client for a specific user to listen for messages."""
    if user_id in temp.LIVE_FORWARD_CLIENTS:
        logging.warning(f"Live forwarder for user {user_id} is already running.")
        return

    userbots = await db.get_userbots(user_id)
    if not userbots:
        logging.error(f"Attempted to start live forwarder for user {user_id} but no userbot found.")
        return
        
    # Using the first available userbot for listening
    userbot_session = userbots[0]['session']
    
    try:
        user_client = VJ(
            name=f"userbot_{user_id}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=userbot_session,
            no_updates=False # Ensure it receives updates
        )
        await user_client.start()
        user_client.add_handler(MessageHandler(live_forward_handler, filters.channel))
        temp.LIVE_FORWARD_CLIENTS[user_id] = user_client
        logging.info(f"Successfully started live forwarder listener for user {user_id}.")
    except Exception as e:
        logging.error(f"Failed to start live forwarder for user {user_id}: {e}", exc_info=True)


async def stop_live_forwarder_for_user(user_id):
    """Stops the listening userbot client for a specific user."""
    if user_id in temp.LIVE_FORWARD_CLIENTS:
        try:
            await temp.LIVE_FORWARD_CLIENTS[user_id].stop()
            logging.info(f"Successfully stopped live forwarder for user {user_id}.")
        except Exception as e:
            logging.error(f"Error stopping live forwarder for user {user_id}: {e}")
        finally:
            del temp.LIVE_FORWARD_CLIENTS[user_id]

async def load_all_live_forwards_on_startup():
    """Finds all unique users with active live forwards and starts their listeners."""
    all_forwards = await db.get_all_live_forwards()
    unique_user_ids = set()
    async for forward in all_forwards:
        Config.LIVE_FORWARD_CONFIG[forward['from_chat_id']] = {
            "user_id": forward['user_id'],
            "to_chat_id": forward['to_chat_id'],
            "bot_id": forward['bot_id'],
            "client_type": forward['client_type']
        }
        unique_user_ids.add(forward['user_id'])
    
    logging.info(f"Found {len(unique_user_ids)} users with active live forwards. Starting listeners...")
    for user_id in unique_user_ids:
        await start_live_forwarder_for_user(user_id)


if __name__ == "__main__":
    VJBot = VJ(
        "VJ-Forward-Bot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        sleep_threshold=120,
        plugins=dict(root="plugins")
    )
      
    async def main():
        await VJBot.start()
        logging.info("Main bot started.")
        
        # Load configurations and start all necessary listeners on restart
        await load_all_live_forwards_on_startup()
        await restart_forwards(VJBot)
        
        logging.info("Bot is now online.")
        await idle()

    asyncio.get_event_loop().run_until_complete(main())