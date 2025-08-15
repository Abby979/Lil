import discord
from discord.ui import Button, View
from discord import app_commands
import re
import logging
import asyncio
from modules.read_csv import load_pattern_data
from modules.config import (
    BOT_TOKEN, OWNER_ID,
    knitting_server_id, knitting_index_file_path, knitting_test_server_id,
    sewing_server_id, sewing_index_file_path, sewing_test_server_id)

# Helper function to normalize names for matching
def normalize_name(name: str) -> str:
    # Lowercase, remove punctuation, collapse multiple spaces
    return re.sub(r"[^\w\s]", "", name).strip().lower()

#Commands
def register_commands(tree, owner_id, get_tags_for_category, load_pattern_data):

# Create Server command
    @tree.command(name="create", description="Create a new server with categories and forums.")
    async def create_server(interaction: discord.Interaction):
        print("Guild ID:", interaction.guild.id)
        if interaction.user.id != owner_id:
            await interaction.response.send_message(
                "You are not authorized to use this command.", ephemeral=True
            )
            return
        #Are you sure
        class ConfirmView(View):
            def __init__(self):
                super().__init__(timeout=60)  # 1 minute to respond
                self.value = None  # store user's choice

            @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                await interaction.response.edit_message(content="Confirmed! Creating now...", view=None)
                self.stop()  # stop listening to buttons

            @discord.ui.button(label="No", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                await interaction.response.edit_message(content="Cancelled.", view=None)
                self.stop()

        view = ConfirmView()
        await interaction.response.send_message(
            "Are you sure you want to create all categories, forums, and posts?", 
            view=view, ephemeral=True
        )

        # Wait for user to click
        await view.wait()

        # If user cancelled or timeout
        if not view.value:
            return  # Exit command

        # Read the pattern data from the CSV file
        if interaction.guild.id == knitting_server_id or interaction.guild.id == knitting_test_server_id:
            index_file = knitting_index_file_path
        elif interaction.guild.id == sewing_server_id or interaction.guild.id == sewing_test_server_id:
            index_file = sewing_index_file_path
        else:
            await interaction.response.send_message("Unsupported server", ephemeral=True)
            return
        categories = load_pattern_data(index_file)

        # Pre-fetch existing categories and forums for duplicate checks
        existing_categories = {
            normalize_name(category.name): category 
            for category in interaction.guild.categories}
        existing_forums = {
            normalize_name(forum.name): forum 
            for forum in interaction.guild.channels if isinstance(forum, discord.ForumChannel)}
        existing_posts = {}

        # Failed categories, forums, and posts for logging
        failed_categories = []
        failed_forums = []
        failed_posts = []

        for forum_name, forum in {
            ch.name: ch for ch in interaction.guild.channels if isinstance(ch, discord.ForumChannel)
        }.items():
            try:
                active_threads = forum.threads  # Fetch active threads
                archived_threads = [thread async for thread in forum.archived_threads(limit=None)]  # Fetch public archived threads
                all_threads = active_threads + archived_threads
                logging.debug(f"Forum '{forum_name}' total threads: {len(all_threads)}, active threads: {len(active_threads)}, archived threads: {len(archived_threads)}")
                existing_posts[normalize_name(forum_name)] = [thread.name for thread in all_threads]  # Store existing post title
            except Exception as e:
                logging.error(f"Failed to fetch threads for forum '{forum_name}': {str(e)}")
                existing_posts[normalize_name(forum_name)] = []  # Default to an empty list if there's an error

        logging.debug(f"Existing categories: {existing_categories}")
        logging.debug(f"Existing forums: {existing_forums}")
        logging.debug(f"Existing posts: {existing_posts}")

        # Begin creating categories, forums, and posts
        forums = {}  # Initialize forums to avoid scope issues
        # CATEGORIES
        for category_name, forums in categories.items():
            try:
                # Retrieve or create the category
                normalized_cat= normalize_name(category_name)
                category = existing_categories.get(normalized_cat)
                if not category:
                    print(f"Creating category: {category_name}")
                    category = await interaction.guild.create_category(category_name)
                    existing_categories[category_name] = category  # Update the pre-fetched dictionary
                    await asyncio.sleep(1)  # Pause to avoid rate limits
                else:
                    logging.info(f"Did not create {category_name} because it already exists.")
            except Exception as e:
                logging.error(f"Failed to create category '{category_name}': {str(e)}")
                failed_categories.append({"category_name": category_name, "error": str(e)})
                continue  # Move to next category

            # FORUM CHANNELS
            for forum_name, posts in forums.items():
                try:
                # Determine which tags to use based on the category
                    forum_tags = get_tags_for_category(category_name)
                    normalized_forum= normalize_name(forum_name)
                    forum_channel = existing_forums.get(normalized_forum)

                    if not forum_channel:
                        print(f"Creating forum channel: {forum_name} in category {category_name}")
                        forum_channel = await interaction.guild.create_forum(
                            name=forum_name, 
                            category=category,
                            available_tags=forum_tags)
                        existing_forums[forum_name] = forum_channel  # Update the pre-fetched dictionary
                        existing_posts[forum_name] = []  # Initialize posts for this forum
                        await asyncio.sleep(1)  # Pause to avoid rate limits
                    else:
                        await forum_channel.edit(
                            available_tags=forum_tags)  # Update tags
                        logging.info(f"Did not create {forum_name} because it already exists.")
                except Exception as e:
                    error_message = str(e)
                    failed_forums.append({"forum_name": forum_name, "category_name": category_name, "error": error_message})
                    continue  # Skip further processing for this forum


                # POSTS
                for post in posts:
                    try:
                        # Check if a post with the same name already exists
                        if post['post_title'] in existing_posts.get(normalized_forum, []):
                            logging.debug(f"Post '{post['post_title']}' already exists in forum '{forum_name}'. Skipping creation.")
                            continue  # Skip to the next post if already exists

                        # Create the post if it doesn't exist
                        thread = await forum_channel.create_thread(
                            name=post['post_title'],  # Post title
                            content=post['message'],
                            applied_tags=[tag for tag in forum_channel.available_tags if tag.name in post['tags']] if post['tags'] else [],
                            auto_archive_duration=60
                        )
                        print(f"Created post: {post['post_title']} in forum: {forum_name}")
                        logging.info(f"Created post: {post['post_title']} in forum: {forum_name}")
                        existing_posts[forum_name].append(post['post_title']) # Add the post to the existing posts dictionary
                        await asyncio.sleep(3)  # Pause to avoid rate limits AND active posts limits
                        
                    except Exception as e:
                        logging.exception(f"Exception occurred while creating post '{post['post_title']}' in forum '{forum_name}': {str(e)}")
                        error_message = str(e)
                        failed_posts.append({"post_title": post['post_title'], "forum_name": forum_name, "error": error_message})

        # Log summaries for all failures
        if failed_categories:
            logging.error("\n--- Failed Categories Summary ---")
            for failure in failed_categories:
                logging.error(f"Category: {failure['category_name']}, Error: {failure['error']}")

        if failed_forums:
            logging.error("\n--- Failed Forums Summary ---")
            for failure in failed_forums:
                logging.error(f"Forum: {failure['forum_name']}, Category: {failure['category_name']}, Error: {failure['error']}")

        if failed_posts:
            logging.error("\n--- Failed Posts Summary ---")
            for failure in failed_posts:
                logging.error(f"Post: {failure['post_title']}, Forum: {failure['forum_name']}, Error: {failure['error']}")

        if not (failed_categories or failed_forums or failed_posts):
            print("\nAll categories, forums, and posts created successfully!")
        else:
            print("\nSome operations failed. Check 'bot_debug.log' for details.")

            print("All done creating categories, channels, and posts!")
        print("Create command finished. Check the console for any errors or messages.")

# Fetch Catbox link command
    @tree.command(name="love", description="Tell us you love this pattern.")
    async def love(interaction: discord.Interaction):
        # Check if we're in a thread
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message(
                "Please use this command inside a pattern's thread.", 
                ephemeral=True
            )
            return

        thread_title = interaction.channel.name
        normalized_thread = normalize_name(thread_title)

        # Decide which CSV to use based on server ID
        if interaction.guild.id in [knitting_server_id, knitting_test_server_id]:
            index_file = knitting_index_file_path
        elif interaction.guild.id in [sewing_server_id, sewing_test_server_id]:
            index_file = sewing_index_file_path
        else:
            await interaction.response.send_message("Unsupported server.", ephemeral=True)
            return

        # Load your CSV — but we want direct row access, not the nested category/forum structure
        import csv
        found_link = None
        with open(index_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if normalize_name(row["Title"]) == normalized_thread:
                    found_link = row["Catbox link"].strip()
                    break

        if found_link:
            await interaction.response.send_message(
                f"❤️ Here's your Catbox link:\n{found_link}", 
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Sorry, I couldn't find a Catbox link for this pattern.",
                ephemeral=True
            )
