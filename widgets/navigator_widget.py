from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTreeWidget, QTreeWidgetItem, QMenu
)

from domain.services.pending_service import count_pending_for_bay, count_pending_for_device


class NavigatorWidget(QWidget):
    """Panel de navegación (combo bahía + árbol bahías/equipos)."""
    baySelected = pyqtSignal(str)                 # bay_id
    deviceSelected = pyqtSignal(str, str)         # bay_id, device_id
    bayRenameRequested = pyqtSignal(str)          # bay_id
    deviceRenameRequested = pyqtSignal(str, str)  # bay_id, device_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = None
        self._suspend_signals = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)

        hdr = QLabel("Bahías / Equipos")
        hdr.setStyleSheet("font-weight:600;")
        lay.addWidget(hdr)

        row = QHBoxLayout()
        row.addWidget(QLabel("Bahía:"))
        self.bay_combo = QComboBox()
        self.bay_combo.currentIndexChanged.connect(self._on_combo_changed)
        row.addWidget(self.bay_combo, 1)
        lay.addLayout(row)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_tree_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        lay.addWidget(self.tree, 1)

    def set_project(self, project) -> None:
        self._project = project
        self.refresh()

    def refresh(self) -> None:
        self._suspend_signals = True
        try:
            self.bay_combo.clear()
            self.tree.clear()
            project = self._project
            if not project:
                return

            # combo
            for bay_id, bay in project.bays.items():
                self.bay_combo.addItem(bay.name, bay_id)

            # tree
            for bay_id, bay in project.bays.items():
                counts = count_pending_for_bay(bay)
                label = bay.name
                if counts["total_pending"]:
                    label = f"{bay.name}  •  P:{counts['total_pending']} (OUT {counts['out_pending']}/IN {counts['in_pending']})"
                bay_item = QTreeWidgetItem([label])
                bay_item.setData(0, Qt.UserRole, ("BAY", bay_id, None))
                self.tree.addTopLevelItem(bay_item)

                for dev in bay.devices.values():
                    dcounts = count_pending_for_device(dev)
                    dlabel = dev.name
                    if dcounts["total_pending"]:
                        dlabel = f"{dev.name}  •  P:{dcounts['total_pending']} (OUT {dcounts['out_pending']}/IN {dcounts['in_pending']})"
                    dev_item = QTreeWidgetItem([dlabel])
                    dev_item.setData(0, Qt.UserRole, ("DEV", bay_id, dev.device_id))
                    bay_item.addChild(dev_item)

                bay_item.setExpanded(True)
        finally:
            self._suspend_signals = False

    def select_bay(self, bay_id: str) -> None:
        idx = self.bay_combo.findData(bay_id)
        if idx >= 0:
            self.bay_combo.setCurrentIndex(idx)

    def _on_combo_changed(self, _idx: int) -> None:
        if self._suspend_signals:
            return
        bay_id = self.bay_combo.currentData()
        if bay_id:
            self.baySelected.emit(bay_id)

    def _on_tree_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.UserRole)
        if not data or self._suspend_signals:
            return
        kind, bay_id, dev_id = data
        if kind == "BAY":
            self.baySelected.emit(bay_id)
        elif kind == "DEV":
            self.deviceSelected.emit(bay_id, dev_id)

    def _on_context_menu(self, pos: QPoint) -> None:
        """Menú contextual para renombrar bahías/equipos."""
        item = self.tree.itemAt(pos)
        if not item or self._suspend_signals:
            return
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        kind, bay_id, dev_id = data
        menu = QMenu(self)
        act_rename = None
        if kind == "BAY":
            act_rename = menu.addAction("Renombrar bahía…")
        elif kind == "DEV":
            act_rename = menu.addAction("Renombrar equipo…")

        chosen = menu.exec_(self.tree.mapToGlobal(pos))
        if not chosen or chosen != act_rename:
            return

        if kind == "BAY":
            self.bayRenameRequested.emit(bay_id)
        elif kind == "DEV":
            self.deviceRenameRequested.emit(bay_id, dev_id)

