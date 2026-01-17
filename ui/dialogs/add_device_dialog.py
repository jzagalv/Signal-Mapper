from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton

class AddDeviceDialog(QDialog):
    """Crear equipo: el ID es interno/autogenerado por el software.
    El usuario sólo define bahía, nombre visible y tipo."""

    def __init__(self, bay_choices: list[tuple[str, str]], default_bay_id: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo equipo")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Bahía:"))
        self.bay_combo = QComboBox()
        for name, bay_id in bay_choices:
            self.bay_combo.addItem(name, bay_id)
        if default_bay_id is not None:
            idx = self.bay_combo.findData(default_bay_id)
            if idx >= 0:
                self.bay_combo.setCurrentIndex(idx)
        lay.addWidget(self.bay_combo)

        lay.addWidget(QLabel("Nombre del equipo (visible):"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: 52H1, IED-Protección 1, DS-101")
        lay.addWidget(self.name_edit)

        lay.addWidget(QLabel("Tipo de equipo:"))
        self.type_combo = QComboBox()
        self.type_combo.addItem("IED / Relé", "IED")
        self.type_combo.addItem("Interruptor", "BREAKER")
        self.type_combo.addItem("Desconectador", "DISCONNECTOR")
        self.type_combo.addItem("Cuchilla Tierra", "EARTH_SWITCH")
        self.type_combo.addItem("Caja Agrupamiento", "JB")
        self.type_combo.addItem("Otro", "OTHER")
        lay.addWidget(self.type_combo)

        btns = QHBoxLayout()
        ok = QPushButton("Agregar")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok)
        btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_data(self):
        return {
            "bay_id": self.bay_combo.currentData(),
            "name": (self.name_edit.text() or "").strip() or "SIN_NOMBRE",
            "dev_type": self.type_combo.currentData(),
        }
