import discord
from discord import app_commands
import logging
import asyncio
from modules.read_csv import load_pattern_data
from modules.config import BOT_TOKEN, OWNER_ID, index_file_path

def register_commands(tree: app_commands.CommandTree, 
    owner_id: int,
    get_tags_for_category,
    load_pattern_data,
    index_file_path,):

# Create Server command
    @tree.command(name="create", description="Create a new server with categories and forums.")
    async def create_server(interaction: discord.Interaction):
        if interaction.user.id != owner_id:
            await interaction.response.send_message(
                "You are not authorized to use this command.", ephemeral=True
            )
            return
        await interaction.response.defer(thinking=False)

        # Read the pattern data from the CSV file
        categories = load_pattern_data(index_file_path)

        # Pre-fetch existing categories and forums for duplicate checks
        existing_categories = {category.name: category for category in interaction.guild.categories}
        existing_forums = {forum.name: forum for forum in interaction.guild.channels if isinstance(forum, discord.ForumChannel)}
        existing_posts = {}
        # Failed categories, forums, and posts for logging
        failed_categories = []
        failed_forums = []
        failed_posts = []
        for forum_name, forum in existing_forums.items():
            try:
                active_threads = forum.threads  # Fetch active threads
                archived_threads = [thread async for thread in forum.archived_threads(limit=None)]  # Fetch public archived threads
                all_threads = active_threads + archived_threads
                logging.debug(f"Forum '{forum_name}' total threads: {len(all_threads)}, active threads: {len(active_threads)}, archived threads: {len(archived_threads)}")
                existing_posts[forum_name] = [thread.name for thread in all_threads]  # Store existing post title
                logging.debug(f"Existing posts in forum '{forum_name}': {existing_posts[forum_name]}")
            except Exception as e:
                logging.error(f"Failed to fetch threads for forum '{forum_name}': {str(e)}")
                existing_posts[forum_name] = []  # Default to an empty list if there's an error

        logging.debug(f"Existing categories: {existing_categories}")
        logging.debug(f"Existing forums: {existing_forums}")
        logging.debug(f"Existing posts: {existing_posts}")

        # Begin creating categories, forums, and posts
        forums = {}  # Initialize forums to avoid scope issues
        # CATEGORIES
        for category_name, forums in categories.items():
            try:
                # Retrieve or create the category
                category = existing_categories.get(category_name)
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

                    # Get or create the forum channel
                    forum_channel = existing_forums.get(forum_name)
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
                        if post['post_title'] in existing_posts.get(forum_name, []):
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
