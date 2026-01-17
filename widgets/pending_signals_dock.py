from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QAbstractItemView, QCheckBox
)

from ui.dialogs.recognize_signal_dialog import RecognizeSignalDialog
from ui.dialogs.edit_signal_dialog import EditSignalDialog
from domain.services.link_service import recognize_pending_link_cross, remove_link_project, rename_signal_texts


class PendingSignalsDock(QDockWidget):
    jumpRequested = pyqtSignal(str, str)      # bay_id, device_id
    projectMutated = pyqtSignal(set)          # bay_ids affected

    def __init__(self, parent=None):
        super().__init__("Pendientes", parent)
        self.setObjectName("PendingSignalsDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self._project = None

        w = QWidget()
        self.setWidget(w)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)

        # Filters
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Bahía:"))
        self.cmb_bay = QComboBox()
        self.cmb_bay.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.cmb_bay, 1)

        self.chk_only_out = QCheckBox("Solo OUT")
        self.chk_only_out.setChecked(True)
        self.chk_only_out.stateChanged.connect(self.refresh)
        fl.addWidget(self.chk_only_out)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar…")
        self.txt_search.textChanged.connect(self.refresh)
        fl.addWidget(self.txt_search, 2)

        lay.addLayout(fl)

        # Table
        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(["Bahía", "Equipo", "Dir", "SignalID", "Nombre", "Texto", "Estado"])
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.doubleClicked.connect(self._on_double_click)
        self.tbl.setAlternatingRowColors(True)
        lay.addWidget(self.tbl, 1)

        # Actions
        btns = QHBoxLayout()
        self.btn_jump = QPushButton("Ir al equipo")
        self.btn_rec = QPushButton("Reconocer…")
        self.btn_edit = QPushButton("Editar…")
        self.btn_del = QPushButton("Eliminar…")
        self.btn_next = QPushButton("Siguiente pendiente")
        self.btn_refresh = QPushButton("Actualizar")

        self.btn_jump.clicked.connect(self.jump_to_selected)
        self.btn_rec.clicked.connect(self.recognize_selected)
        self.btn_edit.clicked.connect(self.edit_selected)
        self.btn_del.clicked.connect(self.delete_selected)
        self.btn_next.clicked.connect(self.next_pending)
        self.btn_refresh.clicked.connect(self.refresh)

        for b in [self.btn_jump, self.btn_rec, self.btn_edit, self.btn_del]:
            btns.addWidget(b)
        btns.addWidget(self.btn_next)
        btns.addStretch(1)
        btns.addWidget(self.btn_refresh)
        lay.addLayout(btns)

    def set_project(self, project):
        self._project = project
        self._populate_bays()
        self.refresh()

    def _populate_bays(self):
        self.cmb_bay.blockSignals(True)
        self.cmb_bay.clear()
        self.cmb_bay.addItem("Todas", None)
        if self._project:
            for bay_id, bay in self._project.bays.items():
                self.cmb_bay.addItem(bay.name, bay_id)
        self.cmb_bay.blockSignals(False)

    def _collect_pending(self):
        if not self._project:
            return []

        filter_bay = self.cmb_bay.currentData()
        search = (self.txt_search.text() or "").strip().lower()
        only_out = self.chk_only_out.isChecked()

        rows = []
        for bay_id, bay in self._project.bays.items():
            if filter_bay and bay_id != filter_bay:
                continue
            for dev in bay.devices.values():
                ends = [("IN", e) for e in dev.inputs] + [("OUT", e) for e in dev.outputs]
                for direction, e in ends:
                    if only_out and direction != "OUT":
                        continue
                    if (e.status or "").upper() != "PENDING":
                        continue
                    sig = bay.signals.get(e.signal_id)
                    name = sig.name if sig else e.signal_id
                    txt_ = e.text or ""
                    if search and (search not in name.lower()
                                   and search not in txt_.lower()
                                   and search not in e.signal_id.lower()
                                   and search not in dev.name.lower()):
                        continue
                    rows.append({
                        "bay_id": bay_id,
                        "bay_name": bay.name,
                        "device_id": dev.device_id,
                        "device_name": dev.name,
                        "direction": direction,
                        "signal_id": e.signal_id,
                        "signal_name": name,
                        "text": txt_,
                        "status": e.status,
                    })
        return rows

    def refresh(self):
        data = self._collect_pending()
        self.tbl.setRowCount(0)
        for r in data:
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            values = [r["bay_name"], r["device_name"], r["direction"], r["signal_id"], r["signal_name"], r["text"], r["status"]]
            for c, v in enumerate(values):
                it = QTableWidgetItem(str(v))
                if c in (2, 6):
                    it.setTextAlignment(Qt.AlignCenter)
                self.tbl.setItem(row, c, it)
            self.tbl.item(row, 0).setData(Qt.UserRole, (r["bay_id"], r["device_id"], r["direction"], r["signal_id"]))

        self.tbl.resizeColumnsToContents()

    def _get_selected_rows(self):
        rows = sorted({it.row() for it in self.tbl.selectedItems()})
        out = []
        for r in rows:
            data = self.tbl.item(r, 0).data(Qt.UserRole)
            if data:
                out.append(data)
        return out

    def _get_selected(self):
        rows = self._get_selected_rows()
        return rows[0] if rows else None

    def jump_to_selected(self):
        sel = self._get_selected()
        if not sel:
            return
        bay_id, dev_id, _, _ = sel
        self.jumpRequested.emit(bay_id, dev_id)

    def _on_double_click(self):
        sel = self._get_selected()
        if not sel:
            return
        bay_id, dev_id, direction, _ = sel
        if direction == "OUT":
            self.recognize_selected()
        else:
            self.jumpRequested.emit(bay_id, dev_id)

    def next_pending(self):
        """Avanza al siguiente pendiente según filtros.
        - Si es OUT: abre el diálogo de reconocimiento automáticamente.
        - Si es IN: salta al equipo (no reconoce).
        """
        if self.tbl.rowCount() == 0:
            return

        sel_rows = sorted({it.row() for it in self.tbl.selectedItems()})
        cur = sel_rows[0] if sel_rows else -1

        next_row = cur + 1
        if next_row >= self.tbl.rowCount():
            next_row = 0

        self.tbl.clearSelection()
        self.tbl.selectRow(next_row)
        self.tbl.scrollToItem(self.tbl.item(next_row, 0), QAbstractItemView.PositionAtCenter)

        sel = self._get_selected()
        if not sel:
            return
        bay_id, dev_id, direction, _ = sel
        if direction == "OUT":
            self.recognize_selected()
        else:
            self.jumpRequested.emit(bay_id, dev_id)

    def recognize_selected(self):
        sel = self._get_selected()
        if not sel or not self._project:
            return
        bay_id, dev_id, direction, signal_id = sel
        if direction != "OUT":
            QMessageBox.information(self, "Reconocer", "Solo se reconoce desde una salida (OUT).")
            return

        dlg = RecognizeSignalDialog(self._project, origin_bay_id=bay_id, origin_device_id=dev_id, parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        dest_bay_id, dest_dev_id = dlg.get_selection()
        if not dest_bay_id or not dest_dev_id:
            return

        recognize_pending_link_cross(self._project, bay_id, dev_id, signal_id, dest_bay_id, dest_dev_id)
        self.refresh()
        self.projectMutated.emit({bay_id, dest_bay_id})
        QMessageBox.information(self, "OK", "Señal reconocida (creada entrada espejo y confirmada salida).")

    def edit_selected(self):
        sel = self._get_selected()
        if not sel or not self._project:
            return
        bay_id, _, _, signal_id = sel
        bay = self._project.bays.get(bay_id)
        if not bay:
            return
        sig = bay.signals.get(signal_id)
        if not sig:
            QMessageBox.warning(self, "Editar", "No se encontró la definición de la señal en esta bahía.")
            return

        dlg = EditSignalDialog(current_name=sig.name, current_nature=sig.nature, parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        new_name, new_nature = dlg.get_data()

        affected = set()
        for b in self._project.bays.values():
            if signal_id in b.signals:
                affected.add(b.bay_id)
                rename_signal_texts(b, signal_id, new_name)
                b.signals[signal_id].nature = new_nature

        self.refresh()
        self.projectMutated.emit(affected)
        QMessageBox.information(self, "OK", "Señal actualizada en el proyecto.")

    def delete_selected(self):
        if not self._project:
            return
        selected = self._get_selected_rows()
        if not selected:
            return

        signal_ids = sorted({sid for (_bay, _dev, _dir, sid) in selected})
        msg = f"Se eliminarán {len(signal_ids)} señales en todo el proyecto (IN/OUT).\n¿Continuar?"
        btn = QMessageBox.question(self, "Eliminar", msg, QMessageBox.Yes | QMessageBox.No)
        if btn != QMessageBox.Yes:
            return

        affected = set()
        for sid in signal_ids:
            for b in self._project.bays.values():
                if sid in b.signals:
                    affected.add(b.bay_id)
            remove_link_project(self._project, sid)

        self.refresh()
        self.projectMutated.emit(affected)
        QMessageBox.information(self, "OK", "Señales eliminadas del proyecto.")
