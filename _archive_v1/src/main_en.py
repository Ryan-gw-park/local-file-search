# src/main_en.py
# Phase 1: 3.4. main_en.py 수정 (필수)에 따라 구현
# Phase 2: licensing 패키지로 변경

from PyQt6.QtWidgets import QApplication
import sys
from ui import ChatWindow
from config import load_config
from licensing import LicenseManager  # Phase 2: 패키지에서 import

def main():
    app = QApplication(sys.argv)
    config = load_config()
    license_manager = LicenseManager(config)

    # Initialize with English settings
    window = ChatWindow(language="en", config=config, license_manager=license_manager)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
