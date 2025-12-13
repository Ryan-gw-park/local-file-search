"""
Local Finder X v2.0 - About Page

Comprehensive product information (restored from v1).
"""

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QTextEdit
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

QTextEdit {
    background-color: #1e1e32;
    border: none;
    color: #ffffff;
    font-size: 14px;
}
"""


class AboutPage(QWidget if PYQT6_AVAILABLE else object):
    """About page with comprehensive product information (v1 content)."""
    
    def __init__(self, parent=None):
        if not PYQT6_AVAILABLE:
            return
        super().__init__(parent)
        self.setStyleSheet(ABOUT_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # About content in QTextEdit for rich formatting
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
        <p>Email: <a href="mailto:backnine.works@gmail.com" style="color: #6366f1;">backnine.works@gmail.com</a></p>
        
        <br>
        <p style="color: #666680; font-size: 12px;">© 2025 Local Finder X. All rights reserved. Version 2.0</p>
        """
        
        about_text.setHtml(content)
        layout.addWidget(about_text)


__all__ = ["AboutPage"]
