from __future__ import annotations

import json
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QBrush, QPen, QFont, QColor, QPainter, QPainterPath
from PyQt5.QtWidgets import QGraphicsRectItem, QMenu, QGraphicsPathItem, QGraphicsSimpleTextItem

from canvas.items.signal_chip_item import SignalChipItem
from canvas.items.test_block import should_show_test_block


class DeviceItem(QGraphicsRectItem):
    """Nodo de equipo (IED o primario) con chips IN/OUT.

    - Sin líneas entre equipos: claridad por listas IN/OUT separadas.
    - Auto-resize por cantidad de señales (hasta tope) + scroll interno con rueda.
    """

    MIN_H = 160
    MAX_H = 320
    W = 340

    HEADER_H = 44      # nombre + tipo
    CAPTIONS_H = 16    # DESDE/HACIA
    PAD_TOP = 8
    ROW_H = 26         # chip(22) + gap
    BOTTOM_PAD = 10

    RIGHT_X = 175

    # Distancia (en px) entre el borde del equipo y el borde más cercano del chip.
    # Necesaria para dibujar decoraciones "en serie" (B.P. / enclavamientos).
    CONNECTOR_GAP = 80

    def __init__(self, device_id: str, name: str, dev_type: str):
        super().__init__(0, 0, self.W, self.MIN_H)
        self.device_id = device_id
        self.name = name
        self.dev_type = dev_type

        self._pending_in = 0
        self._pending_out = 0

        self._in_chips: list[SignalChipItem] = []
        self._out_chips: list[SignalChipItem] = []

        # Decorators (línea base + símbolos de BP / enclavamientos)
        self._in_lines: list[QGraphicsPathItem] = []
        self._out_lines: list[QGraphicsPathItem] = []

        # OUT: B.P.
        self._out_bp_symbols: list[QGraphicsPathItem] = []
        self._out_bp_labels: list[QGraphicsSimpleTextItem] = []
        self._in_bp_symbols: list[QGraphicsPathItem] = []
        self._in_bp_labels: list[QGraphicsSimpleTextItem] = []

        # IN: interlocks (serie). Cada fila puede tener 0..N símbolos.
        self._in_ilk_symbols: list[list[QGraphicsPathItem]] = []
        self._in_ilk_labels: list[list[QGraphicsSimpleTextItem]] = []

        self._scroll = 0
        self._has_overflow = False
        self._overflow_hidden = 0

        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setAcceptDrops(True)

        self.setPen(QPen(QColor(170, 180, 190), 1))
        self.setBrush(QBrush(QColor(250, 252, 255)))

    # ---------------- Public API ----------------
    def set_pending_counts(self, pending_in: int, pending_out: int):
        self._pending_in = int(pending_in)
        self._pending_out = int(pending_out)
        self.update()

    def set_signals(self, in_chips: list[SignalChipItem], out_chips: list[SignalChipItem]) -> None:
        # detach old
        for c in self._in_chips + self._out_chips:
            c.setParentItem(None)

        # detach / delete old decorators
        self._reset_decorators()

        self._in_chips = list(in_chips)
        self._out_chips = list(out_chips)

        for c in self._in_chips + self._out_chips:
            c.setParentItem(self)

        self._auto_resize_and_layout()

    def _reset_decorators(self) -> None:
        """Elimina todos los items decorativos (líneas, BP, enclavamientos).

        Nota: los QGraphicsItem se garbage-coleccionan cuando quedan sin escena/parent.
        """
        for it in self._in_lines + self._out_lines:
            it.setParentItem(None)
        for it in self._out_bp_symbols + self._out_bp_labels:
            it.setParentItem(None)
        for it in self._in_bp_symbols + self._in_bp_labels:
            it.setParentItem(None)
        for row in self._in_ilk_symbols:
            for it in row:
                it.setParentItem(None)
        for row in self._in_ilk_labels:
            for it in row:
                it.setParentItem(None)

        self._in_lines = []
        self._out_lines = []
        self._out_bp_symbols = []
        self._out_bp_labels = []
        self._in_bp_symbols = []
        self._in_bp_labels = []
        self._in_ilk_symbols = []
        self._in_ilk_labels = []

    def _ensure_line(self, lines: list[QGraphicsPathItem], idx: int) -> QGraphicsPathItem:
        while len(lines) <= idx:
            item = QGraphicsPathItem(self)
            item.setPen(QPen(QColor(170, 180, 190), 1))
            item.setBrush(QBrush(Qt.NoBrush))
            item.setZValue(-10)  # detrás de chips
            lines.append(item)
        return lines[idx]

    def _ensure_bp_items(self, idx: int):
        while len(self._out_bp_symbols) <= idx:
            sym = QGraphicsPathItem(self)
            sym.setPen(QPen(QColor(160, 40, 40), 1.6))
            sym.setBrush(QBrush(Qt.NoBrush))
            sym.setZValue(-9)
            lbl = QGraphicsSimpleTextItem("B.P.", self)
            f = QFont("Segoe UI", 7)
            f.setBold(True)
            lbl.setFont(f)
            lbl.setBrush(QColor(160, 40, 40))
            lbl.setZValue(-9)
            self._out_bp_symbols.append(sym)
            self._out_bp_labels.append(lbl)

    def _ensure_in_bp_items(self, idx: int):
        while len(self._in_bp_symbols) <= idx:
            sym = QGraphicsPathItem(self)
            sym.setPen(QPen(QColor(160, 40, 40), 1.6))
            sym.setBrush(QBrush(Qt.NoBrush))
            sym.setZValue(-9)
            lbl = QGraphicsSimpleTextItem("B.P.", self)
            f = QFont("Segoe UI", 7)
            f.setBold(True)
            lbl.setFont(f)
            lbl.setBrush(QColor(160, 40, 40))
            lbl.setZValue(-9)
            self._in_bp_symbols.append(sym)
            self._in_bp_labels.append(lbl)

    def _ensure_ilk_row(self, idx: int):
        while len(self._in_ilk_symbols) <= idx:
            self._in_ilk_symbols.append([])
            self._in_ilk_labels.append([])

    def _auto_resize_and_layout(self):
        top = self.HEADER_H + self.CAPTIONS_H + self.PAD_TOP
        desired_rows = max(len(self._in_chips), len(self._out_chips), 1)
        desired_h = top + desired_rows * self.ROW_H + self.BOTTOM_PAD
        h = max(self.MIN_H, min(self.MAX_H, desired_h))

        if abs(self.rect().height() - h) > 0.1:
            r = self.rect()
            self.setRect(r.x(), r.y(), r.width(), h)

        # clamp scroll
        max_rows = max(1, int((self.rect().height() - top - self.BOTTOM_PAD) / self.ROW_H))
        max_scroll = max(0, desired_rows - max_rows)
        self._scroll = max(0, min(self._scroll, max_scroll))

        self._layout_chips()
        self.update()

    def _layout_chips(self) -> None:
        top = self.HEADER_H + self.CAPTIONS_H + self.PAD_TOP
        max_rows = max(1, int((self.rect().height() - top - self.BOTTOM_PAD) / self.ROW_H))

        total_rows = max(len(self._in_chips), len(self._out_chips), 1)
        max_scroll = max(0, total_rows - max_rows)
        self._scroll = max(0, min(self._scroll, max_scroll))

        start = self._scroll
        end = start + max_rows

        self._has_overflow = total_rows > max_rows
        self._overflow_hidden = max(0, total_rows - max_rows)

        for idx, chip in enumerate(self._in_chips):
            if start <= idx < end:
                chip.setVisible(True)
                chip.setPos(-chip.boundingRect().width() - self.CONNECTOR_GAP, top + (idx - start) * self.ROW_H)

                # Línea base IN (siempre visible)
                line = self._ensure_line(self._in_lines, idx)
                y = chip.pos().y() + chip.boundingRect().height() / 2
                x0 = 0
                x1 = chip.pos().x() + chip.boundingRect().width()  # ~ -CONNECTOR_GAP
                path = QPainterPath()
                path.moveTo(x0, y)
                path.lineTo(x1, y)
                line.setPath(path)
                line.setVisible(True)

                self._ensure_in_bp_items(idx)
                if bool(getattr(chip, "test_block", False)) and should_show_test_block("IN", chip.nature):
                    cx = x0 + (x1 - x0) / 2
                    p = QPainterPath()
                    p.moveTo(cx - 6, y - 6)
                    p.lineTo(cx + 6, y + 6)
                    p.moveTo(cx - 6, y + 6)
                    p.lineTo(cx + 6, y - 6)
                    self._in_bp_symbols[idx].setPath(p)
                    self._in_bp_symbols[idx].setVisible(True)

                    br = self._in_bp_labels[idx].boundingRect()
                    self._in_bp_labels[idx].setPos(cx - br.width()/2, y - 18)
                    self._in_bp_labels[idx].setVisible(True)
                else:
                    self._in_bp_symbols[idx].setVisible(False)
                    self._in_bp_labels[idx].setVisible(False)

                # Enclavamientos (IN): símbolo NC en serie + relay_tag(s)
                self._ensure_ilk_row(idx)
                tags = [t for t in (chip.interlocks or []) if (t or '').strip()]
                # Mostrar hasta 2 tags (para no sobrecargar); el resto se resume como +N
                vis = tags[:2]
                extra = max(0, len(tags) - len(vis))

                # Ensure items count (símbolos+labels) para tags visibles
                while len(self._in_ilk_symbols[idx]) < len(vis):
                    sym = QGraphicsPathItem(self)
                    sym.setPen(QPen(QColor(40, 40, 40), 1.2))
                    sym.setBrush(QBrush(Qt.NoBrush))
                    sym.setZValue(-9)
                    self._in_ilk_symbols[idx].append(sym)
                    lbl = QGraphicsSimpleTextItem("", self)
                    f = QFont("Segoe UI", 7)
                    f.setBold(True)
                    lbl.setFont(f)
                    lbl.setBrush(QColor(55, 65, 80))
                    lbl.setZValue(-9)
                    self._in_ilk_labels[idx].append(lbl)

                # Hide unused existing
                for k in range(len(vis), len(self._in_ilk_symbols[idx])):
                    self._in_ilk_symbols[idx][k].setVisible(False)
                    self._in_ilk_labels[idx][k].setVisible(False)

                # Draw tags in serie along the line
                if vis:
                    # positions from device towards chip (dentro del gap)
                    for j, tag in enumerate(vis):
                        cx = -(26 + j * 30)
                        # clamp within [x1+14, -14]
                        cx = max(min(cx, -14), x1 + 14)

                        # NC contact: two bars + slash
                        p = QPainterPath()
                        p.moveTo(cx - 6, y - 7)
                        p.lineTo(cx - 6, y + 7)
                        p.moveTo(cx + 2, y - 7)
                        p.lineTo(cx + 2, y + 7)
                        p.moveTo(cx - 8, y - 3)
                        p.lineTo(cx + 4, y + 3)
                        self._in_ilk_symbols[idx][j].setPath(p)
                        self._in_ilk_symbols[idx][j].setVisible(True)

                        self._in_ilk_labels[idx][j].setText(tag)
                        # center text above symbol
                        br = self._in_ilk_labels[idx][j].boundingRect()
                        self._in_ilk_labels[idx][j].setPos(cx - br.width()/2, y - 18)
                        self._in_ilk_labels[idx][j].setVisible(True)

                    # extra summary
                    if extra > 0:
                        # reuse/add a label without symbol (3rd slot)
                        if len(self._in_ilk_labels[idx]) < len(vis) + 1:
                            lbl = QGraphicsSimpleTextItem("", self)
                            f = QFont("Segoe UI", 7)
                            f.setBold(True)
                            lbl.setFont(f)
                            lbl.setBrush(QColor(55, 65, 80))
                            lbl.setZValue(-9)
                            self._in_ilk_labels[idx].append(lbl)
                            sym = QGraphicsPathItem(self)
                            sym.setPen(QPen(QColor(40, 40, 40), 1.2))
                            sym.setBrush(QBrush(Qt.NoBrush))
                            sym.setZValue(-9)
                            self._in_ilk_symbols[idx].append(sym)

                        j = len(vis)
                        self._in_ilk_symbols[idx][j].setVisible(False)
                        self._in_ilk_labels[idx][j].setText(f"+{extra}")
                        br = self._in_ilk_labels[idx][j].boundingRect()
                        self._in_ilk_labels[idx][j].setPos(x1 - br.width() - 4, y - 18)
                        self._in_ilk_labels[idx][j].setVisible(True)
                else:
                    # no interlocks => hide any prior row symbols/labels
                    for it in self._in_ilk_symbols[idx]:
                        it.setVisible(False)
                    for it in self._in_ilk_labels[idx]:
                        it.setVisible(False)
            else:
                chip.setVisible(False)

                if idx < len(self._in_lines):
                    self._in_lines[idx].setVisible(False)
                if idx < len(self._in_bp_symbols):
                    self._in_bp_symbols[idx].setVisible(False)
                    self._in_bp_labels[idx].setVisible(False)
                if idx < len(self._in_ilk_symbols):
                    for it in self._in_ilk_symbols[idx]:
                        it.setVisible(False)
                if idx < len(self._in_ilk_labels):
                    for it in self._in_ilk_labels[idx]:
                        it.setVisible(False)

        for idx, chip in enumerate(self._out_chips):
            if start <= idx < end:
                chip.setVisible(True)
                # OUT: anclar al borde derecho del rect + gap (igual que IN usa -gap)
                x = self.rect().width() + self.CONNECTOR_GAP
                chip.setPos(x, top + (idx - start) * self.ROW_H)

                # Línea base OUT (siempre visible)
                line = self._ensure_line(self._out_lines, idx)
                y = chip.pos().y() + chip.boundingRect().height() / 2
                x0 = self.rect().width()
                x1 = chip.pos().x()
                path = QPainterPath()
                path.moveTo(x0, y)
                path.lineTo(x1, y)
                line.setPath(path)
                line.setVisible(True)

                # Block de pruebas (OUT): símbolo X + texto fijo "B.P."
                self._ensure_bp_items(idx)
                if bool(getattr(chip, "test_block", False)) and should_show_test_block("OUT", chip.nature):
                    cx = x0 + (x1 - x0) / 2
                    p = QPainterPath()
                    p.moveTo(cx - 6, y - 6)
                    p.lineTo(cx + 6, y + 6)
                    p.moveTo(cx - 6, y + 6)
                    p.lineTo(cx + 6, y - 6)
                    self._out_bp_symbols[idx].setPath(p)
                    self._out_bp_symbols[idx].setVisible(True)

                    br = self._out_bp_labels[idx].boundingRect()
                    self._out_bp_labels[idx].setPos(cx - br.width()/2, y - 18)
                    self._out_bp_labels[idx].setVisible(True)
                else:
                    self._out_bp_symbols[idx].setVisible(False)
                    self._out_bp_labels[idx].setVisible(False)
            else:
                chip.setVisible(False)

                if idx < len(self._out_lines):
                    self._out_lines[idx].setVisible(False)
                if idx < len(self._out_bp_symbols):
                    self._out_bp_symbols[idx].setVisible(False)
                    self._out_bp_labels[idx].setVisible(False)

    # ---------------- Events ----------------
    def wheelEvent(self, event):
        if not self._has_overflow:
            return
        step = -1 if event.delta() > 0 else 1
        self._scroll += step
        self._layout_chips()
        self.update()
        event.accept()

    def paint(self, painter: QPainter, option, widget=None):
        # base rect
        super().paint(painter, option, widget)

        # selection overlay
        if self.isSelected():
            painter.save()
            painter.setPen(QPen(QColor(60, 120, 200), 2))
            painter.setBrush(QBrush(Qt.NoBrush))
            painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
            painter.restore()

        painter.save()
        painter.setPen(QColor(35, 45, 55))

        # header text
        f1 = QFont(); f1.setPointSize(10); f1.setBold(True)
        painter.setFont(f1)
        painter.drawText(QRectF(10, 6, 320, 18), Qt.AlignLeft | Qt.AlignVCenter, self.name)

        f2 = QFont(); f2.setPointSize(8); f2.setBold(False)
        painter.setFont(f2)
        painter.setPen(QColor(90, 100, 110))
        painter.drawText(QRectF(10, 24, 320, 14), Qt.AlignLeft | Qt.AlignVCenter, f"{self.dev_type}")

        # captions
        painter.setPen(QColor(110, 120, 130))
        f3 = QFont(); f3.setPointSize(7); f3.setBold(True)
        painter.setFont(f3)
        painter.drawText(QRectF(10, 36, 150, 12), Qt.AlignLeft | Qt.AlignVCenter, "DESDE (IN)")
        painter.drawText(QRectF(175, 36, 150, 12), Qt.AlignLeft | Qt.AlignVCenter, "HACIA (OUT)")

        # pending badge
        total = self._pending_in + self._pending_out
        if total:
            badge = f"P:{total}"
            painter.setPen(QColor(160, 90, 0))
            painter.setBrush(QColor(255, 235, 200))
            bw, bh = 54, 16
            x = self.rect().width() - bw - 10
            y = 8
            painter.drawRoundedRect(QRectF(x, y, bw, bh), 6, 6)
            painter.drawText(QRectF(x, y, bw, bh), Qt.AlignCenter, badge)

        # overflow indicator + scrollbar
        if self._has_overflow:
            painter.setPen(QColor(120, 130, 140))
            f4 = QFont(); f4.setPointSize(7); f4.setBold(False)
            painter.setFont(f4)
            if self._overflow_hidden > 0:
                painter.drawText(
                    QRectF(10, self.rect().height() - 14, 240, 12),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    f"+{self._overflow_hidden} señales (rueda para desplazarte)"
                )

            top = self.HEADER_H + self.CAPTIONS_H + self.PAD_TOP
            track_x = self.rect().width() - 8
            track_y = top
            track_h = self.rect().height() - top - self.BOTTOM_PAD

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(230, 235, 240))
            painter.drawRoundedRect(QRectF(track_x, track_y, 4, track_h), 2, 2)

            total_rows = max(len(self._in_chips), len(self._out_chips), 1)
            max_rows = max(1, int(track_h / self.ROW_H))
            thumb_h = max(14.0, track_h * (max_rows / total_rows))
            max_scroll = max(1, total_rows - max_rows)
            thumb_y = track_y + (track_h - thumb_h) * (self._scroll / max_scroll)

            painter.setBrush(QColor(180, 190, 200))
            painter.drawRoundedRect(QRectF(track_x, thumb_y, 4, thumb_h), 2, 2)

        painter.restore()

    # ---------- Context menu ----------
    def contextMenuEvent(self, event):
        menu = QMenu()
        act_rename = menu.addAction("Renombrar equipo…")
        act_copy = menu.addAction("Copiar nodo")
        act_del = menu.addAction("Eliminar nodo")
        act = menu.exec_(event.screenPos())

        if act == act_rename:
            if hasattr(self.scene(), "rename_device"):
                self.scene().rename_device(self.device_id)  # type: ignore[attr-defined]
        elif act == act_copy:
            self.scene().copy_device(self.device_id)  # type: ignore[attr-defined]
        elif act == act_del:
            self.scene().delete_device(self.device_id)  # type: ignore[attr-defined]

    # ---------- Drag & Drop ----------
    def dragEnterEvent(self, event):
        md = event.mimeData()
        if md.hasFormat("application/x-signal-template"):
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        md = event.mimeData()
        if not md.hasFormat("application/x-signal-template"):
            event.ignore()
            return
        payload = json.loads(bytes(md.data("application/x-signal-template")).decode("utf-8"))
        self.scene().on_template_dropped(self.device_id, payload)  # type: ignore[attr-defined]
        event.acceptProposedAction()

    def _no_brush(self, gitem):
        gitem.setBrush(QBrush(Qt.NoBrush))

    def _std_pen(self):
        pen = QPen(QColor(0, 0, 0, 140))
        pen.setCosmetic(True)
        pen.setWidthF(1.2)
        return pen
