from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton

class DuplicateDeviceDialog(QDialog):
    def __init__(self, suggested_id: str, suggested_name: str, dev_type: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicar equipo")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel(f"Tipo: {dev_type}"))
        lay.addWidget(QLabel("Nuevo ID:"))
        self.id_edit = QLineEdit(suggested_id); lay.addWidget(self.id_edit)

        lay.addWidget(QLabel("Nuevo nombre:"))
        self.name_edit = QLineEdit(suggested_name); lay.addWidget(self.name_edit)

        self.copy_signals_chk = QCheckBox("Copiar señales como PENDIENTE (hacia/desde EXTERNO)")
        lay.addWidget(self.copy_signals_chk)

        btns = QHBoxLayout()
        ok = QPushButton("Duplicar"); cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_data(self):
        return {"device_id": self.id_edit.text().strip(),
                "name": self.name_edit.text().strip() or "SIN_NOMBRE",
                "copy_signals": self.copy_signals_chk.isChecked()}
