import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv(override=True)

# Tokens and IDs for both test and real servers
BOT_TOKEN = os.getenv("BOT_TOKEN")
REAL_SERVER_ID = os.getenv("REAL_SERVER_ID")
TEST_SERVER_ID = os.getenv("TEST_SERVER_ID")
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None

LOCAL_TZ = timezone(os.getenv("LOCAL_TZ", "UTC"))
index_file_path = os.getenv("INDEX_FILE_PATH")
