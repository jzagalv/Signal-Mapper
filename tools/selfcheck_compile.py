from __future__ import annotations
import compileall
import sys

def main() -> int:
    ok = compileall.compile_dir(".", quiet=1)
    if not ok:
        print("compileall: FAILED")
        return 2

    # Minimal smoke: instantiate MainWindow
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.main_window import MainWindow
        app = QApplication.instance() or QApplication([])
        w = MainWindow()
        # methods that must exist
        assert hasattr(w, "proj_ctrl")
        assert hasattr(w, "canvas_ctrl")
        assert hasattr(w, "pending_dock")
        print("smoke: OK")
        w.close()
    except Exception as e:
        print("smoke: FAILED:", e)
        return 3
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
