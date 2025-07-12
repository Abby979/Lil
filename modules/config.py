import os
from dotenv import load_dotenv
from pytz import timezone

load_dotenv(override=True)

# Convert to integers safely
def parse_id(id_str):
    return int(id_str) if id_str and id_str.isdigit() else None

# Global settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None
LOCAL_TZ = timezone(os.getenv("LOCAL_TZ", "UTC"))

#SERVER IDs
REAL_KNITTING_SERVER_ID = parse_id(os.getenv("REAL_KNITTING_SERVER_ID"))
TEST_KNITTING_SERVER_ID = parse_id(os.getenv("TEST_KNITTING_SERVER_ID"))
REAL_SEWING_SERVER_ID = parse_id(os.getenv("REAL_SEWING_SERVER_ID"))
TEST_SEWING_SERVER_ID = parse_id(os.getenv("TEST_SEWING_SERVER_ID"))

#Shared file paths
DATA_DIR = "data/"
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
UPDATES_DIR = os.path.join(DATA_DIR, "updates")

# File paths per craft
CRAFTERS = {
    "knitting": {
        "index_file": os.path.join(BACKUPS_DIR, "knitting_backup.csv"),  # will become the index
        "last_backup_file": os.path.join(BACKUPS_DIR, "knitting_last_backup.txt"),
    },
    "sewing": {
        "index_file": os.path.join(BACKUPS_DIR, "sewing_backup.csv"),
        "last_backup_file": os.path.join(BACKUPS_DIR, "sewing_last_backup.txt"),
    },
}

# Server map
SERVERS = {
    "real_knitting": {
        "id": REAL_KNITTING_SERVER_ID,
        "craft": "knitting",
    },
    "test_knitting": {
        "id": TEST_KNITTING_SERVER_ID,
        "craft": "knitting",
    },
    "real_sewing": {
        "id": REAL_SEWING_SERVER_ID,
        "craft": "sewing",
    },
    "test_sewing": {
        "id": TEST_SEWING_SERVER_ID,
        "craft": "sewing",
    },
}