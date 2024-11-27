import os
from datetime import datetime
from pathlib import Path
from config import config

def add_to_history(query: str, command: str) -> None:
    """
    Add the command and its natural language query to bash history
    """
    if not config.get('history.enabled', True):
        return

    history_file = os.path.expanduser(config.get('history.file', '~/.bash_history'))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(history_file, "a") as f:
            f.write(f"# {timestamp} - NL: {query}\n")
            f.write(f"{command}\n")
    except Exception as e:
        # Fail silently - history is not critical
        pass

def get_history(limit: int = 10) -> list:
    """
    Get recent commands from history
    """
    if not config.get('history.enabled', True):
        return []

    history_file = os.path.expanduser(config.get('history.file', '~/.bash_history'))
    history = []
    max_entries = config.get('history.max_entries', 1000)
    
    try:
        with open(history_file, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if line.startswith("#") and "NL:" in line:
                    history.append(line.strip())
                if len(history) >= min(limit, max_entries):
                    break
    except Exception:
        return []
    
    return history
