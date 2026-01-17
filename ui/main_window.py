from __future__ import annotations

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QSplitter,
    QAction, QMessageBox, QInputDialog
)

from ui.widgets.start_page import StartPage
from ui.widgets.template_library_dock import TemplateLibraryDock
from ui.widgets.canvas_host import CanvasHost
from widgets.navigator_widget import NavigatorWidget
from widgets.pending_signals_dock import PendingSignalsDock

from controllers.canvas_controller import CanvasController
from controllers.project_controller import ProjectController


class MainWindow(QMainWindow):
    """Ventana principal: layout + menú + wiring.

    Nota de arquitectura:
    - ProjectController maneja proyecto/I/O/diálogos.
    - CanvasController maneja escena/vista/layout por bahía.
    - MainWindow sólo coordina.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Mapper")
        self.resize(1400, 850)

        self.proj_ctrl = ProjectController(self, app_dir=os.getcwd())
        self.canvas_ctrl: CanvasController | None = None

        self._build_ui()
        self._build_menu()

        self._show_start_page()

    # ---------------- UI ----------------
    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        self.nav = NavigatorWidget(self)
        self.nav.baySelected.connect(self._on_bay_selected)
        self.nav.deviceSelected.connect(self._on_device_selected)
        self.nav.bayRenameRequested.connect(self._on_bay_rename_requested)
        self.nav.deviceRenameRequested.connect(self._on_device_rename_requested)
        splitter.addWidget(self.nav)
        splitter.setStretchFactor(0, 0)

        right = QWidget(self)
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(8, 8, 8, 8)
        self.lbl_canvas = QLabel("Canvas")
        self.lbl_canvas.setStyleSheet("font-weight:600;")
        rlay.addWidget(self.lbl_canvas, 0)

        self.canvas_host = CanvasHost(self)
        rlay.addWidget(self.canvas_host, 1)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        # Docks
        self.lib_dock = TemplateLibraryDock(self, app_dir=os.getcwd())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.lib_dock)

        self.pending_dock = PendingSignalsDock(self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.pending_dock)
        self.pending_dock.jumpRequested.connect(self._on_device_selected)
        self.pending_dock.projectMutated.connect(self._on_project_mutated)
        self.pending_dock.setVisible(False)

        # Canvas controller
        self.canvas_ctrl = CanvasController(
            get_project=lambda: self.proj_ctrl.project,
            template_dock=self.lib_dock,
            canvas_host=self.canvas_host,
            canvas_title_label=self.lbl_canvas,
            on_project_mutated=self._on_project_mutated,
        )

    def _build_menu(self):
        mb = self.menuBar()

        mproj = mb.addMenu("Proyecto")
        act_new = QAction("Nuevo…", self); act_new.triggered.connect(self.new_project); mproj.addAction(act_new)
        act_open = QAction("Abrir…", self); act_open.triggered.connect(self.open_project); mproj.addAction(act_open)
        act_save = QAction("Guardar", self); act_save.triggered.connect(self.save_project); mproj.addAction(act_save)
        act_saveas = QAction("Guardar como…", self); act_saveas.triggered.connect(self.save_project_as); mproj.addAction(act_saveas)

        mproj.addSeparator()
        act_add_bay = QAction("Nueva bahía…", self); act_add_bay.triggered.connect(self.add_bay); mproj.addAction(act_add_bay)
        act_add_dev = QAction("Nuevo equipo…", self); act_add_dev.triggered.connect(self.add_device); mproj.addAction(act_add_dev)
        act_rep_bay = QAction("Replicar bahía…", self); act_rep_bay.triggered.connect(self.replicate_bay); mproj.addAction(act_rep_bay)

        mexp = mb.addMenu("Exportar")
        act_xls = QAction("Excel (por bahía)…", self); act_xls.triggered.connect(self.export_excel); mexp.addAction(act_xls)
        act_png = QAction("Imagen PNG del canvas…", self); act_png.triggered.connect(self.export_canvas_png); mexp.addAction(act_png)

        mtemp = mb.addMenu("Plantillas")
        act_open_global = QAction("Abrir biblioteca global", self); act_open_global.triggered.connect(self.open_global_library); mtemp.addAction(act_open_global)
        act_import = QAction("Importar global → proyecto", self); act_import.triggered.connect(self.import_global_to_project); mtemp.addAction(act_import)

        mview = mb.addMenu("Ver")
        act_lib = QAction("Biblioteca de señales", self); act_lib.setCheckable(True); act_lib.setChecked(True)
        act_lib.toggled.connect(self.lib_dock.setVisible); mview.addAction(act_lib)

        act_pending = QAction("Pendientes", self); act_pending.setCheckable(True); act_pending.setChecked(False)
        act_pending.toggled.connect(self.pending_dock.setVisible); mview.addAction(act_pending)

    # ---------------- Actions ----------------
    def new_project(self):
        self.canvas_ctrl.persist_layout()
        self.proj_ctrl.new_project()
        self._after_project_changed()

    def open_project(self):
        self.canvas_ctrl.persist_layout()
        self.proj_ctrl.open_project()
        self._after_project_changed()

    def save_project(self):
        self.canvas_ctrl.persist_layout()
        self.proj_ctrl.save_project()

    def save_project_as(self):
        self.canvas_ctrl.persist_layout()
        self.proj_ctrl.save_project_as()

    def add_bay(self):
        if not self.proj_ctrl.project:
            QMessageBox.information(self, "Proyecto", "Abra o cree un proyecto primero.")
            return
        bay_id = self.proj_ctrl.add_bay()
        if bay_id:
            self._after_project_changed(open_bay_id=bay_id)

    def add_device(self):
        if not self.proj_ctrl.project:
            QMessageBox.information(self, "Proyecto", "Abra o cree un proyecto primero.")
            return
        if not self.proj_ctrl.project.bays:
            QMessageBox.information(self, "Equipo", "Primero cree una bahía.")
            return

        bay_id = self.canvas_ctrl.bay_id or self.proj_ctrl.default_bay_id()
        result = self.proj_ctrl.add_device(bay_id=bay_id, suggest_pos=self.canvas_ctrl.suggest_position_for_new_device())
        if not result:
            return
        device_id, data = result
        bay_id = data["bay_id"]

        if self.canvas_ctrl.bay_id != bay_id:
            self.canvas_ctrl.open_bay(bay_id)
            self.nav.select_bay(bay_id)

        pos = self.canvas_ctrl.suggest_position_for_new_device()
        self.canvas_ctrl.scene.add_device(device_id=device_id, name=data["name"], dev_type=data["dev_type"], pos=pos)
        self._after_project_changed(open_bay_id=bay_id)

    def replicate_bay(self):
        if not self.proj_ctrl.project:
            QMessageBox.information(self, "Proyecto", "Abra o cree un proyecto primero.")
            return
        new_id = self.proj_ctrl.replicate_bay()
        if new_id:
            self._after_project_changed(open_bay_id=new_id)

    def export_excel(self):
        if not self.proj_ctrl.project:
            QMessageBox.information(self, "Exportar", "Abra o cree un proyecto primero.")
            return
        self.canvas_ctrl.persist_layout()
        self.proj_ctrl.export_excel()

    def export_canvas_png(self):
        if not self.proj_ctrl.project or not self.canvas_ctrl.scene:
            QMessageBox.information(self, "Exportar", "Abra un proyecto y seleccione una bahía primero.")
            return
        self.canvas_ctrl.scene.export_canvas_png_dialog()

    def open_global_library(self):
        self.proj_ctrl.open_global_library()

    def import_global_to_project(self):
        if not self.proj_ctrl.project:
            QMessageBox.information(self, "Plantillas", "Abra o cree un proyecto primero.")
            return
        self.proj_ctrl.import_global_to_project()
        self._after_project_changed(open_bay_id=self.canvas_ctrl.bay_id)

    # ---------------- Navigation handlers ----------------
    def _on_bay_selected(self, bay_id: str):
        if not self.proj_ctrl.project:
            return
        self.canvas_ctrl.open_bay(bay_id)
        self.nav.select_bay(bay_id)

    def _on_device_selected(self, bay_id: str, device_id: str):
        if not self.proj_ctrl.project:
            return
        if self.canvas_ctrl.bay_id != bay_id:
            self.canvas_ctrl.open_bay(bay_id)
            self.nav.select_bay(bay_id)
        self.canvas_ctrl.select_device(device_id)

    def _on_bay_rename_requested(self, bay_id: str):
        if not self.proj_ctrl.project:
            return
        changed = self.proj_ctrl.rename_bay(bay_id)
        if changed:
            # refrescar navegador, docks, título del canvas
            self._on_project_mutated({bay_id})

    def _on_device_rename_requested(self, bay_id: str, device_id: str):
        if not self.proj_ctrl.project:
            return
        changed = self.proj_ctrl.rename_device(bay_id, device_id)
        if changed:
            self._on_project_mutated({bay_id})

    def _on_project_mutated(self, bay_ids: set):
        self._refresh_navigation()
        self.lib_dock.set_project(self.proj_ctrl.project)
        current = self.canvas_ctrl.bay_id
        if current and (not bay_ids or current in bay_ids):
            self.canvas_ctrl.open_bay(current)

    # ---------------- Helpers ----------------
    def _after_project_changed(self, open_bay_id: str | None = None):
        self._refresh_navigation()
        self.pending_dock.set_project(self.proj_ctrl.project)

        if self.proj_ctrl.project and self.proj_ctrl.project.bays:
            bay_id = open_bay_id or self.canvas_ctrl.bay_id or next(iter(self.proj_ctrl.project.bays.keys()))
            self.canvas_ctrl.open_bay(bay_id)
            self.nav.select_bay(bay_id)
        else:
            self._show_start_page()

    def _refresh_navigation(self):
        self.nav.set_project(self.proj_ctrl.project)

    def _show_start_page(self):
        lay = self.canvas_host.layout()
        while lay.count() > 0:
            w = lay.takeAt(0).widget()
            if w:
                w.setParent(None)
        sp = StartPage(self)
        sp.newProjectRequested.connect(self.new_project)
        sp.openProjectRequested.connect(self.open_project)
        sp.globalLibraryRequested.connect(self.open_global_library)
        lay.addWidget(sp, 1)
        self.lbl_canvas.setText("Canvas")
