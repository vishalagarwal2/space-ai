import re
from typing import Optional

def extract_agent_tag(message: str) -> Optional[str]:
    """
    Extract agent name from message using @agent_name pattern.
    """
    match = re.search(r'@(\w+)', message)
    return match.group(1) if match else None

def clean_message(message: str) -> str:
    """
    Remove @agent_name tags from the message.
    """
    return re.sub(r'@\w+', '', message).strip()