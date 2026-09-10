"""
Notification bars shown at the top of the content area for low stock
and near-expiry products. Refreshes every time the user navigates.
"""
from datetime import date
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import database as db
from ui.styles import card_shadow, C_DANGER, C_TEXT_DARK, C_TEXT_MED, TABLE_STYLE

LOW_THRESHOLD   = 30   # warning
CRIT_THRESHOLD  = 10   # critical
EXPIRY_DAYS     = 90   # warn when expiry is within this many days


class LowStockDialog(QDialog):
    """Full list of low-stock products with a Print-PDF button."""

    def __init__(self, parent, products):
        super().__init__(parent)
        self.products = products
        self.setWindowTitle("المنتجات ذات المخزون المنخفض")
        self.resize(740, 480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("""
            QDialog { background: #f4f7fa; font-family: Tahoma; }
            QLabel  { font-family: Tahoma; background: transparent; }
        """ + TABLE_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet("""
            QFrame { background:#1a2535; border-radius:10px; border:none; }
        """)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(18, 14, 18, 14)

        title = QLabel("⚠️  المنتجات ذات المخزون المنخفض")
        title.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        hl.addWidget(title)
        hl.addStretch()

        critical_count = sum(1 for p in self.products if p['quantity'] <= CRIT_THRESHOLD)
        low_count      = len(self.products) - critical_count

        if critical_count:
            crit_lbl = QLabel(f"🔴  حرج: {critical_count}")
            crit_lbl.setStyleSheet("color: #ff8080; font-size: 12px; font-weight: bold;")
            hl.addWidget(crit_lbl)

        if low_count:
            low_lbl = QLabel(f"  🟡  منخفض: {low_count}")
            low_lbl.setStyleSheet("color: #ffd080; font-size: 12px;")
            hl.addWidget(low_lbl)

        layout.addWidget(hdr)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "الحالة", "سعر البيع (ج.م)", "سعر الشراء (ج.م)", "الكمية", "الوحدة", "اسم الدواء"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().hide()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.table)

        self._fill_table()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        print_btn = QPushButton("🖨  طباعة تقرير PDF")
        print_btn.setStyleSheet("""
            QPushButton { background:#e67e22; color:white; border:none;
                padding:10px 22px; border-radius:7px; font-size:13px;
                font-family:Tahoma; font-weight:bold; }
            QPushButton:hover { background:#d35400; }
        """)
        print_btn.clicked.connect(self._print_pdf)

        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("""
            QPushButton { background:#6c757d; color:white; border:none;
                padding:10px 20px; border-radius:7px; font-size:13px; font-family:Tahoma; }
            QPushButton:hover { background:#5a6268; }
        """)
        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(print_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _fill_table(self):
        self.table.setRowCount(len(self.products))
        for row, p in enumerate(self.products):
            is_crit = p['quantity'] <= CRIT_THRESHOLD

            status_item = QTableWidgetItem("🔴  حرج" if is_crit else "🟡  منخفض")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setForeground(QColor(C_DANGER if is_crit else "#e67e22"))
            status_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            self.table.setItem(row, 0, status_item)

            name_item = QTableWidgetItem(p['name'])
            name_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            name_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 5, name_item)

            unit_item = QTableWidgetItem(p['unit'])
            unit_item.setForeground(QColor("#5d6d7e"))
            self.table.setItem(row, 4, unit_item)

            qty_item = QTableWidgetItem(f"{p['quantity']:.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_item.setForeground(QColor(C_DANGER if is_crit else "#e67e22"))
            qty_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            self.table.setItem(row, 3, qty_item)

            for col, val, clr in [
                (2, f"{p['purchase_price']:.2f}", "#5d6d7e"),
                (1, f"{p['selling_price']:.2f}",  "#1a7a4a"),
            ]:
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setForeground(QColor(clr))
                self.table.setItem(row, col, it)

            self.table.setRowHeight(row, 50)

    def _print_pdf(self):
        try:
            from pdf_report import generate_low_stock_report, open_pdf
            path = generate_low_stock_report(self.products, threshold=LOW_THRESHOLD)
            open_pdf(path)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            from ui.styles import show_error
            show_error(self, "خطأ", f"فشل إنشاء ملف PDF:\n{e}")


class ExpiryDialog(QDialog):
    """Dialog listing products whose batches are expiring within EXPIRY_DAYS days."""

    def __init__(self, parent, products):
        super().__init__(parent)
        self.products = products
        self.setWindowTitle("المنتجات قاربت على الانتهاء")
        self.resize(680, 420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("""
            QDialog { background: #f4f7fa; font-family: Tahoma; }
            QLabel  { font-family: Tahoma; background: transparent; }
        """ + TABLE_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        hdr = QFrame()
        hdr.setStyleSheet("QFrame { background: #6c3483; border-radius: 10px; border: none; }")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(18, 14, 18, 14)
        title = QLabel("⏰  المنتجات قاربت على الانتهاء")
        title.setFont(QFont("Tahoma", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        hl.addWidget(title)
        hl.addStretch()
        today_str = date.today().strftime('%Y-%m-%d')
        expired_count = sum(1 for p in self.products if p['expiry_date'] < today_str)
        soon_count = len(self.products) - expired_count
        if expired_count:
            el = QLabel(f"🔴  منتهي: {expired_count}")
            el.setStyleSheet("color: #ff8080; font-size: 12px; font-weight: bold;")
            hl.addWidget(el)
        if soon_count:
            sl = QLabel(f"  🟡  قريباً: {soon_count}")
            sl.setStyleSheet("color: #ffd080; font-size: 12px;")
            hl.addWidget(sl)
        layout.addWidget(hdr)

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["الحالة", "تاريخ الانتهاء", "الكمية", "اسم المنتج"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().hide()
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setFrameShape(QFrame.Shape.NoFrame)
        table.setRowCount(len(self.products))
        layout.addWidget(table)

        today_str = date.today().strftime('%Y-%m-%d')
        for row, p in enumerate(self.products):
            is_expired = p['expiry_date'] < today_str
            days_left = (date.fromisoformat(p['expiry_date']) - date.today()).days

            if is_expired:
                status = "🔴  منتهي الصلاحية"
                clr = C_DANGER
            elif days_left <= 7:
                status = f"🟠  ينتهي بعد {days_left} يوم"
                clr = "#e67e22"
            else:
                status = f"🟡  ينتهي بعد {days_left} يوم"
                clr = "#d4ac0d"

            st = QTableWidgetItem(status)
            st.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            st.setForeground(QColor(clr))
            st.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
            table.setItem(row, 0, st)

            exp_it = QTableWidgetItem(p['expiry_date'])
            exp_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            exp_it.setForeground(QColor(clr))
            table.setItem(row, 1, exp_it)

            qty_it = QTableWidgetItem(f"{p['total_qty']:.2f}  {p['unit']}")
            qty_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_it.setForeground(QColor(C_TEXT_MED))
            table.setItem(row, 2, qty_it)

            name_it = QTableWidgetItem(p['name'])
            name_it.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            name_it.setForeground(QColor(C_TEXT_DARK))
            table.setItem(row, 3, name_it)
            table.setRowHeight(row, 44)

        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet("""
            QPushButton { background: #6c757d; color: white; border: none;
                padding: 10px 20px; border-radius: 7px; font-size: 13px; font-family: Tahoma; }
            QPushButton:hover { background: #5a6268; }
        """)
        close_btn.clicked.connect(self.accept)
        bl = QHBoxLayout()
        bl.addStretch()
        bl.addWidget(close_btn)
        layout.addLayout(bl)


def _make_inner_bar(parent, msg_attr, open_fn):
    """Helper: create one horizontal notification strip. Returns (QFrame, msg_label)."""
    bar = QFrame(parent)
    bar.setFixedHeight(44)
    layout = QHBoxLayout(bar)
    layout.setContentsMargins(16, 0, 16, 0)
    layout.setSpacing(14)

    bell = QLabel("🔔")
    bell.setStyleSheet("font-size: 18px; background: transparent;")
    layout.addWidget(bell)

    msg = QLabel()
    msg.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
    layout.addWidget(msg)
    layout.addStretch()

    view_btn = QPushButton("عرض التفاصيل  ›")
    view_btn.setStyleSheet("""
        QPushButton {
            background: rgba(255,255,255,0.22); color: white;
            border: 1.5px solid rgba(255,255,255,0.45);
            padding: 6px 14px; border-radius: 6px;
            font-size: 12px; font-family: Tahoma; font-weight: bold;
        }
        QPushButton:hover { background: rgba(255,255,255,0.35); }
    """)
    view_btn.clicked.connect(open_fn)
    layout.addWidget(view_btn)

    dismiss_btn = QPushButton("✕")
    dismiss_btn.setFixedSize(26, 26)
    dismiss_btn.setStyleSheet("""
        QPushButton {
            background: rgba(255,255,255,0.15); color: white;
            border: none; border-radius: 13px; font-size: 13px; font-family: Tahoma;
        }
        QPushButton:hover { background: rgba(255,255,255,0.30); }
    """)
    dismiss_btn.clicked.connect(bar.hide)
    layout.addWidget(dismiss_btn)

    return bar, msg


class NotificationBar(QWidget):
    """
    Container for two independent notification strips:
      - Low-stock (red/orange)
      - Near-expiry (purple)
    Each strip is independently shown/hidden.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._products  = []
        self._expiring  = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stock_bar, self._stock_msg = _make_inner_bar(self, '_stock_msg', self._open_stock_dialog)
        self._expiry_bar, self._expiry_msg = _make_inner_bar(self, '_expiry_msg', self._open_expiry_dialog)

        layout.addWidget(self._stock_bar)
        layout.addWidget(self._expiry_bar)

        self._stock_bar.hide()
        self._expiry_bar.hide()
        self.hide()

        self.refresh()

    def refresh(self):
        """Re-query the database and update both strips."""
        # ── Low stock ──────────────────────────────────────────────────────────
        self._products     = db.get_low_stock_products(LOW_THRESHOLD)
        critical_count     = sum(1 for p in self._products if p['quantity'] <= CRIT_THRESHOLD)
        low_count          = len(self._products) - critical_count

        if self._products:
            parts = []
            if critical_count:
                parts.append(f"{critical_count} منتج حرج (أقل من {CRIT_THRESHOLD} وحدات)")
            if low_count:
                parts.append(f"{low_count} منتج منخفض")
            self._stock_msg.setText("⚠   " + "  |  ".join(parts))
            if critical_count:
                self._stock_bar.setStyleSheet("""
                    QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #922b21, stop:1 #e74c3c); border-bottom: 1px solid #7b241c; }
                    QLabel { color: white; background: transparent; font-family: Tahoma; }
                """)
            else:
                self._stock_bar.setStyleSheet("""
                    QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 #b7770d, stop:1 #e67e22); border-bottom: 1px solid #9c6508; }
                    QLabel { color: white; background: transparent; font-family: Tahoma; }
                """)
            self._stock_bar.show()
        else:
            self._stock_bar.hide()

        # ── Near-expiry ────────────────────────────────────────────────────────
        self._expiring = db.get_expiring_batches(EXPIRY_DAYS)
        today_str = date.today().strftime('%Y-%m-%d')
        expired_count = sum(1 for p in self._expiring if p['expiry_date'] < today_str)
        soon_count    = len(self._expiring) - expired_count

        if self._expiring:
            parts = []
            if expired_count:
                parts.append(f"{expired_count} منتج منتهي الصلاحية")
            if soon_count:
                parts.append(f"{soon_count} منتج ينتهي خلال {EXPIRY_DAYS} يوم")
            self._expiry_msg.setText("⏰   " + "  |  ".join(parts))
            self._expiry_bar.setStyleSheet("""
                QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #6c3483, stop:1 #9b59b6); border-bottom: 1px solid #5b2c6f; }
                QLabel { color: white; background: transparent; font-family: Tahoma; }
            """)
            self._expiry_bar.show()
        else:
            self._expiry_bar.hide()

        self.setVisible(bool(self._products or self._expiring))

    def _open_stock_dialog(self):
        LowStockDialog(self.window(), self._products).exec()

    def _open_expiry_dialog(self):
        ExpiryDialog(self.window(), self._expiring).exec()
