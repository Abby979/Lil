import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv(override=True)

# Convert to integers safely
def parse_id(id_str):
    return int(id_str) if id_str and id_str.isdigit() else None

# Settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = parse_id(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None
LOCAL_TZ = timezone(os.getenv("LOCAL_TZ", "UTC"))

#Servers
knitting_server_id= parse_id(os.getenv("REAL_KNITTING_SERVER_ID"))
knitting_test_server_id = parse_id(os.getenv("KNITTING_TEST_SERVER_ID"))
knitting_index_file_path = os.getenv("KNITTING_INDEX_FILE_PATH", "data/KnittingIndex.csv")
sewing_server_id = parse_id(os.getenv("REAL_SEWING_SERVER_ID"))
sewing_test_server_id = parse_id(os.getenv("SEWING_TEST_SERVER_ID"))
sewing_index_file_path = os.getenv("SEWING_INDEX_FILE_PATH", "data/SewingIndex.csv")