import sys
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox
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


def _show_overdue_alert(window):
    """Modal alert shown once at startup — only for invoices already past their due date."""
    from datetime import date as _date
    today = _date.today().isoformat()
    overdue = [p for p in db.get_upcoming_due_payments(days_ahead=0)
               if (p.get('payment_due_date') or '') < today]
    if not overdue:
        return

    lines = []
    for p in overdue:
        remaining = max(0.0, (p.get('total_amount') or 0) - (p.get('paid_amount') or 0))
        due = p.get('payment_due_date', '')
        supplier = p.get('supplier_display') or p.get('supplier') or '—'
        from datetime import date as _d
        days_late = (_d.today() - _d.fromisoformat(due)).days
        lines.append(f"• فاتورة #{p['id']}  —  {supplier}\n  المتبقي: {remaining:.2f} ج.م  |  متأخرة {days_late} يوم")

    msg = QMessageBox(window)
    msg.setWindowTitle("⚠  تنبيه: مدفوعات متأخرة")
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText(f"يوجد {len(overdue)} فاتورة شراء تجاوزت تاريخ السداد ولم تُسدَّد بعد:")
    msg.setInformativeText("\n\n".join(lines))
    ok_btn = msg.addButton("حسناً، سأتابع الأمر", QMessageBox.ButtonRole.AcceptRole)
    ok_btn.setStyleSheet(
        "background:#e74c3c; color:white; border:none; padding:9px 28px;"
        " border-radius:7px; font-size:13px; font-family:Tahoma; font-weight:bold;"
    )
    msg.setStyleSheet("""
        QMessageBox { background: #ffffff; font-family: Tahoma; }
        QMessageBox QLabel { color: #1a2535; font-size: 13px; font-family: Tahoma; background: transparent; }
    """)
    msg.exec()


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

    _show_overdue_alert(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
