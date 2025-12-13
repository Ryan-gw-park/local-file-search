"""
Local Finder X v2.0 - Main Window

Main application window with Global Sidebar navigation.
Based on PRD UI specifications.
"""

import sys
from typing import Optional

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QStackedWidget, QLabel, QFrame, QSizePolicy
    )
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QIcon, QFont
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False


# =============================================================================
# Styles
# =============================================================================

SIDEBAR_STYLE = """
QFrame#sidebar {
    background-color: #1a1a2e;
    border: none;
}

QPushButton.nav-button {
    background-color: transparent;
    color: #8888aa;
    border: none;
    padding: 15px;
    text-align: left;
    font-size: 14px;
    border-radius: 8px;
    margin: 2px 8px;
}

QPushButton.nav-button:hover {
    background-color: #2d2d44;
    color: #ffffff;
}

QPushButton.nav-button:checked {
    background-color: #3d3d5c;
    color: #ffffff;
}
"""

MAIN_STYLE = """
QMainWindow {
    background-color: #0f0f1a;
}

QWidget#content {
    background-color: #16162a;
}

QLabel {
    color: #ffffff;
}
"""


# =============================================================================
# Sidebar Navigation
# =============================================================================

class SidebarButton(QPushButton if PYQT6_AVAILABLE else object):
    """Navigation button for sidebar."""
    
    def __init__(self, text: str, icon_text: str = ""):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(f"{icon_text}  {text}" if icon_text else text)
        self.setCheckable(True)
        self.setProperty("class", "nav-button")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(50)


class Sidebar(QFrame if PYQT6_AVAILABLE else object):
    """Global sidebar with navigation buttons."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(5)
        
        # Logo/Title
        title = QLabel("Local Finder X")
        title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        version = QLabel("v2.0")
        version.setStyleSheet("color: #666680; font-size: 12px; padding-bottom: 20px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        
        # Navigation buttons
        self.btn_search = SidebarButton("검색", "🔍")
        self.btn_indexing = SidebarButton("인덱싱", "📁")
        self.btn_about = SidebarButton("정보", "ℹ️")
        self.btn_mypage = SidebarButton("마이페이지", "👤")
        
        layout.addWidget(self.btn_search)
        layout.addWidget(self.btn_indexing)
        layout.addWidget(self.btn_about)
        layout.addWidget(self.btn_mypage)
        
        layout.addStretch()
        
        # Default selection
        self.btn_search.setChecked(True)
        
        # Button group behavior
        self.buttons = [self.btn_search, self.btn_indexing, self.btn_about, self.btn_mypage]
        for btn in self.buttons:
            btn.clicked.connect(lambda checked, b=btn: self._on_button_clicked(b))
    
    def _on_button_clicked(self, clicked_btn):
        """Handle button click - ensure only one is checked."""
        for btn in self.buttons:
            btn.setChecked(btn == clicked_btn)


# =============================================================================
# Placeholder Pages
# =============================================================================

class PlaceholderPage(QWidget if PYQT6_AVAILABLE else object):
    """Placeholder page for development."""
    
    def __init__(self, title: str, description: str = "", parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("font-size: 14px; color: #888899; margin-top: 10px;")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(desc_label)


# =============================================================================
# Main Window
# =============================================================================

class MainWindow(QMainWindow if PYQT6_AVAILABLE else object):
    """Main application window with sidebar navigation."""
    
    def __init__(self):
        if not PYQT6_AVAILABLE:
            print("PyQt6 is not installed. Install with: pip install PyQt6")
            return
        
        super().__init__()
        self.setWindowTitle("Local Finder X v2.0")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(MAIN_STYLE + SIDEBAR_STYLE)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area (stacked pages)
        self.content = QStackedWidget()
        self.content.setObjectName("content")
        main_layout.addWidget(self.content)
        
        # Create pages
        self._create_pages()
        
        # Connect navigation
        self._connect_navigation()
    
    def _create_pages(self):
        """Create all pages."""
        # Import actual pages if available, otherwise use placeholders
        try:
            from src.ui.search_page import SearchPage
            self.search_page = SearchPage()
        except ImportError:
            self.search_page = PlaceholderPage("🔍 검색", "검색 페이지가 로드됩니다")
        
        try:
            from src.ui.indexing_page import IndexingPage
            self.indexing_page = IndexingPage()
        except ImportError:
            self.indexing_page = PlaceholderPage("📁 인덱싱", "인덱싱 페이지가 로드됩니다")
        
        try:
            from src.ui.about_page import AboutPage
            self.about_page = AboutPage()
        except ImportError:
            self.about_page = PlaceholderPage("ℹ️ 정보", "Local Finder X v2.0\n설명 가능한 하이브리드 로컬 검색 엔진")
        
        try:
            from src.ui.mypage import MyPage
            self.mypage = MyPage()
        except ImportError:
            self.mypage = PlaceholderPage("👤 마이페이지", "라이선스 및 설정")
        
        self.content.addWidget(self.search_page)
        self.content.addWidget(self.indexing_page)
        self.content.addWidget(self.about_page)
        self.content.addWidget(self.mypage)
    
    def _connect_navigation(self):
        """Connect sidebar buttons to page switching."""
        self.sidebar.btn_search.clicked.connect(lambda: self.content.setCurrentIndex(0))
        self.sidebar.btn_indexing.clicked.connect(lambda: self.content.setCurrentIndex(1))
        self.sidebar.btn_about.clicked.connect(lambda: self.content.setCurrentIndex(2))
        self.sidebar.btn_mypage.clicked.connect(lambda: self.content.setCurrentIndex(3))


# =============================================================================
# Application Entry
# =============================================================================

def create_app():
    """Create the application instance."""
    if not PYQT6_AVAILABLE:
        return None
    return QApplication(sys.argv)


def run_app():
    """Run the main application."""
    if not PYQT6_AVAILABLE:
        print("PyQt6 is not installed. Install with: pip install PyQt6")
        return 1
    
    import json
    from pathlib import Path
    
    app = create_app()
    
    # Check for first run
    settings_dir = Path.home() / ".local-finder-x"
    settings_file = settings_dir / "settings.json"
    
    first_run = True
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)
                first_run = not settings.get("first_run_complete", False)
        except:
            pass
    
    # Show setup wizard on first run
    if first_run:
        try:
            from src.ui.setup_wizard import SetupWizard
            wizard = SetupWizard()
            
            def on_setup_complete(settings_data):
                # Save settings
                settings_dir.mkdir(parents=True, exist_ok=True)
                with open(settings_file, "w") as f:
                    json.dump(settings_data, f, indent=2)
            
            wizard.setup_complete.connect(on_setup_complete)
            result = wizard.exec()
            
            if result == 0:  # User cancelled
                return 0
        except ImportError as e:
            print(f"Setup wizard not available: {e}")
    
    window = MainWindow()
    window.show()
    return app.exec()



__all__ = [
    "MainWindow",
    "Sidebar",
    "SidebarButton",
    "PlaceholderPage",
    "create_app",
    "run_app",
    "PYQT6_AVAILABLE",
]
