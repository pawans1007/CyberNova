
import html

from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)


class ChatWidget(QWidget):
    message_submitted = Signal(str)
    voice_requested = Signal()
    stop_requested = Signal()

    def __init__(self):
        super().__init__()

        self._stream_cursor = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            24, 20, 24, 20
        )
        layout.setSpacing(14)

        heading = QLabel("AI Assistant")
        heading.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
        )

        description = QLabel(
            "Ask questions, research topics, "
            "or use approved tools."
        )
        description.setObjectName("Muted")

        layout.addWidget(heading)
        layout.addWidget(description)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        layout.addWidget(
            self.chat_display,
            1,
        )

        input_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText(
            "Message CyberNova..."
        )
        self.input_box.returnPressed.connect(
            self.submit_message
        )

        self.voice_button = QPushButton(
            "Voice"
        )
        self.voice_button.clicked.connect(
            self.voice_requested.emit
        )

        self.send_button = QPushButton(
            "Send"
        )
        self.send_button.setObjectName(
            "Primary"
        )
        self.send_button.clicked.connect(
            self.submit_message
        )

        self.stop_button = QPushButton(
            "Stop"
        )
        self.stop_button.setObjectName(
            "Stop"
        )
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(
            self.stop_requested.emit
        )

        input_layout.addWidget(
            self.input_box,
            1,
        )
        input_layout.addWidget(
            self.voice_button
        )
        input_layout.addWidget(
            self.send_button
        )
        input_layout.addWidget(
            self.stop_button
        )

        layout.addLayout(input_layout)

    def submit_message(self):
        text = self.input_box.text().strip()

        if not text:
            return

        self.input_box.clear()
        self.message_submitted.emit(text)

    def add_message(
        self,
        sender,
        message,
    ):
        safe_sender = html.escape(
            str(sender)
        )

        safe_message = html.escape(
            str(message)
        ).replace("\n", "<br>")

        color = (
            "#55b6ff"
            if sender == "You"
            else "#57e39b"
        )

        self.chat_display.append(
            f'<p><b style="color:{color}">'
            f'{safe_sender}:</b> '
            f'{safe_message}</p>'
        )

    def start_streaming_message(
        self,
        sender="CyberNova",
    ):
        color = (
            "#55b6ff"
            if sender == "You"
            else "#57e39b"
        )

        safe_sender = html.escape(
            str(sender)
        )

        self.chat_display.moveCursor(
            QTextCursor.End
        )

        self.chat_display.insertHtml(
            f'<p><b style="color:{color}">'
            f'{safe_sender}:</b> '
        )

        self._stream_cursor = (
            self.chat_display.textCursor()
        )

        self._stream_cursor.movePosition(
            QTextCursor.End
        )

        self.chat_display.setTextCursor(
            self._stream_cursor
        )

    def append_streaming_chunk(
        self,
        chunk,
    ):
        if self._stream_cursor is None:
            return

        self._stream_cursor.insertText(
            str(chunk)
        )

        self.chat_display.setTextCursor(
            self._stream_cursor
        )

        self.chat_display.ensureCursorVisible()

    def finish_streaming_message(self):
        if self._stream_cursor is None:
            return

        self._stream_cursor.insertHtml(
            "</p>"
        )

        self.chat_display.setTextCursor(
            self._stream_cursor
        )

        self.chat_display.ensureCursorVisible()

        self._stream_cursor = None

    def set_busy(self, busy):
        self.send_button.setEnabled(
            not busy
        )

        self.input_box.setEnabled(
            not busy
        )

        self.voice_button.setEnabled(
            not busy
        )

        self.stop_button.setEnabled(
            busy
        )