"""
Local Finder X v2.0 - Search Page

3-Panel search UI: Left (Results), Center (Evidence), Right (Query Input).
Based on PRD UI specifications.
"""

from typing import Optional, List

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
        QLabel, QLineEdit, QPushButton, QScrollArea,
        QFrame, QListWidget, QListWidgetItem, QTextEdit,
        QComboBox, QSizePolicy
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object
    pyqtSignal = lambda *args: None


# =============================================================================
# Styles
# =============================================================================

SEARCH_PAGE_STYLE = """
QFrame.panel {
    background-color: #1e1e32;
    border-radius: 10px;
    padding: 10px;
}

QLineEdit {
    background-color: #2a2a44;
    border: 1px solid #3d3d5c;
    border-radius: 8px;
    padding: 12px 15px;
    color: #ffffff;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #6366f1;
}

QPushButton.search-btn {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton.search-btn:hover {
    background-color: #7c7ff2;
}

QListWidget {
    background-color: transparent;
    border: none;
    color: #ffffff;
}

QListWidget::item {
    background-color: #2a2a44;
    border-radius: 8px;
    padding: 10px;
    margin: 4px 0;
}

QListWidget::item:selected {
    background-color: #3d3d66;
}

QComboBox {
    background-color: #2a2a44;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 8px;
    color: #ffffff;
}
"""


# =============================================================================
# Left Panel - Results List
# =============================================================================

class ResultItem(QFrame if PYQT6_AVAILABLE else object):
    """Single result item in the results list."""
    
    def __init__(self, filename: str, path: str, score: float, content_indexed: bool = True, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #2a2a44;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #3a3a55;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Filename with badge
        header = QHBoxLayout()
        
        name_label = QLabel(filename)
        name_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        header.addWidget(name_label)
        
        if not content_indexed:
            badge = QLabel("메타데이터만")
            badge.setStyleSheet("""
                background-color: #ff9800;
                color: #000000;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 10px;
            """)
            header.addWidget(badge)
        
        header.addStretch()
        
        score_label = QLabel(f"{score:.2f}")
        score_label.setStyleSheet("color: #6366f1; font-size: 12px;")
        header.addWidget(score_label)
        
        layout.addLayout(header)
        
        # Path
        path_label = QLabel(path)
        path_label.setStyleSheet("color: #888899; font-size: 11px;")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)


class LeftPanel(QFrame if PYQT6_AVAILABLE else object):
    """Left panel showing search results list."""
    
    if PYQT6_AVAILABLE:
        item_selected = pyqtSignal(str)  # file_id
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setProperty("class", "panel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("검색 결과")
        header.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Results count
        self.count_label = QLabel("0개 파일")
        self.count_label.setStyleSheet("color: #888899; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(self.count_label)
        
        # Scroll area for results
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch()
        
        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)
    
    def set_results(self, results: List[dict]):
        """Update results list."""
        # Clear existing
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new results
        for result in results:
            item = ResultItem(
                filename=result.get("filename", "Unknown"),
                path=result.get("path", ""),
                score=result.get("score", 0.0),
                content_indexed=result.get("content_indexed", True),
            )
            self.results_layout.insertWidget(self.results_layout.count() - 1, item)
        
        self.count_label.setText(f"{len(results)}개 파일")


# =============================================================================
# Center Panel - Evidence Cards
# =============================================================================

class EvidenceCard(QFrame if PYQT6_AVAILABLE else object):
    """Single evidence card."""
    
    def __init__(self, snippet: str, location: str = "", score: float = 0.0, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #252540;
                border-radius: 8px;
                border-left: 3px solid #6366f1;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Location header
        if location:
            loc_label = QLabel(location)
            loc_label.setStyleSheet("color: #6366f1; font-size: 11px; margin-bottom: 5px;")
            layout.addWidget(loc_label)
        
        # Snippet
        snippet_label = QLabel(snippet)
        snippet_label.setStyleSheet("color: #ccccdd; font-size: 13px; line-height: 1.5;")
        snippet_label.setWordWrap(True)
        layout.addWidget(snippet_label)


class CenterPanel(QFrame if PYQT6_AVAILABLE else object):
    """Center panel showing evidence cards for selected file."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setProperty("class", "panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        self.header = QLabel("근거")
        self.header.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.header)
        
        # File info
        self.file_label = QLabel("파일을 선택하세요")
        self.file_label.setStyleSheet("color: #888899; font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(self.file_label)
        
        # Scroll area for evidence cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
    
    def set_evidences(self, filename: str, evidences: List[dict]):
        """Update evidence cards."""
        self.file_label.setText(filename)
        
        # Clear existing
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not evidences:
            no_evidence = QLabel("근거 정보가 없습니다")
            no_evidence.setStyleSheet("color: #666680; font-size: 13px;")
            self.cards_layout.insertWidget(0, no_evidence)
            return
        
        # Add new cards
        for evidence in evidences:
            location = ""
            loc = evidence.get("location", {})
            if loc.get("page"):
                location = f"📄 {loc['page']}페이지"
            elif loc.get("slide"):
                location = f"📽️ {loc['slide']}번 슬라이드"
            elif loc.get("sheet"):
                location = f"📊 {loc['sheet']} 시트"
            
            card = EvidenceCard(
                snippet=evidence.get("snippet", ""),
                location=location,
                score=evidence.get("score", 0.0),
            )
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)


# =============================================================================
# Right Panel - Query Input
# =============================================================================

class RightPanel(QFrame if PYQT6_AVAILABLE else object):
    """Right panel with query input and mode selection."""
    
    if PYQT6_AVAILABLE:
        search_requested = pyqtSignal(str, str)  # query, mode
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setProperty("class", "panel")
        self.setMinimumWidth(350)
        self.setMaximumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("검색")
        header.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(header)
        
        # Mode selector
        mode_layout = QHBoxLayout()
        mode_label = QLabel("모드:")
        mode_label.setStyleSheet("color: #888899; font-size: 12px;")
        mode_layout.addWidget(mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["FAST", "SMART", "ASSIST"])
        self.mode_combo.setCurrentIndex(1)  # Default to SMART
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        
        layout.addLayout(mode_layout)
        
        # Query input
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("검색어를 입력하세요...")
        self.query_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.query_input)
        
        # Search button
        self.search_btn = QPushButton("검색")
        self.search_btn.setProperty("class", "search-btn")
        self.search_btn.clicked.connect(self._on_search)
        layout.addWidget(self.search_btn)
        
        layout.addStretch()
        
        # History (placeholder)
        history_label = QLabel("최근 검색")
        history_label.setStyleSheet("color: #666680; font-size: 12px; margin-top: 20px;")
        layout.addWidget(history_label)
    
    def _on_search(self):
        """Handle search request."""
        query = self.query_input.text().strip()
        mode = self.mode_combo.currentText()
        if query:
            self.search_requested.emit(query, mode)


# =============================================================================
# Search Page (Combined 3-Panel)
# =============================================================================

class SearchPage(QWidget if PYQT6_AVAILABLE else object):
    """Main search page with 3-panel layout."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet(SEARCH_PAGE_STYLE)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Left panel (Results)
        self.left_panel = LeftPanel()
        layout.addWidget(self.left_panel)
        
        # Center panel (Evidence)
        self.center_panel = CenterPanel()
        layout.addWidget(self.center_panel, 1)  # Stretch factor 1
        
        # Right panel (Query)
        self.right_panel = RightPanel()
        layout.addWidget(self.right_panel)
        
        # Connect signals
        self.right_panel.search_requested.connect(self._on_search)
    
    def _on_search(self, query: str, mode: str):
        """Handle search request."""
        # TODO: Connect to actual search engine
        print(f"Search: '{query}' in mode {mode}")
        
        # Demo results
        demo_results = [
            {"filename": "Q4_예산계획.xlsx", "path": "/Users/docs/Q4_예산계획.xlsx", "score": 0.95, "content_indexed": True},
            {"filename": "프로젝트_현황.pptx", "path": "/Users/docs/프로젝트_현황.pptx", "score": 0.82, "content_indexed": True},
            {"filename": "계약서_v2.docx", "path": "/Users/docs/계약서_v2.docx", "score": 0.75, "content_indexed": True},
        ]
        self.left_panel.set_results(demo_results)
        
        # Demo evidence
        demo_evidences = [
            {"snippet": "Q4 예산 계획에 따르면 마케팅 부서의 예산은 전년 대비 15% 증가하였습니다.", "location": {"sheet": "요약"}, "score": 0.9},
            {"snippet": "신규 프로젝트 런칭을 위한 예산 배분이 필요합니다.", "location": {"sheet": "상세"}, "score": 0.7},
        ]
        self.center_panel.set_evidences("Q4_예산계획.xlsx", demo_evidences)


__all__ = [
    "SearchPage",
    "LeftPanel",
    "CenterPanel",
    "RightPanel",
    "ResultItem",
    "EvidenceCard",
]
