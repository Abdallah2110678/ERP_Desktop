from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QApplication, QSizePolicy,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont

import database as db
from config import PHARMACY_NAME, PHARMACY_SUBTITLE, APP_VERSION, APP_YEAR
from ui.app_icon import get_app_icon


_INPUT_CSS = """
    QLineEdit {
        border: 2px solid #dce3ec;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 13px;
        font-family: Tahoma;
        color: #1a2535;
        background: #f7f9fc;
        min-height: 20px;
    }
    QLineEdit:focus {
        border-color: #27ae60;
        background: white;
    }
    QLineEdit:hover {
        border-color: #b0bec5;
    }
"""

_BTN_GREEN = """
    QPushButton {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 #2ecc71, stop:1 #27ae60);
        color: white;
        border: none;
        border-radius: 10px;
        font-family: Tahoma;
        font-size: 14px;
        font-weight: bold;
        padding: 14px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 #27ae60, stop:1 #229954);
    }
    QPushButton:pressed {
        background: #1e8449;
    }
"""


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._first_setup       = not db.has_any_user()
        self.logged_in_username = ""

        self.setWindowTitle(PHARMACY_NAME)
        self.setWindowIcon(get_app_icon())
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self.adjustSize()
        self._center()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        # ── Outer dark card ───────────────────────────────────────────────────
        outer = QFrame()
        outer.setObjectName("outer")
        outer.setStyleSheet("""
            QFrame#outer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #152535, stop:1 #0d1b27);
                border-radius: 20px;
            }
        """)
        outer.setMinimumWidth(480)
        outer.setMaximumWidth(520)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 14)
        shadow.setColor(QColor(0, 0, 0, 160))
        outer.setGraphicsEffect(shadow)

        ol = QVBoxLayout(outer)
        ol.setContentsMargins(44, 38, 44, 32)
        ol.setSpacing(0)

        # ── Top: icon + pharmacy name ─────────────────────────────────────────
        ico_lbl = QLabel()
        ico_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico_lbl.setPixmap(get_app_icon().pixmap(QSize(80, 80)))
        ico_lbl.setStyleSheet("background: transparent;")
        ol.addWidget(ico_lbl)

        ol.addSpacing(12)

        name_lbl = QLabel(PHARMACY_NAME)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: white; background: transparent;")
        name_lbl.setWordWrap(True)
        ol.addWidget(name_lbl)

        ol.addSpacing(4)

        sub_lbl = QLabel(PHARMACY_SUBTITLE)
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setFont(QFont("Tahoma", 10))
        sub_lbl.setStyleSheet("color: #4a8aab; background: transparent;")
        ol.addWidget(sub_lbl)

        ol.addSpacing(28)

        # ── White inner card ──────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(0)

        # Card header
        if self._first_setup:
            card_icon  = "🛠"
            card_title = "إنشاء حساب جديد"
            card_hint  = "أول تشغيل — اختر اسم المستخدم وكلمة المرور"
        else:
            card_icon  = "🔐"
            card_title = "تسجيل الدخول"
            card_hint  = "أدخل بياناتك للدخول إلى النظام"

        t = QLabel(f"{card_icon}  {card_title}")
        t.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        t.setStyleSheet("color: #1a2535; background: transparent;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(t)

        cl.addSpacing(6)

        h = QLabel(card_hint)
        h.setFont(QFont("Tahoma", 10))
        h.setStyleSheet("color: #95a5a6; background: transparent;")
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.setWordWrap(True)
        cl.addWidget(h)

        cl.addSpacing(22)

        # Username
        cl.addWidget(self._field_label("👤  اسم المستخدم"))
        cl.addSpacing(6)
        self.username_edit = self._field_input("اسم المستخدم")
        self.username_edit.returnPressed.connect(self._attempt)
        cl.addWidget(self.username_edit)

        cl.addSpacing(16)

        # Password
        cl.addWidget(self._field_label("🔒  كلمة المرور"))
        cl.addSpacing(6)
        self.password_edit = self._field_input("كلمة المرور", password=True)
        self.password_edit.returnPressed.connect(self._attempt)
        cl.addWidget(self.password_edit)

        # Confirm password — first setup only
        if self._first_setup:
            cl.addSpacing(16)
            cl.addWidget(self._field_label("🔒  تأكيد كلمة المرور"))
            cl.addSpacing(6)
            self.confirm_edit = self._field_input("أعد إدخال كلمة المرور", password=True)
            self.confirm_edit.returnPressed.connect(self._attempt)
            cl.addWidget(self.confirm_edit)

        cl.addSpacing(14)

        # Error label
        self.error_lbl = QLabel("")
        self.error_lbl.setFont(QFont("Tahoma", 10))
        self.error_lbl.setStyleSheet("color: #e74c3c; background: transparent;")
        self.error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setMinimumHeight(22)
        cl.addWidget(self.error_lbl)

        cl.addSpacing(6)

        # Submit button
        btn_text = "  إنشاء الحساب والدخول  " if self._first_setup else "  دخول  "
        self.submit_btn = QPushButton(btn_text)
        self.submit_btn.setStyleSheet(_BTN_GREEN)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self._attempt)
        cl.addWidget(self.submit_btn)

        ol.addWidget(card)
        ol.addSpacing(20)

        # Footer
        ver_lbl = QLabel(f"الإصدار {APP_VERSION}  •  {APP_YEAR}")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver_lbl.setFont(QFont("Tahoma", 9))
        ver_lbl.setStyleSheet("color: #2a4a62; background: transparent;")
        ol.addWidget(ver_lbl)

        root.addWidget(outer, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _field_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #2c3e50; background: transparent;")
        return lbl

    @staticmethod
    def _field_input(placeholder: str, password: bool = False) -> QLineEdit:
        e = QLineEdit()
        e.setPlaceholderText(placeholder)
        e.setStyleSheet(_INPUT_CSS)
        e.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if password:
            e.setEchoMode(QLineEdit.EchoMode.Password)
        return e

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )

    def _set_error(self, msg: str):
        self.error_lbl.setText(msg)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _attempt(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username:
            self._set_error("يرجى إدخال اسم المستخدم"); return
        if not password:
            self._set_error("يرجى إدخال كلمة المرور"); return

        if self._first_setup:
            confirm = self.confirm_edit.text()
            if len(username) < 3:
                self._set_error("اسم المستخدم يجب أن يكون 3 أحرف على الأقل"); return
            if len(password) < 4:
                self._set_error("كلمة المرور يجب أن تكون 4 أحرف على الأقل"); return
            if password != confirm:
                self._set_error("كلمتا المرور غير متطابقتان"); return
            db.set_credentials(username, password)
            self.logged_in_username = username
            self.accept()
        elif not db.user_exists(username):
            self._set_error("اسم المستخدم غير موجود")
            self.username_edit.selectAll()
            self.username_edit.setFocus()
        elif not db.verify_credentials(username, password):
            self._set_error("كلمة المرور غير صحيحة")
            self.password_edit.clear()
            self.password_edit.setFocus()
        else:
            self.logged_in_username = username
            self.accept()
