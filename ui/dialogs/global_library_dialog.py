from __future__ import annotations

import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

from ui.widgets.template_library_dock import TemplateLibraryDock


class GlobalLibraryDialog(QDialog):
    """Editor explícito de la biblioteca global (opcional).

    Nota: la aplicación principal ya permite editar Global desde el dock.
    Este diálogo se deja por completitud y para flujos donde se quiera abrirlo dedicado.
    """

    def __init__(self, app_dir: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Biblioteca global de señales")
        self.resize(760, 520)

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(f"Archivo: {os.path.join(app_dir, 'template_library.json')}"))

        self.dock = TemplateLibraryDock(parent=self, app_dir=app_dir)
        self.dock.set_project(None)
        self.dock.source.setCurrentIndex(1)  # Global
        lay.addWidget(self.dock.widget(), 1)

        btns = QHBoxLayout()
        btns.addStretch(1)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        btns.addWidget(close)
        lay.addLayout(btns)
