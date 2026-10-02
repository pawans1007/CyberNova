from dataclasses import dataclass
from enum import Enum


class IntentType(str, Enum):
    CHAT = "chat"
    OPEN = "open"
    WEB_SEARCH = "web_search"
    READ_PAGE = "read_page"
    SAVE_MEMORY = "save_memory"
    SEARCH_MEMORY = "search_memory"
    LIST_MEMORY = "list_memory"
    DELETE_MEMORY = "delete_memory"
    SYSTEM_INFO = "system_info"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    type: IntentType
    value: str = ""


class IntentRouter:
    def classify(self, message):
        text = str(message).strip()
        lowered = text.lower()

        if not text:
            return Intent(IntentType.UNKNOWN)

        commands = [
            ("open ", IntentType.OPEN),
            ("launch ", IntentType.OPEN),
            ("start ", IntentType.OPEN),
            ("search web for ", IntentType.WEB_SEARCH),
            ("search the web for ", IntentType.WEB_SEARCH),
            ("look up ", IntentType.WEB_SEARCH),
            ("read page ", IntentType.READ_PAGE),
            ("summarize page ", IntentType.READ_PAGE),
            ("remember ", IntentType.SAVE_MEMORY),
            ("save memory ", IntentType.SAVE_MEMORY),
            ("search memory ", IntentType.SEARCH_MEMORY),
            ("find memory ", IntentType.SEARCH_MEMORY),
            ("list memories", IntentType.LIST_MEMORY),
            ("show memories", IntentType.LIST_MEMORY),
            ("delete memory ", IntentType.DELETE_MEMORY),
            ("system info", IntentType.SYSTEM_INFO),
            ("show system info", IntentType.SYSTEM_INFO),
        ]

        for prefix, intent_type in commands:
            if lowered.startswith(prefix):
                value = text[len(prefix):].strip()
                return Intent(intent_type, value)

        return Intent(IntentType.CHAT)