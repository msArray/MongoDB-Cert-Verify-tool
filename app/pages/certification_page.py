import os

from PySide6.QtCore import Signal, QDate, QThread
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QDateEdit,
    QAbstractSpinBox,
    QMessageBox,
    QFileDialog,
    QProgressBar,
)
from qasync import asyncSlot
import sys
from pathlib import Path
from dotenv import load_dotenv

from app.services.mongo_adaptor import MongoAdaptor
from app.services.check_dir import checkDir
from app.services.verify_pdfs import VerifyPDFsWorker
from app.services.export_excel import export_excel

def get_env_path() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstallerで実行されている場合
        base_dir = Path(sys._MEIPASS)
    else:
        # app/pages/certification_page.py → project/
        base_dir = Path(__file__).resolve().parents[2]

    return base_dir / ".env"

env_path = get_env_path()

load_dotenv(env_path)


class CertificationPage(QWidget):

    finished = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.certname_input = QLineEdit()
        self.folder_path_input = QLineEdit()
        self.complete_date_input = QDateEdit()
        self.mongo_uri = os.getenv("MONGODB_URI")
        self.mongo_adaptor = MongoAdaptor(self.mongo_uri)

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("MongoDB Certification Verify Tool")
        header_label.setObjectName("headerLabel")

        layout.addWidget(header_label)

        # Certification name
        certname_layout = QHBoxLayout()

        certname_label = QLabel("Certification Name:")

        self.certname_input.setPlaceholderText("Enter Certification Name")

        certname_layout.addWidget(certname_label)
        certname_layout.addWidget(self.certname_input)

        layout.addLayout(certname_layout)

        # URL of the Folder that is to be processed
        folder_path_layout = QHBoxLayout()

        folder_path_label = QLabel("Folder URL (Path):")

        self.folder_path_input.setPlaceholderText(
            "Enter Folder Path or Select by click Button"
        )

        self.select_folder_button = QPushButton("📁")
        self.select_folder_button.setObjectName("folderIconButton")

        folder_path_layout.addWidget(folder_path_label)
        folder_path_layout.addWidget(self.folder_path_input)
        folder_path_layout.addWidget(self.select_folder_button)

        layout.addLayout(folder_path_layout)

        # Target Completion Date
        date_input_layout = QHBoxLayout()

        date_input_label = QLabel("Target Completion Date:")
        self.complete_date_input.setDisplayFormat("d/M/yyyy")
        self.complete_date_input.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self.complete_date_input.setDate(QDate.currentDate())

        date_input_layout.addWidget(date_input_label)
        date_input_layout.addWidget(self.complete_date_input)

        layout.addLayout(date_input_layout)

        # Button
        self.verify_button = QPushButton("Verify")

        layout.addWidget(self.verify_button)

        self.verify_progress = QProgressBar(minimum=0, maximum=100)
        self.verify_progress.setValue(0)
        layout.addWidget(self.verify_progress)

        self.export_excel_button = QPushButton("Export as Excel File")
        self.export_excel_button.setObjectName("exportExcelButton")
        layout.addWidget(self.export_excel_button)

    def setup_connections(self):
        self.select_folder_button.clicked.connect(self.on_sel_fldr_clicked)
        self.verify_button.clicked.connect(self.on_verify_clicked)
        self.export_excel_button.clicked.connect(self.on_save_excel_clicked)

    def on_sel_fldr_clicked(self):
        dialog = QFileDialog()
        folder_path = dialog.getExistingDirectory(None, "Select Folder")
        self.folder_path_input.setText(folder_path)

    def on_verify_clicked(self):
        self.verify_button.setDisabled(True)
        self.verify_button.setText("Verifying...")
        certification_name = self.certname_input.text()
        check_path = self.folder_path_input.text()
        _result = checkDir(check_path)
        if _result == False:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(
                "The target item was not found in the entered URL or path."
            )
            msg.setWindowTitle("Error")
            msg.exec_()
            self.verify_button.setDisabled(False)
            self.verify_button.setText("Verify")
            return
        self.verify_progress.setMaximum(len(_result))
        # print(_result)
        self.thread = QThread()
        self.worker = VerifyPDFsWorker(
            _result,
            check_path,
            self.complete_date_input.date().toString(),
            certification_name,
            self.mongo_adaptor,
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.on_progress)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)

        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_finished(self, result):
        # print(result)

        self.verify_button.setEnabled(True)
        self.verify_button.setText("Verify")
        self.verify_progress.setValue(self.verify_progress.maximum())

    def on_error(self, message):
        print("Error:", message)

        self.verify_button.setEnabled(True)

    def on_progress(self, value):
        self.verify_progress.setValue(value)

    @asyncSlot()
    async def on_save_excel_clicked(self):
        self.export_excel_button.setDisabled(True)
        self.export_excel_button.setText("Exporting...")
        result = await export_excel(self.mongo_uri, "total_scores.xlsx")
        if result:
            self.export_excel_button.setDisabled(False)
            self.export_excel_button.setText("Export as Excel File")
