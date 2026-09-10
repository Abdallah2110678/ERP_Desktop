from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import database as db


_INPUT_CSS = """
    QLineEdit {
        border: 1.5px solid #cdd5df; border-radius: 8px;
        padding: 9px 12px; font-size: 12px; font-family: Tahoma;
        color: #1a2535; background: #f8fafc;
    }
    QLineEdit:focus { border-color: #27ae60; background: white; }
"""
_LABEL_CSS = "color: #2c3e50; font-size: 12px; font-weight: bold; background: transparent;"


class ChangePasswordDialog(QDialog):
    def __init__(self, current_username: str, parent=None):
        super().__init__(parent)
        self._current_username = current_username
        self.setWindowTitle("تغيير بيانات الدخول")
        self.setFixedWidth(420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("QDialog { background: white; }")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 26, 30, 26)
        layout.setSpacing(12)

        title = QLabel("⚙  تغيير بيانات الدخول")
        title.setFont(QFont("Tahoma", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a2535; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        who = QLabel(f"المستخدم الحالي:  {self._current_username}")
        who.setStyleSheet("color: #27ae60; font-size: 12px; font-weight: bold; background: transparent;")
        who.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(who)
        layout.addSpacing(4)

        layout.addWidget(self._lbl("كلمة المرور الحالية"))
        self.current_pw = self._inp("كلمة المرور الحالية", password=True)
        layout.addWidget(self.current_pw)

        layout.addWidget(self._lbl("اسم المستخدم الجديد"))
        self.new_username = self._inp("اسم المستخدم")
        self.new_username.setText(self._current_username)
        layout.addWidget(self.new_username)

        layout.addWidget(self._lbl("كلمة المرور الجديدة  (اتركها فارغة للإبقاء على الحالية)"))
        self.new_pw = self._inp("كلمة مرور جديدة — اختياري", password=True)
        layout.addWidget(self.new_pw)

        layout.addWidget(self._lbl("تأكيد كلمة المرور الجديدة"))
        self.confirm_pw = self._inp("تأكيد كلمة المرور", password=True)
        self.confirm_pw.returnPressed.connect(self._save)
        layout.addWidget(self.confirm_pw)

        self.msg_lbl = QLabel("")
        self.msg_lbl.setStyleSheet("font-size: 11px; background: transparent;")
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setMinimumHeight(18)
        layout.addWidget(self.msg_lbl)

        save_btn = QPushButton("💾  حفظ التغييرات")
        save_btn.setMinimumHeight(42)
        save_btn.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60; color: white; border: none;
                border-radius: 8px; font-family: Tahoma; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover   { background: #229954; }
            QPushButton:pressed { background: #1e8449; }
        """)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ecf0f1; color: #2c3e50; border: none;
                border-radius: 8px; font-family: Tahoma; font-size: 12px;
            }
            QPushButton:hover { background: #d5d8dc; }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    @staticmethod
    def _lbl(text):
        l = QLabel(text)
        l.setStyleSheet(_LABEL_CSS)
        return l

    @staticmethod
    def _inp(placeholder, password=False):
        e = QLineEdit()
        e.setPlaceholderText(placeholder)
        e.setMinimumHeight(40)
        e.setStyleSheet(_INPUT_CSS)
        if password:
            e.setEchoMode(QLineEdit.EchoMode.Password)
        return e

    def _err(self, msg):
        self.msg_lbl.setStyleSheet("color: #e74c3c; font-size: 11px; background: transparent;")
        self.msg_lbl.setText(msg)

    def _ok(self, msg):
        self.msg_lbl.setStyleSheet("color: #27ae60; font-size: 11px; background: transparent;")
        self.msg_lbl.setText(msg)

    def _save(self):
        current_pw   = self.current_pw.text()
        new_username = self.new_username.text().strip()
        new_pw       = self.new_pw.text()
        confirm_pw   = self.confirm_pw.text()

        if not db.verify_credentials(self._current_username, current_pw):
            self._err("كلمة المرور الحالية غير صحيحة")
            self.current_pw.clear()
            self.current_pw.setFocus()
            return

        if len(new_username) < 3:
            self._err("اسم المستخدم يجب أن يكون 3 أحرف على الأقل")
            return

        if new_pw:
            if len(new_pw) < 4:
                self._err("كلمة المرور الجديدة يجب أن تكون 4 أحرف على الأقل")
                return
            if new_pw != confirm_pw:
                self._err("كلمتا المرور غير متطابقتان")
                return

        # Find current user's id
        users = db.get_all_users()
        user = next((u for u in users if u['username'] == self._current_username), None)
        if not user:
            self._err("حدث خطأ — المستخدم غير موجود")
            return

        if new_username != self._current_username:
            if not db.update_username(user['id'], new_username):
                self._err("اسم المستخدم هذا مستخدم بالفعل")
                return

        if new_pw:
            db.update_user_password(user['id'], new_pw)

        self._ok("✅  تم حفظ البيانات بنجاح")
        QTimer.singleShot(1200, self.accept)
