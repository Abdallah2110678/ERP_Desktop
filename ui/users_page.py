from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDialog, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD, BTN_DELETE, BTN_EDIT,
    PAGE_STYLE, INPUT_STYLE, card_shadow,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER,
)
from ui.products import page_header


_INPUT_CSS = """
    QLineEdit {
        border: 1.5px solid #cdd5df; border-radius: 8px;
        padding: 10px 14px; font-size: 13px; font-family: Tahoma;
        color: #1a2535; background: #f8fafc;
    }
    QLineEdit:focus { border-color: #27ae60; background: white; }
"""
_LABEL_CSS = "color: #2c3e50; font-size: 12px; font-weight: bold; background: transparent;"


# ── Shared small dialogs ──────────────────────────────────────────────────────

class _AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة مستخدم جديد")
        self.setFixedWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("QDialog { background: white; }")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel("➕  إضافة مستخدم جديد")
        title.setFont(QFont("Tahoma", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a2535; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(4)

        layout.addWidget(self._lbl("👤  اسم المستخدم"))
        self.username_edit = self._inp("اسم المستخدم (3 أحرف على الأقل)")
        layout.addWidget(self.username_edit)

        layout.addWidget(self._lbl("🔒  كلمة المرور"))
        self.pw_edit = self._inp("كلمة المرور (4 أحرف على الأقل)", password=True)
        layout.addWidget(self.pw_edit)

        layout.addWidget(self._lbl("🔒  تأكيد كلمة المرور"))
        self.confirm_edit = self._inp("أعد إدخال كلمة المرور", password=True)
        self.confirm_edit.returnPressed.connect(self._save)
        layout.addWidget(self.confirm_edit)

        self.msg_lbl = QLabel("")
        self.msg_lbl.setStyleSheet("font-size: 11px; background: transparent;")
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_lbl.setMinimumHeight(18)
        layout.addWidget(self.msg_lbl)

        save_btn = QPushButton("➕  إضافة")
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
            QPushButton { background: #ecf0f1; color: #2c3e50; border: none;
                          border-radius: 8px; font-family: Tahoma; font-size: 12px; }
            QPushButton:hover { background: #d5d8dc; }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    @staticmethod
    def _lbl(text):
        l = QLabel(text); l.setStyleSheet(_LABEL_CSS); return l

    @staticmethod
    def _inp(placeholder, password=False):
        e = QLineEdit()
        e.setPlaceholderText(placeholder)
        e.setMinimumHeight(42)
        e.setStyleSheet(_INPUT_CSS)
        if password:
            e.setEchoMode(QLineEdit.EchoMode.Password)
        return e

    def _err(self, msg):
        self.msg_lbl.setStyleSheet("color: #e74c3c; font-size: 11px; background: transparent;")
        self.msg_lbl.setText(msg)

    def _save(self):
        username = self.username_edit.text().strip()
        pw       = self.pw_edit.text()
        confirm  = self.confirm_edit.text()

        if len(username) < 3:
            self._err("اسم المستخدم يجب أن يكون 3 أحرف على الأقل"); return
        if len(pw) < 4:
            self._err("كلمة المرور يجب أن تكون 4 أحرف على الأقل"); return
        if pw != confirm:
            self._err("كلمتا المرور غير متطابقتان"); return
        if not db.add_user(username, pw):
            self._err("اسم المستخدم هذا موجود بالفعل"); return
        self.accept()


class _ChangeUserPasswordDialog(QDialog):
    """Change another user's password — no current-password check (admin action)."""
    def __init__(self, user_id: int, username: str, parent=None):
        super().__init__(parent)
        self._user_id  = user_id
        self._username = username
        self.setWindowTitle(f"تغيير كلمة مرور: {username}")
        self.setFixedWidth(380)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("QDialog { background: white; }")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        title = QLabel(f"🔑  تغيير كلمة مرور\n{self._username}")
        title.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #1a2535; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(4)

        lbl_new = QLabel("🔒  كلمة المرور الجديدة")
        lbl_new.setStyleSheet(_LABEL_CSS)
        layout.addWidget(lbl_new)
        self.new_pw = QLineEdit()
        self.new_pw.setPlaceholderText("كلمة مرور جديدة (4 أحرف على الأقل)")
        self.new_pw.setMinimumHeight(42)
        self.new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pw.setStyleSheet(_INPUT_CSS)
        layout.addWidget(self.new_pw)

        lbl_confirm = QLabel("🔒  تأكيد كلمة المرور")
        lbl_confirm.setStyleSheet(_LABEL_CSS)
        layout.addWidget(lbl_confirm)
        self.confirm_pw = QLineEdit()
        self.confirm_pw.setPlaceholderText("أعد إدخال كلمة المرور")
        self.confirm_pw.setMinimumHeight(42)
        self.confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pw.setStyleSheet(_INPUT_CSS)
        self.confirm_pw.returnPressed.connect(self._save)
        layout.addWidget(self.confirm_pw)

        self.msg_lbl = QLabel("")
        self.msg_lbl.setStyleSheet("font-size: 11px; background: transparent;")
        self.msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_lbl.setMinimumHeight(18)
        layout.addWidget(self.msg_lbl)

        save_btn = QPushButton("💾  حفظ")
        save_btn.setMinimumHeight(42)
        save_btn.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2980b9; color: white; border: none;
                border-radius: 8px; font-family: Tahoma; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover   { background: #2471a3; }
            QPushButton:pressed { background: #1a5276; }
        """)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton { background: #ecf0f1; color: #2c3e50; border: none;
                          border-radius: 8px; font-family: Tahoma; font-size: 12px; }
            QPushButton:hover { background: #d5d8dc; }
        """)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def _save(self):
        pw      = self.new_pw.text()
        confirm = self.confirm_pw.text()
        if len(pw) < 4:
            self.msg_lbl.setStyleSheet("color: #e74c3c; font-size: 11px; background: transparent;")
            self.msg_lbl.setText("كلمة المرور يجب أن تكون 4 أحرف على الأقل"); return
        if pw != confirm:
            self.msg_lbl.setStyleSheet("color: #e74c3c; font-size: 11px; background: transparent;")
            self.msg_lbl.setText("كلمتا المرور غير متطابقتان"); return
        db.update_user_password(self._user_id, pw)
        self.msg_lbl.setStyleSheet("color: #27ae60; font-size: 11px; background: transparent;")
        self.msg_lbl.setText("✅  تم تغيير كلمة المرور")
        QTimer.singleShot(1000, self.accept)


# ── Main page ─────────────────────────────────────────────────────────────────

class UsersPage(QWidget):
    def __init__(self, current_username: str):
        super().__init__()
        self._current_username = current_username
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self.load_users()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        hdr, _ = page_header("👥  إدارة المستخدمين", "إضافة وحذف وتغيير كلمات مرور المستخدمين")
        layout.addWidget(hdr)

        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame { background: #f4f7fb; border-radius: 10px; border: 1px solid #cdd8e8; }
        """)
        card_shadow(toolbar, blur=8, y=2, alpha=12)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(16, 12, 16, 12)

        self.count_lbl = QLabel("عدد المستخدمين: 0")
        self.count_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px; background: transparent;")
        tl.addWidget(self.count_lbl)
        tl.addStretch()

        add_btn = QPushButton("➕  إضافة مستخدم")
        add_btn.setStyleSheet(BTN_ADD)
        add_btn.setMinimumWidth(160)
        add_btn.clicked.connect(self._add_user)
        tl.addWidget(add_btn)
        layout.addWidget(toolbar)

        # Table
        card = QFrame()
        card.setStyleSheet("QFrame { background: white; border-radius: 10px; border: 1px solid #dce3ec; }")
        card_shadow(card)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["الإجراءات", "اسم المستخدم"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 200)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        cl.addWidget(self.table)
        layout.addWidget(card)

    # ── Data ──────────────────────────────────────────────────────────────────

    def load_users(self):
        users = db.get_all_users()
        self.table.setRowCount(len(users))
        self.count_lbl.setText(f"عدد المستخدمين: {len(users)}")

        for row, u in enumerate(users):
            uid      = u['id']
            username = u['username']
            is_me    = (username == self._current_username)

            # Username cell
            name_item = QTableWidgetItem(
                f"  {username}  {'  ← أنت' if is_me else ''}"
            )
            name_item.setForeground(QColor(C_PRIMARY if is_me else C_TEXT_DARK))
            if is_me:
                name_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            self.table.setItem(row, 1, name_item)

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(6, 4, 6, 4)
            btn_layout.setSpacing(6)

            pw_btn = QPushButton("🔑  كلمة المرور")
            pw_btn.setStyleSheet(BTN_EDIT)
            pw_btn.setFixedHeight(30)
            pw_btn.clicked.connect(lambda _, i=uid, n=username: self._change_pw(i, n))
            btn_layout.addWidget(pw_btn)

            del_btn = QPushButton("🗑  حذف")
            del_btn.setStyleSheet(BTN_DELETE)
            del_btn.setFixedHeight(30)
            del_btn.setEnabled(not is_me)
            if is_me:
                del_btn.setToolTip("لا يمكن حذف حسابك الحالي")
            del_btn.clicked.connect(lambda _, i=uid, n=username: self._delete_user(i, n))
            btn_layout.addWidget(del_btn)

            self.table.setCellWidget(row, 0, btn_widget)
            self.table.setRowHeight(row, 48)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_user(self):
        dlg = _AddUserDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_users()

    def _change_pw(self, user_id: int, username: str):
        dlg = _ChangeUserPasswordDialog(user_id, username, self)
        dlg.exec()

    def _delete_user(self, user_id: int, username: str):
        if db.has_any_user() and len(db.get_all_users()) <= 1:
            from ui.styles import show_warning
            show_warning(self, "لا يمكن الحذف", "يجب أن يكون هناك مستخدم واحد على الأقل.")
            return
        from ui.styles import confirm_delete
        if confirm_delete(self, f"هل أنت متأكد من حذف المستخدم «{username}»؟"):
            db.delete_user(user_id)
            self.load_users()
