"""
Local Finder X v2.0 - Setup Wizard

First-time user onboarding with step-by-step setup.
F042: Setup Wizard (Onboarding)
"""

from typing import List
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QStackedWidget, QWidget, QFrame, QRadioButton, QCheckBox,
        QButtonGroup, QFileDialog
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QDialog = object


WIZARD_STYLE = """
QDialog {
    background-color: #13132a;
}

QFrame.card {
    background-color: #1e1e32;
    border-radius: 8px;
    border: 1px solid #2d2d44;
    padding: 16px;
    margin: 4px 0;
}

QFrame.card-selected {
    background-color: #252545;
    border: 1px solid #6366f1;
}

QPushButton.primary {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: bold;
    min-width: 100px;
}

QPushButton.primary:hover {
    background-color: #7c7ff2;
}

QPushButton.secondary {
    background-color: transparent;
    color: #888899;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    min-width: 80px;
}

QPushButton.secondary:hover {
    background-color: #2d2d44;
    color: #ffffff;
}

QRadioButton {
    color: #ffffff;
    font-size: 13px;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #3d3d5c;
    background-color: #252540;
}

QRadioButton::indicator:checked {
    background-color: #6366f1;
    border-color: #6366f1;
}

QCheckBox {
    color: #ccccdd;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid #3d3d5c;
    background-color: #252540;
}

QCheckBox::indicator:checked {
    background-color: #6366f1;
    border-color: #6366f1;
}
"""


class SetupWizard(QDialog if PYQT6_AVAILABLE else object):
    """First-time setup wizard with 5 steps."""
    
    if PYQT6_AVAILABLE:
        setup_complete = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setWindowTitle("Local Finder X - 설정")
        self.setFixedSize(520, 480)
        self.setStyleSheet(WIZARD_STYLE)
        
        self.selected_model = "balanced"
        self.selected_folders: List[str] = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.setSpacing(16)
        
        # Step indicator
        self.step_label = QLabel("1 / 5")
        self.step_label.setStyleSheet("color: #666680; font-size: 11px;")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.step_label)
        
        # Pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_welcome())
        self.stack.addWidget(self._page_model())
        self.stack.addWidget(self._page_folder())
        self.stack.addWidget(self._page_pro())
        self.stack.addWidget(self._page_complete())
        layout.addWidget(self.stack)
        
        # Navigation
        nav = QHBoxLayout()
        self.prev_btn = QPushButton("이전")
        self.prev_btn.setProperty("class", "secondary")
        self.prev_btn.clicked.connect(self._prev)
        self.prev_btn.hide()
        nav.addWidget(self.prev_btn)
        nav.addStretch()
        
        self.next_btn = QPushButton("시작하기")
        self.next_btn.setProperty("class", "primary")
        self.next_btn.clicked.connect(self._next)
        nav.addWidget(self.next_btn)
        layout.addLayout(nav)
    
    def _page_welcome(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("Local Finder X")
        title.setStyleSheet("color: #ffffff; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        sub = QLabel("100% 오프라인 AI 파일 검색")
        sub.setStyleSheet("color: #888899; font-size: 14px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        
        features = QLabel("✓ 시맨틱 검색 - 내용으로 파일 찾기\n✓ 완전 오프라인 - 데이터 외부 전송 없음\n✓ MS Office 지원 - docx, xlsx, pptx, pdf")
        features.setStyleSheet("color: #aaaacc; font-size: 12px; margin-top: 16px; line-height: 1.6;")
        features.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(features)
        
        return page
    
    def _page_model(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        
        title = QLabel("AI 모델 선택")
        title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        sub = QLabel("PC 사양에 맞는 모델을 선택하세요")
        sub.setStyleSheet("color: #888899; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(sub)
        
        self.model_group = QButtonGroup(self)
        models = [
            ("fast", "빠른 모드", "80MB · 영어 최적화 · 4GB RAM"),
            ("balanced", "균형 모드", "400MB · 한국어+영어 · 8GB RAM"),
            ("advanced", "정밀 모드", "2.3GB · 최고 정확도 · 16GB+ RAM"),
        ]
        
        for i, (key, name, spec) in enumerate(models):
            card = QFrame()
            card.setProperty("class", "card")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            
            radio = QRadioButton(name)
            radio.setChecked(key == "balanced")
            self.model_group.addButton(radio, i)
            card_layout.addWidget(radio)
            card_layout.addStretch()
            
            info = QLabel(spec)
            info.setStyleSheet("color: #666680; font-size: 11px;")
            card_layout.addWidget(info)
            
            if key == "balanced":
                rec = QLabel("[권장]")
                rec.setStyleSheet("color: #6366f1; font-size: 10px; font-weight: bold;")
                card_layout.addWidget(rec)
            
            layout.addWidget(card)
        
        self.model_group.buttonClicked.connect(self._on_model)
        
        hint = QLabel("💡 모든 모델은 Free/Pro 동일 사용 · 나중에 변경 가능")
        hint.setStyleSheet("color: #88aa88; font-size: 11px; margin-top: 8px;")
        layout.addWidget(hint)
        layout.addStretch()
        
        return page
    
    def _page_folder(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        
        title = QLabel("검색 폴더 선택")
        title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        sub = QLabel("어떤 폴더의 파일을 검색할까요?")
        sub.setStyleSheet("color: #888899; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(sub)
        
        home = str(Path.home())
        self.folder_checks = []
        folders = [
            (f"{home}/Documents", "📁 문서"),
            (f"{home}/Downloads", "📥 다운로드"),
            (f"{home}/Desktop", "🖥️ 바탕화면"),
        ]
        
        for path, name in folders:
            chk = QCheckBox(f"{name}  ({self._short(path)})")
            chk.setChecked(True)
            chk.setProperty("path", path)
            chk.setStyleSheet("padding: 6px 0;")
            self.folder_checks.append(chk)
            layout.addWidget(chk)
        
        add_btn = QPushButton("+ 다른 폴더 추가")
        add_btn.setProperty("class", "secondary")
        add_btn.clicked.connect(self._add_folder)
        layout.addWidget(add_btn)
        
        self.custom_label = QLabel("")
        self.custom_label.setStyleSheet("color: #aaaacc; font-size: 11px;")
        layout.addWidget(self.custom_label)
        
        hint = QLabel("💡 나중에 인덱싱 탭에서 변경 가능")
        hint.setStyleSheet("color: #88aa88; font-size: 11px; margin-top: 8px;")
        layout.addWidget(hint)
        layout.addStretch()
        
        return page
    
    def _page_pro(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        
        title = QLabel("Pro 기능 안내")
        title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        sub = QLabel("검색 품질은 Free와 Pro가 동일합니다!")
        sub.setStyleSheet("color: #88aa88; font-size: 12px; margin-bottom: 8px;")
        layout.addWidget(sub)
        
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet("QFrame { border-color: #6366f1; }")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        
        pro_title = QLabel("⭐ Pro 전용 기능")
        pro_title.setStyleSheet("color: #6366f1; font-size: 13px; font-weight: bold;")
        card_layout.addWidget(pro_title)
        
        for f in ["🔒 Outlook 이메일 검색", "🔒 OneDrive 클라우드 연동", "🔒 PII 마스킹", "🔒 감사 로그"]:
            lbl = QLabel(f)
            lbl.setStyleSheet("color: #ccccdd; font-size: 12px; padding-left: 8px;")
            card_layout.addWidget(lbl)
        
        layout.addWidget(card)
        
        hint = QLabel("💡 마이페이지에서 Pro 라이선스 활성화")
        hint.setStyleSheet("color: #888899; font-size: 11px; margin-top: 8px;")
        layout.addWidget(hint)
        layout.addStretch()
        
        return page
    
    def _page_complete(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        
        icon = QLabel("✅")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        
        title = QLabel("설정 완료!")
        title.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        sub = QLabel("이제 파일 검색을 시작할 수 있습니다")
        sub.setStyleSheet("color: #888899; font-size: 13px;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        
        return page
    
    def _short(self, path: str) -> str:
        home = str(Path.home())
        return "~" + path[len(home):] if path.startswith(home) else path
    
    def _on_model(self, btn):
        self.selected_model = ["fast", "balanced", "advanced"][self.model_group.id(btn)]
    
    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder and folder not in self.selected_folders:
            self.selected_folders.append(folder)
            self.custom_label.setText("추가: " + ", ".join([self._short(f) for f in self.selected_folders]))
    
    def _prev(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._update(idx - 1)
    
    def _next(self):
        idx = self.stack.currentIndex()
        if idx < 4:
            self.stack.setCurrentIndex(idx + 1)
            self._update(idx + 1)
        else:
            self._finish()
    
    def _update(self, idx):
        self.step_label.setText(f"{idx + 1} / 5")
        self.prev_btn.setVisible(idx > 0)
        self.next_btn.setText("시작하기" if idx == 0 else "인덱싱 시작" if idx == 4 else "다음")
    
    def _finish(self):
        folders = [c.property("path") for c in self.folder_checks if c.isChecked()]
        folders.extend(self.selected_folders)
        self.setup_complete.emit({"model": self.selected_model, "folders": folders, "first_run_complete": True})
        self.accept()


__all__ = ["SetupWizard"]
