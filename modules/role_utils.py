# modules/role_utils.py

from enum import IntEnum
from modules import role_data

class Role(IntEnum):
    UNVERIFIED = 0
    VERIFIED = 1
    TRUSTED = 2
    ADMIN = 3
    OWNER = 4

def get_user_role(user_id: int) -> Role:
    role_name = role_data.role_assignments.get(str(user_id), "UNVERIFIED")
    return Role[role_name]

def has_role_at_least(user_id: int, required: Role) -> bool:
    return get_user_role(user_id) >= required

def assign_role(user_id: int, role_name: str):
    """Set a role and save to disk."""
    if role_name.upper() not in Role.__members__:
        raise ValueError(f"{role_name} is not a valid role name.")
    role_data.role_assignments[str(user_id)] = role_name.upper()
    role_data.save_roles(role_data.role_assignments)
