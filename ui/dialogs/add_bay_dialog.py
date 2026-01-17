from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

class AddBayDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva bahía")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Nombre de la bahía (ej: H1, H2, L1):"))
        self.name_edit = QLineEdit("H1")
        lay.addWidget(self.name_edit)

        btns = QHBoxLayout()
        ok = QPushButton("Agregar"); cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_data(self):
        name = (self.name_edit.text() or "").strip()
        return name
