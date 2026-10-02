from ai.prompts import SYSTEM_PROMPT


class ConversationContext:
    def __init__(self, max_messages=30):
        self.max_messages = max_messages
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    def add_user_message(self, message):
        self.messages.append({
            "role": "user",
            "content": message
        })
        self._trim()

    def add_assistant_message(self, message):
        self.messages.append({
            "role": "assistant",
            "content": message
        })
        self._trim()

    def get_messages(self):
        return [message.copy() for message in self.messages]

    def clear(self):
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

    def _trim(self):
        # Keep the system prompt and the most recent messages.
        recent = self.messages[1:]
        recent = recent[-self.max_messages:]
        self.messages = [self.messages[0], *recent]