from __future__ import annotations
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox

class EditSignalDialog(QDialog):
    def __init__(
        self,
        current_name: str,
        current_nature: str,
        *,
        is_output: bool = False,
        current_test_block: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Editar señal")
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Nombre:"))
        self.name_edit = QLineEdit(current_name); lay.addWidget(self.name_edit)

        lay.addWidget(QLabel("Naturaleza:"))
        self.nature_combo = QComboBox()
        self.nature_combo.addItem("Digital", "DIGITAL")
        self.nature_combo.addItem("Análoga", "ANALOG")
        self.nature_combo.setCurrentIndex(0 if current_nature == "DIGITAL" else 1)
        lay.addWidget(self.nature_combo)

        # Block de pruebas (sólo OUT)
        self._is_output = bool(is_output)
        if self._is_output:
            self.chk_test_block = QCheckBox('Block de pruebas (se mostrará como "B.P." en la salida)')
            self.chk_test_block.setChecked(bool(current_test_block))
            lay.addWidget(self.chk_test_block)
        else:
            self.chk_test_block = None

        btns = QHBoxLayout()
        ok = QPushButton("Guardar"); cancel = QPushButton("Cancelar")
        ok.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        btns.addWidget(ok); btns.addWidget(cancel)
        lay.addLayout(btns)

    def get_data(self):
        name = self.name_edit.text().strip() or "SIN_NOMBRE"
        nature = self.nature_combo.currentData()
        tb = bool(self.chk_test_block.isChecked()) if self.chk_test_block else False
        return name, nature, tb
