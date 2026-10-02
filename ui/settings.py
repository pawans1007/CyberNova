
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QMessageBox,
)

from app.settings_manager import SettingsManager


class SettingsPage(QWidget):
    settings_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.settings_manager = SettingsManager()

        self.setObjectName("settingsPage")

        self.create_ui()
        self.load_settings()

    def create_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Configure CyberNova's AI connection and voice options."
        )
        subtitle.setObjectName("pageSubtitle")
        layout.addWidget(subtitle)

        # Ollama settings
        ai_title = QLabel("AI Connection")
        ai_title.setObjectName("sectionTitle")
        layout.addWidget(ai_title)

        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText(
            "http://localhost:11434"
        )

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText(
            "qwen2.5:3b-instruct"
        )

        layout.addWidget(QLabel("Ollama Host"))
        layout.addWidget(self.host_input)

        layout.addWidget(QLabel("Model Name"))
        layout.addWidget(self.model_input)

        # Voice settings
        voice_title = QLabel("Voice Settings")
        voice_title.setObjectName("sectionTitle")
        layout.addWidget(voice_title)

        self.voice_enabled = QCheckBox(
            "Enable voice features"
        )
        layout.addWidget(self.voice_enabled)

        rate_row = QHBoxLayout()

        rate_label = QLabel("Speech Rate")
        self.speech_rate = QSpinBox()
        self.speech_rate.setRange(100, 300)
        self.speech_rate.setValue(175)

        rate_row.addWidget(rate_label)
        rate_row.addWidget(self.speech_rate)

        layout.addLayout(rate_row)

        # Theme
        theme_title = QLabel("Appearance")
        theme_title.setObjectName("sectionTitle")
        layout.addWidget(theme_title)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "Dark",
            "Light",
        ])
        layout.addWidget(QLabel("Theme"))
        layout.addWidget(self.theme_combo)

        layout.addStretch()

        # Save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.save_settings)

        layout.addWidget(self.save_button)

    def load_settings(self):
        self.host_input.setText(
            self.settings_manager.get(
                "ollama_host",
                "http://localhost:11434",
            )
        )

        self.model_input.setText(
            self.settings_manager.get(
                "ollama_model",
                "qwen2.5:3b-instruct",
            )
        )

        self.voice_enabled.setChecked(
            bool(
                self.settings_manager.get(
                    "voice_enabled",
                    True,
                )
            )
        )

        self.speech_rate.setValue(
            int(
                self.settings_manager.get(
                    "speech_rate",
                    175,
                )
            )
        )

        theme = self.settings_manager.get(
            "theme",
            "dark",
        )

        index = self.theme_combo.findText(
            str(theme).capitalize()
        )

        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

    def save_settings(self):
        host = self.host_input.text().strip()
        model = self.model_input.text().strip()

        if not host or not model:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "Ollama host and model cannot be empty.",
            )
            return

        values = {
            "ollama_host": host,
            "ollama_model": model,
            "voice_enabled": self.voice_enabled.isChecked(),
            "speech_rate": self.speech_rate.value(),
            "theme": self.theme_combo.currentText().lower(),
        }

        try:
            for key, value in values.items():
                self.settings_manager.set(key, value)

            self.settings_saved.emit(values)

            QMessageBox.information(
                self,
                "Settings Saved",
                "Your settings have been saved.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Save Failed",
                str(error),
            )