from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit

class EditTemplateDialog(QDialog):
    def __init__(self, template=None, existing_codes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plantilla de señal")
        existing_codes = set(existing_codes or [])
        self._existing_codes = existing_codes
        self._editing_code = template.code if template else None

        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Código (único):"))
        self.code_edit = QLineEdit(template.code if template else "")
        lay.addWidget(self.code_edit)

        lay.addWidget(QLabel("Etiqueta (visible):"))
        self.label_edit = QLineEdit(template.label if template else "")
        lay.addWidget(self.label_edit)

        lay.addWidget(QLabel("Categoría:"))
        self.cat_edit = QLineEdit(template.category if template else "General")
        lay.addWidget(self.cat_edit)

        lay.addWidget(QLabel("Naturaleza:"))
        self.nature = QComboBox()
        self.nature.addItem("Digital", "DIGITAL")
        self.nature.addItem("Análoga", "ANALOG")
        if template and template.nature == "ANALOG":
            self.nature.setCurrentIndex(1)
        lay.addWidget(self.nature)

        lay.addWidget(QLabel("Descripción (opcional):"))
        self.desc = QTextEdit(template.description if template else "")
        self.desc.setFixedHeight(80)
        lay.addWidget(self.desc)

        btns = QHBoxLayout()
        ok = QPushButton("Guardar")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_data(self):
        code = self.code_edit.text().strip()
        label = self.label_edit.text().strip() or code
        category = self.cat_edit.text().strip() or "General"
        nature = self.nature.currentData()
        desc = self.desc.toPlainText().strip()

        if not code:
            return None, "El código no puede estar vacío."
        if self._editing_code != code and code in self._existing_codes:
            return None, "Ya existe una plantilla con ese código."
        return {"code": code, "label": label, "category": category, "nature": nature, "description": desc}, None
