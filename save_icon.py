"""Run once before building — saves icon.ico to disk for PyInstaller."""
import sys
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)

from ui.app_icon import _draw_icon

pix = _draw_icon(256)
if pix.save("icon.ico"):
    print("icon.ico saved successfully.")
else:
    # Fallback: save as PNG (Qt sometimes can't write ICO outside Windows GUI context)
    pix.save("icon.png")
    print("icon.png saved (ICO write failed — build.bat will still work).")
