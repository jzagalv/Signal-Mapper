from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo proyecto")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Nombre del proyecto:"))
        self.name_edit = QLineEdit("Proyecto Nuevo")
        lay.addWidget(self.name_edit)

        btns = QHBoxLayout()
        ok = QPushButton("Crear")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_name(self) -> str:
        return self.name_edit.text().strip() or "Proyecto"
