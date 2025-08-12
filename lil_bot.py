import discord
import logging #Debug logging
import os
from datetime import timezone as dt_timezone

# Import from modules
from modules.read_csv import load_pattern_data
from modules.tags_dictionaries import get_tags_for_category
from modules.config import BOT_TOKEN, OWNER_ID, index_file_path
from modules.commands import register_commands


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
    test_guild = discord.Object(id=1384052827642658869)
    await tree.sync(guild=test_guild)
    print("Commands synced to test guild!")

# Run the bot
if BOT_TOKEN is None:
    logging.critical("BOT_TOKEN is not set in the environment variables. Exiting.")
    raise ValueError("BOT_TOKEN is not set in the environment variables.")
client.run(BOT_TOKEN)
