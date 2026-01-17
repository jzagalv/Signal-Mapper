from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QVBoxLayout


class CanvasHost(QWidget):
    """Contenedor simple para la vista del canvas.
    CanvasController inserta y reemplaza el CanvasView dentro de este layout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
