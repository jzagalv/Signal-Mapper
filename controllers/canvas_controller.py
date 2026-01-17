from __future__ import annotations

from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QMessageBox

from canvas.scene import CanvasScene
from ui.widgets.canvas_view import CanvasView


class CanvasController:
    """Gestiona la escena/vista por bahía y operaciones de selección/centrado."""

    def __init__(self, *, get_project, template_dock, canvas_host, canvas_title_label, on_project_mutated=None):
        self._get_project = get_project
        self._template_dock = template_dock
        self._canvas_host = canvas_host
        self._canvas_title = canvas_title_label
        self._on_project_mutated = on_project_mutated

        self.bay_id: str | None = None
        self.scene: CanvasScene | None = None
        self.view: CanvasView | None = None

    def persist_layout(self):
        if self.scene:
            self.scene.persist_layout_to_model()

    def open_bay(self, bay_id: str):
        project = self._get_project()
        if not project:
            return

        self.persist_layout()

        lay = self._canvas_host.layout()
        while lay.count() > 0:
            w = lay.takeAt(0).widget()
            if w:
                w.setParent(None)

        self.bay_id = bay_id
        self.scene = CanvasScene(project, bay_id, on_project_mutated=self._on_project_mutated)
        self.scene.build_from_model()
        self.view = CanvasView(self.scene)

        if hasattr(self._template_dock, "set_scene"):
            self._template_dock.set_scene(self.scene)

        self._canvas_title.setText(f"Canvas — {project.bays[bay_id].name}")
        lay.addWidget(self.view, 1)

    def select_device(self, device_id: str):
        if not self.scene or not self.view:
            return
        if not hasattr(self.scene, "select_device_item"):
            QMessageBox.warning(None, "Canvas", "CanvasScene no soporta selección por ID.")
            return
        item = self.scene.select_device_item(device_id)
        if item:
            self.view.centerOn(item)

    def suggest_position_for_new_device(self) -> QPointF | None:
        if not self.scene:
            return None
        if getattr(self.scene, "device_items", None):
            rect = self.scene.itemsBoundingRect()
            return QPointF(rect.right() + 120, rect.top() + 40)
        return None
