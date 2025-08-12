import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv(override=True)

# Convert to integers safely
def parse_id(id_str):
    return int(id_str) if id_str and id_str.isdigit() else None

# Settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None
LOCAL_TZ = timezone(os.getenv("LOCAL_TZ", "UTC"))
index_file_path = os.getenv("INDEX_FILE_PATH", "data/index.csv")
test_guild_id = parse_id(os.getenv("TEST_SERVER_ID"))