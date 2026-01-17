from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class StartPage(QWidget):
    newProjectRequested = pyqtSignal()
    openProjectRequested = pyqtSignal()
    globalLibraryRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        title = QLabel("Signal Mapper")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        lay.addWidget(title)

        sub = QLabel("Crea o abre un proyecto para comenzar.\nTambién puedes editar la biblioteca global de señales.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #64748b; font-size: 12px;")
        lay.addWidget(sub)

        lay.addSpacing(18)

        row = QHBoxLayout()
        self.btn_new = QPushButton("Nuevo proyecto…")
        self.btn_open = QPushButton("Abrir proyecto…")
        self.btn_global = QPushButton("Biblioteca global de señales…")

        for b in (self.btn_new, self.btn_open, self.btn_global):
            b.setMinimumWidth(220)
            b.setStyleSheet("padding: 10px 14px; font-size: 13px;")

        row.addWidget(self.btn_new)
        row.addWidget(self.btn_open)
        row.addWidget(self.btn_global)
        lay.addLayout(row)

        self.btn_new.clicked.connect(self.newProjectRequested.emit)
        self.btn_open.clicked.connect(self.openProjectRequested.emit)
        self.btn_global.clicked.connect(self.globalLibraryRequested.emit)
