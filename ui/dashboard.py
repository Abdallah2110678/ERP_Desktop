from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
import database as db
from config import PHARMACY_NAME, PHARMACY_SUBTITLE, APP_VERSION, APP_YEAR
from ui.styles import card_shadow, C_PRIMARY, C_INFO, C_DANGER, C_PURPLE, C_ORANGE, C_TEXT_DARK, C_TEXT_MED


class StatCard(QFrame):
    def __init__(self, title, color, icon):
        super().__init__()
        self.setMinimumHeight(130)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #dce3ec;
            }}
        """)
        card_shadow(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(5)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"""
            font-size: 26px;
            background: {color}1a;
            border-radius: 10px;
            padding: 6px 8px;
            border: none;
        """)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFixedSize(48, 48)
        top.addStretch()
        top.addWidget(icon_lbl)
        layout.addLayout(top)

        self.value_label = QLabel("0")
        self.value_label.setFont(QFont("Tahoma", 23, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.value_label)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 11px; background: transparent; border: none;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title_lbl)

        bar = QFrame()
        bar.setFixedHeight(4)
        bar.setStyleSheet(f"background: {color}; border-radius: 2px; border: none;")
        layout.addWidget(bar)


class DashboardPage(QWidget):
    def __init__(self, navigate_cb=None):
        super().__init__()
        self.navigate_cb = navigate_cb  # function(index) to switch pages
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("background-color: #eef1f5; font-family: Tahoma;")
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ── Header banner ────────────────────────────────────────────────────
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16a085, stop:1 #1abc9c);
                border-radius: 14px;
                border: none;
            }
        """)
        card_shadow(banner, blur=25, y=6, alpha=35)
        bl = QHBoxLayout(banner)
        bl.setContentsMargins(24, 18, 24, 18)

        left = QVBoxLayout()
        left.setSpacing(4)
        welcome = QLabel(f"مرحباً بك في {PHARMACY_NAME}")
        welcome.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        welcome.setStyleSheet("color: white; background: transparent;")
        left.addWidget(welcome)

        today = QDate.currentDate()
        ar_months = {
            1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
            7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
        }
        date_str = f"{today.day()} {ar_months[today.month()]} {today.year()}"
        date_lbl = QLabel(f"اليوم: {date_str}")
        date_lbl.setStyleSheet("color: #c8f5ea; font-size: 12px; background: transparent;")
        left.addWidget(date_lbl)

        sub_lbl = QLabel(PHARMACY_SUBTITLE)
        sub_lbl.setStyleSheet("color: #a0e8d8; font-size: 11px; background: transparent;")
        left.addWidget(sub_lbl)

        bl.addLayout(left)
        bl.addStretch()
        icon_lbl = QLabel("🏥")
        icon_lbl.setStyleSheet("font-size: 44px; background: transparent;")
        bl.addWidget(icon_lbl)
        layout.addWidget(banner)

        # ── Stat cards ───────────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(14)
        for i in range(5):
            grid.setColumnStretch(i, 1)

        self.card_products       = StatCard("إجمالي الأدوية في المخزون",    C_INFO,    "💊")
        self.card_customers      = StatCard("إجمالي العملاء المسجلين",      C_PURPLE,  "👥")
        self.card_sales          = StatCard("مبيعات اليوم  (ج.م)",          C_PRIMARY, "💰")
        self.card_debt           = StatCard("إجمالي الديون المستحقة  (ج.م)", C_DANGER,  "📋")
        self.card_supplier_debt  = StatCard("إجمالي الديون (علينا)  (ج.م)", C_ORANGE,  "💸")

        grid.addWidget(self.card_products,      0, 0)
        grid.addWidget(self.card_customers,     0, 1)
        grid.addWidget(self.card_sales,         0, 2)
        grid.addWidget(self.card_debt,          0, 3)
        grid.addWidget(self.card_supplier_debt, 0, 4)
        layout.addLayout(grid)

        # ── Warning banner ───────────────────────────────────────────────────
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("""
            background-color: #fff8e6;
            color: #7d5a00;
            padding: 12px 18px;
            border-radius: 9px;
            font-size: 13px;
            border: 1px solid #f4c842;
        """)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        # ── Quick actions ────────────────────────────────────────────────────
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #dce3ec;
            }
        """)
        card_shadow(actions_frame)
        al = QVBoxLayout(actions_frame)
        al.setContentsMargins(20, 16, 20, 16)
        al.setSpacing(12)

        acts_title = QLabel("إجراءات سريعة")
        acts_title.setFont(QFont("Tahoma", 13, QFont.Weight.Bold))
        acts_title.setStyleSheet(f"color: {C_TEXT_DARK};")
        al.addWidget(acts_title)

        acts_row = QHBoxLayout()
        acts_row.setSpacing(12)

        # (label, color, hover, page_index)
        quick = [
            ("🛒  بيع جديد",     C_PRIMARY, "#1e8449", 3),
            ("📦  شراء جديد",    C_ORANGE,  "#d35400", 4),
            ("💊  الأدوية",      C_INFO,    "#2471a3", 1),
            ("👥  العملاء",      C_PURPLE,  "#7d3c98", 2),
        ]
        for text, color, hover, page_idx in quick:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color}18;
                    color: {color};
                    border: 1.5px solid {color}55;
                    padding: 11px 18px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-family: Tahoma;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: white;
                    border-color: {color};
                }}
                QPushButton:pressed {{
                    background-color: {hover};
                    color: white;
                    border-color: {hover};
                }}
            """)
            if self.navigate_cb:
                btn.clicked.connect(lambda _, i=page_idx: self.navigate_cb(i))
            acts_row.addWidget(btn)

        al.addLayout(acts_row)
        layout.addWidget(actions_frame)
        layout.addStretch()

    def refresh(self):
        stats = db.get_dashboard_stats()
        self.card_products.value_label.setText(str(stats['total_products']))
        self.card_customers.value_label.setText(str(stats['total_customers']))
        self.card_sales.value_label.setText(f"{stats['today_sales']:.2f}")
        self.card_debt.value_label.setText(f"{stats['total_debt']:.2f}")
        self.card_supplier_debt.value_label.setText(f"{stats['total_supplier_debt']:.2f}")

        if stats['low_stock'] > 0:
            self.warning_label.setText(
                f"⚠️   تنبيه: يوجد {stats['low_stock']} دواء في مخزون منخفض (أقل من 10 وحدات) — يُنصح بالتزود"
            )
            self.warning_label.show()
        else:
            self.warning_label.hide()
