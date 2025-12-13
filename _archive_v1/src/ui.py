import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QFileDialog, QLabel, QProgressBar, QSplitter,
                             QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
                             QTabWidget, QMessageBox, QProgressDialog, QCheckBox,
                             QTreeWidget, QTreeWidgetItem, QComboBox, QGroupBox,
                             QScrollArea, QRadioButton, QButtonGroup, QListWidget,
                             QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QDesktopServices, QColor, QFont
from indexer import FileIndexer
from search_engine import SearchEngine
from config import IndexingSettings, load_indexing_settings, save_indexing_settings
from datetime import datetime

def get_user_folders():
    """Get common user folders to index."""
    user_home = Path.home()
    folders = []
    
    # Common Windows user folders
    common_folders = [
        user_home / "Documents",
        user_home / "Desktop",
        user_home / "Downloads",
    ]
    
    for folder in common_folders:
        if folder.exists() and folder.is_dir():
            folders.append(str(folder))
    
    return folders


class IndexingThread(QThread):
    progress = pyqtSignal(str, int)  # Progress message, percentage (0-100)
    finished = pyqtSignal(str, int, int, list)  # message, indexed_count, skipped_count, errors

    def __init__(self, folder_paths, model_name, include_outlook=False, connector=None, settings=None):
        super().__init__()
        self.folder_paths = folder_paths if isinstance(folder_paths, list) else [folder_paths]
        self.model_name = model_name
        self.include_outlook = include_outlook
        self.connector = connector
        self.settings = settings  # IndexingSettings
        self.current_folder_index = 0
        self.total_folders = len(self.folder_paths)

    def _make_progress_callback(self, folder_index):
        """Create a progress callback for a specific folder."""
        def callback(filename, file_percent, processed, total):
            # Simple approach: just pass file counts, not percentage
            # Format: "PROGRESS:processed:total:folder_index:total_folders"
            progress_info = f"PROGRESS:{processed}:{total}:{folder_index}:{self.total_folders}"
            self.progress.emit(progress_info, 0)  # 0 is dummy, we'll calculate in UI
        return callback

    def run(self):
        # Initialize indexer in the thread to avoid blocking
        indexer = FileIndexer(model_name=self.model_name)
        
        total_indexed = 0
        total_skipped = 0
        all_errors = []
        
        # Priority: Connector Indexing (if provided)
        if self.connector:
            self.progress.emit(f"Connecting to: {self.connector.name}", 5)
            result = indexer.index_connector(self.connector)
            total_indexed += result["indexed"]
            total_skipped += result["skipped"]
            all_errors.extend(result["errors"])
        
        # Folder Indexing with file-level progress
        for i, folder_path in enumerate(self.folder_paths):
            folder_name = os.path.basename(folder_path) if folder_path else "Unknown"
            base_percent = int((i / max(len(self.folder_paths), 1)) * 90)
            self.progress.emit(f"📂 {folder_name} (scanning...)", base_percent)
            
            # Create progress callback for this folder
            callback = self._make_progress_callback(i)
            result = indexer.index_directory(folder_path, progress_callback=callback, settings=self.settings)
            total_indexed += result["indexed"]
            total_skipped += result["skipped"]
            all_errors.extend(result["errors"])
            
        if self.include_outlook:
            self.progress.emit("📧 Outlook (Inbox & Sent Items)", 92)
            print(f"[DEBUG] Starting Outlook indexing, include_outlook={self.include_outlook}")
            result = indexer.index_outlook()
            print(f"[DEBUG] Outlook indexing result: indexed={result['indexed']}, skipped={result['skipped']}, errors={result['errors']}")
            total_indexed += result["indexed"]
            total_skipped += result["skipped"]
            all_errors.extend(result["errors"])
        else:
            print(f"[DEBUG] Outlook indexing skipped, include_outlook={self.include_outlook}")
        
        self.progress.emit("✅ Finalizing...", 98)
        
        self.finished.emit(
            f"Indexing complete: {len(self.folder_paths)} folders scanned",
            total_indexed,
            total_skipped,
            all_errors
        )


class ChatWindow(QMainWindow):
    # Phase 1: 3.5. ChatWindow 생성자 수정
    def __init__(self, language="en", config=None, license_manager=None, parent=None):
        super().__init__(parent)
        self.language = language
        self.config = config
        self.license_manager = license_manager

        if language == "kr":
            self.setWindowTitle("로컬 AI 파일 검색")
            self.model_name = "paraphrase-multilingual-MiniLM-L12-v2"
            self.system_prefix = "시스템: "
            self.user_prefix = "나: "
            self.ai_prefix = "AI: "
            self.placeholder = "파일을 찾으려면 질문하세요..."
            self.btn_text = "추가 폴더 색인"
            self.rescan_text = "전체 다시 색인"
            self.send_text = "검색"
            self.headers = ["타입", "파일명", "경로", "관련도", "미리보기"]
        else:
            self.setWindowTitle("Local AI File Search")
            self.model_name = "all-MiniLM-L6-v2"
            self.system_prefix = "System: "
            self.user_prefix = "You: "
            self.ai_prefix = "AI: "
            self.placeholder = "Ask to find files..."
            self.btn_text = "Add Folder"
            self.rescan_text = "Rescan All"
            self.send_text = "Search"
            self.headers = ["Type", "Filename", "Path", "Score", "Preview"]
            
        self.setGeometry(100, 100, 1200, 700)
        
        # Initialize engine
        self.engine = SearchEngine(model_name=self.model_name, language=self.language)
        
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create Tabs
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Search (Explorer Mode)
        self.search_tab = QWidget()
        self.setup_search_tab()
        self.tabs.addTab(self.search_tab, "검색" if language == "kr" else "Search")
        
        # Tab 2: Documents
        self.documents_tab = QWidget()
        self.setup_documents_tab()
        self.tabs.addTab(self.documents_tab, "문서" if language == "kr" else "Documents")
        
        # Tab 3: Network Activity
        self.network_tab = QWidget()
        self.setup_network_tab()
        self.tabs.addTab(self.network_tab, "네트워크 활동" if language == "kr" else "Network Activity")
        
        # Tab 4: (Removed - Cloud Connections merged into Documents tab)
        
        # Tab 5: (Removed - Security Center removed, info shown in About)
        
        # Tab 4: About
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.settings_tab, "About")
        
        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Connect tab change signal to refresh Documents tree when selected
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        # Check if first run and start auto-indexing
        self.check_and_auto_index()

    # Phase 1: 헬퍼 메서드 — Pro 모드 확인
    def _is_pro(self) -> bool:
        """현재 Pro 모드인지 확인"""
        if self.license_manager:
            return self.license_manager.is_pro()
        return False
    
    def _on_tab_changed(self, index):
        """Handle tab change - refresh Documents tree when Documents tab is selected."""
        if index == 1:  # Documents tab is index 1
            self._refresh_documents_tree()

    # Phase 1: 3.7. Pro 차단 팝업 구현
    def show_pro_required_dialog(self):
        """Free 모드에서 Pro 기능 클릭 시 표시되는 안내 팝업"""
        msg = QMessageBox(self)
        if self.language == "kr":
            msg.setWindowTitle("Pro 기능 안내")
            msg.setText(
                "이 기능은 Pro 버전에서만 사용 가능합니다.\n"
                "검색 품질은 Free/Pro 동일하며,\n"
                "Pro는 검색 가능한 데이터 소스 범위가 확장됩니다.\n\n"
                "테스트 모드에서는 APP_MODE=pro 로 실행하여 검증할 수 있습니다."
            )
        else:
            msg.setWindowTitle("Pro Feature")
            msg.setText(
                "This feature is only available in the Pro version.\n"
                "Search quality is identical for Free/Pro,\n"
                "Pro extends the range of searchable data sources.\n\n"
                "In test mode, run with APP_MODE=pro to verify."
            )
        msg.exec()

    # Phase 1: 3.6. Pro 기능 버튼 핸들러 (Outlook 인덱싱)
    def handle_index_outlook(self):
        """Outlook 인덱싱 버튼 클릭 핸들러"""
        if self.license_manager and not self.license_manager.has_feature("outlook_indexing"):
            self.show_pro_required_dialog()
            return

        # Phase 1에서는 실제 Outlook 인덱싱을 하지 않고 Mock 처리
        if self.language == "kr":
            QMessageBox.information(
                self,
                "Pro 기능(Mock)",
                "Outlook 인덱싱은 Phase 2에서 실제 구현됩니다."
            )
        else:
            QMessageBox.information(
                self,
                "Pro Feature (Mock)",
                "Outlook indexing will be implemented in Phase 2."
            )

    def setup_search_tab(self):
        layout = QVBoxLayout(self.search_tab)
        
        # Top Bar - simplified with link to Documents tab
        top_layout = QHBoxLayout()
        
        if self.language == "kr":
            self.folder_label = QLabel("📁 문서, 바탕화면, 다운로드 폴더가 자동으로 검색됩니다")
        else:
            self.folder_label = QLabel("📁 Documents, Desktop, Downloads are automatically indexed")
        
        # Button to go to Documents tab for indexing management
        self.go_to_docs_btn = QPushButton("📂 인덱싱 관리" if self.language == "kr" else "📂 Manage Indexing")
        self.go_to_docs_btn.setToolTip("인덱싱 설정은 문서 탭에서 관리합니다" if self.language == "kr" else "Manage indexing settings in Documents tab")
        self.go_to_docs_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))  # Switch to Documents tab
        
        top_layout.addWidget(self.folder_label)
        top_layout.addStretch()
        top_layout.addWidget(self.go_to_docs_btn)
        layout.addLayout(top_layout)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel: File Explorer Table
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(self.headers)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Type
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Filename
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Path
        self.file_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Score
        self.file_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Preview
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.file_table.doubleClicked.connect(self.open_file)
        splitter.addWidget(self.file_table)
        
        # Right Panel: Chat Sidebar
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("검색 결과와 대화 내용이 여기에 표시됩니다.")
        
        # Welcome Message
        if self.language == "kr":
            welcome_msg = (
                "언어 모델이 준비되었습니다. 현재 PC의 오피스 문서(.pptx, .docx, .xlsx, .pdf, .txt) 및 이메일을 검색할 수 있습니다.\n\n"
                "※ 안심하세요: 이 프로그램은 외부 인터넷과 연결되지 않으며, 사용자의 파일 정보는 절대 외부로 유출되지 않습니다."
            )
        else:
            welcome_msg = (
                "Language model ready. You can search Office documents (.pptx, .docx, .xlsx, .pdf, .txt) and Emails on your PC.\n\n"
                "※ Note: This program runs completely offline. Your file information is never sent to external servers."
            )
            
        self.chat_display.append(f"<b>{self.ai_prefix}</b> {welcome_msg}")
        self.chat_display.append("-" * 20)
        
        right_layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.placeholder)
        self.input_field.returnPressed.connect(self.send_message)
        self.send_btn = QPushButton(self.send_text)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        right_layout.addLayout(input_layout)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        
        layout.addWidget(splitter)

    def setup_documents_tab(self):
        """Setup Documents tab with full folder tree and indexing controls."""
        layout = QVBoxLayout(self.documents_tab)
        
        # Header
        header = QLabel("📁 문서 관리" if self.language == "kr" else "📁 Document Management")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # ===== Filter Section (Top) =====
        filter_group = QGroupBox("🔍 인덱싱 필터" if self.language == "kr" else "🔍 Indexing Filters")
        filter_layout = QVBoxLayout(filter_group)
        
        # Row 1: File Type Filter
        type_row = QHBoxLayout()
        type_label = QLabel("파일 형식:" if self.language == "kr" else "File Types:")
        type_row.addWidget(type_label)
        
        self.filter_docx = QCheckBox("Word (.docx)")
        self.filter_docx.setChecked(True)
        type_row.addWidget(self.filter_docx)
        
        self.filter_xlsx = QCheckBox("Excel (.xlsx)")
        self.filter_xlsx.setChecked(True)
        type_row.addWidget(self.filter_xlsx)
        
        self.filter_pptx = QCheckBox("PowerPoint (.pptx)")
        self.filter_pptx.setChecked(True)
        type_row.addWidget(self.filter_pptx)
        
        self.filter_pdf = QCheckBox("PDF (.pdf)")
        self.filter_pdf.setChecked(True)
        type_row.addWidget(self.filter_pdf)
        
        self.filter_txt = QCheckBox("Text (.txt, .md)")
        self.filter_txt.setChecked(True)
        type_row.addWidget(self.filter_txt)
        
        # Email filter - when checked, auto-selects Outlook folders
        self.filter_email = QCheckBox("Email")
        self.filter_email.setChecked(False)
        self.filter_email.toggled.connect(self._on_email_filter_changed)
        type_row.addWidget(self.filter_email)
        
        type_row.addStretch()
        filter_layout.addLayout(type_row)
        
        # Row 2: Date Range Filter
        date_row = QHBoxLayout()
        date_label = QLabel("기간 필터:" if self.language == "kr" else "Date Range:")
        date_row.addWidget(date_label)
        
        from PyQt6.QtWidgets import QDateEdit
        from PyQt6.QtCore import QDate
        
        self.date_filter_enabled = QCheckBox("적용" if self.language == "kr" else "Enable")
        self.date_filter_enabled.setChecked(False)
        date_row.addWidget(self.date_filter_enabled)
        
        date_row.addWidget(QLabel("시작일:" if self.language == "kr" else "From:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addMonths(-6))
        self.date_start.setEnabled(False)
        date_row.addWidget(self.date_start)
        
        date_row.addWidget(QLabel("종료일:" if self.language == "kr" else "To:"))
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setEnabled(False)
        date_row.addWidget(self.date_end)
        
        # Connect date filter checkbox
        self.date_filter_enabled.toggled.connect(self._toggle_date_filter)
        
        date_row.addStretch()
        filter_layout.addLayout(date_row)
        
        # Row 3: Action Buttons (moved to top)
        action_row = QHBoxLayout()
        
        select_all_btn = QPushButton("✅ 전체 선택" if self.language == "kr" else "✅ Select All")
        select_all_btn.clicked.connect(self._select_all_folders)
        action_row.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("⬜ 전체 해제" if self.language == "kr" else "⬜ Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all_folders)
        action_row.addWidget(deselect_all_btn)
        
        # DB Cleanup button
        cleanup_btn = QPushButton("🗑️ DB 정리" if self.language == "kr" else "🗑️ Clean DB")
        cleanup_btn.setToolTip("삭제된 파일의 인덱스를 정리합니다" if self.language == "kr" else "Remove index entries for deleted files")
        cleanup_btn.clicked.connect(self._cleanup_deleted_files)
        action_row.addWidget(cleanup_btn)
        
        action_row.addStretch()
        
        # Indexing button (prominent, at top)
        self.index_btn_docs = QPushButton("🔄 인덱싱 시작" if self.language == "kr" else "🔄 Start Indexing")
        self.index_btn_docs.clicked.connect(self._start_selected_indexing)
        self.index_btn_docs.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px 20px; font-size: 14px;")
        action_row.addWidget(self.index_btn_docs)
        
        filter_layout.addLayout(action_row)
        layout.addWidget(filter_group)
        
        # ===== Indexing Performance Section =====
        perf_group = QGroupBox("⚡ 인덱싱 성능" if self.language == "kr" else "⚡ Indexing Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        # Row 1: Performance Mode dropdown + Parallel Workers
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("성능 모드:" if self.language == "kr" else "Performance Mode:"))
        self.perf_mode_combo = QComboBox()
        self.perf_mode_combo.addItems([
            "🤖 Auto (자동)" if self.language == "kr" else "🤖 Auto (Recommended)",
            "💚 Power Saving (노트북)" if self.language == "kr" else "💚 Power Saving (Laptops)",
            "💙 Balanced (기본)" if self.language == "kr" else "💙 Balanced (Default)",
            "🔥 High Performance (고성능)" if self.language == "kr" else "🔥 High Performance (Desktops)"
        ])
        self.perf_mode_combo.setCurrentIndex(0)  # Auto as default
        self.perf_mode_combo.currentIndexChanged.connect(self._on_perf_mode_changed)
        mode_row.addWidget(self.perf_mode_combo)
        
        mode_row.addSpacing(20)
        
        # Parallel Workers display (read-only)
        mode_row.addWidget(QLabel("병렬 작업자:" if self.language == "kr" else "Parallel Workers:"))
        self.workers_spinbox = QSpinBox()
        self.workers_spinbox.setRange(1, 8)
        self.workers_spinbox.setValue(2)
        self.workers_spinbox.setEnabled(False)  # Read-only
        mode_row.addWidget(self.workers_spinbox)
        
        mode_row.addStretch()
        perf_layout.addLayout(mode_row)
        
        # Row 2: Recommended info label + Apply button
        rec_row = QHBoxLayout()
        self.recommended_label = QLabel("")
        self.recommended_label.setStyleSheet("color: #666; font-style: italic;")
        rec_row.addWidget(self.recommended_label)
        
        rec_row.addStretch()
        
        self.apply_recommended_btn = QPushButton("🔄 권장 설정 적용" if self.language == "kr" else "🔄 Apply Recommended Settings")
        self.apply_recommended_btn.clicked.connect(self._on_apply_recommended)
        rec_row.addWidget(self.apply_recommended_btn)
        
        perf_layout.addLayout(rec_row)
        
        # Row 3: Info text about Auto mode
        info_text = ("💡 Auto는 이 PC의 CPU 코어 수와 메모리 용량을 기준으로 "
                     "인덱싱 속도와 시스템 부하를 자동으로 조절합니다.") if self.language == "kr" else \
                    ("💡 Auto mode automatically adjusts indexing speed and system load "
                     "based on this PC's CPU cores and memory.")
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        perf_layout.addWidget(info_label)
        
        layout.addWidget(perf_group)
        
        # ===== Advanced Indexing Options (Collapsible) =====
        self.advanced_toggle = QPushButton("▶ 고급 인덱싱 옵션" if self.language == "kr" else "▶ Advanced Indexing Options")
        self.advanced_toggle.setFlat(True)
        self.advanced_toggle.setStyleSheet("text-align: left; font-weight: bold; padding: 5px;")
        self.advanced_toggle.clicked.connect(self._toggle_advanced_options)
        layout.addWidget(self.advanced_toggle)
        
        self.advanced_group = QGroupBox()
        self.advanced_group.setVisible(False)  # Collapsed by default
        advanced_layout = QVBoxLayout(self.advanced_group)
        
        # Large File Handling
        large_file_row = QHBoxLayout()
        self.skip_large_files = QCheckBox("대용량 파일 건너뛰기" if self.language == "kr" else "Skip very large files during indexing")
        self.skip_large_files.setChecked(True)
        self.skip_large_files.toggled.connect(self._on_skip_large_toggled)
        large_file_row.addWidget(self.skip_large_files)
        
        large_file_row.addWidget(QLabel("최대 파일 크기:" if self.language == "kr" else "Max file size:"))
        self.max_file_size = QSpinBox()
        self.max_file_size.setRange(5, 500)
        self.max_file_size.setValue(50)
        self.max_file_size.setSuffix(" MB")
        large_file_row.addWidget(self.max_file_size)
        large_file_row.addStretch()
        advanced_layout.addLayout(large_file_row)
        
        # Excel Indexing Options
        excel_group = QGroupBox("Excel (.xlsx) 인덱싱" if self.language == "kr" else "Excel (xlsx) Indexing")
        excel_layout = QVBoxLayout(excel_group)
        
        excel_row1 = QHBoxLayout()
        self.excel_limit_rows = QCheckBox("시트당 행 제한" if self.language == "kr" else "Limit rows per sheet")
        self.excel_limit_rows.setChecked(True)
        self.excel_limit_rows.toggled.connect(self._on_excel_limit_toggled)
        excel_row1.addWidget(self.excel_limit_rows)
        
        excel_row1.addWidget(QLabel("최대 행 수:" if self.language == "kr" else "Max rows per sheet:"))
        self.excel_max_rows = QSpinBox()
        self.excel_max_rows.setRange(100, 100000)
        self.excel_max_rows.setValue(5000)
        self.excel_max_rows.setSingleStep(1000)
        excel_row1.addWidget(self.excel_max_rows)
        excel_row1.addStretch()
        excel_layout.addLayout(excel_row1)
        
        excel_row2 = QHBoxLayout()
        self.excel_skip_raw = QCheckBox("Raw/Log/History 시트 제외" if self.language == "kr" else "Skip Raw/Log/History sheets")
        self.excel_skip_raw.setChecked(True)
        self.excel_skip_raw.setToolTip("시트 이름에 'Raw', 'Log', 'History'가 포함된 경우 인덱싱에서 제외" if self.language == "kr" else "Skip sheets with 'Raw', 'Log', 'History' in their names")
        excel_row2.addWidget(self.excel_skip_raw)
        excel_row2.addStretch()
        excel_layout.addLayout(excel_row2)
        
        advanced_layout.addWidget(excel_group)
        layout.addWidget(self.advanced_group)
        
        # Load settings and apply to UI
        self._load_indexing_settings_to_ui()
        
        # ===== Folder Tree =====
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabels([
            "폴더" if self.language == "kr" else "Folder",
            "대상 파일" if self.language == "kr" else "Indexable",
            "인덱싱됨" if self.language == "kr" else "Indexed",
            "",  # Icon column (no header)
            "상태" if self.language == "kr" else "Status",
            "최근 인덱싱" if self.language == "kr" else "Last Indexed"
        ])
        self.folder_tree.setColumnWidth(0, 280)
        self.folder_tree.setColumnWidth(1, 70)
        self.folder_tree.setColumnWidth(2, 70)
        self.folder_tree.setColumnWidth(3, 30)  # Icon column
        self.folder_tree.setColumnWidth(4, 80)
        self.folder_tree.setColumnWidth(5, 140)
        
        # Enable checkboxes
        self.folder_tree.itemChanged.connect(self._on_folder_check_changed)
        
        # Populate folders - Outlook first as separate top-level
        self._populate_outlook_item()
        
        # Populate Local folders
        self._populate_local_folders()
        
        # Populate Cloud section (OneDrive, SharePoint - without Outlook)
        self._populate_cloud_folders()
        
        layout.addWidget(self.folder_tree)
    
    def _toggle_date_filter(self, enabled):
        """Toggle date filter controls."""
        self.date_start.setEnabled(enabled)
        self.date_end.setEnabled(enabled)
    
    def _populate_outlook_item(self):
        """Add Outlook as a separate top-level item with local and cloud options."""
        is_pro = self._is_pro()
        
        # Get indexed email counts by folder
        inbox_count = self._get_outlook_folder_indexed_count("Inbox")
        sent_count = self._get_outlook_folder_indexed_count("Sent Items")
        total_count = inbox_count + sent_count
        
        indexed_str = str(total_count) if total_count > 0 else "—"
        
        # Determine icon and status
        if not is_pro:
            icon = "🔒"
            status_text = "Pro Only"
        elif total_count > 0:
            icon = "✅"
            status_text = "Done"
        else:
            icon = "🔴"
            status_text = ""  # Will show Connect button
        
        self.outlook_item = QTreeWidgetItem(self.folder_tree, [
            "Outlook",
            "—",  # Indexable
            indexed_str,  # Indexed count
            icon,  # Icon column
            status_text,  # Status
            "—" if total_count == 0 else self._get_last_indexed("outlook")
        ])
        outlook_item = self.outlook_item
        outlook_item.setFlags(outlook_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
        is_indexed = total_count > 0
        default_checked = is_indexed or (hasattr(self, 'filter_email') and self.filter_email.isChecked())
        outlook_item.setCheckState(0, Qt.CheckState.Checked if default_checked else Qt.CheckState.Unchecked)
        outlook_item.setData(0, Qt.ItemDataRole.UserRole, "outlook")
        outlook_item.setExpanded(True)
        
        if not is_pro:
            outlook_item.setDisabled(True)
        
        # Add connect button for cloud Outlook if Pro and not connected
        if is_pro and total_count == 0:
            connect_btn = QPushButton("연결" if self.language == "kr" else "Connect")
            connect_btn.setFixedWidth(60)
            connect_btn.clicked.connect(lambda: self._connect_cloud("outlook"))
            self.folder_tree.setItemWidget(outlook_item, 4, connect_btn)  # Column 4 = Status
        
        # Add Outlook sub-items with individual counts
        if is_pro:
            inbox_icon = "✅" if inbox_count > 0 else "⏳"
            inbox_status = "Done" if inbox_count > 0 else "Pending"
            inbox = QTreeWidgetItem(outlook_item, [
                "받은편지함" if self.language == "kr" else "Inbox", 
                "—", 
                str(inbox_count) if inbox_count > 0 else "—",
                inbox_icon,
                inbox_status,
                "—" if inbox_count == 0 else self._get_last_indexed("outlook:inbox")
            ])
            inbox.setFlags(inbox.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            inbox_checked = inbox_count > 0 or (hasattr(self, 'filter_email') and self.filter_email.isChecked())
            inbox.setCheckState(0, Qt.CheckState.Checked if inbox_checked else Qt.CheckState.Unchecked)
            inbox.setData(0, Qt.ItemDataRole.UserRole, "outlook:inbox")
            
            sent_icon = "✅" if sent_count > 0 else "⏳"
            sent_status = "Done" if sent_count > 0 else "Pending"
            sent = QTreeWidgetItem(outlook_item, [
                "보낸편지함" if self.language == "kr" else "Sent Items", 
                "—", 
                str(sent_count) if sent_count > 0 else "—",
                sent_icon,
                sent_status,
                "—" if sent_count == 0 else self._get_last_indexed("outlook:sent")
            ])
            sent.setFlags(sent.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
            sent_checked = sent_count > 0 or (hasattr(self, 'filter_email') and self.filter_email.isChecked())
            sent.setCheckState(0, Qt.CheckState.Checked if sent_checked else Qt.CheckState.Unchecked)
            sent.setData(0, Qt.ItemDataRole.UserRole, "outlook:sent")
    
    def _on_email_filter_changed(self, checked):
        """Handle Email filter checkbox - auto-select/deselect Outlook folders."""
        print(f"[DEBUG] _on_email_filter_changed called, checked={checked}")
        
        try:
            if not hasattr(self, 'outlook_item'):
                 # Try to find it again if for some reason it's missing (fallback)
                if not hasattr(self, 'folder_tree'):
                    return
                root = self.folder_tree.invisibleRootItem()
                found = False
                for i in range(root.childCount()):
                    item = root.child(i)
                    try:
                        if item.data(0, Qt.ItemDataRole.UserRole) == "outlook":
                            self.outlook_item = item
                            found = True
                            break
                    except:
                        continue
                
                if not found:
                    print("[DEBUG] Outlook item not found in tree")
                    return
            
            if hasattr(self, 'outlook_item') and self.outlook_item:
                 # Check if C++ object is valid
                 try:
                     if not self.outlook_item.treeWidget():
                         # If not associated with a tree, it might be deleted or invalid
                         print("[DEBUG] Outlook item not associated with tree")
                         return
                 except Exception as e:
                     print(f"[DEBUG] Outlook item invalid: {e}")
                     return

                 if not self.outlook_item.isDisabled():
                    self._set_check_state_recursive(self.outlook_item, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        except Exception as e:
            print(f"[ERROR] Error in _on_email_filter_changed: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_local_folders(self):
        """Populate the tree with local folders (excluding system/hidden)."""
        local_root = QTreeWidgetItem(self.folder_tree, ["Local", "", "", "", "", ""])
        local_root.setExpanded(True)
        local_root.setFlags(local_root.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
        local_root.setCheckState(0, Qt.CheckState.Unchecked)
        
        user_home = Path.home()
        
        # Main user folders to show
        main_folders = [
            ("Documents", user_home / "Documents"),
            ("Downloads", user_home / "Downloads"),
            ("Desktop", user_home / "Desktop"),
            ("Pictures", user_home / "Pictures"),
            ("Music", user_home / "Music"),
            ("Videos", user_home / "Videos"),
        ]
        
        for name, path in main_folders:
            if path.exists():
                self._add_folder_item(local_root, name, path)
        
        # Add drives (C:, D:, etc.) excluding system folders
        try:
            import string
            for drive_letter in string.ascii_uppercase:
                drive_path = Path(f"{drive_letter}:/")
                if drive_path.exists() and drive_path.is_dir():
                    # Skip if it's the system drive root to avoid system folders
                    if drive_letter == 'C':
                        continue  # Skip C: root, we already show user folders
                    drive_item = QTreeWidgetItem(local_root, [
                        f"{drive_letter}:",
                        "",
                        "",
                        "⏳",  # Icon
                        "Pending",
                        ""
                    ])
                    drive_item.setFlags(drive_item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
                    drive_item.setCheckState(0, Qt.CheckState.Unchecked)
                    drive_item.setData(0, Qt.ItemDataRole.UserRole, str(drive_path))
                    
                    # Add subfolders (first level only, excluding hidden/system)
                    self._add_subfolders(drive_item, drive_path, max_depth=1)
        except:
            pass
    
    def _add_folder_item(self, parent, name, path, depth=0):
        """Add a folder item with checkbox and indexing status."""
        total_files = self._count_files(path) if depth == 0 else "—"
        is_indexed = self._is_folder_indexed(str(path))
        indexed_count = self._get_indexed_count(str(path)) if is_indexed else "—"
        
        # Icon and status based on indexed state
        icon = "✅" if is_indexed else "⏳"
        status_text = "Done" if is_indexed else "Pending"
        
        last_indexed = self._get_last_indexed(str(path)) if is_indexed else "—"
        
        item = QTreeWidgetItem(parent, [
            name,
            str(total_files) if total_files != "—" else "—",
            str(indexed_count) if indexed_count != "—" else "—",
            icon,  # Icon column
            status_text,
            last_indexed
        ])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsAutoTristate | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked if is_indexed else Qt.CheckState.Unchecked)
        item.setData(0, Qt.ItemDataRole.UserRole, str(path))
        
        # Add subfolders (expandable)
        if depth < 2:  # Limit depth for performance
            self._add_subfolders(item, path, max_depth=2-depth)
        
        return item
    
    def _add_subfolders(self, parent_item, path, max_depth=1):
        """Add subfolders to a tree item, excluding hidden/system folders."""
        try:
            hidden_prefixes = ('.', '$', '~')
            system_folders = {
                'Windows', 'Program Files', 'Program Files (x86)', 'ProgramData',
                'System Volume Information', 'Recovery', 'Config.Msi',
                'AppData', '__pycache__', 'node_modules', '.git', '.vscode'
            }
            
            subfolders = []
            for item in path.iterdir():
                if item.is_dir():
                    name = item.name
                    # Skip hidden and system folders
                    if name.startswith(hidden_prefixes):
                        continue
                    if name in system_folders:
                        continue
                    # Skip if hidden attribute on Windows
                    try:
                        import ctypes
                        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(item))
                        if attrs != -1 and (attrs & 2):  # FILE_ATTRIBUTE_HIDDEN
                            continue
                    except:
                        pass
                    subfolders.append((name, item))
            
            # Sort and limit to first 20 folders for performance
            subfolders.sort(key=lambda x: x[0].lower())
            for name, folder_path in subfolders[:20]:
                sub_item = QTreeWidgetItem(parent_item, [
                    name,
                    "—",
                    "—",
                    "⏳",  # Icon: Pending
                    "Pending",
                    "—"
                ])
                sub_item.setFlags(sub_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                sub_item.setCheckState(0, Qt.CheckState.Unchecked)
                sub_item.setData(0, Qt.ItemDataRole.UserRole, str(folder_path))
                
                # Recursively add subfolders if depth allows (no placeholder needed)
                if max_depth > 0:
                    self._add_subfolders(sub_item, folder_path, max_depth - 1)
        except PermissionError:
            pass
        except Exception:
            pass

    def _populate_cloud_folders(self):
        """Populate cloud section with connect buttons."""
        cloud_root = QTreeWidgetItem(self.folder_tree, ["Cloud", "", "", "", "", ""])
        cloud_root.setExpanded(True)
        
        # Cloud sources with connect buttons
        cloud_sources = [
            ("OneDrive", "onedrive"),
            ("SharePoint", "sharepoint")
        ]
        
        for display_name, source_id in cloud_sources:
            is_pro = self._is_pro()
            
            # Icon and status based on Pro mode
            if is_pro:
                icon = "🔴"  # Need to connect
                status_text = ""  # Will show connect button
            else:
                icon = "🔒"
                status_text = "Pro Only"
            
            item = QTreeWidgetItem(cloud_root, [
                display_name,
                "—",
                "—",
                icon,  # Icon column
                status_text,
                "—"
            ])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Unchecked)
            item.setData(0, Qt.ItemDataRole.UserRole, f"cloud:{source_id}")
            
            # Add connect button as item widget
            if is_pro:
                connect_btn = QPushButton("연결" if self.language == "kr" else "Connect")
                connect_btn.setFixedWidth(60)
                connect_btn.clicked.connect(lambda checked, s=source_id: self._connect_cloud(s))
                self.folder_tree.setItemWidget(item, 4, connect_btn)  # Column 4 = Status
            else:
                item.setDisabled(True)
    
    def _on_folder_check_changed(self, item, column):
        """Handle folder checkbox state change."""
        pass  # Auto-tristate handles parent/child relationships
    
    def _select_all_folders(self):
        """Select all folders in the tree."""
        root = self.folder_tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._set_check_state_recursive(root.child(i), Qt.CheckState.Checked)
    
    def _deselect_all_folders(self):
        """Deselect all folders in the tree."""
        root = self.folder_tree.invisibleRootItem()
        for i in range(root.childCount()):
            self._set_check_state_recursive(root.child(i), Qt.CheckState.Unchecked)
    
    def _set_check_state_recursive(self, item, state):
        """Set check state for item and all children."""
        if not item.isDisabled():
            item.setCheckState(0, state)
        for i in range(item.childCount()):
            self._set_check_state_recursive(item.child(i), state)
    
    def _start_selected_indexing(self):
        """Start indexing for selected folders."""
        selected_folders = []
        root = self.folder_tree.invisibleRootItem()
        
        for i in range(root.childCount()):
            self._collect_checked_folders(root.child(i), selected_folders)
        
        if not selected_folders:
            msg = "인덱싱할 폴더를 선택해주세요." if self.language == "kr" else "Please select folders to index."
            QMessageBox.warning(self, "Warning", msg)
            return
        
        # Separate local folders and Outlook
        local_folders = []
        include_outlook = False
        
        for folder in selected_folders:
            if folder.startswith("outlook"):
                # Outlook item selected (outlook, outlook:inbox, outlook:sent)
                include_outlook = True
            elif folder.startswith("cloud:"):
                # Other cloud sources (OneDrive, SharePoint) - skip for now
                pass
            else:
                # Local folder
                local_folders.append(folder)
        
        if not local_folders and not include_outlook:
            msg = "인덱싱할 로컬 폴더 또는 Outlook을 선택해주세요." if self.language == "kr" else "Please select local folders or Outlook to index."
            QMessageBox.warning(self, "Warning", msg)
            return
        
        # Setup progress dialog with simple UI - only percentage and elapsed time
        if self.language == "kr":
            progress_text = "🔄 인덱싱 중...\n\n진행률: 0%\n경과시간: 0초"
        else:
            progress_text = "🔄 Indexing...\n\nProgress: 0%\nElapsed: 0s"
        
        self.progress_dialog = QProgressDialog(
            progress_text,
            "취소" if self.language == "kr" else "Cancel",
            0, 100,
            self
        )
        self.progress_dialog.setWindowTitle("🔄 인덱싱 진행 중" if self.language == "kr" else "🔄 Indexing in Progress")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setMinimumWidth(280)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
        
        # Setup activity spinner animation and elapsed time tracking
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.last_progress_percent = 0
        import time
        self.indexing_start_time = time.time()
        
        # Timer for spinner animation and elapsed time (every 500ms)
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self._update_spinner)
        self.spinner_timer.start(500)
        
        self.status_bar.showMessage("Indexing started..." + (" (Including Outlook)" if include_outlook else ""))
        self.index_btn_docs.setEnabled(False)
        
        # Start indexing thread with current settings
        current_settings = getattr(self, 'indexing_settings', None) or load_indexing_settings()
        self.indexer_thread = IndexingThread(
            local_folders if local_folders else [], 
            self.model_name, 
            include_outlook,
            connector=None,
            settings=current_settings
        )
        self.indexer_thread.progress.connect(self._on_indexing_progress_update)
        self.indexer_thread.finished.connect(self._on_docs_indexing_finished)
        self.indexer_thread.start()
    
    def _on_indexing_progress_update(self, message, percent):
        """Update progress dialog with indexing progress."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            # Parse progress info if in new format: "PROGRESS:processed:total:folder_idx:total_folders"
            if message.startswith("PROGRESS:"):
                try:
                    parts = message.split(":")
                    processed = int(parts[1])
                    total = int(parts[2])
                    folder_idx = int(parts[3])
                    total_folders = int(parts[4])
                    
                    # Store for spinner display
                    self.last_processed = processed
                    self.last_total = total
                    self.last_folder_idx = folder_idx
                    self.last_total_folders = total_folders
                except:
                    pass
        
        # Status bar shows simple info
        self.status_bar.showMessage("Indexing in progress...")
    
    def _update_spinner(self):
        """Update spinner animation and elapsed time display."""
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            # Cycle through spinner frames
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
            spinner = self.spinner_frames[self.spinner_index]
            
            # Calculate elapsed time
            import time
            elapsed_seconds = int(time.time() - getattr(self, 'indexing_start_time', time.time()))
            
            # Get file counts
            processed = getattr(self, 'last_processed', 0)
            total = getattr(self, 'last_total', 0)
            folder_idx = getattr(self, 'last_folder_idx', 0) + 1  # 1-indexed for display
            total_folders = getattr(self, 'last_total_folders', 1)
            
            # Simple display: file count instead of percentage
            if self.language == "kr":
                display_msg = f"{spinner} 인덱싱 중...\n\n처리: {processed}/{total} 파일\n폴더: {folder_idx}/{total_folders}\n경과시간: {elapsed_seconds}초"
            else:
                display_msg = f"{spinner} Indexing...\n\nProcessed: {processed}/{total} files\nFolder: {folder_idx}/{total_folders}\nElapsed: {elapsed_seconds}s"
            
            self.progress_dialog.setLabelText(display_msg)
            
            # Update progress bar based on file count
            if total > 0:
                bar_percent = min(100, int((processed / total) * 100))
                self.progress_dialog.setValue(bar_percent)
    
    def _collect_checked_folders(self, item, result):
        """Collect all checked folder paths."""
        if item.checkState(0) == Qt.CheckState.Checked:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and path != "...":
                result.append(path)
        
        for i in range(item.childCount()):
            self._collect_checked_folders(item.child(i), result)
    
    def _on_docs_indexing_finished(self, message, indexed_count, skipped_count, errors):
        """Handle indexing completion from documents tab."""
        # Stop spinner timer
        if hasattr(self, 'spinner_timer') and self.spinner_timer:
            self.spinner_timer.stop()
            self.spinner_timer = None
        
        # Close progress dialog
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.setValue(100)
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.index_btn_docs.setEnabled(True)
        self.status_bar.showMessage("Ready")
        
        # Reload engine to pick up new index
        self.engine = SearchEngine(model_name=self.model_name, language=self.language)
        
        # Show completion message
        if self.language == "kr":
            complete_msg = f"인덱싱 완료!\n처리된 파일: {indexed_count}개"
            if skipped_count > 0:
                complete_msg += f"\n건너뛴 파일: {skipped_count}개"
        else:
            complete_msg = f"Indexing Complete!\nFiles processed: {indexed_count}"
            if skipped_count > 0:
                complete_msg += f"\nFiles skipped: {skipped_count}"
        
        QMessageBox.information(self, "Complete" if self.language != "kr" else "완료", complete_msg)
        
        # Refresh the tree to show updated status
        self._refresh_documents_tree()
    
    def _refresh_documents_tree(self):
        """Refresh the documents tree to reflect updated indexing status."""
        # Clear and repopulate the tree
        self.folder_tree.clear()
        
        # Repopulate all sections
        self._populate_outlook_item()
        self._populate_local_folders()
        self._populate_cloud_folders()
    
    # ===== Indexing Performance Settings Methods =====
    def _load_indexing_settings_to_ui(self):
        """Load indexing settings from file and apply to UI."""
        self.indexing_settings = load_indexing_settings()
        
        # Set performance mode combo (auto=0, power_saving=1, balanced=2, high_performance=3)
        mode_map = {"auto": 0, "power_saving": 1, "balanced": 2, "high_performance": 3}
        self.perf_mode_combo.setCurrentIndex(mode_map.get(self.indexing_settings.performance_mode, 0))
        self.workers_spinbox.setValue(self.indexing_settings.parallel_workers)
        
        # Update recommended label
        if self.language == "kr":
            rec_text = f"💻 이 PC 권장: {self.indexing_settings.recommended_mode.title()} ({self.indexing_settings.recommended_comment})"
        else:
            rec_text = f"💻 Recommended for this PC: {self.indexing_settings.recommended_mode.title()} ({self.indexing_settings.recommended_comment})"
        self.recommended_label.setText(rec_text)
        
        # Set advanced options
        self.skip_large_files.setChecked(self.indexing_settings.skip_large_files)
        self.max_file_size.setValue(self.indexing_settings.max_file_size_mb)
        self.max_file_size.setEnabled(self.indexing_settings.skip_large_files)
        
        self.excel_limit_rows.setChecked(self.indexing_settings.excel.limit_rows)
        self.excel_max_rows.setValue(self.indexing_settings.excel.max_rows_per_sheet)
        self.excel_max_rows.setEnabled(self.indexing_settings.excel.limit_rows)
        self.excel_skip_raw.setChecked(self.indexing_settings.excel.skip_raw_like_sheets)
    
    def _save_indexing_settings_from_ui(self):
        """Save current UI settings to file."""
        mode_list = ["auto", "power_saving", "balanced", "high_performance"]
        self.indexing_settings.performance_mode = mode_list[self.perf_mode_combo.currentIndex()]
        self.indexing_settings.use_auto_tuning = (self.indexing_settings.performance_mode == "auto")
        self.indexing_settings.parallel_workers = self.workers_spinbox.value()
        self.indexing_settings.skip_large_files = self.skip_large_files.isChecked()
        self.indexing_settings.max_file_size_mb = self.max_file_size.value()
        self.indexing_settings.excel.limit_rows = self.excel_limit_rows.isChecked()
        self.indexing_settings.excel.max_rows_per_sheet = self.excel_max_rows.value()
        self.indexing_settings.excel.skip_raw_like_sheets = self.excel_skip_raw.isChecked()
        
        save_indexing_settings(self.indexing_settings)
    
    def _on_perf_mode_changed(self, index):
        """Handle performance mode selection change."""
        mode_list = ["auto", "power_saving", "balanced", "high_performance"]
        mode = mode_list[index]
        
        if mode == "auto":
            # Apply auto-tuning based on system profile
            self.indexing_settings.apply_auto_tuning()
        else:
            # Apply preset for the selected mode
            self.indexing_settings.apply_mode_preset(mode)
        
        # Update UI with current values
        self.workers_spinbox.setValue(self.indexing_settings.parallel_workers)
        self.max_file_size.setValue(self.indexing_settings.max_file_size_mb)
        self.excel_max_rows.setValue(self.indexing_settings.excel.max_rows_per_sheet)
        self.excel_skip_raw.setChecked(self.indexing_settings.excel.skip_raw_like_sheets)
        
        self._save_indexing_settings_from_ui()
    
    def _on_apply_recommended(self):
        """Apply recommended settings for this PC."""
        try:
            # Try relative import first, then absolute
            try:
                from .system_profile import recommend_indexing_profile
            except ImportError:
                from system_profile import recommend_indexing_profile
            
            profile = recommend_indexing_profile()
            
            # Update settings
            self.indexing_settings.performance_mode = "auto"
            self.indexing_settings.use_auto_tuning = True
            self.indexing_settings.parallel_workers = profile.parallel_workers
            self.indexing_settings.max_file_size_mb = profile.max_file_size_mb
            self.indexing_settings.excel.max_rows_per_sheet = profile.excel_max_rows
            self.indexing_settings.excel.skip_raw_like_sheets = profile.excel_skip_raw_like_sheets
            
            # Update UI
            self.perf_mode_combo.setCurrentIndex(0)  # Auto
            self.workers_spinbox.setValue(profile.parallel_workers)
            self.max_file_size.setValue(profile.max_file_size_mb)
            self.excel_max_rows.setValue(profile.excel_max_rows)
            self.excel_skip_raw.setChecked(profile.excel_skip_raw_like_sheets)
            
            self._save_indexing_settings_from_ui()
        except Exception as e:
            print(f"Error applying recommended settings: {e}")
    
    def _toggle_advanced_options(self):
        """Toggle visibility of advanced options panel."""
        is_visible = self.advanced_group.isVisible()
        self.advanced_group.setVisible(not is_visible)
        
        # Update toggle button text
        if is_visible:
            self.advanced_toggle.setText("▶ 고급 인덱싱 옵션" if self.language == "kr" else "▶ Advanced Indexing Options")
        else:
            self.advanced_toggle.setText("▼ 고급 인덱싱 옵션" if self.language == "kr" else "▼ Advanced Indexing Options")
    
    def _on_skip_large_toggled(self, checked):
        """Handle skip large files checkbox toggle."""
        self.max_file_size.setEnabled(checked)
        self._save_indexing_settings_from_ui()
    
    def _on_excel_limit_toggled(self, checked):
        """Handle Excel row limit checkbox toggle."""
        self.excel_max_rows.setEnabled(checked)
        self._save_indexing_settings_from_ui()
    
    def _toggle_date_filter(self, enabled):
        """Toggle date filter inputs."""
        self.date_start.setEnabled(enabled)
        self.date_end.setEnabled(enabled)
    
    def _on_email_filter_changed(self, checked):
        """Handle email filter checkbox change."""
        # Auto-select Outlook folders when email filter is enabled
        pass  # Placeholder for future implementation
    
    def _is_folder_indexed(self, path):
        """Check if a folder has been indexed."""
        # Simple check - would need actual implementation
        try:
            user_home = str(Path.home())
            default_folders = [
                os.path.join(user_home, "Documents"),
                os.path.join(user_home, "Downloads"),
                os.path.join(user_home, "Desktop")
            ]
            return path in default_folders
        except:
            return False

    def setup_network_tab(self):
        """Setup Network Activity tab."""
        layout = QVBoxLayout(self.network_tab)
        
        # Header
        header = QLabel("🌐 네트워크 활동" if self.language == "kr" else "🌐 Network Activity")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Summary cards
        cards_layout = QHBoxLayout()
        
        # Today's activity card
        activity_card = QGroupBox("오늘의 활동" if self.language == "kr" else "Today's Activity")
        activity_layout = QVBoxLayout(activity_card)
        activity_count = QLabel("0")
        activity_count.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        activity_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activity_layout.addWidget(activity_count)
        activity_desc = QLabel("네트워크 요청" if self.language == "kr" else "Network Requests")
        activity_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activity_layout.addWidget(activity_desc)
        cards_layout.addWidget(activity_card)
        
        # Blocked requests card
        blocked_card = QGroupBox("차단됨" if self.language == "kr" else "Blocked")
        blocked_layout = QVBoxLayout(blocked_card)
        blocked_count = QLabel("0")
        blocked_count.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        blocked_count.setStyleSheet("color: green;")
        blocked_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blocked_layout.addWidget(blocked_count)
        blocked_desc = QLabel("의심스러운 요청" if self.language == "kr" else "Suspicious Requests")
        blocked_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        blocked_layout.addWidget(blocked_desc)
        cards_layout.addWidget(blocked_card)
        
        layout.addLayout(cards_layout)
        
        # Activity log
        log_label = QLabel("📋 활동 로그" if self.language == "kr" else "📋 Activity Log")
        log_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(log_label)
        
        self.network_log = QTableWidget()
        self.network_log.setColumnCount(3)
        self.network_log.setHorizontalHeaderLabels([
            "시간" if self.language == "kr" else "Time",
            "설명" if self.language == "kr" else "Description",
            "상태" if self.language == "kr" else "Status"
        ])
        self.network_log.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Add sample offline message
        self.network_log.setRowCount(1)
        self.network_log.setItem(0, 0, QTableWidgetItem(datetime.now().strftime("%H:%M:%S")))
        offline_msg = "이 프로그램은 100% 오프라인으로 작동합니다" if self.language == "kr" else "This program runs 100% offline"
        self.network_log.setItem(0, 1, QTableWidgetItem(offline_msg))
        status_item = QTableWidgetItem("✅ " + ("안전" if self.language == "kr" else "Safe"))
        status_item.setForeground(QColor("green"))
        self.network_log.setItem(0, 2, status_item)
        
        layout.addWidget(self.network_log)

    # setup_security_tab removed - security info now in About tab

    def setup_settings_tab(self):
        """Setup About tab with comprehensive product information."""
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # About content in QTextEdit for rich formatting - fills entire window
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        
        content = """
        <h2>🛠 Why This Product Exists</h2>
        <p>In a cloud-first, AI-driven era, the daily struggles of office workers bound to Windows, 
        MS Office files, shared drives, and strict corporate networks are still largely ignored.</p>
        
        <p>As someone who constantly had to trace the context of ever-changing file versions—remembering 
        which draft contained what, and endlessly digging through folders—I built the solution I personally needed: 
        <b>a fully local, offline, enterprise-safe AI search engine</b> that finally makes finding the right file effortless.</p>
        
        <hr>
        
        <h2>🎯 About</h2>
        <p>A semantic AI file search tool designed specifically for corporate environments where:</p>
        <ul>
            <li>Files live on Windows PCs, network drives, and legacy folder structures</li>
            <li>Cloud search tools cannot be used due to privacy or IT restrictions</li>
            <li>AI models must run locally with no external data transmission</li>
            <li>MS Office–centric workflows generate endless versions and duplicates</li>
        </ul>
        <p>Local AI File Search overcomes these constraints by providing on-device semantic understanding, 
        enabling fast, accurate discovery of documents purely within the local environment—no cloud dependency, no policy conflicts.</p>
        
        <hr>
        
        <h2>⭐ Key Differentiators</h2>
        <ul>
            <li><b>Semantic Search:</b> Understands content, not just filenames</li>
            <li><b>Windows & Office Optimized:</b> Built for E-MAIL, DOCX, XLSX, PPTX, PDF-heavy workflows</li>
            <li><b>Local-Only Operation:</b> Works entirely offline in secure corporate networks</li>
            <li><b>Version-Chaos Relief:</b> Instantly finds the correct draft among duplicates</li>
            <li><b>IT-Friendly:</b> Safe, deterministic, and compliant with strict corporate policies</li>
        </ul>
        
        <hr>
        
        <h2>🔐 Security & Privacy</h2>
        <ul>
            <li><b>100% Offline Operation:</b> No cloud access, no telemetry, no external communication</li>
            <li><b>Local-Only Search:</b> Even cloud-origin files (email attachments, cloud drive documents) are searched only after they exist on your local disk — no online indexing, no server-side activity</li>
            <li><b>Local Storage Only:</b> All embeddings and indexes remain entirely on your device</li>
            <li><b>Read-Only Access:</b> Never modifies, moves, or deletes any files</li>
            <li><b>Local LLM:</b> The AI model runs fully on-device</li>
            <li><b>Inference-Only Model:</b> The LLM does not learn from, store, or train on your files — it performs search and ranking only</li>
        </ul>
        
        <hr>
        
        <h2>🧠 AI Model</h2>
        <ul>
            <li><b>Model:</b> all-MiniLM-L6-v2</li>
            <li>Lightweight, high-accuracy semantic embedding model</li>
            <li>Multilingual support (including Korean & English)</li>
            <li>Runs fully on-device without GPU or internet</li>
        </ul>
        
        <hr>
        
        <h2>📞 Contact</h2>
        <p>Email: <a href="mailto:backnine.works@gmail.com">backnine.works@gmail.com</a></p>
        """
        
        about_text.setHtml(content)
        layout.addWidget(about_text)

    # Helper methods for Documents tab
    def _count_files(self, path):
        """Count document files in a directory."""
        count = 0
        extensions = {'.docx', '.xlsx', '.pptx', '.pdf', '.txt', '.md'}
        try:
            for f in Path(path).rglob('*'):
                if f.suffix.lower() in extensions:
                    count += 1
        except:
            pass
        return count
    
    def _get_indexed_count(self, path):
        """Get count of indexed files from a path (only files that still exist)."""
        try:
            # SimpleVectorStore doesn't support regex queries, so iterate metadatas
            path_normalized = path.replace('\\', '/').rstrip('/')
            seen_files = set()
            
            for meta in self.engine.indexer.collection.metadatas:
                source = meta.get('source', '')
                if isinstance(source, str):
                    source_normalized = source.replace('\\', '/').rstrip('/')
                    # Check if file is in this path (including subdirectories)
                    if source_normalized.startswith(path_normalized + '/'):
                        # Use full source path for unique identification
                        # Only count if file still exists on disk
                        if source_normalized not in seen_files and os.path.exists(source):
                            seen_files.add(source_normalized)
            return len(seen_files)
        except:
            return 0
    
    def _get_outlook_indexed_count(self):
        """Get count of indexed Outlook emails."""
        try:
            count = 0
            seen_emails = set()
            
            for meta in self.engine.indexer.collection.metadatas:
                # Check if it's an Outlook email
                if meta.get('type') == 'email' or meta.get('source') == 'Outlook':
                    filename = meta.get('filename', '')
                    if filename and filename not in seen_emails:
                        seen_emails.add(filename)
                        count += 1
            return count
        except:
            return 0
    
    def _get_outlook_folder_indexed_count(self, folder_name):
        """Get count of indexed Outlook emails for a specific folder (Inbox, Sent Items)."""
        try:
            count = 0
            seen_emails = set()
            
            # DEBUG: Check if collection exists and has items
            if not hasattr(self.engine.indexer, 'collection'):
                print("[DEBUG] No collection found in indexer")
                return 0
                
            total_meta = len(self.engine.indexer.collection.metadatas)
            print(f"[DEBUG] _get_outlook_folder_indexed_count({folder_name}): Total metadatas: {total_meta}")
            
            for i, meta in enumerate(self.engine.indexer.collection.metadatas):
                # Check if it's an Outlook email from the specific folder
                # Print first few for debugging
                if i < 3:
                    print(f"[DEBUG] Meta[{i}]: {meta}")
                    
                if (meta.get('type') == 'email' or meta.get('source') == 'Outlook'):
                    if meta.get('folder') == folder_name:
                        filename = meta.get('filename', '')
                        if filename and filename not in seen_emails:
                            seen_emails.add(filename)
                            count += 1
            
            print(f"[DEBUG] _get_outlook_folder_indexed_count({folder_name}) returning {count}")
            return count
        except Exception as e:
            print(f"[ERROR] _get_outlook_folder_indexed_count error: {e}")
            return 0
    
    def _get_last_indexed(self, path):
        """Get last indexed time for a path."""
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def _refresh_documents_tree(self):
        """Refresh the documents tree."""
        self.folder_tree.clear()
        # Re-populate all sections including Outlook
        self._populate_outlook_item()
        self._populate_local_folders()
        self._populate_cloud_folders()
    
    def _cleanup_deleted_files(self):
        """Clean up database entries for files that no longer exist."""
        try:
            removed_count = self.engine.indexer.collection.cleanup_deleted_files()
            
            if removed_count > 0:
                # Reload engine to reflect changes
                self.engine = SearchEngine(model_name=self.model_name, language=self.language)
                
                if self.language == "kr":
                    msg = f"DB 정리 완료!\n\n삭제된 파일 {removed_count}개의 인덱스를 제거했습니다."
                else:
                    msg = f"DB Cleanup Complete!\n\nRemoved {removed_count} index entries for deleted files."
            else:
                if self.language == "kr":
                    msg = "정리할 항목이 없습니다.\n\n모든 인덱스된 파일이 존재합니다."
                else:
                    msg = "Nothing to clean up.\n\nAll indexed files still exist."
            
            QMessageBox.information(self, "DB 정리" if self.language == "kr" else "DB Cleanup", msg)
            
            # Refresh the tree to show updated counts
            self._refresh_documents_tree()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"DB 정리 중 오류 발생: {e}" if self.language == "kr" else f"Error during cleanup: {e}")
    def _connect_cloud(self, service):
        """Handle cloud service connection."""
        if not self._is_pro():
            self.show_pro_required_dialog()
            return
            
        if service == "outlook" or service == "onedrive":
            try:
                from connectors.graph import GraphConnector
                import webbrowser
                
                # Start Device Code Flow
                connector = GraphConnector()
                flow = connector.initiate_device_flow()
                
                user_code = flow.get("user_code", "")
                verification_uri = flow.get("verification_uri", "https://microsoft.com/devicelogin")
                
                # Copy code to clipboard first
                clipboard = QApplication.clipboard()
                clipboard.setText(user_code)
                
                # Show instructions to user with improved message
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Microsoft 365 연결")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setText(
                    f"🔗 Microsoft 365 클라우드 연결 안내\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📋 인증 코드 (자동 복사됨!):\n\n"
                    f"    {user_code}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📌 진행 순서:\n"
                    f"  1. '브라우저 열기' 버튼 클릭\n"
                    f"  2. 코드 붙여넣기 (Ctrl+V)\n"
                    f"  3. Microsoft 계정 로그인\n"
                    f"  4. 권한 허용\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"💡 한 번만 연동하면 됩니다!\n"
                    f"   연동 후에는 인덱싱할 때마다 자동으로\n"
                    f"   클라우드 이메일을 검색할 수 있습니다."
                )
                
                # Only show browser button and cancel
                msg_box.setStandardButtons(QMessageBox.StandardButton.Cancel)
                open_browser_btn = msg_box.addButton("🌐 브라우저 열기", QMessageBox.ButtonRole.AcceptRole)
                
                # Handle button clicks
                def on_button_clicked(button):
                    if button == open_browser_btn:
                        webbrowser.open(verification_uri)
                        # Start device flow completion after opening browser
                        msg_box.close()
                        self._run_device_flow_completion(connector, flow, service)
                
                msg_box.buttonClicked.connect(on_button_clicked)
                msg_box.exec()
                        
            except ImportError as ie:
                if 'msal' in str(ie):
                    QMessageBox.critical(self, "Error", f"Missing dependency: {ie}\nPlease install msal: pip install msal")
                else:
                    QMessageBox.critical(self, "Error", f"Import Error: {ie}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Connection failed: {str(e)}")
        else:
            msg = f"{service} connection will be implemented soon."
            QMessageBox.information(self, "Info", msg)
    
    def _run_device_flow_completion(self, connector, flow, service):
        """Run device flow completion in a background thread."""
        from PyQt6.QtCore import QThread, pyqtSignal
        
        class DeviceFlowWorker(QThread):
            finished = pyqtSignal(bool)
            
            def __init__(self, connector, flow):
                super().__init__()
                self.connector = connector
                self.flow = flow
                self.success = False
                
            def run(self):
                try:
                    self.success = self.connector.complete_device_flow(self.flow)
                except Exception as e:
                    print(f"Device flow error: {e}")
                    self.success = False
                self.finished.emit(self.success)
        
        # Create progress dialog
        progress = QProgressDialog("로그인 대기 중...", "취소", 0, 0, self)
        progress.setWindowTitle("Microsoft 365 연결")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        # Create and start worker thread
        self._device_flow_worker = DeviceFlowWorker(connector, flow)
        
        def on_finished(success):
            progress.close()
            if success:
                QMessageBox.information(self, "성공", f"{service}에 연결되었습니다!")
                self.start_cloud_indexing(connector)
            else:
                QMessageBox.warning(self, "실패", "로그인이 실패했거나 시간이 초과되었습니다.")
        
        def on_cancelled():
            self._device_flow_worker.terminate()
            progress.close()
        
        self._device_flow_worker.finished.connect(on_finished)
        progress.canceled.connect(on_cancelled)
        self._device_flow_worker.start()
            
    def start_cloud_indexing(self, connector):
        """Start indexing from a cloud connector."""
        self.status_bar.showMessage(f"Indexing {connector.name}...")
        
        # Disable buttons
        self.index_btn.setEnabled(False)
        self.rescan_btn.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Start IndexingThread with connector
        current_settings = getattr(self, 'indexing_settings', None) or load_indexing_settings()
        self.indexer_thread = IndexingThread(
            folders=[], 
            model_name=self.model_name, 
            include_outlook=False,
            connector=connector,
            settings=current_settings
        )
        self.indexer_thread.progress.connect(self.on_indexing_progress)
        self.indexer_thread.finished.connect(self.on_indexing_finished)
        self.indexer_thread.start()


    def check_and_auto_index(self):
        """Check if indexing is needed and start auto-indexing."""
        # Check if we have any indexed documents
        doc_count = self.engine.indexer.collection.count()
        
        if doc_count == 0:
            # First run - start auto indexing
            if self.language == "kr":
                self.chat_display.append(f"<i>{self.system_prefix}첫 실행입니다. 내 문서, 바탕화면, 다운로드 폴더를 자동으로 색인합니다...</i>")
            else:
                self.chat_display.append(f"<i>{self.system_prefix}First run detected. Auto-indexing Documents, Desktop, Downloads...</i>")
            
            self.start_auto_indexing()
        else:
            if self.language == "kr":
                self.chat_display.append(f"<i>{self.system_prefix}기존 색인 발견: {doc_count}개 문서 청크가 검색 가능합니다.</i>")
            else:
                self.chat_display.append(f"<i>{self.system_prefix}Existing index found: {doc_count} document chunks ready to search.</i>")

    def start_auto_indexing(self):
        """Start auto-indexing of common user folders."""
        folders = get_user_folders()
        if not folders:
            if self.language == "kr":
                self.chat_display.append(f"<i>{self.system_prefix}색인할 폴더를 찾을 수 없습니다.</i>")
            else:
                self.chat_display.append(f"<i>{self.system_prefix}No folders found to index.</i>")
            return
        
        self.status_bar.showMessage("Auto-indexing...")
        self.index_btn.setEnabled(False)
        self.rescan_btn.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Create progress dialog
        if self.language == "kr":
            self.progress_dialog = QProgressDialog(
                "파일을 색인하는 중입니다...\n잠시만 기다려주세요.",
                None,  # No cancel button
                0, 0,  # Indeterminate progress
                self
            )
            self.progress_dialog.setWindowTitle("색인 진행 중")
        else:
            self.progress_dialog = QProgressDialog(
                "Indexing files...\nPlease wait.",
                None,
                0, 0,
                self
            )
            self.progress_dialog.setWindowTitle("Indexing in Progress")
        
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.show()
        
        include_outlook = self.outlook_check.isChecked()
        current_settings = getattr(self, 'indexing_settings', None) or load_indexing_settings()
        self.indexer_thread = IndexingThread(folders, self.model_name, include_outlook, settings=current_settings)
        self.indexer_thread.progress.connect(self.on_indexing_progress)
        self.indexer_thread.finished.connect(self.on_indexing_finished)
        self.indexer_thread.start()

    def rescan_all_folders(self):
        """Rescan all default folders."""
        if self.language == "kr":
            reply = QMessageBox.question(
                self, '확인', 
                '내 문서, 바탕화면, 다운로드 폴더를 다시 색인하시겠습니까?\n시간이 좀 걸릴 수 있습니다.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self, 'Confirm', 
                'Rescan Documents, Desktop, Downloads folders?\nThis may take a while.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_auto_indexing()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Additional Directory to Index")
        if folder:
            self.status_bar.showMessage("Indexing started...")
            self.index_btn.setEnabled(False)
            self.rescan_btn.setEnabled(False)
            self.chat_display.append(f"<i>{self.system_prefix}Indexing {folder}...</i>")
            
            include_outlook = self.outlook_check.isChecked()
            current_settings = getattr(self, 'indexing_settings', None) or load_indexing_settings()
            self.indexer_thread = IndexingThread(folder, self.model_name, include_outlook, settings=current_settings)
            self.indexer_thread.progress.connect(self.on_indexing_progress)
            self.indexer_thread.finished.connect(self.on_indexing_finished)
            self.indexer_thread.start()

    def on_indexing_progress(self, message):
        self.status_bar.showMessage(message)
        # Update progress dialog if exists
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            if self.language == "kr":
                self.progress_dialog.setLabelText(f"파일을 색인하는 중입니다...\n{message}")
            else:
                self.progress_dialog.setLabelText(f"Indexing files...\n{message}")
        
        # Log to chat specific milestones
        if "Outlook" in message:
             msg_prefix = "시스템" if self.language == "kr" else "System"
             self.chat_display.append(f"<i>{msg_prefix}: {message}</i>")

    def on_outlook_toggled(self, checked):
        # Phase 1: 3.6 Pro 기능 버튼 구현
        if checked:
            # Free 모드에서 시도하면 차단 팝업 표시
            if self.license_manager and not self.license_manager.has_feature("outlook_indexing"):
                self.outlook_check.setChecked(False)
                self.show_pro_required_dialog()
                return
            
            msg = "아웃룩 검색을 활성화했습니다. '전체 다시 색인' 버튼을 눌러야 적용됩니다." if self.language == "kr" else "Outlook search enabled. Please click 'Rescan All' to apply."
            QMessageBox.information(self, "알림" if self.language == "kr" else "Info", msg)

    def on_indexing_finished(self, message, indexed_count, skipped_count, errors):
        # Close progress dialog
        if hasattr(self, 'progress_dialog') and self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        self.status_bar.showMessage("Ready")
        self.index_btn.setEnabled(True)
        self.rescan_btn.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        # Reload engine to pick up new index
        self.engine = SearchEngine(model_name=self.model_name, language=self.language)

        # Display indexing summary
        if self.language == "kr":
            summary = f"✅ 색인 완료: {indexed_count}개 파일 처리"
            if skipped_count > 0:
                summary += f", {skipped_count}개 제외됨"
            if errors:
                summary += f"<br>⚠️ {len(errors)}개 파일 읽기 오류"
        else:
            summary = f"✅ Indexing complete: {indexed_count} files processed"
            if skipped_count > 0:
                summary += f", {skipped_count} skipped"
            if errors:
                summary += f"<br>⚠️ {len(errors)} file(s) had read errors"

        self.chat_display.append(f"<i>{self.system_prefix}{summary}</i>")
        self.chat_display.append("-" * 20)

    def send_message(self):
        query = self.input_field.text().strip()
        if not query:
            return
            
        self.chat_display.append(f"<b>{self.user_prefix}</b> {query}")
        self.input_field.clear()
        self.status_bar.showMessage("Searching...")
        QApplication.processEvents()
        
        try:
            result = self.engine.search_and_answer(query)
            
            # Update Chat
            self.chat_display.append(f"<b>{self.ai_prefix}</b> {result['answer']}")
            self.chat_display.append("-" * 20)
            
            # Update File Table
            self.update_file_table(result['files'])
            
        except Exception as e:
            self.chat_display.append(f"<b>Error:</b> {str(e)}")
            
        self.status_bar.showMessage("Ready")

    def update_file_table(self, files):
        self.file_table.setRowCount(0)
        for file_data in files:
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            
            # Icon / Type
            filename = file_data['filename']
            file_path = file_data['path']
            meta = file_data.get('metadata', {})
            
            # Default
            file_type = "문서" if self.language == "kr" else "File"
            
            # Detect type
            is_email = meta.get('type') == 'email' or "outlook" in file_path.lower()
            
            if is_email:
                file_type = "아웃룩" if self.language == "kr" else "Outlook"
            elif filename.lower().endswith('.pdf'):
                file_type = "PDF"
            elif filename.lower().endswith('.docx') or filename.lower().endswith('.doc'):
                file_type = "워드" if self.language == "kr" else "Word"
            elif filename.lower().endswith('.xlsx') or filename.lower().endswith('.xls'):
                file_type = "엑셀" if self.language == "kr" else "Excel"
            elif filename.lower().endswith('.pptx') or filename.lower().endswith('.ppt'):
                file_type = "PPT"
            elif filename.lower().endswith('.txt'):
                file_type = "텍스트" if self.language == "kr" else "Text"
            
            type_item = QTableWidgetItem(file_type)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.file_table.setItem(row, 0, type_item)
            
            # Filename
            self.file_table.setItem(row, 1, QTableWidgetItem(filename))
            # Path
            self.file_table.setItem(row, 2, QTableWidgetItem(file_path))
            # Score
            self.file_table.setItem(row, 3, QTableWidgetItem(file_data['score']))
            # Preview
            self.file_table.setItem(row, 4, QTableWidgetItem(file_data['preview']))

    def open_file(self, index):
        # Get path from the third column (index 2)
        row = index.row()
        path_item = self.file_table.item(row, 2)
        if path_item:
            file_path = path_item.text()
            
            # Handle Outlook emails (path format: outlook:EntryID)
            if file_path.startswith('outlook:'):
                entry_id = file_path[8:]  # Remove 'outlook:' prefix
                try:
                    import win32com.client
                    import pythoncom
                    pythoncom.CoInitialize()
                    outlook = win32com.client.GetActiveObject("Outlook.Application")
                    namespace = outlook.GetNamespace("MAPI")
                    item = namespace.GetItemFromID(entry_id)
                    item.Display()  # Opens the email in Outlook
                    pythoncom.CoUninitialize()
                except Exception as e:
                    self.status_bar.showMessage(f"Cannot open email: {e}")
                return
            
            # Normalize path (convert forward slashes to backslashes on Windows)
            normalized_path = os.path.normpath(file_path)
            
            if os.path.exists(normalized_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(normalized_path))
            else:
                # Try the original path as-is
                if os.path.exists(file_path):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                else:
                    self.status_bar.showMessage(f"File not found: {file_path}")


def main():
    from config import load_config
    from licensing.manager import LicenseManager
    
    app = QApplication(sys.argv)
    
    # 개발 모드에서는 Pro 기능을 기본으로 사용
    config = load_config()
    license_manager = LicenseManager(config)
    
    # 개발 모드 상태 출력
    if config.debug:
        print(f"[DEBUG] Running in {config.mode.upper()} mode (debug={config.debug})")
    
    window = ChatWindow(language="en", config=config, license_manager=license_manager)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

