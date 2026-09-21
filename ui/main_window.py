from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame,
    QFileDialog, QMessageBox, QMenu, QApplication,
)
from PyQt6.QtCore import Qt, QTimer, QDateTime
from PyQt6.QtGui import QFont
import shutil
from datetime import date
from pathlib import Path

from ui.dashboard import DashboardPage
from ui.products import ProductsPage
from ui.customers import CustomersPage
from ui.sales import SalesPage
from ui.purchases import PurchasesPage
from ui.suppliers import SuppliersPage
from ui.purchase_returns import PurchaseReturnsPage
from ui.sale_returns import SaleReturnsPage
from ui.payments_screen import PaymentsPage
from ui.customer_account import CustomerAccountPage
from ui.supplier_account import SupplierAccountPage
from ui.product_report import ProductReportPage
from ui.change_password import ChangePasswordDialog
from ui.users_page import UsersPage
from ui.notification_bar import NotificationBar
from ui.styles import SIDEBAR_STYLE, C_SIDEBAR, C_PRIMARY
from config import PHARMACY_NAME, APP_VERSION, APP_YEAR
import database as db


class MainWindow(QMainWindow):
    def __init__(self, current_user: str = ""):
        super().__init__()
        self._current_user = current_user
        self.setWindowTitle(f"🏥  {PHARMACY_NAME} — نظام إدارة متكامل")
        self.setMinimumSize(1220, 740)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("QMainWindow { background-color: #eef1f5; }")

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.notif_bar = NotificationBar()
        right_layout.addWidget(self.notif_bar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background-color: #eef1f5; }")

        self.dashboard_page       = DashboardPage(navigate_cb=self._navigate)
        self.products_page        = ProductsPage()
        self.customers_page       = CustomersPage()
        self.sales_page           = SalesPage()
        self.purchases_page       = PurchasesPage()
        self.suppliers_page       = SuppliersPage()
        self.purchase_returns_page = PurchaseReturnsPage()
        self.sale_returns_page    = SaleReturnsPage()
        self.payments_page        = PaymentsPage()
        self.customer_account_page = CustomerAccountPage()
        self.supplier_account_page = SupplierAccountPage()
        self.product_report_page   = ProductReportPage()
        self.users_page            = UsersPage(current_user)

        for page in (
            self.dashboard_page,           # 0
            self.products_page,            # 1
            self.customers_page,           # 2
            self.sales_page,               # 3
            self.purchases_page,           # 4
            self.suppliers_page,           # 5
            self.purchase_returns_page,    # 6
            self.sale_returns_page,        # 7
            self.payments_page,            # 8
            self.customer_account_page,    # 9
            self.supplier_account_page,    # 10
            self.product_report_page,      # 11
            self.users_page,              # 12
        ):
            self.stack.addWidget(page)

        right_layout.addWidget(self.stack)
        root.addWidget(right_widget)
        self._build_statusbar()
        self._navigate(0)

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(215)
        sidebar.setStyleSheet(SIDEBAR_STYLE + f"QFrame#sidebar {{ background-color: {C_SIDEBAR}; }}")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Logo ────────────────────────────────────────────────────────────
        logo = QWidget()
        logo.setFixedHeight(68)
        logo.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {C_PRIMARY}, stop:1 #1a8449);
        """)
        ll = QHBoxLayout(logo)
        ll.setContentsMargins(12, 8, 12, 8)
        ll.setSpacing(6)
        icon_lbl = QLabel("🏥")
        icon_lbl.setStyleSheet("color: white; font-size: 22px; background: transparent;")
        icon_lbl.setFixedWidth(30)
        ll.addWidget(icon_lbl)
        txt_col = QVBoxLayout()
        txt_col.setSpacing(1)
        name_lbl = QLabel(PHARMACY_NAME)
        name_lbl.setFont(QFont("Tahoma", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: white; background: transparent;")
        name_lbl.setWordWrap(True)
        txt_col.addWidget(name_lbl)
        sub_lbl = QLabel("نظام إدارة متكامل")
        sub_lbl.setStyleSheet("color: #c8f7e8; font-size: 9px; background: transparent;")
        txt_col.addWidget(sub_lbl)
        ll.addLayout(txt_col)
        layout.addWidget(logo)

        def _sep():
            s = QFrame()
            s.setFixedHeight(1)
            s.setStyleSheet("background-color: #1e3a52; border: none;")
            layout.addWidget(s)

        _sep()

        # ── Nav groups ──────────────────────────────────────────────────────
        # (group_label, start_expanded, [(text, page_index), ...])
        groups = [
            (None, True, [
                ("🏠  لوحة التحكم", 0),
            ]),
            ("الإدارة", True, [
                ("💊  الأصناف",   1),
                ("👥  العملاء",   2),
                ("🏭  الموردون",  5),
            ]),
            ("العمليات", True, [
                ("🛒  المبيعات",        3),
                ("📦  المشتريات",       4),
                ("↩  مرتجعات البيع",    7),
                ("↩  مرتجعات الشراء",   6),
                ("💳  الدفعات",         8),
            ]),
            ("الحسابات", False, [
                ("📊  حساب العميل",  9),
                ("📊  حساب المورد", 10),
                ("📋  تقرير الصنف", 11),
            ]),
            ("الإعدادات", False, [
                ("👤  المستخدمون", 12),
            ]),
        ]

        self.nav_buttons  = []           # [(page_idx, QPushButton)]
        self._groups      = {}           # group_label -> {'hdr': btn, 'children': [btn], 'expanded': bool}
        self._idx_to_group = {}          # page_idx -> group_label

        _CAT_STYLE_ON = (
            "QPushButton#cat_toggle {"
            "  color: #6b93ae; background: transparent; border: none;"
            "  font-family: Tahoma; font-size: 9px; font-weight: bold;"
            "  letter-spacing: 1px; text-align: right; padding: 5px 12px 2px;"
            "}"
            "QPushButton#cat_toggle:hover {"
            "  color: #8ab4cc; background: rgba(255,255,255,0.04);"
            "  border-radius: 4px;"
            "}"
        )

        for group_label, start_expanded, items in groups:
            hdr_btn = None
            if group_label:
                arrow = "▼" if start_expanded else "◀"
                hdr_btn = QPushButton(f"{arrow}  {group_label}")
                hdr_btn.setObjectName("cat_toggle")
                hdr_btn.setFixedHeight(28)
                hdr_btn.setFont(QFont("Tahoma", 9))
                hdr_btn.setStyleSheet(_CAT_STYLE_ON)
                hdr_btn.clicked.connect(lambda _, g=group_label: self._toggle_group(g))
                layout.addWidget(hdr_btn)

            child_btns = []
            for text, idx in items:
                btn = QPushButton(text)
                btn.setObjectName("nav_btn")
                btn.setCheckable(True)
                btn.setFixedHeight(44)
                btn.setFont(QFont("Tahoma", 11))
                btn.setVisible(start_expanded)
                btn.clicked.connect(lambda _, i=idx: self._navigate(i))
                layout.addWidget(btn)
                self.nav_buttons.append((idx, btn))
                child_btns.append(btn)
                if group_label:
                    self._idx_to_group[idx] = group_label

            if group_label:
                self._groups[group_label] = {
                    'hdr': hdr_btn,
                    'children': child_btns,
                    'expanded': start_expanded,
                }

        layout.addStretch()
        _sep()

        # ── Bottom utility buttons ───────────────────────────────────────────
        _UTIL_STYLE = """
            QPushButton {{
                color: #4a7a9b; background: transparent; border: none;
                font-family: Tahoma; font-size: 10px;
                padding: 0 12px; text-align: right;
            }}
            QPushButton:hover {{
                color: {hover}; background: rgba(255,255,255,0.06);
                border-radius: 4px;
            }}
        """
        backup_btn = QPushButton("💾  النسخ الاحتياطي")
        backup_btn.setFixedHeight(34)
        backup_btn.setFont(QFont("Tahoma", 10))
        backup_btn.setStyleSheet(_UTIL_STYLE.format(hover="#27ae60"))
        backup_btn.clicked.connect(self._show_backup_menu)
        self._backup_btn = backup_btn
        layout.addWidget(backup_btn)

        cred_btn = QPushButton("⚙  بيانات الدخول")
        cred_btn.setFixedHeight(34)
        cred_btn.setFont(QFont("Tahoma", 10))
        cred_btn.setStyleSheet(_UTIL_STYLE.format(hover="#6b93ae"))
        cred_btn.clicked.connect(self._change_credentials)
        layout.addWidget(cred_btn)

        ver_lbl = QLabel(f"v{APP_VERSION}  •  {APP_YEAR}")
        ver_lbl.setStyleSheet("color: #2d5470; font-size: 9px; padding: 4px 0 6px; background: transparent;")
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver_lbl)

        return sidebar

    def _toggle_group(self, group_label):
        g = self._groups[group_label]
        new_expanded = not g['expanded']
        g['expanded'] = new_expanded
        arrow = "▼" if new_expanded else "◀"
        g['hdr'].setText(f"{arrow}  {group_label}")
        for btn in g['children']:
            btn.setVisible(new_expanded)

    def _show_backup_menu(self):
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        menu.setStyleSheet("""
            QMenu {
                background: #0f1f2e; border: 1px solid #1e3a52;
                border-radius: 6px; padding: 4px;
                font-family: Tahoma; font-size: 11px; color: #c8d8e8;
            }
            QMenu::item { padding: 8px 20px 8px 12px; border-radius: 4px; }
            QMenu::item:selected { background: #1e3a52; color: white; }
        """)
        menu.addAction("📤  تصدير البيانات (نسخة احتياطية)", self._export_data)
        menu.addAction("📥  استيراد البيانات (استعادة)", self._import_data)
        menu.addSeparator()
        menu.addAction("🗄  استيراد من Access (.mdb)", self._import_access)
        btn = self._backup_btn
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _build_statusbar(self):
        bar = self.statusBar()
        bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {C_SIDEBAR};
                color: #6b93ae;
                font-family: Tahoma;
                font-size: 11px;
                padding: 3px 12px;
                border-top: 1px solid #1e3a52;
            }}
        """)

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("background: transparent;")
        self.clock_label.setTextFormat(Qt.TextFormat.RichText)
        bar.addPermanentWidget(self.clock_label)

        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(60_000)
        bar.showMessage("جاهز")

    def _tick(self):
        dt = QDateTime.currentDateTime()
        ar_days   = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
        ar_months = {
            1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
            7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
        }
        time_str  = dt.time().toString('hh:mm')
        day_name  = ar_days[dt.date().dayOfWeek() - 1]
        day_num   = dt.date().day()
        month_str = ar_months[dt.date().month()]
        year_str  = dt.date().year()
        self.clock_label.setText(
            f"<span style='color:#f39c12;font-weight:bold;'>🕐 {time_str}</span>"
            f"<span style='color:#4a7a9b;'>  |  </span>"
            f"<span style='color:#2ecc71;font-weight:bold;'>{day_name}</span>"
            f"<span style='color:#4a7a9b;'> </span>"
            f"<span style='color:#e74c3c;font-weight:bold;'>{day_num}</span>"
            f"<span style='color:#4a7a9b;'> </span>"
            f"<span style='color:#9b59b6;font-weight:bold;'>{month_str}</span>"
            f"<span style='color:#4a7a9b;'> </span>"
            f"<span style='color:#3498db;font-weight:bold;'>{year_str}</span>"
        )

    def _export_data(self):
        default_name = f"pharmacy_backup_{date.today().strftime('%Y-%m-%d')}.db"
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ نسخة احتياطية", default_name, "قاعدة البيانات (*.db)"
        )
        if not path:
            return
        try:
            shutil.copy2(str(db.DB_PATH), path)
            QMessageBox.information(self, "تم بنجاح",
                f"✓  تم تصدير البيانات بنجاح\n\nالملف محفوظ في:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في التصدير", f"فشل التصدير:\n{e}")

    def _import_data(self):
        reply = QMessageBox.warning(
            self, "تحذير — استيراد البيانات",
            "⚠️  سيتم استبدال جميع البيانات الحالية بالبيانات المستوردة.\n\n"
            "تأكد أن الملف المختار هو نسخة احتياطية صحيحة من هذا التطبيق.\n\n"
            "هل تريد المتابعة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف النسخة الاحتياطية", "", "قاعدة البيانات (*.db)"
        )
        if not path:
            return
        try:
            shutil.copy2(path, str(db.DB_PATH))
            QMessageBox.information(self, "تم بنجاح",
                "✓  تم استيراد البيانات بنجاح.\nيتم الآن إعادة تحميل البيانات.")
            self._navigate(0)
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الاستيراد", f"فشل الاستيراد:\n{e}")

    def _import_access(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر قاعدة بيانات Access", "", "Access (*.mdb *.accdb)"
        )
        if not path:
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("استيراد من Access")
        box.setText(
            "سيتم إضافة العملاء والموردين والأصناف والفواتير والمرتجعات والدفعات "
            "إلى البيانات الحالية (بدون حذف أي شيء).\n\n"
            "قبل البدء تُحفظ نسخة احتياطية تلقائياً بجوار قاعدة البيانات.\n\n"
            "هل تريد استيراد أرصدة الديون المحسوبة من الفواتير؟\n"
            "(الأرصدة المحسوبة من الملف القديم قد تكون كبيرة وغير دقيقة — يُنصح بعدم استيرادها)"
        )
        no_debt = box.addButton("استيراد بدون الديون (موصى به)", QMessageBox.ButtonRole.AcceptRole)
        with_debt = box.addButton("استيراد مع الديون", QMessageBox.ButtonRole.AcceptRole)
        box.addButton("إلغاء", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked not in (no_debt, with_debt):
            return

        try:
            import import_access
        except ImportError:
            QMessageBox.critical(self, "خطأ", "مكتبة pyodbc غير مثبتة.\nثبّتها بالأمر: pip install pyodbc")
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            stats, backup = import_access.run_import(
                Path(path), commit=True, skip_debt=(clicked is no_debt))
        except import_access.AlreadyImported:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "تم الاستيراد سابقاً",
                "فواتير Access موجودة بالفعل في قاعدة البيانات.\n"
                "إعادة الاستيراد ستكرر الفواتير، لذلك تم إيقافه.")
            return
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "خطأ في الاستيراد",
                f"فشل الاستيراد ولم يتم تغيير أي بيانات:\n{e}")
            return
        QApplication.restoreOverrideCursor()

        labels = [
            ("products", "أصناف جديدة"), ("customers", "عملاء جدد"), ("suppliers", "موردون جدد"),
            ("sales", "فواتير بيع"), ("sale returns", "مرتجعات بيع"),
            ("purchases", "فواتير شراء"), ("purchase returns", "مرتجعات شراء"),
            ("customer payments", "دفعات عملاء"), ("supplier payments", "دفعات موردين"),
        ]
        lines = "\n".join(f"{name}: {stats.get(key, 0):,}" for key, name in labels)
        QMessageBox.information(self, "تم بنجاح",
            f"✓  تم استيراد البيانات من Access\n\n{lines}\n\n"
            f"النسخة الاحتياطية السابقة:\n{backup}")
        self._navigate(0)

    def _change_credentials(self):
        dlg = ChangePasswordDialog(self._current_user, self)
        dlg.exec()

    def _navigate(self, index):
        # Auto-expand the group that owns this page if it's currently collapsed
        group_label = self._idx_to_group.get(index)
        if group_label and not self._groups[group_label]['expanded']:
            self._toggle_group(group_label)

        self.stack.setCurrentIndex(index)
        for idx, btn in self.nav_buttons:
            btn.setChecked(idx == index)

        if index == 0:
            self.dashboard_page.refresh()
        elif index == 1:
            self.products_page.load_products()
        elif index == 2:
            self.customers_page.load_customers()
        elif index == 3:
            self.sales_page.load_sales()
        elif index == 4:
            self.purchases_page.load_purchases()
        elif index == 5:
            self.suppliers_page.load_suppliers()
        elif index == 6:
            self.purchase_returns_page.load_returns()
        elif index == 7:
            self.sale_returns_page.load_returns()
        elif index == 8:
            self.payments_page.load_payments()
        elif index == 9:
            self.customer_account_page._load_customers()
        elif index == 10:
            self.supplier_account_page._load_suppliers()
        elif index == 11:
            self.product_report_page._load_products()
        elif index == 12:
            self.users_page.load_users()

        self.notif_bar.refresh()

        page_names = [
            "لوحة التحكم", "الأصناف", "العملاء", "المبيعات", "المشتريات", "الموردون",
            "مرتجعات الشراء", "مرتجعات البيع", "الدفعات", "حساب العميل", "حساب المورد",
            "تقرير الصنف", "المستخدمون",
        ]
        self.statusBar().showMessage(f"الصفحة الحالية:  {page_names[index]}")
