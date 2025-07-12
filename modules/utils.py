import os
from datetime import datetime, timezone as dt_timezone
from modules.config import LOCAL_TZ  # Import default timezone from config
from modules.config import SERVERS, CRAFTERS  # Import server and crafter configurations

# Timezone configuration
def convert_to_local_time(utc_datetime, timezone_obj=None, fmt="%d.%m.%y_%H%M"):
    tz = timezone_obj if timezone_obj else LOCAL_TZ  # Use the imported constant
    local_time = utc_datetime.astimezone(tz)
    return local_time.strftime(fmt)

#  Function to save time of last backup
backup_folder = os.path.join ("data", "backups")  # Folder to store backup files
os.makedirs(backup_folder, exist_ok=True)  # Create the backup folder if it doesn't exist
last_backup_file = os.path.join(backup_folder, "last_backup.txt")
def save_last_backup_time():
    with open(last_backup_file, "w") as file:
        file.write(datetime.now(dt_timezone.utc).isoformat())

# Function to get server configuration by guild ID
def get_server_config(guild_id: int):
    for server_key, server_info in SERVERS.items():
        if server_info["id"] == guild_id:
            craft = server_info["craft"]
            return {
                "server_key": server_key,
                "craft": craft,
                "index_file": CRAFTERS[craft]["index_file"],
                "last_backup_file": CRAFTERS[craft]["last_backup_file"],
            }
    return None