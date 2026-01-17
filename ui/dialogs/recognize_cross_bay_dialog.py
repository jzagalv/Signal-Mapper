
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton

class RecognizeCrossBayDialog(QDialog):
    def __init__(self, project, origin_bay_id, origin_device_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reconocer señal (otra bahía)")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Destino:"))
        self.combo = QComboBox()
        for bay in project.bays.values():
            for dev in bay.devices.values():
                self.combo.addItem(f"{bay.name} / {dev.name}", (bay.bay_id, dev.device_id))
        lay.addWidget(self.combo)

        btn = QPushButton("Reconocer")
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)

    def get_selection(self):
        return self.combo.currentData()
