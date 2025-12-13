"""
Local Finder X v2.0 - Indexing Page (Pro Mode UI)

Simple folder list with Pro mode features.
F039: Simplified Folder List + F040: Pro Mode UI
"""

from typing import List
from pathlib import Path
import time

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QFrame, QListWidget, QListWidgetItem,
        QProgressBar, QCheckBox, QFileDialog, QMessageBox,
        QScrollArea, QSizePolicy
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QTimer
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QWidget = object
    pyqtSignal = lambda *args: None


# =============================================================================
# Styles
# =============================================================================

INDEXING_PAGE_STYLE = """
QFrame.section {
    background-color: #1e1e32;
    border-radius: 10px;
    padding: 12px;
}

QFrame.pro-section {
    background-color: #1e1e32;
    border-radius: 10px;
    border: 1px solid #6366f1;
    padding: 12px;
}

QPushButton.primary {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
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
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
}

QPushButton.secondary:hover {
    background-color: #4d4d6c;
}

QPushButton.secondary:disabled {
    background-color: #2d2d44;
    color: #666680;
}

QListWidget {
    background-color: #252540;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    color: #ffffff;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: #2d2d44;
}

QListWidget::item:selected {
    background-color: #3d3d66;
}

QProgressBar {
    background-color: #252540;
    border-radius: 4px;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #6366f1;
    border-radius: 4px;
}

QCheckBox {
    color: #ccccdd;
    spacing: 6px;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid #3d3d5c;
    background-color: #252540;
}

QCheckBox::indicator:checked {
    background-color: #6366f1;
    border-color: #6366f1;
}

QCheckBox:disabled {
    color: #666680;
}

QScrollArea {
    border: none;
    background-color: transparent;
}
"""


# =============================================================================
# Indexing Page (Pro Mode UI)
# =============================================================================

class IndexingPage(QWidget if PYQT6_AVAILABLE else object):
    """Indexing configuration page with Pro mode features."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet(INDEXING_PAGE_STYLE)
        
        # State
        self.folders: List[str] = []
        self.is_indexing = False
        self.is_pro = False
        self.indexing_start_time = 0
        self.processed_files = 0
        self.total_files = 0
        
        # Main layout with scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("인덱싱 설정")
        header.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: bold;")
        layout.addWidget(header)
        
        desc = QLabel("검색할 폴더를 추가하고 인덱싱을 시작하세요.")
        desc.setStyleSheet("color: #888899; font-size: 13px;")
        layout.addWidget(desc)
        
        # =========== File Type Filters ===========
        filter_section = QFrame()
        filter_section.setProperty("class", "section")
        filter_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        filter_layout = QVBoxLayout(filter_section)
        filter_layout.setSpacing(8)
        
        filter_label = QLabel("📁 파일 유형")
        filter_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        filter_layout.addWidget(filter_label)
        
        # Row 1: Local file types
        filter_row1 = QHBoxLayout()
        filter_row1.setSpacing(16)
        self.chk_docx = QCheckBox("Word")
        self.chk_docx.setChecked(True)
        self.chk_xlsx = QCheckBox("Excel")
        self.chk_xlsx.setChecked(True)
        self.chk_pptx = QCheckBox("PowerPoint")
        self.chk_pptx.setChecked(True)
        self.chk_pdf = QCheckBox("PDF")
        self.chk_pdf.setChecked(True)
        self.chk_md = QCheckBox("Markdown")
        self.chk_md.setChecked(True)
        
        filter_row1.addWidget(self.chk_docx)
        filter_row1.addWidget(self.chk_xlsx)
        filter_row1.addWidget(self.chk_pptx)
        filter_row1.addWidget(self.chk_pdf)
        filter_row1.addWidget(self.chk_md)
        filter_row1.addStretch()
        filter_layout.addLayout(filter_row1)
        
        # Row 2: Metadata + Outlook
        filter_row2 = QHBoxLayout()
        filter_row2.setSpacing(16)
        self.chk_metadata_only = QCheckBox("기타 파일 (메타데이터)")
        self.chk_metadata_only.setChecked(False)
        self.chk_outlook = QCheckBox("🔒 Outlook 이메일 [PRO]")
        self.chk_outlook.setChecked(False)
        self.chk_outlook.setEnabled(self.is_pro)
        self.chk_outlook.clicked.connect(self._on_outlook_clicked)
        
        filter_row2.addWidget(self.chk_metadata_only)
        filter_row2.addWidget(self.chk_outlook)
        filter_row2.addStretch()
        filter_layout.addLayout(filter_row2)
        
        layout.addWidget(filter_section)
        
        # =========== Folder List ===========
        folder_section = QFrame()
        folder_section.setProperty("class", "section")
        folder_layout = QVBoxLayout(folder_section)
        folder_layout.setSpacing(8)
        
        folder_header = QHBoxLayout()
        folder_label = QLabel("📂 검색 폴더")
        folder_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        folder_header.addWidget(folder_label)
        folder_header.addStretch()
        
        self.add_folder_btn = QPushButton("+ 추가")
        self.add_folder_btn.setProperty("class", "secondary")
        self.add_folder_btn.clicked.connect(self._add_folder)
        folder_header.addWidget(self.add_folder_btn)
        
        self.remove_btn = QPushButton("- 삭제")
        self.remove_btn.setProperty("class", "secondary")
        self.remove_btn.clicked.connect(self._remove_selected_folder)
        folder_header.addWidget(self.remove_btn)
        
        folder_layout.addLayout(folder_header)
        
        self.folder_list = QListWidget()
        self.folder_list.setMinimumHeight(80)
        self.folder_list.setMaximumHeight(120)
        folder_layout.addWidget(self.folder_list)
        
        self.summary_label = QLabel("선택됨: 0개 폴더")
        self.summary_label.setStyleSheet("color: #888899; font-size: 11px;")
        folder_layout.addWidget(self.summary_label)
        
        layout.addWidget(folder_section)
        
        # =========== Cloud Section (Pro) ===========
        cloud_section = QFrame()
        cloud_section.setProperty("class", "pro-section")
        cloud_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        cloud_layout = QVBoxLayout(cloud_section)
        cloud_layout.setSpacing(6)
        
        cloud_header = QHBoxLayout()
        cloud_label = QLabel("☁️ 클라우드 연동 [PRO]")
        cloud_label.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: bold;")
        cloud_header.addWidget(cloud_label)
        cloud_header.addStretch()
        
        self.onedrive_btn = QPushButton("🔒 OneDrive 연결")
        self.onedrive_btn.setProperty("class", "secondary")
        self.onedrive_btn.setEnabled(self.is_pro)
        self.onedrive_btn.clicked.connect(self._on_cloud_clicked)
        cloud_header.addWidget(self.onedrive_btn)
        cloud_layout.addLayout(cloud_header)
        
        if not self.is_pro:
            upgrade_hint = QLabel("💡 Pro 라이선스로 클라우드 파일 검색 가능")
            upgrade_hint.setStyleSheet("color: #888899; font-size: 11px;")
            cloud_layout.addWidget(upgrade_hint)
        
        layout.addWidget(cloud_section)
        
        # =========== Progress Section ===========
        progress_section = QFrame()
        progress_section.setProperty("class", "section")
        progress_section.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        progress_layout = QVBoxLayout(progress_section)
        progress_layout.setSpacing(6)
        
        progress_header = QHBoxLayout()
        self.progress_label = QLabel("인덱싱 대기 중")
        self.progress_label.setStyleSheet("color: #ffffff; font-size: 13px;")
        progress_header.addWidget(self.progress_label)
        progress_header.addStretch()
        self.progress_percent = QLabel("0%")
        self.progress_percent.setStyleSheet("color: #6366f1; font-size: 13px; font-weight: bold;")
        progress_header.addWidget(self.progress_percent)
        progress_layout.addLayout(progress_header)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        detail_row = QHBoxLayout()
        self.current_file_label = QLabel("")
        self.current_file_label.setStyleSheet("color: #666680; font-size: 11px;")
        detail_row.addWidget(self.current_file_label)
        detail_row.addStretch()
        self.elapsed_label = QLabel("")
        self.elapsed_label.setStyleSheet("color: #666680; font-size: 11px;")
        detail_row.addWidget(self.elapsed_label)
        progress_layout.addLayout(detail_row)
        
        self.nudge_label = QLabel("")
        self.nudge_label.setStyleSheet("color: #88aa88; font-size: 11px;")
        progress_layout.addWidget(self.nudge_label)
        
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
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)
        
        # Timer for progress
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress_display)
        
        self._update_list_display()
    
    def _on_outlook_clicked(self):
        if not self.is_pro:
            self.chk_outlook.setChecked(False)
            QMessageBox.information(self, "Pro 기능", "Outlook 이메일 검색은 Pro 라이선스가 필요합니다.")
    
    def _on_cloud_clicked(self):
        if not self.is_pro:
            QMessageBox.information(self, "Pro 기능", "클라우드 연동은 Pro 라이선스가 필요합니다.")
    
    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder and folder not in self.folders:
            self.folders.append(folder)
            self._update_list_display()
    
    def _remove_selected_folder(self):
        current_item = self.folder_list.currentItem()
        if current_item:
            path = current_item.data(Qt.ItemDataRole.UserRole)
            if path and path in self.folders:
                self.folders.remove(path)
                self._update_list_display()
    
    def _update_list_display(self):
        self.folder_list.clear()
        if not self.folders:
            item = QListWidgetItem("폴더를 추가하세요")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            self.folder_list.addItem(item)
        else:
            for path in self.folders:
                home = str(Path.home())
                display = "~" + path[len(home):] if path.startswith(home) else path
                item = QListWidgetItem(f"📁 {display}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                item.setToolTip(path)
                self.folder_list.addItem(item)
        self.summary_label.setText(f"선택됨: {len(self.folders)}개 폴더")
    
    def _start_indexing(self):
        if self.is_indexing:
            return
        if not self.folders:
            self.progress_label.setText("폴더를 추가해주세요")
            return
        
        self.is_indexing = True
        self.indexing_start_time = time.time()
        self.processed_files = 0
        self.total_files = 100
        
        self.start_btn.setText("인덱싱 중...")
        self.start_btn.setEnabled(False)
        self.progress_label.setText("인덱싱 진행 중...")
        self.nudge_label.setText("💡 인덱싱 중에도 검색 가능")
        
        self.progress_timer.start(500)
        self._demo_progress()
    
    def _demo_progress(self):
        self.processed_files += 10
        percent = min(100, int(self.processed_files / self.total_files * 100))
        self.progress_bar.setValue(percent)
        self.progress_percent.setText(f"{percent}%")
        
        if percent < 100:
            QTimer.singleShot(500, self._demo_progress)
        else:
            self._on_indexing_complete()
    
    def _update_progress_display(self):
        if not self.is_indexing:
            return
        elapsed = int(time.time() - self.indexing_start_time)
        self.elapsed_label.setText(f"경과: {elapsed}초")
        self.current_file_label.setText(f"처리: {self.processed_files}/{self.total_files}")
    
    def _on_indexing_complete(self):
        self.is_indexing = False
        self.progress_timer.stop()
        self.start_btn.setText("인덱싱 시작")
        self.start_btn.setEnabled(True)
        self.progress_label.setText("✅ 인덱싱 완료!")
        self.nudge_label.setText("검색 탭에서 파일을 검색하세요")
    
    def _clear_index(self):
        self.folders.clear()
        self._update_list_display()
        self.progress_bar.setValue(0)
        self.progress_percent.setText("0%")
        self.progress_label.setText("인덱스 초기화됨")
        self.current_file_label.setText("")
        self.elapsed_label.setText("")
        self.nudge_label.setText("")
        self.is_indexing = False
        self.start_btn.setText("인덱싱 시작")
        self.start_btn.setEnabled(True)


__all__ = ["IndexingPage"]
