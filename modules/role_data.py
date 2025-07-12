# modules/role_data.py

import json
import os

ROLES_FILE = os.path.join("data", "roles.json")

# Load role data from the JSON file
def load_roles():
    if not os.path.exists(ROLES_FILE):
        return {}
    with open(ROLES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Save role data to the JSON file
def save_roles(role_dict):
    with open(ROLES_FILE, "w", encoding="utf-8") as f:
        json.dump(role_dict, f, indent=4)

# At startup
role_assignments = load_roles()
