from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QHeaderView, QFrame,
    QTabWidget, QDateEdit, QSplitter,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont, QPalette
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD, BTN_SECONDARY,
    DIALOG_STYLE, PAGE_STYLE, INPUT_STYLE, card_shadow,
    confirm_delete, show_info, show_warning, show_error,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER, C_ORANGE, style_calendar,
)
from ui.products import page_header

C_PURPLE = "#8e44ad"
C_PURPLE_DARK = "#7d3c98"
C_TEAL = "#16a085"
C_TEAL_DARK = "#117a65"
C_BLUE = "#2980b9"
C_BLUE_DARK = "#2471a3"

BTN_TABLE = """
    QPushButton {{
        background: {bg};
        color: white;
        border: none;
        padding: 7px 14px;
        border-radius: 6px;
        font-size: 12px;
        font-family: Tahoma;
        font-weight: bold;
        min-width: 60px;
    }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:pressed {{ background: {hover}; }}
"""


def _btn(text, bg, hover):
    b = QPushButton(text)
    b.setStyleSheet(BTN_TABLE.format(bg=bg, hover=hover))
    return b


class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("تعديل عميل" if customer else "إضافة عميل جديد")
        self.setFixedWidth(430)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_PURPLE}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("تعديل العميل" if self.customer else "إضافة عميل جديد")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("الاسم الكامل للعميل")
        self.name_input.setStyleSheet(INPUT_STYLE)
        form.addRow("اسم العميل *:", self.name_input)

        layout.addLayout(form)

        if self.customer:
            self.name_input.setText(self.customer['name'])

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #e8ecf0; border: none; max-height: 1px;")
        layout.addWidget(sep)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("حفظ  ✓")
        save_btn.setStyleSheet(BTN_ADD)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        if not self.name_input.text().strip():
            show_warning(self, "خطأ", "يرجى إدخال اسم العميل")
            return
        self.accept()

    def get_data(self):
        return {'name': self.name_input.text().strip()}


class PaymentDialog(QDialog):
    def __init__(self, parent, customer):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("تسجيل دفعة")
        self.setFixedWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_ORANGE}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("تسجيل دفعة مالية")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        info_box = QFrame()
        debt = self.customer['total_debt']
        info_box.setStyleSheet(f"""
            QFrame {{
                background: {'#fff8e6' if debt > 0 else '#eafaf1'};
                border-radius: 8px;
                border: 1px solid {'#f4c842' if debt > 0 else '#a9dfbf'};
            }}
        """)
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(4)

        name_lbl = QLabel(f"👤  {self.customer['name']}")
        name_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 13px; font-weight: bold;")
        info_layout.addWidget(name_lbl)

        debt_color = C_DANGER if debt > 0 else C_PRIMARY
        debt_lbl = QLabel(f"الرصيد الحالي: {debt:.2f} ج.م")
        debt_lbl.setStyleSheet(f"color: {debt_color}; font-size: 14px; font-weight: bold;")
        info_layout.addWidget(debt_lbl)
        layout.addWidget(info_box)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.01, 999999)
        self.amount_input.setDecimals(2)
        self.amount_input.setSuffix("  ج.م")
        self.amount_input.setValue(max(0.01, debt))
        self.amount_input.setStyleSheet(INPUT_STYLE)
        form.addRow("المبلغ المدفوع:", self.amount_input)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        self.notes_input.setStyleSheet(INPUT_STYLE)
        form.addRow("ملاحظات:", self.notes_input)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("✓  تسجيل الدفعة")
        save_btn.setStyleSheet(BTN_ADD)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def get_data(self):
        return {'amount': self.amount_input.value(), 'notes': self.notes_input.text().strip()}


class CustomerHistoryDialog(QDialog):
    def __init__(self, parent, customer):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle(f"سجل العميل — {customer['name']}")
        self.resize(1050, 680)
        self.setMinimumSize(900, 580)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE + TABLE_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header banner
        hdr = QFrame()
        hdr.setStyleSheet("QFrame { background: #1a2535; border-radius: 10px; border: none; }")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(20, 14, 20, 14)

        name_lbl = QLabel(f"👤  {self.customer['name']}")
        name_lbl.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: white; background: transparent;")
        hdr_layout.addWidget(name_lbl)

        if self.customer.get('phone'):
            phone_lbl = QLabel(f"📞  {self.customer['phone']}")
            phone_lbl.setStyleSheet("color: #8fa8bf; font-size: 12px; background: transparent;")
            hdr_layout.addWidget(phone_lbl)

        hdr_layout.addStretch()

        debt = self.customer['total_debt']
        debt_color = C_DANGER if debt > 0 else C_PRIMARY
        debt_lbl = QLabel(f"الرصيد الحالي:  {debt:.2f} ج.م")
        debt_lbl.setFont(QFont("Tahoma", 13, QFont.Weight.Bold))
        debt_lbl.setStyleSheet(f"color: {debt_color}; background: transparent;")
        hdr_layout.addWidget(debt_lbl)
        layout.addWidget(hdr)

        # Tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #dce3ec;
                border-radius: 8px;
                background: white;
            }}
            QTabBar::tab {{
                padding: 10px 22px;
                font-family: Tahoma;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px 6px 0 0;
                min-width: 120px;
            }}
            QTabBar::tab:selected {{ background: {C_PURPLE}; color: white; }}
            QTabBar::tab:!selected {{ background: #f0f2f5; color: #5d6d7e; }}
            QTabBar::tab:hover:!selected {{ background: #e0e4ea; }}
        """)

        # ── Tab 1: Invoices ──────────────────────────────────────────────────
        inv_widget = QWidget()
        inv_layout = QVBoxLayout(inv_widget)
        inv_layout.setContentsMargins(10, 10, 10, 10)
        inv_layout.setSpacing(8)

        # Summary row at top of tab
        summary_row = QHBoxLayout()
        self.inv_count_lbl = QLabel()
        self.inv_count_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
        self.inv_total_lbl = QLabel()
        self.inv_total_lbl.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        self.inv_total_lbl.setStyleSheet(f"color: {C_TEXT_DARK};")
        summary_row.addWidget(self.inv_count_lbl)
        summary_row.addStretch()
        summary_row.addWidget(self.inv_total_lbl)
        inv_layout.addLayout(summary_row)

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels([
            "التاريخ", "رقم الفاتورة", "نوع الفاتورة", "الإجمالي (ج.م)",
            "المدفوع (ج.م)", "المتبقي (ج.م)", "نوع الدفع"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.verticalHeader().hide()
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.setShowGrid(False)
        self.sales_table.setFrameShape(QFrame.Shape.NoFrame)
        self.sales_table.currentCellChanged.connect(lambda row, *_: self._on_invoice_row_changed(row))
        inv_layout.addWidget(self.sales_table)

        # Item detail panel inside tab 1
        detail_lbl = QLabel("الأصناف المشتراة في هذه الفاتورة:")
        detail_lbl.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
        detail_lbl.setStyleSheet(f"color: {C_PURPLE}; background: transparent;")
        inv_layout.addWidget(detail_lbl)

        self.items_detail_table = QTableWidget()
        self.items_detail_table.setColumnCount(5)
        self.items_detail_table.setHorizontalHeaderLabels([
            "اسم الصنف", "الكمية", "الوحدة", "السعر (ج.م)", "الإجمالي (ج.م)"
        ])
        self.items_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_detail_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_detail_table.verticalHeader().hide()
        self.items_detail_table.setAlternatingRowColors(True)
        self.items_detail_table.setShowGrid(False)
        self.items_detail_table.setFrameShape(QFrame.Shape.NoFrame)
        self.items_detail_table.setMaximumHeight(200)
        inv_layout.addWidget(self.items_detail_table)

        tabs.addTab(inv_widget, "📄  فواتير البيع")

        # ── Tab 2: All Items ─────────────────────────────────────────────────
        all_items_widget = QWidget()
        all_items_layout = QVBoxLayout(all_items_widget)
        all_items_layout.setContentsMargins(10, 10, 10, 10)

        self.all_items_table = QTableWidget()
        self.all_items_table.setColumnCount(7)
        self.all_items_table.setHorizontalHeaderLabels([
            "التاريخ", "رقم الفاتورة", "اسم الصنف", "الكمية",
            "الوحدة", "السعر (ج.م)", "الإجمالي (ج.م)"
        ])
        self.all_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.all_items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.all_items_table.verticalHeader().hide()
        self.all_items_table.setAlternatingRowColors(True)
        self.all_items_table.setShowGrid(False)
        self.all_items_table.setFrameShape(QFrame.Shape.NoFrame)
        all_items_layout.addWidget(self.all_items_table)
        tabs.addTab(all_items_widget, "🛍  تفاصيل المشتريات")

        # ── Tab 3: Payments ──────────────────────────────────────────────────
        p_widget = QWidget()
        p_layout = QVBoxLayout(p_widget)
        p_layout.setContentsMargins(10, 10, 10, 10)

        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(3)
        self.payments_table.setHorizontalHeaderLabels(["التاريخ", "المبلغ (ج.م)", "ملاحظات"])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payments_table.verticalHeader().hide()
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.setShowGrid(False)
        self.payments_table.setFrameShape(QFrame.Shape.NoFrame)
        p_layout.addWidget(self.payments_table)
        tabs.addTab(p_widget, "💳  سجل الدفعات")

        layout.addWidget(tabs)

        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(BTN_SECONDARY)
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self._sales_data = []
        self._load_data()

    def _load_data(self):
        sales, payments = db.get_customer_history(self.customer['id'])
        all_items = db.get_customer_sales_items(self.customer['id'])
        type_map = {'cash': 'نقدي', 'credit': 'آجل', 'partial': 'جزئي'}

        self._sales_data = sales

        def _cell(text, color, align=True, bold=False):
            it = QTableWidgetItem(str(text))
            it.setForeground(QColor(color))
            if align:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bold:
                it.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            return it

        # ── Invoices table ───────────────────────────────────────────────────
        self.sales_table.setRowCount(len(sales))
        total_sales = 0
        for row, s in enumerate(sales):
            self.sales_table.setItem(row, 0, _cell(s['date'], C_TEXT_MED))
            self.sales_table.setItem(row, 1, _cell(str(s['id']), C_TEXT_MED))

            inv_type = _cell(s.get('invoice_type', 'بيطري'),
                             C_ORANGE if s.get('invoice_type') == 'أعلاف' else C_TEAL)
            self.sales_table.setItem(row, 2, inv_type)

            total = s['total_amount']
            total_sales += total
            self.sales_table.setItem(row, 3, _cell(f"{total:.2f}", C_TEXT_DARK, bold=True))
            self.sales_table.setItem(row, 4, _cell(f"{s['paid_amount']:.2f}", C_PRIMARY))
            rem_color = C_DANGER if s['remaining'] > 0 else C_PRIMARY
            self.sales_table.setItem(row, 5, _cell(f"{s['remaining']:.2f}", rem_color))
            self.sales_table.setItem(row, 6, _cell(type_map.get(s['payment_type'], ''), C_TEXT_MED))
            self.sales_table.setRowHeight(row, 44)

        self.inv_count_lbl.setText(f"عدد الفواتير: {len(sales)}")
        self.inv_total_lbl.setText(f"إجمالي المبيعات: {total_sales:.2f} ج.م")

        if sales:
            self.sales_table.selectRow(0)

        # ── All items table ──────────────────────────────────────────────────
        self.all_items_table.setRowCount(len(all_items))
        for row, item in enumerate(all_items):
            self.all_items_table.setItem(row, 0, _cell(item['date'], C_TEXT_MED))
            self.all_items_table.setItem(row, 1, _cell(f"#{item['sale_id']}", C_PURPLE))
            self.all_items_table.setItem(row, 2, _cell(item['product_name'], C_TEXT_DARK, align=False, bold=True))
            self.all_items_table.setItem(row, 3, _cell(f"{item['quantity']:.2f}", C_TEXT_DARK))
            self.all_items_table.setItem(row, 4, _cell(item.get('unit_name', ''), C_TEXT_MED))
            self.all_items_table.setItem(row, 5, _cell(f"{item['unit_price']:.2f}", C_TEXT_MED))
            self.all_items_table.setItem(row, 6, _cell(f"{item['total']:.2f}", C_PRIMARY, bold=True))
            self.all_items_table.setRowHeight(row, 40)

        # ── Payments table ───────────────────────────────────────────────────
        self.payments_table.setRowCount(len(payments))
        for row, p in enumerate(payments):
            self.payments_table.setItem(row, 0, _cell(p['date'], C_TEXT_MED))
            amt = _cell(f"{p['amount']:.2f}", C_PRIMARY, bold=True)
            amt.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            self.payments_table.setItem(row, 1, amt)
            self.payments_table.setItem(row, 2, _cell(p.get('notes', ''), C_TEXT_MED))
            self.payments_table.setRowHeight(row, 42)

    def _on_invoice_row_changed(self, current_row):
        if current_row < 0 or current_row >= len(self._sales_data):
            self.items_detail_table.setRowCount(0)
            return

        sale_id = self._sales_data[current_row]['id']
        items = db.get_sale_items(sale_id)
        self.items_detail_table.setRowCount(len(items))

        def _dcell(text, color, align=True, bold=False):
            it = QTableWidgetItem(str(text))
            it.setForeground(QColor(color))
            if align:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bold:
                it.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            return it

        for row, item in enumerate(items):
            self.items_detail_table.setItem(row, 0, _dcell(item['product_name'], C_TEXT_DARK, align=False, bold=True))
            self.items_detail_table.setItem(row, 1, _dcell(f"{item['quantity']:.2f}", C_TEXT_DARK))
            self.items_detail_table.setItem(row, 2, _dcell(item.get('unit_name', ''), C_TEXT_MED))
            self.items_detail_table.setItem(row, 3, _dcell(f"{item['unit_price']:.2f}", C_TEXT_MED))
            self.items_detail_table.setItem(row, 4, _dcell(f"{item['total']:.2f}", C_PRIMARY, bold=True))
            self.items_detail_table.setRowHeight(row, 38)


class PdfRangeDialog(QDialog):
    def __init__(self, parent, customer):
        super().__init__(parent)
        self.setWindowTitle("طباعة كشف حساب PDF")
        self.setFixedWidth(400)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE)
        _light = QPalette()
        _light.setColor(QPalette.ColorRole.Window,          QColor("#f4f7fa"))
        _light.setColor(QPalette.ColorRole.WindowText,      QColor("#1a2535"))
        _light.setColor(QPalette.ColorRole.Base,            QColor("#ffffff"))
        _light.setColor(QPalette.ColorRole.Text,            QColor("#1a2535"))
        _light.setColor(QPalette.ColorRole.Button,          QColor("#f4f7fa"))
        _light.setColor(QPalette.ColorRole.ButtonText,      QColor("#1a2535"))
        _light.setColor(QPalette.ColorRole.Highlight,       QColor("#27ae60"))
        _light.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.setPalette(_light)
        self._setup_ui(customer)

    def _setup_ui(self, customer):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_BLUE}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("طباعة كشف حساب PDF")
        title.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        cust_lbl = QLabel(f"العميل: {customer['name']}")
        cust_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
        layout.addWidget(cust_lbl)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setStyleSheet(INPUT_STYLE)
        style_calendar(self.date_from)
        form.addRow("من تاريخ:", self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setStyleSheet(INPUT_STYLE)
        style_calendar(self.date_to)
        form.addRow("إلى تاريخ:", self.date_to)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)

        print_btn = QPushButton("🖨  طباعة PDF")
        print_btn.setStyleSheet(f"""
            QPushButton {{ background: {C_BLUE}; color: white; border: none;
                padding: 10px 20px; border-radius: 7px; font-size: 13px;
                font-family: Tahoma; font-weight: bold; }}
            QPushButton:hover {{ background: {C_BLUE_DARK}; }}
        """)
        print_btn.setDefault(True)
        print_btn.clicked.connect(self._validate)

        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(print_btn)
        layout.addLayout(btn_row)

    def _validate(self):
        if self.date_from.date() > self.date_to.date():
            show_warning(self, "خطأ", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
            return
        self.accept()

    def get_dates(self):
        return (
            self.date_from.date().toString("yyyy-MM-dd"),
            self.date_to.date().toString("yyyy-MM-dd"),
        )


class CustomersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self.load_customers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header_frame, header_inner = page_header(
            "👥  إدارة العملاء",
            "سجّل عملاءك وتابع ديونهم وسجل مدفوعاتهم"
        )
        add_btn = QPushButton("＋  إضافة عميل جديد")
        add_btn.setStyleSheet(BTN_ADD)
        add_btn.clicked.connect(self._add_customer)
        header_inner.addWidget(add_btn)
        layout.addWidget(header_frame)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍   ابحث عن عميل بالاسم...")
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.setMaximumWidth(320)
        self.search_input.textChanged.connect(self._search)
        toolbar.addWidget(self.search_input)
        toolbar.addStretch()
        self.count_label = QLabel()
        self.count_label.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
        toolbar.addWidget(self.count_label)
        layout.addLayout(toolbar)

        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background: white; border-radius: 12px; border: 1px solid #dce3ec; }")
        card_shadow(table_frame)
        table_inner = QVBoxLayout(table_frame)
        table_inner.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "الإجراءات", "الدين (ج.م)", "اسم العميل", "id"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 420)
        self.table.setColumnHidden(3, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        table_inner.addWidget(self.table)
        layout.addWidget(table_frame)

    def load_customers(self, customers=None):
        if customers is None:
            customers = db.get_all_customers()

        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            self.table.setItem(row, 3, QTableWidgetItem(str(c['id'])))

            name_item = QTableWidgetItem(c['name'])
            name_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            name_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 2, name_item)

            debt = c['total_debt']
            debt_item = QTableWidgetItem(f"{debt:.2f}")
            debt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if debt > 0:
                debt_item.setForeground(QColor(C_DANGER))
                debt_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            else:
                debt_item.setForeground(QColor(C_PRIMARY))
                debt_item.setText("✓ صفر")
            self.table.setItem(row, 1, debt_item)


            # ── Action buttons ───────────────────────────────────────────────
            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(8, 5, 8, 5)
            btn_l.setSpacing(6)

            hist_btn = _btn("📋 السجل", C_PURPLE, C_PURPLE_DARK)
            hist_btn.clicked.connect(lambda _, cid=c['id']: self._view_history(cid))

            pay_btn = _btn("💵 دفعة", C_ORANGE, "#d35400")
            pay_btn.clicked.connect(lambda _, cid=c['id']: self._add_payment(cid))

            edit_btn = _btn("✏ تعديل", C_TEAL, C_TEAL_DARK)
            edit_btn.clicked.connect(lambda _, cid=c['id']: self._edit_customer(cid))

            del_btn = _btn("🗑 حذف", C_DANGER, "#c0392b")
            del_btn.clicked.connect(lambda _, cid=c['id']: self._delete_customer(cid))

            pdf_btn = _btn("🖨 PDF", C_BLUE, C_BLUE_DARK)
            pdf_btn.clicked.connect(lambda _, cid=c['id']: self._print_pdf(cid))

            btn_l.addWidget(hist_btn)
            btn_l.addWidget(pay_btn)
            btn_l.addWidget(edit_btn)
            btn_l.addWidget(del_btn)
            btn_l.addWidget(pdf_btn)
            self.table.setCellWidget(row, 0, btn_w)
            self.table.setRowHeight(row, 60)

        total_debt = sum(c['total_debt'] for c in customers)
        self.count_label.setText(
            f"عدد العملاء: {len(customers)}   |   إجمالي الديون: {total_debt:.2f} ج.م"
        )

    def _search(self, query):
        customers = db.get_all_customers()
        if query.strip():
            q = query.strip().lower()
            customers = [c for c in customers if q in c['name'].lower()]
        self.load_customers(customers)

    def _add_customer(self):
        dlg = CustomerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.add_customer(d['name'])
            self.load_customers()

    def _edit_customer(self, cid):
        customer = next((c for c in db.get_all_customers() if c['id'] == cid), None)
        if not customer:
            return
        dlg = CustomerDialog(self, customer)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.update_customer(cid, d['name'])
            self.load_customers()

    def _delete_customer(self, cid):
        if confirm_delete(self, "هل أنت متأكد من حذف هذا العميل وجميع بياناته؟"):
            db.delete_customer(cid)
            self.load_customers()

    def _add_payment(self, cid):
        customer = next((c for c in db.get_all_customers() if c['id'] == cid), None)
        if not customer:
            return
        dlg = PaymentDialog(self, customer)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.add_payment(cid, d['amount'], d['notes'])
            self.load_customers()
            show_info(self, "تم بنجاح", f"✓  تم تسجيل دفعة {d['amount']:.2f} ج.م")

    def _view_history(self, cid):
        customer = next((c for c in db.get_all_customers() if c['id'] == cid), None)
        if not customer:
            return
        CustomerHistoryDialog(self, customer).exec()

    def _print_pdf(self, cid):
        customer = next((c for c in db.get_all_customers() if c['id'] == cid), None)
        if not customer:
            return
        dlg = PdfRangeDialog(self, customer)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            date_from, date_to = dlg.get_dates()
            try:
                from pdf_report import generate_customer_statement, open_pdf
                path = generate_customer_statement(cid, date_from, date_to)
                open_pdf(path)
            except Exception as e:
                show_error(self, "خطأ", f"فشل إنشاء ملف PDF:\n{e}")
