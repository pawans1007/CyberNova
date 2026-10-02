from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    message_received = Signal(str)
    response_ready = Signal(str)
    task_started = Signal(str)
    task_finished = Signal(str, str)
    error_occurred = Signal(str)


event_bus = EventBus()