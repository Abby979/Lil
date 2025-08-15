import discord
import logging #Debug logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
import threading

# Import from modules
from modules.read_csv import load_pattern_data
from modules.tags_dictionaries import get_tags_for_category
from modules.config import (
    BOT_TOKEN, 
    OWNER_ID, 
    LOCAL_TZ,
    knitting_server_id,
    knitting_index_file_path,
    knitting_test_server_id,
    sewing_server_id,
    sewing_index_file_path,
    sewing_test_server_id,
)
from modules.commands import register_commands

# -----------------------------
# Flask app to keep bot alive
# -----------------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!", 200

def run_webserver():
    port = int(os.environ.get("PORT", 8080))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)

# -----------------------------
# Logging configuration
# -----------------------------
os.makedirs("logs", exist_ok=True)  # Ensure the logs directory exists

# Ensure the log file exists (optional, logging will create it anyway)
log_file_path = os.path.join("logs", "bot_debug.log")
if not os.path.exists(log_file_path):
    open(log_file_path, 'w').close()

logger = logging.getLogger()
if logger.hasHandlers():
    logger.handlers.clear()
logger.setLevel(logging.DEBUG)  # Set gloval level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
file_handler = RotatingFileHandler(
    log_file_path, 
    maxBytes=5*1024*1024, 
    backupCount=3,
    encoding='utf-8'
)

file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Console handler (logs to stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG) #Render logs to console
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# -----------------------------
# Discord client setup
# -----------------------------

# Create a client instance
intents = discord.Intents.default()  # For basic functionality
intents.message_content = True  # Enable message content intent to read messages
intents.guilds = True  # Required for accessing guild-level resources
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)  # Command tree for slash commands

# -----------------------------
# Servers configuration
# -----------------------------
servers = [
    {
        "name": "knitting",
        "guild_id": knitting_test_server_id or knitting_server_id,
        "index_file_path": knitting_index_file_path
    },
    {
        "name": "sewing",
        "guild_id": sewing_test_server_id or sewing_server_id,
        "index_file_path": sewing_index_file_path
    }
]

# Register commands for each server
register_commands(
    tree,
    OWNER_ID,
    get_tags_for_category=get_tags_for_category,
    load_pattern_data=load_pattern_data,
)

# -----------------------------
# Discord events
# -----------------------------

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    
    for server in [knitting_test_server_id, sewing_test_server_id]:
        if server:
            try:
                guild = discord.Object(id=server)
                await tree.sync(guild=guild)
                print(f"Commands synced for guild {server}")
            except Exception as e:
                print(f"Failed to sync commands for guild {server}: {e}")

    # Optional global sync (may fail on dev servers if permissions are restricted)
    try:
        await tree.sync()
        print("Commands synced globally")
    except Exception as e:
        print(f"Global sync failed: {e}")

# -----------------------------
# Run bot and Flask server
# -----------------------------

if __name__ == "__main__":
    # Start Flask server in background thread
    threading.Thread(target=run_webserver, daemon=True).start()

    # Run the bot
    if BOT_TOKEN is None:
        logging.critical("BOT_TOKEN is not set in the environment variables. Exiting.")
        raise ValueError("BOT_TOKEN is not set in the environment variables.")
    client.run(BOT_TOKEN)
