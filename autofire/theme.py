from __future__ import annotations

from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication

def apply_dark_theme(app: QApplication) -> None:
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(30, 30, 30))
    pal.setColor(QPalette.WindowText, QColor(220, 220, 220))
    pal.setColor(QPalette.Base, QColor(20, 20, 20))
    pal.setColor(QPalette.AlternateBase, QColor(35, 35, 35))
    pal.setColor(QPalette.ToolTipBase, QColor(220, 220, 220))
    pal.setColor(QPalette.ToolTipText, QColor(20, 20, 20))
    pal.setColor(QPalette.Text, QColor(220, 220, 220))
    pal.setColor(QPalette.Button, QColor(45, 45, 45))
    pal.setColor(QPalette.ButtonText, QColor(220, 220, 220))
    pal.setColor(QPalette.BrightText, QColor(255, 80, 80))
    pal.setColor(QPalette.Highlight, QColor(90, 140, 255))
    pal.setColor(QPalette.HighlightedText, QColor(10, 10, 10))
    app.setPalette(pal)

def apply_light_theme(app: QApplication) -> None:
    app.setPalette(app.style().standardPalette())
