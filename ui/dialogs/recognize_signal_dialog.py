from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton

class RecognizeSignalDialog(QDialog):
    def __init__(self, project, origin_bay_id: str, origin_device_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reconocer señal (resolver pendiente)")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Seleccione bahía y equipo destino (se creará la entrada espejo):"))

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Bahía:"))
        self.bay_combo = QComboBox()
        for bay_id, bay in project.bays.items():
            self.bay_combo.addItem(bay.name, bay_id)
        # set current bay
        idx = self.bay_combo.findData(origin_bay_id)
        if idx >= 0:
            self.bay_combo.setCurrentIndex(idx)
        self.bay_combo.currentIndexChanged.connect(lambda _=None: self._reload_devices(project, origin_bay_id, origin_device_id))
        row1.addWidget(self.bay_combo, 1)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Equipo:"))
        self.dev_combo = QComboBox()
        row2.addWidget(self.dev_combo, 1)
        lay.addLayout(row2)

        self._reload_devices(project, origin_bay_id, origin_device_id)

        btns = QHBoxLayout()
        ok = QPushButton("Reconocer"); cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def _reload_devices(self, project, origin_bay_id: str, origin_device_id: str):
        bay_id = self.bay_combo.currentData()
        self.dev_combo.clear()
        self.dev_combo.addItem("— Seleccione —", None)
        bay = project.bays.get(bay_id)
        if not bay:
            return
        for dev in bay.devices.values():
            if bay_id == origin_bay_id and dev.device_id == origin_device_id:
                continue
            self.dev_combo.addItem(dev.name, dev.device_id)

    def get_selection(self):
        return (self.bay_combo.currentData(), self.dev_combo.currentData())
