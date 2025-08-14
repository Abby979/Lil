import discord
import logging #Debug logging
import os
from logging.handlers import RotatingFileHandler
from flask import Flask
import threading

# Import from modules
from modules.read_csv import load_pattern_data
from modules.tags_dictionaries import get_tags_for_category
from modules.config import BOT_TOKEN, OWNER_ID, index_file_path, test_guild_id
from modules.commands import register_commands

# Flask app for keeping the bot alive
# This is a simple web server to keep the bot running on Render
app = Flask("")

@app.route("/")
def home():
    return "Bot is alive!", 200

def run_webserver():
    port = int(os.environ.get("PORT", 8080))  # Use Render's assigned port
    app.run(host="0.0.0.0", port=port)

# Debug logging configuration
os.makedirs("logs", exist_ok=True)  # Ensure the logs directory exists

# Ensure the log file exists (optional, logging will create it anyway)
log_file_path = os.path.join("logs", "bot_debug.log")
if not os.path.exists(log_file_path):
    open(log_file_path, 'w').close()

logger = logging.getLogger()
if logger.hasHandlers():
    logger.handlers.clear()
logger.setLevel(logging.DEBUG)  # Set to level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
file_handler = RotatingFileHandler(
    log_file_path, 
    maxBytes=5*1024*1024, 
    backupCount=3,
    encoding='utf-8'
)

file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Console handler (logs to stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Example log message
logger.info("Bot starting up...")

# Create a client instance
intents = discord.Intents.default()  # For basic functionality
intents.message_content = True  # Enable message content intent to read messages
intents.guilds = True  # Required for accessing guild-level resources
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)  # Command tree for slash commands

# Register commands with the command tree
register_commands(
    tree, 
    OWNER_ID,
    get_tags_for_category = get_tags_for_category,
    load_pattern_data = load_pattern_data,
    index_file_path = index_file_path,)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    
    # Sync commands to a test guild for instant update
    if test_guild_id:
            test_guild = discord.Object(id=test_guild_id)
            await tree.sync(guild=test_guild)
            print("Commands synced to test guild")
            
    await tree.sync()
    print("Commands synced globally")

if __name__ == "__main__":
    # Start Flask server in background thread
    threading.Thread(target=run_webserver, daemon=True).start()

    # Run the bot
    if BOT_TOKEN is None:
        logging.critical("BOT_TOKEN is not set in the environment variables. Exiting.")
        raise ValueError("BOT_TOKEN is not set in the environment variables.")
    client.run(BOT_TOKEN)
