from __future__ import annotations
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QBrush, QPen, QFont, QColor
from PyQt5.QtWidgets import QGraphicsItem, QMenu

class SignalChipItem(QGraphicsItem):
    def __init__(
        self, *,
        signal_id: str,
        owner_device_id: str,
        text: str,
        nature: str,
        status: str,
        direction: str,
        test_block: bool = False,
        interlocks: list[str] | None = None,
        tooltip: str = "",
    ):
        super().__init__()
        self.signal_id = signal_id
        self.owner_device_id = owner_device_id
        self.text = text
        self.nature = nature
        self.status = status
        self.direction = direction
        self.test_block = bool(test_block)
        self.interlocks = list(interlocks or [])
        self.setToolTip(tooltip)
        self._w = 300
        self._h = 22
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._w, self._h)

    def paint(self, painter, option, widget=None):
        if self.status == "PENDING":
            fill, border = QColor(255, 230, 160), QColor(190, 140, 0)
        elif self.nature == "ANALOG":
            fill, border = QColor(200, 245, 210), QColor(80, 140, 90)
        else:
            fill, border = QColor(230, 235, 242), QColor(120, 135, 155)

        painter.setPen(QPen(border, 1))
        painter.setBrush(QBrush(fill))
        painter.drawRoundedRect(self.boundingRect(), 6, 6)

        # selection highlight
        if self.isSelected():
            painter.setPen(QPen(QColor(50, 120, 220), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(1, 1, -1, -1), 6, 6)

        painter.setPen(QColor(25, 25, 25))
        painter.setFont(QFont("Segoe UI", 9))

        # reserve space for markers
        marker_space = 54
        text_rect = self.boundingRect().adjusted(8, 0, -marker_space, 0)

        t = self.text
        if len(t) > 62:
            t = t[:59] + "…"
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, t)

        # markers area
        x0 = self.boundingRect().right() - marker_space + 6
        mid_y = self.boundingRect().center().y()

        # Block de pruebas marker (OUT): texto fijo "B.P."
        if self.test_block:
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            painter.setPen(QColor(160, 40, 40))
            painter.drawText(QRectF(x0 - 2, 0, 26, self._h), Qt.AlignCenter, "B.P.")

        # Interlock marker: draw a tiny NC symbol + count
        if self.interlocks:
            painter.setPen(QPen(QColor(40, 40, 40), 1))
            # draw NC contact symbol near right edge
            cx = x0 + 26
            top = mid_y - 6
            bot = mid_y + 6
            painter.drawLine(cx, top, cx, bot)
            painter.drawLine(cx + 8, top, cx + 8, bot)
            # diagonal slash (NC indication)
            painter.drawLine(cx - 2, mid_y - 2, cx + 10, mid_y + 2)

            painter.setFont(QFont("Segoe UI", 7))
            painter.setPen(QColor(55, 65, 80))
            cnt = len(self.interlocks)
            painter.drawText(QRectF(cx + 12, 0, 18, self._h), Qt.AlignVCenter | Qt.AlignLeft, f"x{cnt}")

    def mouseDoubleClickEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, "edit_signal_from_chip"):
            scene.edit_signal_from_chip(self)
            # IMPORTANT: editing a signal typically triggers a scene rebuild, which can delete
            # this QGraphicsItem. Do NOT call super() afterwards.
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        scene = self.scene()
        menu = QMenu()

        act_recognize = None
        if self.status == "PENDING" and self.direction == "OUT":
            act_recognize = menu.addAction("Reconocer señal…")

        act_edit = menu.addAction("Editar señal (nombre/naturaleza)…")
        act_decor = menu.addAction("Editar block de pruebas / enclavamientos…")
        act_validate = menu.addAction("Validar señal")
        menu.addSeparator()
        act_delete = menu.addAction("Eliminar señal (ambos extremos)…")

        chosen = menu.exec_(event.screenPos())
        if not chosen or not scene:
            return

        if chosen == act_recognize and hasattr(scene, "recognize_signal_from_chip"):
            scene.recognize_signal_from_chip(self)
        elif chosen == act_edit and hasattr(scene, "edit_signal_from_chip"):
            scene.edit_signal_from_chip(self)
        elif chosen == act_decor and hasattr(scene, "edit_decorations_from_chip"):
            scene.edit_decorations_from_chip(self)
        elif chosen == act_validate and hasattr(scene, "validate_signal_from_chip"):
            scene.validate_signal_from_chip(self)
        elif chosen == act_delete and hasattr(scene, "delete_signal_from_chip"):
            scene.delete_signal_from_chip(self)
