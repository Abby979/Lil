from functools import wraps
from discord import Interaction
from modules.role_utils import has_role_at_least, Role

def require_role_at_least(required_role: Role):
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: Interaction, *args, **kwargs):
            user_id = interaction.user.id
            if not has_role_at_least(user_id, required_role):
                await interaction.response.send_message(
                    "Sorry, you are not authorized to use this command.", ephemeral=True
                )
                return
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator
