"""
Local Finder X v2.0 - Indexing Page

Folder selection and indexing controls.
"""

from typing import Optional, List

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QFrame, QTreeWidget, QTreeWidgetItem,
        QProgressBar, QCheckBox, QFileDialog, QGroupBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QThread
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object
    pyqtSignal = lambda *args: None
    QThread = object


INDEXING_PAGE_STYLE = """
QFrame.section {
    background-color: #1e1e32;
    border-radius: 10px;
    padding: 15px;
}

QPushButton.primary {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton.primary:hover {
    background-color: #7c7ff2;
}

QPushButton.secondary {
    background-color: #3d3d5c;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}

QPushButton.secondary:hover {
    background-color: #4d4d6c;
}

QTreeWidget {
    background-color: #252540;
    border: 1px solid #3d3d5c;
    border-radius: 8px;
    color: #ffffff;
}

QTreeWidget::item {
    padding: 8px;
}

QTreeWidget::item:selected {
    background-color: #3d3d66;
}

QProgressBar {
    background-color: #252540;
    border-radius: 5px;
    height: 10px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #6366f1;
    border-radius: 5px;
}

QCheckBox {
    color: #ccccdd;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3d3d5c;
    background-color: #252540;
}

QCheckBox::indicator:checked {
    background-color: #6366f1;
    border-color: #6366f1;
}
"""


class IndexingPage(QWidget if PYQT6_AVAILABLE else object):
    """Indexing configuration and control page."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet(INDEXING_PAGE_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("인덱싱 설정")
        header.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")
        layout.addWidget(header)
        
        desc = QLabel("검색할 폴더를 선택하고 인덱싱을 시작하세요.")
        desc.setStyleSheet("color: #888899; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # File type filters
        filter_section = QFrame()
        filter_section.setProperty("class", "section")
        filter_layout = QVBoxLayout(filter_section)
        
        filter_label = QLabel("파일 유형")
        filter_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        filter_layout.addWidget(filter_label)
        
        filter_grid = QHBoxLayout()
        self.chk_docx = QCheckBox("Word (.docx)")
        self.chk_docx.setChecked(True)
        self.chk_xlsx = QCheckBox("Excel (.xlsx)")
        self.chk_xlsx.setChecked(True)
        self.chk_pptx = QCheckBox("PowerPoint (.pptx)")
        self.chk_pptx.setChecked(True)
        self.chk_pdf = QCheckBox("PDF (.pdf)")
        self.chk_pdf.setChecked(True)
        self.chk_md = QCheckBox("Markdown (.md)")
        self.chk_md.setChecked(True)
        
        filter_grid.addWidget(self.chk_docx)
        filter_grid.addWidget(self.chk_xlsx)
        filter_grid.addWidget(self.chk_pptx)
        filter_grid.addWidget(self.chk_pdf)
        filter_grid.addWidget(self.chk_md)
        filter_grid.addStretch()
        filter_layout.addLayout(filter_grid)
        
        layout.addWidget(filter_section)
        
        # Folder selection
        folder_section = QFrame()
        folder_section.setProperty("class", "section")
        folder_layout = QVBoxLayout(folder_section)
        
        folder_header = QHBoxLayout()
        folder_label = QLabel("검색 폴더")
        folder_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        folder_header.addWidget(folder_label)
        folder_header.addStretch()
        
        self.add_folder_btn = QPushButton("+ 폴더 추가")
        self.add_folder_btn.setProperty("class", "secondary")
        self.add_folder_btn.clicked.connect(self._add_folder)
        folder_header.addWidget(self.add_folder_btn)
        
        folder_layout.addLayout(folder_header)
        
        # Folder tree
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels(["폴더 경로", "상태"])
        self.folder_tree.setMinimumHeight(200)
        folder_layout.addWidget(self.folder_tree)
        
        layout.addWidget(folder_section)
        
        # Progress section
        progress_section = QFrame()
        progress_section.setProperty("class", "section")
        progress_layout = QVBoxLayout(progress_section)
        
        progress_header = QHBoxLayout()
        self.progress_label = QLabel("인덱싱 대기 중")
        self.progress_label.setStyleSheet("color: #ffffff; font-size: 14px;")
        progress_header.addWidget(self.progress_label)
        progress_header.addStretch()
        
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet("color: #6366f1; font-size: 14px;")
        progress_header.addWidget(self.progress_percent)
        
        progress_layout.addLayout(progress_header)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("color: #666680; font-size: 11px; margin-top: 5px;")
        progress_layout.addWidget(self.current_file_label)
        
        layout.addWidget(progress_section)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.clear_btn = QPushButton("인덱스 초기화")
        self.clear_btn.setProperty("class", "secondary")
        self.clear_btn.clicked.connect(self._clear_index)
        action_layout.addWidget(self.clear_btn)
        
        self.start_btn = QPushButton("인덱싱 시작")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.clicked.connect(self._start_indexing)
        action_layout.addWidget(self.start_btn)
        
        layout.addLayout(action_layout)
        layout.addStretch()
        
        # State
        self.folders: List[str] = []
        self.is_indexing = False
    
    def _add_folder(self):
        """Open folder dialog and add folder."""
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder and folder not in self.folders:
            self.folders.append(folder)
            item = QTreeWidgetItem([folder, "대기"])
            self.folder_tree.addTopLevelItem(item)
    
    def _start_indexing(self):
        """Start the indexing process."""
        if self.is_indexing:
            return
        
        if not self.folders:
            return
        
        self.is_indexing = True
        self.start_btn.setText("인덱싱 중...")
        self.start_btn.setEnabled(False)
        self.progress_label.setText("인덱싱 진행 중...")
        
        # TODO: Connect to actual indexing orchestrator
        # Demo progress
        self.progress_bar.setValue(50)
        self.progress_percent.setText("50%")
        self.current_file_label.setText("처리 중: /Users/docs/example.docx")
    
    def _clear_index(self):
        """Clear the index."""
        # TODO: Connect to actual clear function
        self.folder_tree.clear()
        self.folders.clear()
        self.progress_bar.setValue(0)
        self.progress_percent.setText("0%")
        self.progress_label.setText("인덱스가 초기화되었습니다")


__all__ = ["IndexingPage"]
