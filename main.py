import sys
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.main_window import MainWindow
from ui.login import LoginDialog
from ui.app_icon import get_app_icon
import database as db


MSGBOX_STYLE = """
QMessageBox {
    background-color: #ffffff;
    font-family: Tahoma;
}
QMessageBox QLabel {
    color: #1a2535;
    font-size: 13px;
    font-family: Tahoma;
    background: transparent;
}
QMessageBox QPushButton {
    background-color: #27ae60;
    color: white;
    border: none;
    padding: 8px 24px;
    border-radius: 6px;
    font-size: 12px;
    font-family: Tahoma;
    min-width: 70px;
}
QMessageBox QPushButton:hover  { background-color: #1e8449; }
QMessageBox QPushButton:default { background-color: #1e8449; }
"""


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setFont(QFont("Tahoma", 11))
    app.setStyle("Fusion")
    app.setStyleSheet(MSGBOX_STYLE)

    icon = get_app_icon()
    app.setWindowIcon(icon)

    db.init_db()
    db.init_auth()

    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    window = MainWindow(current_user=login.logged_in_username)
    window.setWindowIcon(icon)
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
