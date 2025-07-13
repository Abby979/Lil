import discord
from discord import app_commands, Interaction, Object
from discord.utils import get
import logging
import csv
import os
from datetime import datetime
import asyncio
from modules.role_utils import has_role_at_least, Role, get_user_role, assign_role_to_user
from modules.decorators import require_role_at_least

def register_commands(tree: app_commands.CommandTree, 
    server_id: int, 
    owner_id: int,
    last_backup_file:str,
    dt_timezone,
    save_last_backup_time,
    get_tags_for_category,
    load_pattern_data,
    index_file_path,
    convert_to_local_time,
    local_tz):

    BACKUP_FOLDER = os.path.join("data", "backups")

# Assign role command
    @tree.command(name="assign", description="Assign a role to a user.", guild=Object(id=int(server_id)))
    @require_role_at_least(Role.ADMIN)  # Only admins and above can assign roles
    @app_commands.choices(
        role=[app_commands.Choice(name=r.name.capitalize(), value=r.value) for r in Role if r != Role.UNVERIFIED])
    @app_commands.describe(
        user="The user to assign a role to.",
        role="The role to assign."
    )
    async def assign_role(interaction: Interaction, user: discord.Member, role: Role):
        assigner_id = interaction.user.id
        assigner_role = get_user_role(assigner_id)
        target_id = user.id
        target_role = get_user_role(target_id)

        # Prevent assigning a role higher or equal to your own
        if role.value >= assigner_role.value:
            await interaction.response.send_message(
                f"You can only assign roles lower than your own (your role: **{assigner_role.name}**).", ephemeral=True
            )
            return

        # Prevent modifying someone with equal or higher role
        if target_role.value >= assigner_role.value:
            await interaction.response.send_message(
                f"You cannot change the role of someone with an equal or higher role (target: **{target_role.name}**).", ephemeral=True
            )
            return

        # Assign the role using the unified helper function
        success, msg = await assign_role_to_user(user, role, interaction.guild)
        await interaction.response.send_message(msg, ephemeral=True)


# Backup server command
    @tree.command(name="backup", description="Back up the server data.", guild=discord.Object(id=int(server_id)))
    @require_role_at_least(Role.OWNER)
    async def backup_server(interaction: discord.Interaction):

        await interaction.response.defer(thinking=True)  # Acknowledge the command as it might take time.
        # Step 1: Fetch Data
        data = []
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        for category in interaction.guild.categories:
            logging.info(f"Processing category: {category.name}")
            for forum in category.channels:
                logging.info(f"Processing forum: {forum.name} in category: {category.name}")
                
                if isinstance(forum, discord.ForumChannel):
                    # Fetch active threads in the forum
                    try:
                        active_threads = forum.threads  # Fetch active threads
                        archived_threads = [thread async for thread in forum.archived_threads(limit=None)] # Fetch public archived threads
                        logging.debug(f"Forum '{forum.name}' active threads: {len(active_threads)}, archived threads: {len(archived_threads)}")                   
                    except discord.Forbidden as e:
                        logging.warning(f"Missing access to fetch threads in forum '{forum.name}': {e}")
                        continue  # Skip this forum and move to the next
                    except Exception as e:
                        logging.error(f"Unexpected error while fetching threads in forum '{forum.name}': {e}")
                        continue
                        
                    all_threads = active_threads + archived_threads

                    for thread in all_threads:
                        starter_message_content = ""
                        try:
                            if thread.starter_message:
                                starter_message_content = thread.starter_message.content
                            else:
                                starter_message = await thread.fetch_message(thread.id)  # Explicitly fetch starter message
                                starter_message_content = starter_message.content if starter_message else ""
                        except discord.NotFound:
                            logging.warning(f"Starter message for thread '{thread.name}' not found.")
                        except discord.Forbidden:
                            logging.warning(f"Missing permissions to fetch starter message for thread '{thread.name}'.")
                        except Exception as e:
                            logging.error(f"Error fetching starter message for thread '{thread.name}': {e}")
                        
                        thread_data = {
                            "Category": category.name,
                            "Forum Name": forum.name,
                            "Title": thread.name,
                            "Tags": ", ".join(tag.name for tag in thread.applied_tags),
                            "Ravelry Link/Message": starter_message_content,
                            "Catbox Link": [msg async for msg in thread.history(limit=None)],
                            "Date Created": thread.created_at.strftime("%Y-%m-%d %H:%M:%S") if thread.created_at else ""
                    }
                        data.append(thread_data)
                        logging.debug(f"Added thread: {thread.name} to backup.")
        
        # Step 2: Write to CSV
        guild_name = interaction.guild.name if interaction.guild else "Unknown Guild"
        # Ensure the backups folder exists
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        # Save the backup file in the backups folder
        backup_file_path = os.path.join(BACKUP_FOLDER, f"{guild_name}_backup.csv".replace("/", "_").replace("\\", "_"))

        try:
            with open(backup_file_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["Category", "Forum Name", "Title", "Tags", "Ravelry Link/Message", "Catbox Link", "Date Created"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
                    logging.debug(f"Writing row for thread: {row['Title']} in forum: {row['Forum Name']}")
            
            # Step 3: Respond with the CSV file
            file_sent = False
            logging.info(f"Backup complete. Sending file: {backup_file_path}")
            await interaction.followup.send(file=discord.File(backup_file_path), content="Backup complete! Here is the CSV file.")
            file_sent = True
        except discord.HTTPException as e:
            logging.error(f"Failed to send backup file file: {e}")
            print(f"The backup file {backup_file_path} is saved locally. Retrieve it manually.")
        finally:
            if file_sent:
                if os.path.exists(backup_file_path):
                    os.remove(backup_file_path)  # Clean up the file after sending.
            else:
                logging.warning(f"The backup file {backup_file_path} was not sent and is retained for manual retrieval.")
        save_last_backup_time()  # Save the last backup time


    # Create Server command
    @tree.command(name="create", description="Create a new server with categories and forums.", guild=discord.Object(id=int(server_id)))
    @require_role_at_least(Role.OWNER)
    async def create_server(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)

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
                existing_posts[forum_name] = [thread.name for thread in all_threads]  # Store existing post titlee
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
                            # Get existing thread by name
                            existing_thread = discord.utils.get(forum_channel.threads, name=post['post_title'])
                            '''
                            if existing_thread and post['attachments']:
                                # Fetch messages in the thread
                                messages = [message async for message in existing_thread.history(limit=50)]
                                # Check if the attachment message already exists
                                if not any(post['attachments'] in message.content for message in messages):
                                    await existing_thread.send(content=post['attachments'])
                                    logging.info(f"Attachment '{post['attachments']}' added to existing post '{post['post_title']}'.")
                            '''
                            continue  # Skip to the next post if already exists
                            


                        # Create the post if it doesn't exist
                        thread = await forum_channel.create_thread(
                            name=post['post_title'],  # Post title
                            content=post['message'],
                            applied_tags=[tag for tag in forum_channel.available_tags if tag.name in post['tags']] if post['tags'] else [],
                            auto_archive_duration=60 # Posts archive after 1 hour to avoid Discord active post limits
                        )
                        print(f"Created post: {post['post_title']} in forum: {forum_name}")
                        logging.info(f"Created post: {post['post_title']} in forum: {forum_name}")
                        existing_posts[forum_name].append(post['post_title']) # Add the post to the existing posts dictionary

                        '''
                        # If there are attachments, send them in the thread
                        # Check for and send attachments
                        if post['attachments']:
                            await thread.send(content=post['attachments'])
                            logging.info(f"Attachment '{post['attachments']}' added to post '{post['post_title']}'.")
                            '''
                    
                        await asyncio.sleep(3)  # Pause to ensure 1000 posts take over an hour, avoids Discord active posts limits
                        
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
        await interaction.followup.send("Server creation complete! Check the logs for any errors.")


    #Update command
    @tree.command(name="update", description="Update the server backup with new or updated threads.", guild=discord.Object(id=int(server_id)))
    @require_role_at_least(Role.OWNER)
    async def update_backup(interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)  # Acknowledge the command
        logging.info("Starting update process.")

        # Load the last backup time
        try:
            with open(last_backup_file, "r") as file:
                last_backup_time = datetime.fromisoformat(file.read().strip())
        except FileNotFoundError:
            await interaction.followup.send("No previous backup found. Please run the full backup command first.")
            return
            
        # Fetch the current time for new backup
        current_backup_time = datetime.now(dt_timezone.utc)
        
        # Step 1: Fetch Data
        data = []
        ravelry_links = []  # To store Ravelry links from starter messages
        if interaction.guild is None:
            await interaction.followup.send("This command can only be used in a server.", ephemeral=True)
            return
        
        for category in interaction.guild.categories:
            for forum in category.channels:
                if isinstance(forum, discord.ForumChannel):
                    # Fetch only threads updated since the last backup
                    active_threads = [
                        thread for thread in forum.threads 
                        if (thread.last_message and thread.last_message.created_at > last_backup_time) or 
                        (not thread.last_message and thread.created_at and thread.created_at > last_backup_time)
                    ]
                    archived_threads = [
                        thread async for thread in forum.archived_threads(limit=None)
                        if (thread.last_message and thread.last_message.created_at > last_backup_time) or 
                        (not thread.last_message and thread.created_at and thread.created_at > last_backup_time)
                    ]
                    all_threads = active_threads + archived_threads
                    
                    for thread in all_threads:
                        starter_message_content = ""
                        if thread.starter_message:
                            starter_message_content = thread.starter_message.content
                        else:
                            try:
                                starter_message = await thread.fetch_message(thread.id)  # Explicitly fetch starter message
                                starter_message_content = starter_message.content if starter_message else ""
                            except discord.NotFound:
                                logging.warning(f"Starter message for thread '{thread.name}' not found.")
                            except discord.Forbidden:
                                logging.warning(f"Missing permissions to fetch starter message for thread '{thread.name}'.")
                            except Exception as e:
                                logging.error(f"Error fetching starter message for thread '{thread.name}': {e}")
                        
                        # Save Ravelry links from starter messages
                        if starter_message_content:
                            ravelry_links.append(starter_message_content)

                        thread_data = {
                            "Category": category.name,
                            "Forum Name": forum.name,
                            "Title": thread.name,
                            "Tags": ", ".join(tag.name for tag in thread.applied_tags),
                            "Ravelry Link/Message": starter_message_content,
                            "Catbox Link": [msg.content async for msg in thread.history(limit=1)],
                            "Date Created": thread.created_at.strftime("%Y-%m-%d %H:%M:%S") if thread.created_at else ""
                            }
                        logging.debug(thread_data)
                        data.append(thread_data)

        logging.info(f"{len(data)} threads updated since the last backup.")
        
        if not data:
            await interaction.followup.send("No new or updated threads found since the last backup.")
            logging.info("No new or updated threads found since the last backup.")
            print("No new or updated threads found since the last backup.")
            return

        # Step 2: Append New Data to a new CSV
        try:
            #Create a file name with the date range
            update_backup_filename = f"Update {convert_to_local_time(last_backup_time, local_tz)}_to_{convert_to_local_time(current_backup_time, local_tz)}.csv"
            updates_folder = os.path.join("data", "updates")
            os.makedirs(updates_folder, exist_ok=True)

            # Save the update backup file in the updates folder
            update_backup_filepath = os.path.join(updates_folder, update_backup_filename)


            with open(update_backup_filepath, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["Category", "Forum Name", "Title", "Tags", "Ravelry Link/Message", "Catbox Link", "Date Created"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            
            # Update the last backup time
            save_last_backup_time()

            # Ravelry links summary
            ravelry_links_summary = "\n".join(f"{i+1}. {link}" for i, link in enumerate(ravelry_links)) if ravelry_links else "No Ravelry links found."
            
            await interaction.followup.send(f"Updated successfully! Update saved as {update_backup_filename}.\n\n**Ravelry Links/Messages:**\n{ravelry_links_summary}")
            logging.info(f"Successfully created update: {update_backup_filepath}")
            print(f"Successfully created update: {update_backup_filepath}")
        except Exception as e:
            logging.error(f"Failed to create update: {e}")
            await interaction.followup.send("An error occurred creating the update file.")
            