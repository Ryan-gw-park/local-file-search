"""
Local Finder X v2.0 - Indexing Page (Enhanced)

Folder tree with checkboxes and file type filters.
Based on PRD Section 4.1 specifications.

Sprint 7: F035-F038 Implementation
"""

from typing import Optional, List, Set, Dict
from pathlib import Path
import os

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QFrame, QTreeView, QTreeWidget, QTreeWidgetItem,
        QProgressBar, QCheckBox, QFileDialog, QHeaderView,
        QAbstractItemView, QSplitter
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QThread, QDir, QModelIndex
    from PyQt6.QtGui import QFileSystemModel, QStandardItemModel, QStandardItem
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object
    pyqtSignal = lambda *args: None
    QThread = object


# =============================================================================
# Styles
# =============================================================================

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

QPushButton.primary:disabled {
    background-color: #4a4a6a;
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

QTreeView {
    background-color: #252540;
    border: 1px solid #3d3d5c;
    border-radius: 8px;
    color: #ffffff;
    outline: none;
}

QTreeView::item {
    padding: 6px 4px;
    border-radius: 4px;
}

QTreeView::item:selected {
    background-color: #3d3d66;
}

QTreeView::item:hover {
    background-color: #2d2d44;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    image: url(none);
    border-image: none;
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings {
    image: url(none);
    border-image: none;
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

QCheckBox::indicator:indeterminate {
    background-color: #4a4a8a;
    border-color: #6366f1;
}

QLabel.summary {
    color: #aaaacc;
    font-size: 12px;
    padding: 8px 0;
}
"""


# =============================================================================
# Checkable Folder Tree Model
# =============================================================================

class CheckableFolderModel(QStandardItemModel if PYQT6_AVAILABLE else object):
    """
    Custom model for folder tree with checkboxes.
    Supports tristate (partial selection) for parent folders.
    """
    
    if PYQT6_AVAILABLE:
        selection_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setHorizontalHeaderLabels(["폴더", "파일 수"])
        self._checked_paths: Set[str] = set()
        self._file_counts: Dict[str, tuple] = {}  # path -> (total, content)
    
    def populate_from_path(self, root_path: str, max_depth: int = 3):
        """Populate tree from a root path."""
        self.clear()
        self.setHorizontalHeaderLabels(["폴더", "파일 수"])
        
        root = Path(root_path)
        if not root.exists():
            return
        
        root_item = self._create_folder_item(root_path, root.name)
        self.appendRow([root_item, QStandardItem("")])
        
        self._populate_children(root_item, root, 0, max_depth)
    
    def _create_folder_item(self, path: str, name: str) -> QStandardItem:
        """Create a checkable folder item."""
        item = QStandardItem(f"📁 {name}")
        item.setCheckable(True)
        item.setCheckState(Qt.CheckState.Unchecked)
        item.setData(path, Qt.ItemDataRole.UserRole)
        return item
    
    def _populate_children(self, parent_item: QStandardItem, parent_path: Path, depth: int, max_depth: int):
        """Recursively populate child folders."""
        if depth >= max_depth:
            return
        
        try:
            for child in sorted(parent_path.iterdir()):
                if child.is_dir() and not child.name.startswith('.'):
                    child_item = self._create_folder_item(str(child), child.name)
                    count_item = QStandardItem("")
                    parent_item.appendRow([child_item, count_item])
                    
                    self._populate_children(child_item, child, depth + 1, max_depth)
        except PermissionError:
            pass
    
    def get_checked_paths(self) -> List[str]:
        """Get all checked folder paths."""
        paths = []
        self._collect_checked(self.invisibleRootItem(), paths)
        return paths
    
    def _collect_checked(self, parent: QStandardItem, paths: List[str]):
        """Recursively collect checked paths."""
        for row in range(parent.rowCount()):
            item = parent.child(row, 0)
            if item:
                if item.checkState() == Qt.CheckState.Checked:
                    path = item.data(Qt.ItemDataRole.UserRole)
                    if path:
                        paths.append(path)
                self._collect_checked(item, paths)
    
    def handle_item_changed(self, item: QStandardItem):
        """Handle check state changes with parent/child propagation."""
        if not item.isCheckable():
            return
        
        state = item.checkState()
        
        # Propagate to children
        self._set_children_state(item, state)
        
        # Update parent state
        parent = item.parent()
        if parent:
            self._update_parent_state(parent)
        
        self.selection_changed.emit()
    
    def _set_children_state(self, parent: QStandardItem, state: Qt.CheckState):
        """Set all children to the same state."""
        for row in range(parent.rowCount()):
            child = parent.child(row, 0)
            if child and child.isCheckable():
                child.setCheckState(state)
                self._set_children_state(child, state)
    
    def _update_parent_state(self, parent: QStandardItem):
        """Update parent state based on children (tristate logic)."""
        if not parent:
            return
        
        checked_count = 0
        partial_count = 0
        total = parent.rowCount()
        
        for row in range(total):
            child = parent.child(row, 0)
            if child:
                state = child.checkState()
                if state == Qt.CheckState.Checked:
                    checked_count += 1
                elif state == Qt.CheckState.PartiallyChecked:
                    partial_count += 1
        
        if checked_count == total:
            parent.setCheckState(Qt.CheckState.Checked)
        elif checked_count > 0 or partial_count > 0:
            parent.setCheckState(Qt.CheckState.PartiallyChecked)
        else:
            parent.setCheckState(Qt.CheckState.Unchecked)
        
        # Propagate up
        grandparent = parent.parent()
        if grandparent:
            self._update_parent_state(grandparent)


# =============================================================================
# Indexing Page (Enhanced)
# =============================================================================

class IndexingPage(QWidget if PYQT6_AVAILABLE else object):
    """
    Indexing configuration and control page.
    
    PRD Section 4.1 compliance:
    - 파일 타입 필터: Office/PDF/MD + 기타 파일(메타데이터만)
    - 폴더 트리: 체크박스 다중 선택
    - 파일 수 실시간 표시
    """
    
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
        
        # =========== File Type Filters (F036) ===========
        filter_section = QFrame()
        filter_section.setProperty("class", "section")
        filter_layout = QVBoxLayout(filter_section)
        
        filter_label = QLabel("파일 유형")
        filter_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        filter_layout.addWidget(filter_label)
        
        # Content-indexed types
        filter_row1 = QHBoxLayout()
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
        
        filter_row1.addWidget(self.chk_docx)
        filter_row1.addWidget(self.chk_xlsx)
        filter_row1.addWidget(self.chk_pptx)
        filter_row1.addWidget(self.chk_pdf)
        filter_row1.addWidget(self.chk_md)
        filter_row1.addStretch()
        filter_layout.addLayout(filter_row1)
        
        # Metadata-only filter (F036 - NEW)
        filter_row2 = QHBoxLayout()
        self.chk_metadata_only = QCheckBox("기타 파일 (메타데이터만)")
        self.chk_metadata_only.setChecked(False)
        self.chk_metadata_only.setToolTip("지원 포맷 외 파일의 파일명/경로만 인덱싱 (.zip, .psd, .hwp 등)")
        filter_row2.addWidget(self.chk_metadata_only)
        filter_row2.addStretch()
        filter_layout.addLayout(filter_row2)
        
        layout.addWidget(filter_section)
        
        # =========== Folder Tree (F035) ===========
        folder_section = QFrame()
        folder_section.setProperty("class", "section")
        folder_layout = QVBoxLayout(folder_section)
        
        folder_header = QHBoxLayout()
        folder_label = QLabel("검색 폴더")
        folder_label.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        folder_header.addWidget(folder_label)
        folder_header.addStretch()
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setProperty("class", "secondary")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.setToolTip("폴더 목록 새로고침")
        self.refresh_btn.clicked.connect(self._refresh_tree)
        folder_header.addWidget(self.refresh_btn)
        
        self.add_folder_btn = QPushButton("+ 폴더 추가")
        self.add_folder_btn.setProperty("class", "secondary")
        self.add_folder_btn.clicked.connect(self._add_root_folder)
        folder_header.addWidget(self.add_folder_btn)
        
        folder_layout.addLayout(folder_header)
        
        # Folder tree view with checkboxes
        self.folder_model = CheckableFolderModel()
        self.folder_tree = QTreeView()
        self.folder_tree.setModel(self.folder_model)
        self.folder_tree.setMinimumHeight(250)
        self.folder_tree.setHeaderHidden(False)
        self.folder_tree.setAnimated(True)
        self.folder_tree.setIndentation(20)
        self.folder_tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        # Handle check changes
        self.folder_model.itemChanged.connect(self.folder_model.handle_item_changed)
        self.folder_model.selection_changed.connect(self._update_summary)
        
        folder_layout.addWidget(self.folder_tree)
        
        # Summary label (F037)
        self.summary_label = QLabel("선택됨: 0개 폴더 | 총 파일: 0개")
        self.summary_label.setProperty("class", "summary")
        folder_layout.addWidget(self.summary_label)
        
        layout.addWidget(folder_section)
        
        # =========== Progress Section ===========
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
        
        # =========== Action Buttons ===========
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
        self.is_indexing = False
        
        # Initialize with home directory
        self._init_default_tree()
    
    def _init_default_tree(self):
        """Initialize tree with home directory."""
        home = str(Path.home())
        self.folder_model.populate_from_path(home, max_depth=2)
        self.folder_tree.expandToDepth(0)
    
    def _add_root_folder(self):
        """Add a custom root folder."""
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            self.folder_model.populate_from_path(folder, max_depth=3)
            self.folder_tree.expandToDepth(1)
    
    def _refresh_tree(self):
        """Refresh the folder tree."""
        self._init_default_tree()
        self._update_summary()
    
    def _update_summary(self):
        """Update the summary label with selection info (F037)."""
        checked_paths = self.folder_model.get_checked_paths()
        folder_count = len(checked_paths)
        
        # Count files in selected folders
        total_files = 0
        content_files = 0
        
        content_extensions = {'.docx', '.xlsx', '.pptx', '.pdf', '.md', '.txt'}
        
        for folder_path in checked_paths:
            try:
                for root, dirs, files in os.walk(folder_path):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    for f in files:
                        if not f.startswith('.') and not f.startswith('~$'):
                            total_files += 1
                            ext = Path(f).suffix.lower()
                            if ext in content_extensions:
                                content_files += 1
            except (PermissionError, OSError):
                pass
        
        self.summary_label.setText(
            f"선택됨: {folder_count}개 폴더 | 총 파일: {total_files}개 (콘텐츠: {content_files}개)"
        )
    
    def _start_indexing(self):
        """Start the indexing process."""
        if self.is_indexing:
            return
        
        checked_paths = self.folder_model.get_checked_paths()
        if not checked_paths:
            self.progress_label.setText("폴더를 선택해주세요")
            return
        
        self.is_indexing = True
        self.start_btn.setText("인덱싱 중...")
        self.start_btn.setEnabled(False)
        self.progress_label.setText("인덱싱 진행 중...")
        
        # Get filter options
        extensions = []
        if self.chk_docx.isChecked():
            extensions.append('.docx')
        if self.chk_xlsx.isChecked():
            extensions.append('.xlsx')
        if self.chk_pptx.isChecked():
            extensions.append('.pptx')
        if self.chk_pdf.isChecked():
            extensions.append('.pdf')
        if self.chk_md.isChecked():
            extensions.extend(['.md', '.txt'])
        
        include_metadata_only = self.chk_metadata_only.isChecked()
        
        # TODO: Connect to actual indexing orchestrator with:
        # - checked_paths (folders to index)
        # - extensions (content-indexed types)
        # - include_metadata_only (other files)
        
        # Demo progress for now
        self.progress_bar.setValue(50)
        self.progress_percent.setText("50%")
        self.current_file_label.setText(f"처리 중: {checked_paths[0] if checked_paths else ''}")
    
    def _clear_index(self):
        """Clear the index."""
        self.folder_model.clear()
        self._init_default_tree()
        self.progress_bar.setValue(0)
        self.progress_percent.setText("0%")
        self.progress_label.setText("인덱스가 초기화되었습니다")
        self.summary_label.setText("선택됨: 0개 폴더 | 총 파일: 0개")
        
        self.is_indexing = False
        self.start_btn.setText("인덱싱 시작")
        self.start_btn.setEnabled(True)


__all__ = ["IndexingPage", "CheckableFolderModel"]
