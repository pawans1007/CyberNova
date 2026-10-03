
import sys
import threading

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
    QMessageBox,
)

from app.assistant import CyberNovaAssistant
from app.task_manager import TaskManager

from ui.sidebar import Sidebar
from ui.chat_widget import ChatWidget
from ui.settings import SettingsPage
from ui.cybersecurity_page import CybersecurityPage
from ui.memory_page import MemoryPage
from ui.styles import APP_STYLE

from voice.listener import VoiceWorker, VoiceService


class AssistantWorker(QThread):
    chunk_received = Signal(str)
    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, assistant, message):
        super().__init__()

        self.assistant = assistant
        self.message = message
        self._cancel_requested = threading.Event()

    def cancel(self):
        """Request cancellation of the active AI response."""
        self._cancel_requested.set()
        self.assistant.cancel_generation()

    def was_cancelled(self):
        return self._cancel_requested.is_set()

    def run(self):
        try:
            result = self.assistant.process_message_stream(
                self.message,
                self.chunk_received.emit,
            )

            self.response_ready.emit(str(result))

        except Exception as error:
            if self.was_cancelled():
                self.response_ready.emit("")
            else:
                self.error_occurred.emit(str(error))


class CyberNovaDesktop(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CyberNova | AI Workspace")
        self.resize(1200, 760)
        self.setMinimumSize(900, 600)

        # Core services
        self.assistant = CyberNovaAssistant()
        self.task_manager = TaskManager()

        # Worker references
        self.worker = None
        self.voice_worker = None

        # Voice service
        self.voice_service = VoiceService()

        self.init_ui()

    # -----------------------------------------
    # UI setup
    # -----------------------------------------

    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar()
        root_layout.addWidget(self.sidebar)

        # Main content
        main_area = QWidget()
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("Header")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 12, 22, 12)

        self.page_title = QLabel("Chat")
        self.page_title.setStyleSheet(
            "font-size: 17px; font-weight: bold;"
        )

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("Muted")

        self.cybersecurity_nav_button = QPushButton(
            "Cybersecurity Lab"
        )
        self.cybersecurity_nav_button.clicked.connect(
            lambda: self.show_page("cybersecurity")
        )

        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        header_layout.addWidget(
            self.cybersecurity_nav_button
        )
        header_layout.addWidget(self.status_label)

        main_layout.addWidget(header)

        # Page stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        # Chat page
        self.chat_page = ChatWidget()

        # Memory Dashboard page
        self.memory_page = MemoryPage(
            self.assistant.memory
        )

        # Settings page
        self.settings_page = SettingsPage()
        self.settings_page.settings_saved.connect(
            self.handle_settings_saved
        )

        # Tasks page
        self.tasks_page = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_page)
        tasks_layout.setContentsMargins(28, 24, 28, 24)

        tasks_title = QLabel("Background Tasks")
        tasks_title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        self.tasks_display = QLabel(
            "No background tasks have been submitted."
        )
        self.tasks_display.setWordWrap(True)

        refresh_button = QPushButton("Refresh Tasks")
        refresh_button.clicked.connect(self.refresh_tasks)

        tasks_layout.addWidget(tasks_title)
        tasks_layout.addWidget(self.tasks_display)
        tasks_layout.addWidget(refresh_button)
        tasks_layout.addStretch()

        # Voice page
        self.voice_page = QWidget()
        voice_layout = QVBoxLayout(self.voice_page)
        voice_layout.setContentsMargins(28, 24, 28, 24)

        voice_title = QLabel("Voice Assistant")
        voice_title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        voice_description = QLabel(
            "Use the microphone button in the chat "
            "to speak to CyberNova."
        )
        voice_description.setWordWrap(True)

        self.voice_status = QLabel(
            "Voice recognition is ready."
        )
        self.voice_status.setWordWrap(True)

        self.voice_button = QPushButton("Start Listening")
        self.voice_button.clicked.connect(
            self.start_voice_recognition
        )

        voice_layout.addWidget(voice_title)
        voice_layout.addWidget(voice_description)
        voice_layout.addWidget(self.voice_status)
        voice_layout.addWidget(self.voice_button)
        voice_layout.addStretch()

        # Cybersecurity Lab page
        self.cybersecurity_page = CybersecurityPage()

        # Register pages
        self.pages = {
            "chat": self.chat_page,
            "memory": self.memory_page,
            "tasks": self.tasks_page,
            "voice": self.voice_page,
            "settings": self.settings_page,
            "cybersecurity": self.cybersecurity_page,
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        # Navigation
        self.sidebar.page_selected.connect(
            self.show_page
        )

        # Chat events
        self.chat_page.message_submitted.connect(
            self.send_message
        )
        self.chat_page.voice_requested.connect(
            self.start_voice_recognition
        )
        self.chat_page.stop_requested.connect(
            self.stop_generation
        )

        # Layout and appearance
        root_layout.addWidget(main_area, 1)
        self.setStyleSheet(APP_STYLE)

        self.show_page("chat")

        self.chat_page.add_message(
            "CyberNova",
            "Welcome to CyberNova. How can I help?",
        )

    # -----------------------------------------
    # Settings integration
    # -----------------------------------------

    def handle_settings_saved(self, values):
        try:
            self.assistant.update_settings(
                host=values.get("ollama_host"),
                model=values.get("ollama_model"),
            )

            self.status_label.setText(
                "Ollama settings updated"
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Settings Update Failed",
                (
                    "The settings were saved, but the "
                    "assistant could not apply them.\n\n"
                    f"Error: {error}"
                ),
            )

            self.status_label.setText(
                "Settings update failed"
            )

    # -----------------------------------------
    # Navigation
    # -----------------------------------------

    def show_page(self, page_name):
        page = self.pages.get(page_name)

        if page is None:
            return

        self.stack.setCurrentWidget(page)

        self.page_title.setText(
            page_name.replace("_", " ").title()
        )

        # Refresh memories whenever the page is opened
        if page_name == "memory":
            self.memory_page.load_memories()

    # -----------------------------------------
    # Chat and AI
    # -----------------------------------------

    def send_message(self, message):
        message = str(message).strip()

        if not message:
            return

        if (
            self.worker is not None
            and self.worker.isRunning()
        ):
            self.status_label.setText(
                "Please wait for the current response."
            )
            return

        self.chat_page.add_message("You", message)

        self.chat_page.start_streaming_message(
            "CyberNova"
        )

        self.chat_page.set_busy(True)

        self.status_label.setText(
            "Generating response..."
        )

        self.worker = AssistantWorker(
            self.assistant,
            message,
        )

        self.worker.chunk_received.connect(
            self.chat_page.append_streaming_chunk
        )

        self.worker.response_ready.connect(
            self.handle_response
        )

        self.worker.error_occurred.connect(
            self.handle_error
        )

        self.worker.finished.connect(
            self.worker_finished
        )

        self.worker.start()

    def stop_generation(self):
        if (
            self.worker is None
            or not self.worker.isRunning()
        ):
            return

        if self.worker.was_cancelled():
            return

        self.status_label.setText("Stopping generation...")
        self.chat_page.stop_button.setEnabled(False)

        self.worker.cancel()

    def handle_response(self, response):
        self.chat_page.finish_streaming_message()

        if (
            self.worker is not None
            and self.worker.was_cancelled()
        ):
            self.status_label.setText(
                "Generation stopped"
            )

    def handle_error(self, error):
        self.chat_page.finish_streaming_message()

        self.chat_page.add_message(
            "CyberNova",
            f"Error: {error}",
        )

    def worker_finished(self):
        was_cancelled = (
            self.worker is not None
            and self.worker.was_cancelled()
        )

        self.chat_page.set_busy(False)

        if was_cancelled:
            self.status_label.setText(
                "Generation stopped"
            )
        else:
            self.status_label.setText("Ready")

        self.worker = None

    # -----------------------------------------
    # Background tasks
    # -----------------------------------------

    def refresh_tasks(self):
        tasks = self.task_manager.get_tasks()

        if not tasks:
            self.tasks_display.setText(
                "No background tasks have been submitted."
            )
            return

        lines = []

        for task_id, task in tasks.items():
            lines.append(
                f"{task['name']} — {task['status']}"
            )

        self.tasks_display.setText(
            "\n".join(lines)
        )

    # -----------------------------------------
    # Voice recognition
    # -----------------------------------------

    def start_voice_recognition(self):
        if (
            self.voice_worker is not None
            and self.voice_worker.isRunning()
        ):
            self.voice_status.setText(
                "Already listening. Please wait."
            )
            return

        if (
            self.worker is not None
            and self.worker.isRunning()
        ):
            self.voice_status.setText(
                "Wait for the current AI response."
            )
            return

        self.voice_status.setText(
            "Listening for up to 5 seconds..."
        )

        self.status_label.setText("Listening...")
        self.voice_button.setEnabled(False)

        self.voice_worker = VoiceWorker(duration=5)

        self.voice_worker.transcript_ready.connect(
            self.handle_voice_transcript
        )

        self.voice_worker.error_occurred.connect(
            self.handle_voice_error
        )

        self.voice_worker.finished.connect(
            self.voice_worker_finished
        )

        self.voice_worker.start()

    def handle_voice_transcript(self, text):
        text = str(text).strip()

        if not text:
            self.voice_status.setText(
                "No speech detected. Try again."
            )
            return

        self.voice_status.setText(
            f"Recognized: {text}"
        )

        self.send_message(text)

    def handle_voice_error(self, error):
        self.voice_status.setText(
            f"Voice error: {error}"
        )

        self.chat_page.add_message(
            "CyberNova",
            f"Voice error: {error}",
        )

    def voice_worker_finished(self):
        self.voice_button.setEnabled(True)

        if (
            self.worker is None
            or not self.worker.isRunning()
        ):
            self.status_label.setText("Ready")

        self.voice_worker = None

    # -----------------------------------------
    # Application shutdown
    # -----------------------------------------

    def closeEvent(self, event):
        active_workers = []

        if (
            self.worker is not None
            and self.worker.isRunning()
        ):
            active_workers.append(
                ("AI assistant", self.worker)
            )

        if (
            self.voice_worker is not None
            and self.voice_worker.isRunning()
        ):
            active_workers.append(
                ("Voice recognition", self.voice_worker)
            )

        scan_worker = getattr(
            self.cybersecurity_page,
            "scan_worker",
            None,
        )

        if (
            scan_worker is not None
            and scan_worker.isRunning()
        ):
            active_workers.append(
                ("Nmap scan", scan_worker)
            )

        if active_workers:
            names = ", ".join(
                name for name, _ in active_workers
            )

            QMessageBox.warning(
                self,
                "Tasks are still running",
                (
                    "Wait for these tasks to finish "
                    f"before closing: {names}."
                ),
            )

            event.ignore()
            return

        self.task_manager.shutdown()
        event.accept()


def main():
    app = QApplication(sys.argv)

    window = CyberNovaDesktop()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()