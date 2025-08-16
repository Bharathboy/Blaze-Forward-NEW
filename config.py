

from os import environ 

class Config:
    
    BOT_OWNER = int(environ.get("BOT_OWNER", ""))
    API_ID = environ.get("API_ID", "")
    API_HASH = environ.get("API_HASH", "")
    BOT_TOKEN = environ.get("BOT_TOKEN", "") 
    BOT_SESSION = environ.get("BOT_SESSION", "Auto_Forward")
    DATABASE_URI = environ.get("DATABASE", "")
    DATABASE_NAME = environ.get("DATABASE_NAME", "")



class temp(object): 
    lock = {}
    CANCEL = {}
    forwardings = 0
    BANNED_USERS = []
    IS_FRWD_CHAT = []


# import datetime
# from os import environ 



# def is_enabled(value, default):
#     if value.lower() in ["true", "yes", "1", "enable", "y"]:
#         return True
#     elif value.lower() in ["false", "no", "0", "disable", "n"]:
#         return False
#     else:
#         return default
    

# class Config:
#     API_ID = environ.get("API_ID", "22043035")
#     API_HASH = environ.get("API_HASH", "08e002c62185fb3da73d28bceb335a17")
#     BOT_TOKEN = environ.get("BOT_TOKEN", "7968171456:AAFX41KdpmWfWhrnRqSbDXFDwh3D0KCeGjI") 
#     BOT_SESSION = environ.get("BOT_SESSION", "Auto_Forward")
#     DATABASE_URI = environ.get("DATABASE", "mongodb+srv://marifolwra:9Pr5cSBmEOaUVgp9@blaze.fudpqpn.mongodb.net/?retryWrites=true&w=majority&appName=Blaze")
#     DATABASE_NAME = environ.get("DATABASE_NAME", "Blaze")
#     BOT_OWNER_ID = [int(id) for id in environ.get("BOT_OWNER_ID", '634637418').split()]
#     LOG_CHANNEL = int(environ.get('LOG_CHANNEL', '-1001532531973'))
#     FORCE_SUB_CHANNEL = environ.get("FORCE_SUB_CHANNEL", "") 
#     FORCE_SUB_ON = is_enabled(environ.get("FORCE_SUB_ON", "False"), False)
#     PORT = environ.get('PORT', '8080')
