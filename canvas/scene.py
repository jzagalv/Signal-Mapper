from __future__ import annotations
from PyQt5.QtWidgets import QGraphicsScene, QMessageBox, QFileDialog, QInputDialog
from PyQt5.QtCore import QPointF, QRectF,Qt
from PyQt5.QtGui import QImage, QPainter

from canvas.items.device_item import DeviceItem
from canvas.items.signal_chip_item import SignalChipItem
from canvas.items.test_block import should_show_test_block
from domain.services.pending_service import count_pending_for_device

class CanvasScene(QGraphicsScene):
    def __init__(self, project, bay_id: str, parent=None, *, on_project_mutated=None):
        super().__init__(parent)
        self.project = project
        self.bay_id = bay_id
        self.device_items = {}
        self._base_scene_rect = QRectF(0, 0, 2200, 1400)
        self._scene_margin = 200
        self._updating_scene_rect = False
        self.setSceneRect(self._base_scene_rect)
        self._clipboard_device_id = None
        self._on_project_mutated = on_project_mutated
        self.changed.connect(self._on_scene_changed)

    def _on_scene_changed(self, _regions):
        self._update_scene_rect()

    def _update_scene_rect(self):
        if self._updating_scene_rect:
            return
        self._updating_scene_rect = True
        try:
            rect = self.itemsBoundingRect()
            if rect.isNull():
                self.setSceneRect(self._base_scene_rect)
                return
            rect = rect.adjusted(
                -self._scene_margin,
                -self._scene_margin,
                self._scene_margin,
                self._scene_margin,
            )
            self.setSceneRect(rect)
        finally:
            self._updating_scene_rect = False

    # ---------------- Build / Layout ----------------
    def build_from_model(self):
        # IMPORTANT: antes de reconstruir, persistimos posiciones actuales
        if self.device_items:
            self.persist_layout_to_model()

        self.clear()
        self.device_items.clear()

        bay = self.project.bays[self.bay_id]
        out_test_block = {}
        for dev in bay.devices.values():
            for e in dev.outputs:
                if bool(getattr(e, "test_block", False)):
                    out_test_block[e.signal_id] = True
        layout = self.project.canvases.get(self.bay_id)

        x, y = 160, 140
        for dev in bay.devices.values():
            item = DeviceItem(dev.device_id, dev.name, dev.dev_type)
            pc = count_pending_for_device(dev)
            item.set_pending_counts(pc['in_pending'], pc['out_pending'])

            if layout and dev.device_id in layout.device_positions:
                p = layout.device_positions[dev.device_id]
                item.setPos(QPointF(p.get("x", x), p.get("y", y)))
            else:
                item.setPos(QPointF(x, y))
                x += 560
                if x > 1700:
                    x = 160
                    y += 340
            in_chips = []
            for e in dev.inputs:
                sig = bay.signals.get(e.signal_id)
                nature = sig.nature if sig else "DIGITAL"
                itags = e.interlock_tags() if hasattr(e, "interlock_tags") else []
                tooltip = (
                    f"Equipo: {dev.name}\nDirección: IN\nSignalID: {e.signal_id}\nTexto: {e.text}\nEstado: {e.status}"
                    + (f"\nEnclavamientos: {', '.join(itags)}" if itags else "")
                )
                in_chips.append(SignalChipItem(
                    signal_id=e.signal_id,
                    owner_device_id=dev.device_id,
                    text=e.text,
                    nature=nature,
                    status=e.status,
                    direction="IN",
                    tooltip=tooltip,
                    interlocks=itags,
                    test_block=bool(out_test_block.get(e.signal_id, False))
                    and should_show_test_block("IN", nature),
                ))

            out_chips = []
            for e in dev.outputs:
                sig = bay.signals.get(e.signal_id)
                nature = sig.nature if sig else "DIGITAL"
                tooltip = (
                    f"Equipo: {dev.name}\nDirección: OUT\nSignalID: {e.signal_id}\nTexto: {e.text}\nEstado: {e.status}"
                    + ("\nBlock de pruebas: B.P." if bool(getattr(e, "test_block", False)) else "")
                )
                out_chips.append(SignalChipItem(
                    signal_id=e.signal_id,
                    owner_device_id=dev.device_id,
                    text=e.text,
                    nature=nature,
                    status=e.status,
                    direction="OUT",
                    tooltip=tooltip,
                    test_block=bool(getattr(e, "test_block", False))
                    and should_show_test_block("OUT", nature),
                    interlocks=[],
                ))

            item.set_signals(in_chips, out_chips)
            self.addItem(item)
            self.device_items[dev.device_id] = item
        self._update_scene_rect()

    def persist_layout_to_model(self):
        from domain.models import CanvasLayout
        if self.bay_id not in self.project.canvases:
            self.project.canvases[self.bay_id] = CanvasLayout(bay_id=self.bay_id)
        layout = self.project.canvases[self.bay_id]
        for dev_id, item in self.device_items.items():
            pos = item.pos()
            layout.device_positions[dev_id] = {"x": float(pos.x()), "y": float(pos.y())}

    # ---------------- Devices ----------------
    def add_device(self, device_id: str, name: str, dev_type: str, pos: QPointF | None = None):
        from domain.models import Device, CanvasLayout
        bay = self.project.bays[self.bay_id]
        if device_id in bay.devices:
            raise ValueError("Device ID ya existe en esta bahía.")
        dev = Device(device_id=device_id, bay_id=self.bay_id, name=name, dev_type=dev_type)
        bay.devices[device_id] = dev

        if self.bay_id not in self.project.canvases:
            self.project.canvases[self.bay_id] = CanvasLayout(bay_id=self.bay_id)
        p = pos or QPointF(200, 200)
        self.project.canvases[self.bay_id].device_positions[device_id] = {"x": float(p.x()), "y": float(p.y())}
        self.build_from_model()
        if callable(self._on_project_mutated):
            self._on_project_mutated({self.bay_id})

    def delete_device(self, device_id: str):
        bay = self.project.bays[self.bay_id]
        if device_id not in bay.devices:
            return
        del bay.devices[device_id]
        if self.bay_id in self.project.canvases:
            self.project.canvases[self.bay_id].device_positions.pop(device_id, None)
        self.build_from_model()

    # ---------------- Signals creation ----------------
    def on_template_dropped(self, origin_device_id: str, template: dict):
        # persistimos layout actual para no perder reordenamientos
        self.persist_layout_to_model()

        from ui.dialogs.signal_link_dialog import SignalLinkDialog
        from domain.models import Signal, SignalEnd

        bay = self.project.bays[self.bay_id]
        origin = bay.devices[origin_device_id]

        self.persist_layout_to_model()

        dlg = SignalLinkDialog(bay, origin, template)
        if dlg.exec_() != dlg.Accepted:
            return
        data = dlg.get_data()

        sid = f"SIG-{len(bay.signals) + 1:03d}"
        signal = Signal(signal_id=sid, name=data["signal_name"], nature=data["nature"])
        bay.signals[sid] = signal

        if data["dest_device_id"] is None:
            dest_name, status = "EXTERNO", "PENDING"
        else:
            dest_name = bay.devices[data["dest_device_id"]].name
            status = "PENDING" if data["pending"] else "CONFIRMED"

        origin.outputs.append(SignalEnd(
            signal_id=sid,
            direction="OUT",
            text=f"{signal.name} hacia {dest_name}" + (" (pendiente)" if status == "PENDING" else ""),
            status=status
        ))

        if data["dest_device_id"] is not None:
            dest = bay.devices[data["dest_device_id"]]
            dest.inputs.append(SignalEnd(
                signal_id=sid,
                direction="IN",
                text=f"{signal.name} desde {origin.name}",
                status="CONFIRMED"
            ))

        self.build_from_model()

    # ---------------- Chip actions ----------------
    def recognize_signal_from_chip(self, chip: SignalChipItem):
        from ui.dialogs.recognize_signal_dialog import RecognizeSignalDialog
        from domain.services.link_service import recognize_pending_link_cross
        dlg = RecognizeSignalDialog(self.project, origin_bay_id=self.bay_id, origin_device_id=chip.owner_device_id)
        if dlg.exec_() != dlg.Accepted:
            return
        dest_bay_id, dest_id = dlg.get_selection()
        if dest_id is None or dest_bay_id is None:
            return
        recognize_pending_link_cross(self.project, self.bay_id, chip.owner_device_id, chip.signal_id, dest_bay_id, dest_id)
        self.build_from_model()
        QMessageBox.information(None, "OK", "Señal reconocida (se creó entrada espejo en el equipo destino).")

    def edit_signal_from_chip(self, chip: SignalChipItem):
        from ui.dialogs.edit_signal_dialog import EditSignalDialog
        from domain.services.link_service import (
            find_signal_destination_device_id,
            rename_signal_texts,
            update_signal_destination,
        )
        bay = self.project.bays[self.bay_id]
        sig = bay.signals.get(chip.signal_id)
        if not sig:
            QMessageBox.warning(None, "Atención", "No se encontró la señal en el modelo.")
            return

        # Al editar desde un chip OUT, permitir togglear Block de Pruebas.
        # Ojo: el BP es decoración del extremo (SignalEnd), no de la señal lógica.
        tb_current = False
        if chip.direction == "OUT":
            dev = bay.devices.get(chip.owner_device_id)
            if dev:
                end = next((e for e in dev.outputs if e.signal_id == chip.signal_id), None)
                tb_current = bool(getattr(end, "test_block", False)) if end else False

        current_dest_id = find_signal_destination_device_id(bay, chip.signal_id)
        dest_choices = [("EXTERNO / Pendiente", None)]
        for dev in bay.devices.values():
            dest_choices.append((dev.name, dev.device_id))

        dlg = EditSignalDialog(
            current_name=sig.name,
            current_nature=sig.nature,
            current_dest_id=current_dest_id,
            dest_choices=dest_choices,
            is_output=(chip.direction == "OUT"),
            current_test_block=tb_current,
        )
        if dlg.exec_() != dlg.Accepted:
            return
        new_name, new_nature, new_tb, new_dest_id = dlg.get_data()
        rename_signal_texts(bay, chip.signal_id, new_name)  # actualiza IN y OUT
        bay.signals[chip.signal_id].nature = new_nature

        # Persistir BP en el extremo OUT (si aplica)
        if chip.direction == "OUT":
            dev = bay.devices.get(chip.owner_device_id)
            if dev:
                end = next((e for e in dev.outputs if e.signal_id == chip.signal_id), None)
                if end:
                    end.test_block = bool(new_tb)

        if new_dest_id != current_dest_id:
            update_signal_destination(
                bay,
                chip.signal_id,
                new_dest_id,
                origin_device_id=chip.owner_device_id if chip.direction == "OUT" else None,
            )

        self.build_from_model()
        if callable(self._on_project_mutated):
            self._on_project_mutated({self.bay_id})
        QMessageBox.information(None, "OK", "Señal actualizada en ambos extremos.")

    def edit_decorations_from_chip(self, chip: SignalChipItem):
        from ui.dialogs.signal_decorations_dialog import SignalDecorationsDialog
        from domain.models import InterlockItem, InterlockSpec

        bay = self.project.bays[self.bay_id]

        # find the exact endpoint in model: prefer owner device, direction
        dev = bay.devices.get(chip.owner_device_id)
        if not dev:
            return
        ends = dev.outputs if chip.direction == "OUT" else dev.inputs
        end = next((e for e in ends if e.signal_id == chip.signal_id), None)
        if not end:
            return

        dlg = SignalDecorationsDialog(
            is_output=(chip.direction == "OUT"),
            current_test_block=bool(getattr(end, "test_block", False)),
            current_interlocks=interlock_tags(getattr(end, "interlocks", None)),
            parent=None,
        )
        if dlg.exec_() != dlg.Accepted:
            return

        tb, tags = dlg.get_data()

        if chip.direction == "OUT":
            end.test_block = bool(tb)
            end.interlocks = None
        else:
            end.test_block = False
            spec = normalize_interlocks(tags)
            validate_interlocks(spec)
            end.interlocks = spec

        self.build_from_model()

    def validate_signal_from_chip(self, chip: SignalChipItem):
        from domain.services.validation_service import validate_signal
        bay = self.project.bays[self.bay_id]
        issues = validate_signal(bay, chip.signal_id)
        if not issues:
            QMessageBox.information(None, "Validación", "OK: sin observaciones.")
            return
        txt = "\n".join([f"[{lvl}] {msg}" for lvl, msg in issues])
        QMessageBox.warning(None, "Validación", txt)

    def delete_signal_from_chip(self, chip: SignalChipItem, *, confirm: bool = False):
        if confirm:
            btn = QMessageBox.question(
                None,
                "Eliminar señal",
                "Se eliminará la señal y sus enlaces en ambos extremos (IN/OUT).\n¿Deseas continuar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if btn != QMessageBox.Yes:
                return

        from domain.services.link_service import remove_link_project
        bay = self.project.bays[self.bay_id]
        remove_link_project(self.project, chip.signal_id)
        self.build_from_model()

    def delete_signals_bulk(self, chips: list[SignalChipItem], *, confirm: bool = False):
        if not chips:
            return
        signal_ids = sorted({c.signal_id for c in chips})
        if confirm:
            btn = QMessageBox.question(
                None,
                "Eliminar señales",
                f"Se eliminarán {len(signal_ids)} señales y sus enlaces en ambos extremos (IN/OUT).\n¿Deseas continuar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if btn != QMessageBox.Yes:
                return
        from domain.services.link_service import remove_link_project
        bay = self.project.bays[self.bay_id]
        for sid in signal_ids:
            remove_link_project(self.project, sid)
        self.build_from_model()

    # ---------------- Rename ----------------
    def rename_device(self, device_id: str) -> None:
        """Renombra un equipo desde el canvas.

        - Se actualiza el nombre del equipo.
        - Se actualizan referencias "hacia/desde <equipo>" en todo el proyecto.
        """
        from domain.services.rename_service import rename_device_in_project

        if not self.project or self.bay_id not in self.project.bays:
            return
        bay = self.project.bays[self.bay_id]
        dev = bay.devices.get(device_id)
        if not dev:
            return
        new_name, ok = QInputDialog.getText(None, "Renombrar equipo", "Nuevo nombre del equipo:", text=dev.name)
        if not ok:
            return
        new_name = (new_name or "").strip()
        if not new_name:
            QMessageBox.warning(None, "Equipo", "Nombre vacío.")
            return
        if new_name == dev.name:
            return
        try:
            rename_device_in_project(self.project, bay_id=self.bay_id, device_id=device_id, new_name=new_name)
        except Exception as e:
            QMessageBox.critical(None, "Equipo", str(e))
            return
        self.build_from_model()
        if callable(self._on_project_mutated):
            self._on_project_mutated({self.bay_id})

    # ---------------- Copy/paste/duplicate ----------------
    def copy_device(self, device_id: str):
        self._clipboard_device_id = device_id

    def paste_device_at(self, scene_pos):
        if not self._clipboard_device_id:
            QMessageBox.warning(None, "Pegar", "No hay un nodo copiado.")
            return
        bay = self.project.bays[self.bay_id]
        if self._clipboard_device_id not in bay.devices:
            QMessageBox.warning(None, "Pegar", "El nodo copiado ya no existe.")
            return
        src = bay.devices[self._clipboard_device_id]
        new_id = self._generate_device_id(src.device_id, bay)
        new_name = f"{src.name}_COPY"
        self.add_device(new_id, new_name, src.dev_type, scene_pos)

    def duplicate_device(self, device_id: str, scene_pos):
        from ui.dialogs.duplicate_device_dialog import DuplicateDeviceDialog
        from domain.models import Device, SignalEnd, Signal
        bay = self.project.bays[self.bay_id]
        src = bay.devices.get(device_id)
        if not src:
            return
        suggested_id = self._generate_device_id(src.device_id, bay)
        suggested_name = f"{src.name}_2"
        dlg = DuplicateDeviceDialog(suggested_id, suggested_name, src.dev_type)
        if dlg.exec_() != dlg.Accepted:
            return
        data = dlg.get_data()
        new_id = data["device_id"] or suggested_id
        if new_id in bay.devices:
            QMessageBox.warning(None, "Duplicar", "Ese ID ya existe.")
            return
        new_dev = Device(device_id=new_id, bay_id=self.bay_id, name=data["name"], dev_type=src.dev_type)
        bay.devices[new_id] = new_dev

        if data["copy_signals"]:
            for e in src.inputs:
                if e.signal_id not in bay.signals:
                    bay.signals[e.signal_id] = Signal(signal_id=e.signal_id, name=e.signal_id)
                new_dev.inputs.append(SignalEnd(signal_id=e.signal_id, direction="IN",
                                               text=self._normalize_pending_text(e.text, "desde"), status="PENDING"))
            for e in src.outputs:
                if e.signal_id not in bay.signals:
                    bay.signals[e.signal_id] = Signal(signal_id=e.signal_id, name=e.signal_id)
                new_dev.outputs.append(SignalEnd(signal_id=e.signal_id, direction="OUT",
                                                text=self._normalize_pending_text(e.text, "hacia"), status="PENDING"))

        from domain.models import CanvasLayout
        if self.bay_id not in self.project.canvases:
            self.project.canvases[self.bay_id] = CanvasLayout(bay_id=self.bay_id)
        self.project.canvases[self.bay_id].device_positions[new_id] = {"x": float(scene_pos.x()), "y": float(scene_pos.y())}

        self.build_from_model()

    def _generate_device_id(self, base_id: str, bay):
        if base_id not in bay.devices:
            return base_id
        i = 2
        while True:
            cand = f"{base_id}-{i}"
            if cand not in bay.devices:
                return cand
            i += 1

    def _normalize_pending_text(self, text: str, keyword: str) -> str:
        token = f" {keyword} "
        if token in text:
            left, _ = text.split(token, 1)
            return f"{left.strip()}{token}EXTERNO (pendiente)"
        return text.strip() + " (pendiente)"

    # ---------------- Validation / Export ----------------
    def validate_current_bay(self):
        from domain.services.validation_service import validate_bay
        bay = self.project.bays[self.bay_id]
        issues = validate_bay(bay)
        if not issues:
            QMessageBox.information(None, "Validación bahía", "OK: sin observaciones.")
            return
        txt = "\n".join([f"[{lvl}] {msg}" for lvl, msg in issues[:250]])
        if len(issues) > 250:
            txt += f"\n... ({len(issues) - 250} más)"
        QMessageBox.warning(None, "Validación bahía", txt)

def select_device_item(self, device_id: str):
    """Selecciona un equipo (nodo) en el canvas y retorna el item para centrar."""
    item = self.device_items.get(device_id)
    if not item:
        return None
    # limpiar selección previa
    for it in self.selectedItems():
        it.setSelected(False)
    item.setSelected(True)
    return item

def export_canvas_png(self, path: str, *, include_header: bool = True):
    """Exporta una imagen PNG del canvas. Si include_header=True agrega cabecera con metadatos."""
    rect = self.itemsBoundingRect().adjusted(-40, -40, 40, 40)
    if rect.width() < 10 or rect.height() < 10:
        rect = QRectF(0, 0, 1200, 800)

    header_h = 70 if include_header else 0
    img = QImage(int(rect.width()), int(rect.height()) + header_h, QImage.Format_ARGB32)
    img.fill(0xFFFFFFFF)
    painter = QPainter(img)

    # Header
    if include_header:
        from datetime import datetime
        painter.save()
        painter.setPen(0xFF334155)      # slate
        painter.setBrush(0xFFF1F5F9)    # light header
        painter.drawRect(0, 0, int(rect.width()), header_h)

        try:
            project_name = getattr(self.project, "name", "") or "Proyecto"
        except Exception:
            project_name = "Proyecto"

        bay = self.project.bays.get(self.bay_id)
        bay_name = (bay.name if bay else self.bay_id) or self.bay_id

        ver = "?"
        try:
            with open("VERSION", "r", encoding="utf-8") as f:
                ver = f.read().strip()
        except Exception:
            pass

        painter.drawText(QRectF(12, 10, int(rect.width()) - 24, 22),
                         Qt.AlignLeft | Qt.AlignVCenter,
                         f"{project_name}  •  {bay_name}")
        painter.drawText(QRectF(12, 36, int(rect.width()) - 24, 18),
                         Qt.AlignLeft | Qt.AlignVCenter,
                         f"Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M')}   •   Signal Mapper v{ver}")
        painter.restore()

    # Render canvas debajo del header
    target = QRectF(0, header_h, rect.width(), rect.height())
    self.render(painter, target=target, source=rect)
    painter.end()
    img.save(path)

def export_canvas_png_dialog(self):
    path, _ = QFileDialog.getSaveFileName(None, "Exportar canvas a PNG", f"{self.bay_id}.png", "PNG (*.png)")
    if not path:
        return
    if not path.lower().endswith(".png"):
        path += ".png"
    self.export_canvas_png(path, include_header=True)
    QMessageBox.information(None, "Exportación", "Imagen exportada.")
