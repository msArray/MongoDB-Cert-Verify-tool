# 標準ライブラリ
import sys
from pathlib import Path


# 外部ライブラリ
import asyncio
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
# インポート
from app.main_window import MainWindow


qss_path = Path(__file__).resolve().parent / "app" / "styles" / "main.qss"

async def main():
    # 非同期処理対応Qtのセットアップ
    App = QApplication(sys.argv)
    with open(qss_path, encoding="utf-8") as f:
        App.setStyleSheet(f.read())
    
    loop = QEventLoop(App)
    asyncio.set_event_loop(loop)
    window = MainWindow(loop)
    window.show()
    with loop:
        loop.run_forever()
    

if __name__ == "__main__":
    asyncio.run(main())
