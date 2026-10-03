
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy,
)


class Sidebar(QFrame):
    page_selected = Signal(str)

    def __init__(self):
        super().__init__()

        self.setObjectName("Sidebar")
        self.setFixedWidth(210)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(10)

        logo = QLabel("CYBERNOVA")
        logo.setObjectName("Logo")
        layout.addWidget(logo)

        tagline = QLabel("Your intelligent workspace")
        tagline.setObjectName("Muted")
        layout.addWidget(tagline)

        layout.addSpacing(25)

        self.buttons = {}

        pages = [
            ("Chat", "chat"),
            ("Memory", "memory"),
            ("Tasks", "tasks"),
            ("Voice", "voice"),
            ("Settings", "settings"),
        ]

        for label, page in pages:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed
            )
            button.clicked.connect(
                lambda checked=False, p=page: self.select_page(p)
            )

            layout.addWidget(button)
            self.buttons[page] = button

        layout.addStretch()

        footer = QLabel("CyberNova 1.0")
        footer.setObjectName("Muted")
        layout.addWidget(footer)

        self.select_page("chat")

    def select_page(self, page):
        for name, button in self.buttons.items():
            button.setChecked(name == page)

        self.page_selected.emit(page)