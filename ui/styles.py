
APP_STYLE = """
QMainWindow, QWidget {
    background-color: #0d1119;
    color: #e8edf5;
    font-family: Segoe UI;
    font-size: 13px;
}

QFrame#Sidebar {
    background-color: #111824;
    border-right: 1px solid #263247;
}

QFrame#Header {
    background-color: #111824;
    border-bottom: 1px solid #263247;
}

QLabel#Logo {
    color: #53d5ff;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 2px;
}

QLabel#Muted {
    color: #94a3b8;
}

QPushButton {
    background-color: #172337;
    border: 1px solid #2c3e57;
    border-radius: 9px;
    padding: 10px 14px;
    color: #e8edf5;
}

QPushButton:hover {
    background-color: #223550;
    border-color: #53d5ff;
}

QPushButton:checked {
    background-color: #163a50;
    border-color: #53d5ff;
    color: #75dcff;
}

QPushButton#Primary {
    background-color: #087eae;
    border: none;
    color: white;
    font-weight: bold;
}

QPushButton#Primary:hover {
    background-color: #0799d3;
}

QTextEdit, QPlainTextEdit, QLineEdit {
    background-color: #151d2a;
    border: 1px solid #2b3a50;
    border-radius: 10px;
    padding: 10px;
    color: #f0f5fa;
    selection-background-color: #17658d;
}

QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #53d5ff;
}

QScrollArea {
    border: none;
    background: transparent;
}

QGroupBox {
    border: 1px solid #2b3a50;
    border-radius: 12px;
    margin-top: 12px;
    padding: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: #53d5ff;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
"""