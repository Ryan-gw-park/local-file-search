"""
Local Finder X v2.0 - My Page

License management and account settings.
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QFrame, QLineEdit, QGroupBox
    )
    from PyQt6.QtCore import Qt
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object


MYPAGE_STYLE = """
QFrame.card {
    background-color: #1e1e32;
    border-radius: 12px;
    padding: 20px;
}

QLineEdit {
    background-color: #252540;
    border: 1px solid #3d3d5c;
    border-radius: 8px;
    padding: 12px;
    color: #ffffff;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #6366f1;
}

QPushButton.primary {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}

QPushButton.primary:hover {
    background-color: #7c7ff2;
}

QGroupBox {
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    border: 1px solid #3d3d5c;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 15px;
}
"""


class MyPage(QWidget if PYQT6_AVAILABLE else object):
    """My Page with license and settings."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet(MYPAGE_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("마이페이지")
        header.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        # License section
        license_card = QFrame()
        license_card.setProperty("class", "card")
        license_layout = QVBoxLayout(license_card)
        
        license_header = QHBoxLayout()
        license_title = QLabel("라이선스")
        license_title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        license_header.addWidget(license_title)
        
        self.status_badge = QLabel("FREE")
        self.status_badge.setStyleSheet("""
            background-color: #3d5c3d;
            color: #88ff88;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        """)
        license_header.addWidget(self.status_badge)
        license_header.addStretch()
        
        license_layout.addLayout(license_header)
        
        license_desc = QLabel("Free 버전: 로컬 파일 검색만 가능")
        license_desc.setStyleSheet("color: #888899; font-size: 13px; margin-top: 5px;")
        license_layout.addWidget(license_desc)
        
        # License key input
        key_label = QLabel("라이선스 키")
        key_label.setStyleSheet("color: #ccccdd; font-size: 13px; margin-top: 15px;")
        license_layout.addWidget(key_label)
        
        key_layout = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        key_layout.addWidget(self.key_input)
        
        self.activate_btn = QPushButton("활성화")
        self.activate_btn.setProperty("class", "primary")
        self.activate_btn.clicked.connect(self._activate_license)
        key_layout.addWidget(self.activate_btn)
        
        license_layout.addLayout(key_layout)
        
        layout.addWidget(license_card)
        
        # Scope summary
        scope_card = QFrame()
        scope_card.setProperty("class", "card")
        scope_layout = QVBoxLayout(scope_card)
        
        scope_title = QLabel("검색 범위")
        scope_title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        scope_layout.addWidget(scope_title)
        
        # Free scope
        free_group = QFrame()
        free_layout = QVBoxLayout(free_group)
        free_layout.setContentsMargins(0, 10, 0, 0)
        
        free_header = QLabel("✅ Free (활성)")
        free_header.setStyleSheet("color: #88ff88; font-size: 14px; font-weight: bold;")
        free_layout.addWidget(free_header)
        
        free_items = QLabel("  • 로컬 파일 시스템 검색")
        free_items.setStyleSheet("color: #aaaacc; font-size: 13px;")
        free_layout.addWidget(free_items)
        
        scope_layout.addWidget(free_group)
        
        # Pro scope
        pro_group = QFrame()
        pro_layout = QVBoxLayout(pro_group)
        pro_layout.setContentsMargins(0, 15, 0, 0)
        
        pro_header = QLabel("🔒 Pro")
        pro_header.setStyleSheet("color: #888899; font-size: 14px; font-weight: bold;")
        pro_layout.addWidget(pro_header)
        
        pro_items = QLabel(
            "  • Outlook 이메일 검색\n"
            "  • OneDrive/SharePoint 연동\n"
            "  • 감사 로그"
        )
        pro_items.setStyleSheet("color: #666680; font-size: 13px;")
        pro_layout.addWidget(pro_items)
        
        scope_layout.addWidget(pro_group)
        
        layout.addWidget(scope_card)
        layout.addStretch()
    
    def _activate_license(self):
        """Handle license activation."""
        key = self.key_input.text().strip()
        if key:
            # TODO: Implement actual license validation
            self.status_badge.setText("PRO")
            self.status_badge.setStyleSheet("""
                background-color: #5c3d5c;
                color: #ff88ff;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            """)


__all__ = ["MyPage"]
