from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox

class SignalLinkDialog(QDialog):
    def __init__(self, bay, origin_device, template: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Señal / Enlace")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel(f"Plantilla: {template.get('code')} — {template.get('label','')}"))
        lay.addWidget(QLabel(f"Origen: {origin_device.name}"))

        self.dest_combo = QComboBox()
        self.dest_combo.addItem("— EXTERNO / Pendiente —", None)
        for dev in bay.devices.values():
            if dev.device_id != origin_device.device_id:
                self.dest_combo.addItem(dev.name, dev.device_id)
        lay.addWidget(QLabel("Destino:"))
        lay.addWidget(self.dest_combo)

        self.signal_name = QLineEdit(template.get("label") or template.get("code") or "SIN_NOMBRE")
        lay.addWidget(QLabel("Nombre de señal:"))
        lay.addWidget(self.signal_name)

        self.nature_combo = QComboBox()
        self.nature_combo.addItem("Digital", "DIGITAL")
        self.nature_combo.addItem("Análoga", "ANALOG")
        nature = template.get("nature","DIGITAL")
        self.nature_combo.setCurrentIndex(0 if nature == "DIGITAL" else 1)
        lay.addWidget(QLabel("Naturaleza:"))
        lay.addWidget(self.nature_combo)

        # Block de pruebas (siempre en salida)
        self.test_block_chk = QCheckBox("Incluir block de pruebas (solo salida)")
        lay.addWidget(self.test_block_chk)

        self.pending_chk = QCheckBox("Marcar como pendiente (aunque exista destino)")
        lay.addWidget(self.pending_chk)

        btns = QHBoxLayout()
        ok = QPushButton("Crear")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_data(self):
        return {
            "signal_name": self.signal_name.text().strip() or "SIN_NOMBRE",
            "dest_device_id": self.dest_combo.currentData(),
            "pending": self.pending_chk.isChecked(),
            "nature": self.nature_combo.currentData(),
            "test_block": self.test_block_chk.isChecked(),
        }
