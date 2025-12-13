"""
Local Finder X v2.0 - About Page

Application information and credits.
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
    )
    from PyQt6.QtCore import Qt
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object


ABOUT_STYLE = """
QFrame.card {
    background-color: #1e1e32;
    border-radius: 12px;
    padding: 20px;
}
"""


class AboutPage(QWidget if PYQT6_AVAILABLE else object):
    """About page with application information."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet(ABOUT_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Card container
        card = QFrame()
        card.setProperty("class", "card")
        card.setMaximumWidth(600)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        
        # Logo/Title
        title = QLabel("🔍 Local Finder X")
        title.setStyleSheet("color: #ffffff; font-size: 32px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)
        
        version = QLabel("Version 2.0")
        version.setStyleSheet("color: #6366f1; font-size: 16px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(version)
        
        # Description
        desc = QLabel(
            "설명 가능한 하이브리드 로컬 검색 엔진\n\n"
            "Local Finder X는 MS Office 문서, PDF, Markdown 등\n"
            "로컬 파일을 AI 기반으로 검색하고,\n"
            "왜 해당 파일이 검색되었는지 근거를 제시합니다."
        )
        desc.setStyleSheet("color: #ccccdd; font-size: 14px; line-height: 1.6;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(desc)
        
        # Features
        features_label = QLabel("주요 기능")
        features_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; margin-top: 20px;")
        card_layout.addWidget(features_label)
        
        features = [
            "🔒 완전 오프라인 - 파일 정보가 외부로 전송되지 않음",
            "⚡ 하이브리드 검색 - Dense + BM25 + RRF 융합",
            "📊 근거 제시 - 검색 결과에 대한 명확한 설명",
            "📁 다양한 형식 - docx, xlsx, pptx, pdf, md 지원",
        ]
        
        for feature in features:
            feat_label = QLabel(f"  {feature}")
            feat_label.setStyleSheet("color: #aaaacc; font-size: 13px; padding: 3px 0;")
            card_layout.addWidget(feat_label)
        
        # Copyright
        copyright_label = QLabel("© 2025 Local Finder X. All rights reserved.")
        copyright_label.setStyleSheet("color: #666680; font-size: 11px; margin-top: 30px;")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(copyright_label)
        
        layout.addWidget(card)
        layout.addStretch()


__all__ = ["AboutPage"]
