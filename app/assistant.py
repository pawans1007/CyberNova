from app.intent_router import IntentRouter, IntentType
from ai.ollama_client import OllamaClient
from ai.context import ConversationContext

from memory.memory_manager import MemoryManager
from app.settings_manager import SettingsManager

from web.search import WebSearch
from web.browser import WebPageReader

from computer.computer_tools import execute_computer_command


class CyberNovaAssistant:
    def __init__(self):
        self.settings = SettingsManager()
        self.memory = MemoryManager()

        self.router = IntentRouter()
        self.context = ConversationContext()

        self.web_search = WebSearch()
        self.page_reader = WebPageReader()

        self.client = OllamaClient(
            host=self.settings.get(
                "ollama_host",
                "http://localhost:11434",
            ),
            model=self.settings.get(
                "ollama_model",
                "qwen2.5:3b-instruct",
            ),
        )

        self._restore_recent_history()

    def _restore_recent_history(self):
        history = self.memory.get_history(limit=30)

        for item in history:
            role = item["role"]
            content = item["content"]

            if role == "user":
                self.context.add_user_message(content)

            elif role == "assistant":
                self.context.add_assistant_message(content)

    def _save_exchange(
        self,
        user_message,
        assistant_message,
    ):
        self.memory.save_message(
            "user",
            user_message,
        )

        self.memory.save_message(
            "assistant",
            assistant_message,
        )

    def _format_search_results(self, result):
        if not result.get("success"):
            return (
                "Web search failed: "
                + result.get(
                    "error",
                    "Unknown error",
                )
            )

        results = result.get("results", [])

        if not results:
            return "No search results were found."

        lines = ["Web search results:"]

        for index, item in enumerate(
            results,
            start=1,
        ):
            lines.extend([
                f"{index}. {item.get('title', 'Untitled')}",
                f"URL: {item.get('url', '')}",
                f"Summary: {item.get('snippet', '')}",
                "",
            ])

        return "\n".join(lines)

    def _format_page(self, result):
        if not result.get("success"):
            return (
                "Could not read webpage: "
                + result.get(
                    "error",
                    "Unknown error",
                )
            )

        return (
            f"Page: {result.get('title', 'Untitled')}\n"
            f"Source: {result.get('url', '')}\n\n"
            f"{result.get('text', '')}"
        )

    def _handle_intent(self, intent):
        if intent.type == IntentType.OPEN:
            if not intent.value:
                return (
                    "Specify an application, folder, "
                    "or website to open."
                )

            return str(
                execute_computer_command(
                    f"open {intent.value}"
                )
            )

        if intent.type == IntentType.WEB_SEARCH:
            if not intent.value:
                return (
                    "Provide a topic or question "
                    "to search for."
                )

            result = self.web_search.search(
                intent.value
            )

            return self._format_search_results(
                result
            )

        if intent.type == IntentType.READ_PAGE:
            if not intent.value:
                return (
                    "Provide a webpage URL to read."
                )

            result = self.page_reader.read(
                intent.value
            )

            return self._format_page(result)

        if intent.type == IntentType.SAVE_MEMORY:
            if not intent.value:
                return (
                    "Tell me what you want "
                    "me to remember."
                )

            result = self.memory.save_memory(
                intent.value
            )

            if result.get("success"):
                return (
                    "Saved that information "
                    "to local memory."
                )

            return (
                "Could not save memory: "
                + result.get(
                    "error",
                    "Unknown error",
                )
            )

        if intent.type == IntentType.SEARCH_MEMORY:
            results = self.memory.search_memories(
                intent.value
            )

            if not results:
                return (
                    "No matching saved memories "
                    "were found."
                )

            return "\n".join(
                f"- [{item['category']}] "
                f"{item['content']}"
                for item in results
            )

        if intent.type == IntentType.LIST_MEMORY:
            results = self.memory.search_memories()

            if not results:
                return (
                    "There are no saved memories yet."
                )

            return "\n".join(
                f"{item['id']}. {item['content']}"
                for item in results
            )

        if intent.type == IntentType.DELETE_MEMORY:
            try:
                memory_id = int(intent.value)

            except (ValueError, TypeError):
                return (
                    "Use a memory ID, for example: "
                    "delete memory 3."
                )

            if self.memory.delete_memory(
                memory_id
            ):
                return (
                    f"Deleted memory {memory_id}."
                )

            return (
                f"Memory {memory_id} was not found."
            )

        if intent.type == IntentType.SYSTEM_INFO:
            return str(
                execute_computer_command(
                    "system info"
                )
            )

        return None

    def update_settings(
        self,
        host=None,
        model=None,
    ):
        new_host = (
            str(host).strip()
            if host is not None
            else None
        )

        new_model = (
            str(model).strip()
            if model is not None
            else None
        )

        if new_host == "":
            raise ValueError(
                "Ollama host cannot be empty."
            )

        if new_model == "":
            raise ValueError(
                "Ollama model cannot be empty."
            )

        if new_host is not None:
            self.settings.set(
                "ollama_host",
                new_host,
            )

        if new_model is not None:
            self.settings.set(
                "ollama_model",
                new_model,
            )

        self.client.update_connection(
            host=new_host,
            model=new_model,
        )

        return self.client.get_current_settings()

    def process_message_stream(
        self,
        message,
        on_chunk,
    ):
        message = str(message).strip()

        if not message:
            result = "Please enter a message."
            on_chunk(result)
            return result

        intent = self.router.classify(message)

        # Tool or command response.
        result = self._handle_intent(intent)

        if result is not None:
            self.context.add_user_message(
                message
            )

            self.context.add_assistant_message(
                result
            )

            self._save_exchange(
                message,
                result,
            )

            on_chunk(result)
            return result

        # Normal AI conversation.
        self.context.add_user_message(
            message
        )

        full_response = []

        for chunk in self.client.stream(
            self.context.get_messages()
        ):
            full_response.append(chunk)
            on_chunk(chunk)

        response = "".join(
            full_response
        ).strip()

        self.context.add_assistant_message(
            response
        )

        self._save_exchange(
            message,
            response,
        )

        return response

    def process_message(self, message):
        try:
            return self.process_message_stream(
                message,
                lambda chunk: None,
            )

        except Exception as error:
            return (
                "CyberNova encountered an error: "
                f"{error}"
            )