from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QListWidget, QListWidgetItem, QInputDialog, QMessageBox
)


class SignalDecorationsDialog(QDialog):
    """Editor de block de pruebas / enclavamientos.

    Reglas de ingeniería:
    - Block de pruebas sólo en OUT (texto fijo "B.P.").
    - Enclavamientos sólo en IN.
    - Cada enclavamiento requiere relay_tag (ej: 86T2) obligatorio.
    """

    def __init__(
        self,
        *,
        is_output: bool,
        current_test_block: bool,
        current_interlocks: list[str],
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Bloqueos / Enclavamientos")

        self._is_output = bool(is_output)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)

        # Test block (OUT)
        if self._is_output:
            self.chk_test = QCheckBox('Block de pruebas (se mostrará como "B.P." en la salida)')
            self.chk_test.setChecked(bool(current_test_block))
            lay.addWidget(self.chk_test)
        else:
            self.chk_test = None
            hint = QLabel("Block de pruebas: sólo aplica a salidas (OUT).")
            hint.setStyleSheet("color:#555;")
            lay.addWidget(hint)

        # Interlocks (IN)
        if self._is_output:
            hint2 = QLabel("Enclavamientos: sólo aplica a entradas (IN).")
            hint2.setStyleSheet("color:#555;")
            lay.addWidget(hint2)
            self.lst = None
        else:
            lay.addWidget(QLabel("Enclavamientos (relay_tag obligatorio, ej: 86T2):"))
            self.lst = QListWidget()
            self.lst.setSelectionMode(self.lst.SingleSelection)
            for tag in current_interlocks or []:
                tag = (tag or "").strip()
                if tag:
                    self.lst.addItem(QListWidgetItem(tag))
            self.lst.itemDoubleClicked.connect(self._edit_selected)
            lay.addWidget(self.lst, 1)

            btn_row = QHBoxLayout()
            self.btn_add = QPushButton("Agregar…")
            self.btn_edit = QPushButton("Editar…")
            self.btn_del = QPushButton("Eliminar")
            self.btn_add.clicked.connect(self._add)
            self.btn_edit.clicked.connect(self._edit_selected)
            self.btn_del.clicked.connect(self._delete_selected)
            btn_row.addWidget(self.btn_add)
            btn_row.addWidget(self.btn_edit)
            btn_row.addWidget(self.btn_del)
            btn_row.addStretch(1)
            lay.addLayout(btn_row)

        # OK/Cancel
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        ok = QPushButton("Guardar")
        cancel = QPushButton("Cancelar")
        ok.clicked.connect(self._on_accept)
        cancel.clicked.connect(self.reject)
        bottom.addWidget(ok)
        bottom.addWidget(cancel)
        lay.addLayout(bottom)

        self.resize(420, 360)

    def _ask_tag(self, title: str, current: str = "") -> str | None:
        text, ok = QInputDialog.getText(
            self,
            title,
            "Relay tag (obligatorio, ej: 86T2):",
            text=(current or ""),
        )
        if not ok:
            return None
        tag = (text or "").strip()
        if not tag:
            QMessageBox.warning(self, "Enclavamiento", "relay_tag es obligatorio (ej: 86T2).")
            return None
        return tag

    def _add(self):
        if not self.lst:
            return
        tag = self._ask_tag("Agregar enclavamiento")
        if not tag:
            return
        existing = {self.lst.item(i).text().strip() for i in range(self.lst.count())}
        if tag in existing:
            QMessageBox.information(self, "Enclavamiento", "Ese relay_tag ya existe en la lista.")
            return
        self.lst.addItem(QListWidgetItem(tag))

    def _edit_selected(self, *_args):
        if not self.lst:
            return
        it = self.lst.currentItem()
        if not it:
            return
        new_tag = self._ask_tag("Editar enclavamiento", current=it.text())
        if not new_tag:
            return
        it.setText(new_tag)

    def _delete_selected(self):
        if not self.lst:
            return
        row = self.lst.currentRow()
        if row >= 0:
            self.lst.takeItem(row)

    def _on_accept(self):
        # Enforce rules at UI level
        if not self._is_output and self.lst:
            # Ensure no empty tags
            tags = [self.lst.item(i).text().strip() for i in range(self.lst.count())]
            if any(not t for t in tags):
                QMessageBox.warning(self, "Enclavamiento", "Todos los enclavamientos requieren relay_tag.")
                return
        self.accept()

    def get_data(self):
        test_block = bool(self.chk_test.isChecked()) if self.chk_test else False
        if self.lst:
            tags = [self.lst.item(i).text().strip() for i in range(self.lst.count()) if self.lst.item(i).text().strip()]
        else:
            tags = []
        return test_block, tags
