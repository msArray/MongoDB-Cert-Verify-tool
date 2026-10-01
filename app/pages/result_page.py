from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
)


class ResultPage(QWidget):

    finished = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.certname_input = QLineEdit()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("MongoDB Certification Verify Tool")
        header_label.setObjectName("headerLabel")

        layout.addWidget(header_label)