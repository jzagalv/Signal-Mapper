from __future__ import annotations

import json
import os

from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QComboBox, QLineEdit, QMessageBox
)

from domain.models import SignalTemplate
from ui.dialogs.edit_template_dialog import EditTemplateDialog
from persistence.template_store import load_global_templates, save_global_templates


class TemplateList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QListWidget.SingleSelection)

    def mouseMoveEvent(self, event):
        item = self.currentItem()
        if not item:
            return super().mouseMoveEvent(event)
        if not (event.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(event)

        payload = item.data(Qt.UserRole)
        mime = QMimeData()
        mime.setData("application/x-signal-template", json.dumps(payload).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(Qt.CopyAction)


class TemplateLibraryDock(QDockWidget):
    """Biblioteca de señales (plantillas) con drag&drop a nodos.

    Fuente:
    - Proyecto: project.templates
    - Global: template_library.json en app_dir
    """

    def __init__(self, parent=None, app_dir: str | None = None):
        super().__init__("Biblioteca de Señales", parent)
        self._project = None
        self._scene = None
        self._app_dir = app_dir or os.getcwd()
        self._global_templates = load_global_templates(self._app_dir)

        root = QWidget()
        lay = QVBoxLayout(root)
        lay.setContentsMargins(8, 8, 8, 8)

        top = QHBoxLayout()
        top.addWidget(QLabel("Fuente:"))
        self.source = QComboBox()
        self.source.addItem("Proyecto", "PROJECT")
        self.source.addItem("Global", "GLOBAL")
        self.source.currentIndexChanged.connect(self._refresh)
        top.addWidget(self.source, 1)

        top.addWidget(QLabel("Categoría:"))
        self.category = QComboBox()
        self.category.currentIndexChanged.connect(self._refresh)
        top.addWidget(self.category, 2)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar…")
        self.search.textChanged.connect(self._refresh)
        top.addWidget(self.search, 3)
        lay.addLayout(top)

        self.list = TemplateList()
        lay.addWidget(self.list, 1)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("+ Nueva")
        self.btn_edit = QPushButton("Editar")
        self.btn_del = QPushButton("Eliminar")
        self.btn_add.clicked.connect(self.add_template)
        self.btn_edit.clicked.connect(self.edit_selected)
        self.btn_del.clicked.connect(self.delete_selected)
        btns.addWidget(self.btn_add); btns.addWidget(self.btn_edit); btns.addWidget(self.btn_del)
        lay.addLayout(btns)

        self.setWidget(root)

        self._rebuild_categories()
        self._refresh()

    def set_scene(self, scene):
        self._scene = scene

    def set_project(self, project):
        self._project = project
        if project is None:
            self.source.setCurrentIndex(1)  # Global
        self._rebuild_categories()
        self._refresh()

    def set_global_templates(self, templates):
        self._global_templates = list(templates or [])
        self._rebuild_categories()
        self._refresh()

    def _save_global(self):
        save_global_templates(self._app_dir, self._global_templates)

    def _current_templates(self):
        src = self.source.currentData()
        if src == "PROJECT":
            return (self._project.templates if self._project else [])
        return self._global_templates

    def _rebuild_categories(self):
        self.category.blockSignals(True)
        try:
            self.category.clear()
            self.category.addItem("Todas", None)
            cats = sorted({t.category for t in self._current_templates() if getattr(t, "category", None)})
            for c in cats:
                self.category.addItem(c, c)
        finally:
            self.category.blockSignals(False)

    def _refresh(self):
        # si no hay proyecto, forzar global
        if self.source.currentData() == "PROJECT" and not self._project:
            self.source.blockSignals(True)
            self.source.setCurrentIndex(1)
            self.source.blockSignals(False)

        self.list.clear()
        cat = self.category.currentData()
        q = (self.search.text() or "").strip().lower()

        for t in self._current_templates():
            if cat and t.category != cat:
                continue
            if q and (q not in (t.code or "").lower()) and (q not in (t.label or "").lower()):
                continue

            label = f"[{t.category}] {t.code} — {t.label}"
            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, {
                "code": t.code,
                "label": t.label,
                "nature": t.nature,
                "category": t.category,
                "description": t.description,
            })
            self.list.addItem(it)

    def add_template(self):
        existing = [t.code for t in self._current_templates()]
        dlg = EditTemplateDialog(existing_codes=existing, parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        data, err = dlg.get_data()
        if err:
            QMessageBox.warning(self, "Plantilla", err)
            return
        t = SignalTemplate(**data)

        if self.source.currentData() == "PROJECT":
            if not self._project:
                QMessageBox.information(self, "Plantillas", "No hay proyecto.")
                return
            self._project.templates.append(t)
        else:
            self._global_templates.append(t)
            self._save_global()

        self._rebuild_categories()
        self._refresh()

    def _selected_code(self):
        it = self.list.currentItem()
        if not it:
            return None
        payload = it.data(Qt.UserRole) or {}
        return payload.get("code")

    def edit_selected(self):
        code = self._selected_code()
        if not code:
            return
        arr = self._current_templates()
        current = next((t for t in arr if t.code == code), None)
        if not current:
            return
        existing = [t.code for t in arr]
        dlg = EditTemplateDialog(template=current, existing_codes=existing, parent=self)
        if dlg.exec_() != dlg.Accepted:
            return
        data, err = dlg.get_data()
        if err:
            QMessageBox.warning(self, "Plantilla", err)
            return
        new_t = SignalTemplate(**data)

        for i, x in enumerate(arr):
            if x.code == code:
                arr[i] = new_t
                break

        if self.source.currentData() == "GLOBAL":
            self._save_global()

        self._rebuild_categories()
        self._refresh()

    def delete_selected(self):
        code = self._selected_code()
        if not code:
            return
        if QMessageBox.question(self, "Eliminar", "¿Eliminar la plantilla seleccionada?") != QMessageBox.Yes:
            return
        arr = self._current_templates()
        arr[:] = [t for t in arr if t.code != code]
        if self.source.currentData() == "GLOBAL":
            self._save_global()
        self._rebuild_categories()
        self._refresh()
