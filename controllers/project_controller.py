from __future__ import annotations

import os

from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog

from domain.models import Project, Bay, CanvasLayout, SignalTemplate
from persistence.project_io import load_project, save_project
from persistence.template_store import load_global_templates
from export.excel_exporter import export_project_to_excel
from domain.services.replication_service import replicate_bay
from domain.services.rename_service import rename_device_in_project, rename_bay

from ui.dialogs.new_project_dialog import NewProjectDialog
from ui.dialogs.add_bay_dialog import AddBayDialog
from ui.dialogs.add_device_dialog import AddDeviceDialog
from ui.dialogs.replicate_bay_dialog import ReplicateBayDialog


class ProjectController:
    """Controlador de proyecto (I/O + creación + export).

    Objetivo: mantener una API estable para MainWindow y no filtrar IDs internos a la UI.
    """

    def __init__(self, main_window, app_dir: str | None = None):
        self._w = main_window
        self._app_dir = app_dir or os.getcwd()
        self.project: Project | None = None
        self.project_path: str | None = None

    # ---------------- Proyecto ----------------
    def new_project(self) -> None:
        dlg = NewProjectDialog(self._w)
        if dlg.exec_() != dlg.Accepted:
            return
        name = dlg.get_name()

        self.project = Project(schema_version="1.0", name=name)
        self.project_path = None

        # carga biblioteca global por defecto en el proyecto (editable dentro del proyecto)
        self.project.templates = load_global_templates(self._app_dir)

    def open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self._w, "Abrir proyecto", "", "Signal Mapper (*.json)")
        if not path:
            return
        try:
            self.project = load_project(path)
            self.project_path = path
        except Exception as e:
            QMessageBox.critical(self._w, "Abrir", str(e))

    def save_project(self) -> None:
        if not self.project:
            QMessageBox.information(self._w, "Guardar", "No hay proyecto.")
            return
        if not self.project_path:
            self.save_project_as()
            return
        try:
            save_project(self.project, self.project_path)
        except Exception as e:
            QMessageBox.critical(self._w, "Guardar", str(e))

    def save_project_as(self) -> None:
        if not self.project:
            QMessageBox.information(self._w, "Guardar", "No hay proyecto.")
            return
        path, _ = QFileDialog.getSaveFileName(self._w, "Guardar proyecto como", "", "Signal Mapper (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            save_project(self.project, path)
            self.project_path = path
        except Exception as e:
            QMessageBox.critical(self._w, "Guardar", str(e))

    def default_bay_id(self) -> str | None:
        if not self.project or not self.project.bays:
            return None
        return next(iter(self.project.bays.keys()))

    # ---------------- Bahías ----------------
    def _generate_bay_id(self) -> str:
        n = 1
        while True:
            bay_id = f"BAY-{n:03d}"
            if not self.project or bay_id not in self.project.bays:
                return bay_id
            n += 1

    def add_bay(self) -> str | None:
        if not self.project:
            QMessageBox.warning(self._w, "Bahía", "Crea o abre un proyecto primero.")
            return None

        dlg = AddBayDialog(self._w)
        if dlg.exec_() != dlg.Accepted:
            return None
        name = (dlg.get_data() or "").strip()
        if not name:
            QMessageBox.warning(self._w, "Bahía", "Nombre vacío.")
            return None

        bay_id = self._generate_bay_id()
        self.project.bays[bay_id] = Bay(bay_id=bay_id, name=name)
        self.project.canvases[bay_id] = CanvasLayout(bay_id=bay_id)
        return bay_id

    # ---------------- Equipos ----------------
    def _generate_device_id_for_bay(self, bay_id: str) -> str:
        bay = self.project.bays[bay_id]
        prefix = f"DEV-{bay_id}-"
        nums = []
        for dev_id in bay.devices.keys():
            if dev_id.startswith(prefix):
                try:
                    nums.append(int(dev_id.split(prefix, 1)[1]))
                except Exception:
                    pass
        n = (max(nums) + 1) if nums else 1
        return f"{prefix}{n:03d}"

    def add_device(self, bay_id: str | None = None, suggest_pos=None):
        """Muestra diálogo y retorna (device_id, data) o None.

        data = {bay_id, name, dev_type}
        La creación real del nodo+modelo ocurre en CanvasScene.add_device().
        """
        if not self.project:
            QMessageBox.warning(self._w, "Equipo", "Crea o abre un proyecto primero.")
            return None
        if not self.project.bays:
            QMessageBox.information(self._w, "Equipo", "Primero crea una bahía.")
            return None

        bay_choices = [(b.name, b.bay_id) for b in self.project.bays.values()]
        default_bay = bay_id or self.default_bay_id()
        dlg = AddDeviceDialog(bay_choices, default_bay_id=default_bay, parent=self._w)
        if dlg.exec_() != dlg.Accepted:
            return None

        data = dlg.get_data()
        if data["bay_id"] not in self.project.bays:
            QMessageBox.warning(self._w, "Equipo", "Bahía no válida.")
            return None

        device_id = self._generate_device_id_for_bay(data["bay_id"])
        return device_id, data

    # ---------------- Replicar ----------------
    def replicate_bay(self) -> str | None:
        if not self.project or not self.project.bays:
            QMessageBox.warning(self._w, "Replicar", "No hay proyecto/bahías.")
            return None

        bay_choices = [(b.name, b.bay_id) for b in self.project.bays.values()]
        first = next(iter(self.project.bays.values()))
        src_token = (first.name or "").strip()

        dlg = ReplicateBayDialog(bay_choices, default_name="Nueva Bahía", src_token=src_token, parent=self._w)
        if dlg.exec_() != dlg.Accepted:
            return None
        data = dlg.get_data()

        src_id = data["source_bay_id"]
        if src_id not in self.project.bays:
            QMessageBox.critical(self._w, "Replicar", "No se encuentra la bahía origen.")
            return None

        new_id = self._generate_bay_id()

        try:
            created_id = replicate_bay(
                project=self.project,
                src_bay_id=src_id,
                new_bay_id=new_id,
                new_bay_name=data["new_bay_name"],
                dx=data["dx"],
                dy=data["dy"],
                src_token=data["src_token"],
                dst_token=data["dst_token"],
                apply_to_external=data["apply_to_external"],
            )
            QMessageBox.information(self._w, "Replicar", f"Bahía replicada: {self.project.bays[created_id].name}")
            return created_id
        except Exception as e:
            QMessageBox.critical(self._w, "Replicar", str(e))
            return None

    # ---------------- Rename ----------------
    def rename_bay(self, bay_id: str) -> bool:
        if not self.project or bay_id not in self.project.bays:
            return False
        bay = self.project.bays[bay_id]
        new_name, ok = QInputDialog.getText(self._w, "Renombrar bahía", "Nuevo nombre de bahía:", text=bay.name)
        if not ok:
            return False
        new_name = (new_name or "").strip()
        if not new_name:
            QMessageBox.warning(self._w, "Bahía", "Nombre vacío.")
            return False
        rename_bay(self.project, bay_id=bay_id, new_name=new_name)
        return True

    def rename_device(self, bay_id: str, device_id: str) -> bool:
        if not self.project or bay_id not in self.project.bays:
            return False
        bay = self.project.bays[bay_id]
        dev = bay.devices.get(device_id)
        if not dev:
            return False
        new_name, ok = QInputDialog.getText(self._w, "Renombrar equipo", "Nuevo nombre del equipo:", text=dev.name)
        if not ok:
            return False
        new_name = (new_name or "").strip()
        if not new_name:
            QMessageBox.warning(self._w, "Equipo", "Nombre vacío.")
            return False
        if new_name == dev.name:
            return False
        try:
            rename_device_in_project(self.project, bay_id=bay_id, device_id=device_id, new_name=new_name)
            return True
        except Exception as e:
            QMessageBox.critical(self._w, "Equipo", str(e))
            return False

    # ---------------- Plantillas ----------------
    def open_global_library(self) -> None:
        QMessageBox.information(
            self._w, "Plantillas",
            "La biblioteca global se gestiona en el dock (Fuente: Global).\n"
            "Se guarda automáticamente en template_library.json."
        )

    def import_global_to_project(self) -> None:
        if not self.project:
            return
        self.project.templates = load_global_templates(self._app_dir)
        QMessageBox.information(self._w, "Plantillas", "Biblioteca global importada al proyecto.")

    # ---------------- Export ----------------
    def export_excel(self) -> None:
        if not self.project:
            return
        path, _ = QFileDialog.getSaveFileName(self._w, "Exportar a Excel", f"{self.project.name}.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            export_project_to_excel(self.project, path)
            QMessageBox.information(self._w, "Exportación", "Excel exportado.")
        except Exception as e:
            QMessageBox.critical(self._w, "Exportación", str(e))
