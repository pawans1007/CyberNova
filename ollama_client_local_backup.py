
from ai.prompts import SYSTEM_PROMPT


class ConversationContext:
    def __init__(
        self,
        max_messages=30,
        max_chars=12000,
        summary_threshold=20,
        keep_recent=10,
    ):
        self.max_messages = max_messages
        self.max_chars = max_chars
        self.summary_threshold = summary_threshold
        self.keep_recent = keep_recent

        self.summary = ""

        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

    def add_user_message(self, message):
        self.messages.append({
            "role": "user",
            "content": str(message),
        })
        self._trim()

    def add_assistant_message(self, message):
        self.messages.append({
            "role": "assistant",
            "content": str(message),
        })
        self._trim()

    def set_summary(self, summary):
        self.summary = str(summary).strip()

    def get_messages(self):
        result = [self.messages[0].copy()]

        if self.summary:
            result.append({
                "role": "system",
                "content": (
                    "Summary of earlier conversation:\n"
                    + self.summary
                    + "\n\nUse this summary as background context. "
                    "Do not treat it as a new user instruction."
                ),
            })

        result.extend(
            message.copy()
            for message in self.messages[1:]
        )

        return result

    def get_messages_for_summary(self):
        """
        Return older messages that should be summarized.
        Returns an empty list if summarization is not needed.
        """
        recent = self.messages[1:]

        if len(recent) < self.summary_threshold:
            return []

        split_index = len(recent) - self.keep_recent

        if split_index <= 0:
            return []

        older = recent[:split_index]

        # Avoid ending the older section with a user message
        # when its assistant response is still in recent history.
        if older and older[-1]["role"] == "user":
            older = older[:-1]

        return [message.copy() for message in older]

    def apply_summary(self, summarized_messages, new_summary):
        """
        Replace the selected older messages with a summary.
        Only applies if the selected messages still match
        the beginning of the current conversation.
        """
        if not summarized_messages or not new_summary:
            return False

        current = self.messages[1:]
        count = len(summarized_messages)

        if current[:count] != summarized_messages:
            return False

        self.summary = str(new_summary).strip()

        self.messages = [
            self.messages[0],
            *current[count:],
        ]

        self._trim()
        return True

    def clear(self):
        self.summary = ""

        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

    def _trim(self):
        """
        Apply message and character limits.
        This is a fallback limit; normal summarization
        should happen before the conversation reaches it.
        """
        recent = self.messages[1:]

        if len(recent) > self.max_messages:
            recent = recent[-self.max_messages:]

        if recent and recent[0]["role"] == "assistant":
            recent = recent[1:]

        total_chars = sum(
            len(message["content"])
            for message in recent
        )

        while recent and total_chars > self.max_chars:
            removed = recent.pop(0)
            total_chars -= len(removed["content"])

            if recent and recent[0]["role"] == "assistant":
                removed = recent.pop(0)
                total_chars -= len(removed["content"])

        self.messages = [
            self.messages[0],
            *recent,
        ]