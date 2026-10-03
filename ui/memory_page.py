
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QScrollArea,
    QMessageBox,
    QDialog,
    QFormLayout,
    QPlainTextEdit,
)


class MemoryPage(QWidget):
    def __init__(self, memory_manager):
        super().__init__()

        self.memory_manager = memory_manager
        self.memories = []
        self.setObjectName("MemoryPage")

        self.setup_ui()
        self.load_memories()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(18)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Memory Dashboard")
        title.setStyleSheet(
            "font-size: 25px; font-weight: bold;"
        )

        self.count_label = QLabel("0 memories")
        self.count_label.setObjectName("Muted")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)

        main_layout.addLayout(header_layout)

        description = QLabel(
            "View and manage the information CyberNova remembers."
        )
        description.setObjectName("Muted")
        description.setWordWrap(True)
        main_layout.addWidget(description)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search memories..."
        )
        self.search_input.textChanged.connect(
            self.filter_memories
        )
        main_layout.addWidget(self.search_input)

        # Memory list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.memory_container = QWidget()
        self.memory_layout = QVBoxLayout(
            self.memory_container
        )
        self.memory_layout.setContentsMargins(2, 2, 2, 2)
        self.memory_layout.setSpacing(12)
        self.memory_layout.addStretch()

        self.scroll_area.setWidget(self.memory_container)
        main_layout.addWidget(self.scroll_area, 1)

        # Bottom actions
        bottom_layout = QHBoxLayout()

        refresh_button = QPushButton("Refresh Memories")
        refresh_button.clicked.connect(self.load_memories)

        bottom_layout.addStretch()
        bottom_layout.addWidget(refresh_button)

        main_layout.addLayout(bottom_layout)

    def clear_memory_cards(self):
        while self.memory_layout.count() > 1:
            item = self.memory_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def load_memories(self):
        self.clear_memory_cards()

        try:
            self.memories = self.memory_manager.search_memories(
                query="",
                limit=1000
            )

            if self.memories is None:
                self.memories = []

        except Exception as error:
            QMessageBox.critical(
                self,
                "Memory Error",
                f"Could not load memories:\n{error}"
            )
            self.memories = []

        self.count_label.setText(
            f"{len(self.memories)} memories"
        )

        self.filter_memories()

    def filter_memories(self):
        if not hasattr(self, "memories"):
            return

        self.clear_memory_cards()

        query = self.search_input.text().strip().lower()

        filtered = [
            memory for memory in self.memories
            if query in str(memory.get("content", "")).lower()
            or query in str(memory.get("category", "")).lower()
        ]

        if not filtered:
            empty_label = QLabel("No memories found.")
            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            empty_label.setObjectName("Muted")

            self.memory_layout.insertWidget(
                0, empty_label
            )
            return

        for memory in filtered:
            self.add_memory_card(memory)

    def add_memory_card(self, memory):
        card = QFrame()
        card.setObjectName("MemoryCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        top_layout = QHBoxLayout()

        category = QLabel(
            str(memory.get("category", "general")).title()
        )
        category.setObjectName("Muted")

        memory_id = memory.get("id")

        edit_button = QPushButton("Edit")
        edit_button.setFixedWidth(75)
        edit_button.clicked.connect(
            lambda checked=False, mid=memory_id:
            self.edit_memory(mid)
        )

        delete_button = QPushButton("Delete")
        delete_button.setFixedWidth(80)
        delete_button.clicked.connect(
            lambda checked=False, mid=memory_id:
            self.delete_memory(mid)
        )

        top_layout.addWidget(category)
        top_layout.addStretch()
        top_layout.addWidget(edit_button)
        top_layout.addWidget(delete_button)

        content = QLabel(
            str(memory.get("content", ""))
        )
        content.setWordWrap(True)
        content.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        card_layout.addLayout(top_layout)
        card_layout.addWidget(content)

        self.memory_layout.insertWidget(
            self.memory_layout.count() - 1,
            card
        )

    def edit_memory(self, memory_id):
        if memory_id is None:
            QMessageBox.warning(
                self,
                "Cannot Edit",
                "This memory has no ID."
            )
            return

        memory = next(
            (
                item for item in self.memories
                if item.get("id") == memory_id
            ),
            None
        )

        if memory is None:
            QMessageBox.warning(
                self,
                "Memory Not Found",
                "Could not find this memory."
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Memory")
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()

        category_input = QLineEdit(
            str(memory.get("category", "general"))
        )

        content_input = QPlainTextEdit(
            str(memory.get("content", ""))
        )
        content_input.setMinimumHeight(140)

        form_layout.addRow(
            "Category:",
            category_input
        )
        form_layout.addRow(
            "Memory:",
            content_input
        )

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()

        save_button = QPushButton("Save Changes")
        cancel_button = QPushButton("Cancel")

        save_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(save_button)

        layout.addLayout(buttons_layout)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_category = category_input.text().strip()
        new_content = content_input.toPlainText().strip()

        if not new_category or not new_content:
            QMessageBox.warning(
                self,
                "Invalid Memory",
                "Category and memory content cannot be empty."
            )
            return

        try:
            result = self.memory_manager.update_memory(
                memory_id,
                new_content,
                new_category
            )

            if result is False:
                QMessageBox.warning(
                    self,
                    "Update Failed",
                    "The memory could not be updated. "
                    "It may no longer exist."
                )
                return

            self.load_memories()

            QMessageBox.information(
                self,
                "Memory Updated",
                "Memory updated successfully."
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Update Failed",
                f"Could not update memory:\n{error}"
            )

    def delete_memory(self, memory_id):
        if memory_id is None:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "This memory has no ID."
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Memory",
            "Are you sure you want to delete this memory?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.memory_manager.delete_memory(memory_id)
            self.load_memories()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Delete Failed",
                f"Could not delete memory:\n{error}"
            )