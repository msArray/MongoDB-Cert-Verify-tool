# 外部ライブラリ
from PySide6.QtWidgets import QMainWindow, QStackedWidget
import asyncio
# インポート
from app.pages.certification_page import CertificationPage
from app.pages.result_page import ResultPage


class MainWindow(QMainWindow):
    def __init__(self,loop=False):
        super().__init__()

        self.setWindowTitle("MongoDB Certification Verify Tool")
        self.resize(640, 320)

        self.stack = QStackedWidget()

        self.certification_page = CertificationPage()
        self.result_page = ResultPage()

        self.stack.addWidget(self.certification_page)
        self.stack.addWidget(self.result_page)

        self.setCentralWidget(self.stack)

        self.certification_page.finished.connect(
            self.show_result
        )
        self.loop = loop or asyncio.get_event_loop()

    def show_result(self, result):
        self.result_page.set_result(result)
        self.stack.setCurrentWidget(self.result_page)

    def show_certification_page(self):
        self.stack.setCurrentWidget(self.certification_page)