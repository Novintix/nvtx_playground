import os
import json
from pathlib import Path

# Corporate Pathing
SRC_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = SRC_DIR.parent

def get_session_file(role):
    return ROOT_DIR / "data" / f"chat_sessions_{role}.json"

def save_chat_history(messages, role=None):
    if not os.path.exists(ROOT_DIR / "data"):
        os.makedirs(ROOT_DIR / "data")
    
    # If role is not provided, try to get from messages or state (though state is better handled by caller)
    if role is None:
        return # Cannot save without role
        
    session_file = get_session_file(role)
    with open(session_file, "w") as f:
        json.dump(messages, f, indent=2)

def load_chat_history(role):
    session_file = get_session_file(role)
    if session_file.exists():
        try:
            with open(session_file, "r") as f:
                return json.load(f)
        except:
            return []
    return []
