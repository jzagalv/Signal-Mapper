from __future__ import annotations
from PyQt5.QtWidgets import QGraphicsView, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter

from canvas.items.signal_chip_item import SignalChipItem

class CanvasView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self._last_context_scene_pos = None
        self._panning = False
        self._pan_start = None

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            event.accept()
        else:
            if event.modifiers() & Qt.ShiftModifier:
                self.horizontalScrollBar().setValue(
                    self.horizontalScrollBar().value() - event.angleDelta().y()
                )
                event.accept()
                return
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning and self._pan_start is not None:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._panning and event.button() == Qt.MiddleButton:
            self._panning = False
            self._pan_start = None
            self.viewport().setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            sc = self.scene()
            if sc:
                selected = [it for it in sc.selectedItems() if isinstance(it, SignalChipItem)]
                if selected and hasattr(sc, "delete_signals_bulk"):
                    sc.delete_signals_bulk(selected, confirm=True)
                    return
                if selected and hasattr(sc, "delete_signal_from_chip"):
                    sc.delete_signal_from_chip(selected[0], confirm=True)
                    return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        self._last_context_scene_pos = self.mapToScene(event.pos())
        menu = QMenu()
        act_paste = menu.addAction("Pegar")
        menu.addSeparator()
        act_validate = menu.addAction("Validar bahía")
        act_export_png = menu.addAction("Exportar canvas a PNG…")
        chosen = menu.exec_(event.globalPos())
        if not chosen:
            return
        sc = self.scene()
        if chosen == act_paste and hasattr(sc, "paste_device_at"):
            sc.paste_device_at(self._last_context_scene_pos)
        elif chosen == act_validate and hasattr(sc, "validate_current_bay"):
            sc.validate_current_bay()
        elif chosen == act_export_png and hasattr(sc, "export_canvas_png_dialog"):
            sc.export_canvas_png_dialog()
