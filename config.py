from os import environ
from dotenv import load_dotenv


load_dotenv()

class Config:
    
    BOT_OWNER = int(environ.get("BOT_OWNER", ""))
    API_ID = environ.get("API_ID", "")
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "Auto_Forward")
    DATABASE_URI = environ.get("DATABASE_URI", "")
    DATABASE_NAME = environ.get("DATABASE_NAME", "")
    PREMIUM_USERS = {}
    TASK_LIMITS = {
        "gold": 4,
        "silver": 3,
        "bronze": 2,
        "default": 1
    }
    FORWARDING_SPEED = {
        "gold": 0.8,      # 0.5 seconds delay
        "silver": 0.83,        # 1 second delay
        "bronze": 0.85,      # 1.5 seconds delay
        "default": 0.85        # 2 seconds delay for free users
    }


class temp(object): 
    lock = {} # Will be {user_id: [busy_bot_id1, busy_bot_id2]}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []
    USER_LOCKS = {} # To prevent race conditions
    ACTIVE_STATUS_MSGS = {} # {user_id: {bot_id: message_object}}