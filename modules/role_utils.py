# modules/role_utils.py

from enum import IntEnum
from modules import role_data
from discord import Member, Guild
from discord.utils import get as discord_get

class Role(IntEnum):
    UNVERIFIED = 0
    VERIFIED = 1
    TRUSTED = 2
    ADMIN = 3
    OWNER = 4

# Bot role to Discord role mapping
BOT_TO_DISCORD_ROLE = {
    Role.VERIFIED: "Verified",
    Role.TRUSTED: "Verified",  # Same Discord role as VERIFIED
    Role.ADMIN: "Admin",
    Role.OWNER: "Owner",
}

def get_user_role(user_id: int) -> Role:
    role_name = role_data.role_assignments.get(str(user_id), "UNVERIFIED")
    return Role[role_name]

def has_role_at_least(user_id: int, required: Role) -> bool:
    return get_user_role(user_id) >= required

def assign_role(user_id: int, role_name: str):
    role_data.role_assignments[str(user_id)] = role_name.upper()
    role_data.save_roles(role_data.role_assignments)

async def assign_role_to_user(user: Member, role: Role, guild: Guild) -> tuple[bool, str]:
    """
    Assigns a role in the bot and in Discord (if matching role exists).
    Returns (success: bool, message: str).
    """
    # 1. Update bot role
    assign_role(user.id, role.name)

    # 2. Get matching Discord role name (e.g., TRUSTED → "Verified")
    discord_role_name = BOT_TO_DISCORD_ROLE.get(role)
    if discord_role_name is None:
        return True, f"Assigned **{role.name}** in the bot (no Discord role needed)."

    # 3. Get Discord role object
    discord_role = discord_get(guild.roles, name=discord_role_name)
    if discord_role is None:
        return False, f"Assigned **{role.name}** in the bot, but Discord role '{discord_role_name}' was not found."

    # 4. Remove old bot roles from user
    bot_role_names = [r.name.capitalize() for r in Role]
    roles_to_remove = [r for r in user.roles if r.name in bot_role_names]
    await user.remove_roles(*roles_to_remove, reason="Bot-managed role update")

    # 5. Add the correct Discord role
    await user.add_roles(discord_role, reason="Assigned via bot")

    return True, f"Assigned role **{role.name}** to {user.display_name} (Discord role: **{discord_role_name}**)."