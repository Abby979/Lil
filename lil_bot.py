import discord
import logging #Debug logging
import os
from datetime import datetime, timezone as dt_timezone
from modules.role_utils import assign_role, has_role_at_least, Role

# Import from modules
from modules.read_csv import load_pattern_data
from modules.tags_dictionaries import get_tags_for_category
from modules.config import (
    BOT_TOKEN, OWNER_ID, LOCAL_TZ,
    SERVERS, CRAFTERS
)
from modules.commands import register_commands
from modules.utils import convert_to_local_time, save_last_backup_time

# Craft and test Mode toggle
CRAFT = "knitting"  # Set to "knitting" or "sewing" based on your craft
test_mode = True  # Set to True for test server, False for main server

server_key = f"{'test' if test_mode else 'real'}_{CRAFT}"
server_config = SERVERS[server_key]
server_id = server_config["id"]
crafter_config = CRAFTERS[CRAFT]
last_backup_file="last_backup.txt"

print(f"server_id loaded: {server_id}")

# Debug logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=os.path.join("logs", "bot_debug.log"),  # File name for the log file
    filemode='w'  # Overwrite the file on each run. Use 'a' to append to the file.
)

# Create a client instance
intents = discord.Intents.default()  # For basic functionality
intents.message_content = True  # Enable message content intent to read messages
intents.guilds = True  # Required for accessing guild-level resources
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)  # Command tree for slash commands

if server_id is None:
    logging.critical("server_id is not set or invalid in the environment variables. Exiting.")
    raise ValueError("server_id is not set or invalid in the environment variables.")

# Register commands with the command tree
register_commands(
    tree, 
    int(server_id), 
    OWNER_ID,
    dt_timezone=dt_timezone,
    save_last_backup_time = save_last_backup_time,
    get_tags_for_category = get_tags_for_category,
    load_pattern_data = load_pattern_data,
    index_file_path = crafter_config["index_file"],
    convert_to_local_time = convert_to_local_time,
    local_tz = LOCAL_TZ,
    last_backup_file=last_backup_file)

@client.event
async def on_ready():
    
    guild = client.get_guild(int(server_id))
    if guild is None:
        try:
            guild = await client.fetch_guild(int(server_id))
        except Exception as e:
            logging.error(f"Failed to fetch guild: {e}")
            print(f"Failed to fetch guild: {e}")
            return
    
    if guild:
        logging.info(f'Connected to server: {guild.name} (ID: {guild.id})')
        print(f'Connected to server: {guild.name} (ID: {guild.id})')    

        # Sync the slash commands with the server
        await tree.sync(guild=guild)
        logging.info(f'Slash commands synced with server: {guild.name}')
    else:
        logging.error(f'Failed to connect to server with ID: {server_id}')

# Run the bot
if BOT_TOKEN is None:
    logging.critical("BOT_TOKEN is not set in the environment variables. Exiting.")
    raise ValueError("BOT_TOKEN is not set in the environment variables.")
client.run(BOT_TOKEN)
