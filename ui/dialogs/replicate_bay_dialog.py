from __future__ import annotations

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QSpinBox, QCheckBox, QPushButton
)


class ReplicateBayDialog(QDialog):
    """Replicar bahía sin exponer ID interno.
    El usuario elige:
    - bahía origen (por nombre)
    - nombre bahía destino
    - token origen/destino para reemplazo (ej: H1 -> H2)
    - offsets dx/dy para desplazar nodos
    - si aplica reemplazo también en señales externas
    """

    def __init__(self, bay_choices, default_name: str, src_token: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Replicar bahía")
        self.setModal(True)

        lay = QVBoxLayout(self)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Bahía origen:"))
        self.cmb_src = QComboBox()
        for name, bay_id in bay_choices:
            self.cmb_src.addItem(name, bay_id)
        row1.addWidget(self.cmb_src, 1)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Nombre bahía destino:"))
        self.ed_name = QLineEdit(default_name)
        row2.addWidget(self.ed_name, 1)
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Reemplazo token (origen → destino):"))
        self.ed_src = QLineEdit(src_token)
        self.ed_dst = QLineEdit("")
        self.ed_src.setPlaceholderText("H1")
        self.ed_dst.setPlaceholderText("H2")
        row3.addWidget(self.ed_src, 1)
        row3.addWidget(QLabel("→"))
        row3.addWidget(self.ed_dst, 1)
        lay.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Desplazamiento nodos:"))
        self.sp_dx = QSpinBox(); self.sp_dx.setRange(-5000, 5000); self.sp_dx.setValue(180)
        self.sp_dy = QSpinBox(); self.sp_dy.setRange(-5000, 5000); self.sp_dy.setValue(0)
        row4.addWidget(QLabel("dx"))
        row4.addWidget(self.sp_dx)
        row4.addWidget(QLabel("dy"))
        row4.addWidget(self.sp_dy)
        row4.addStretch(1)
        lay.addLayout(row4)

        self.chk_external = QCheckBox("Aplicar reemplazo también a señales externas")
        self.chk_external.setChecked(True)
        lay.addWidget(self.chk_external)

        btns = QHBoxLayout()
        btns.addStretch(1)
        ok = QPushButton("Replicar")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_data(self):
        return {
            "source_bay_id": self.cmb_src.currentData(),
            "new_bay_name": self.ed_name.text().strip(),
            "dx": int(self.sp_dx.value()),
            "dy": int(self.sp_dy.value()),
            "src_token": self.ed_src.text().strip(),
            "dst_token": self.ed_dst.text().strip(),
            "apply_to_external": bool(self.chk_external.isChecked()),
        }
