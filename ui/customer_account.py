from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFrame, QDateEdit, QSplitter,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD, BTN_SECONDARY,
    PAGE_STYLE, INPUT_STYLE, card_shadow, style_calendar, setup_searchable_combo,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER, C_ORANGE, C_PURPLE,
)
from ui.products import page_header
import pdf_report


class CustomerAccountPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self._load_customers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        header_frame, _ = page_header("📊  حساب العميل", "عرض كشف الحساب الكامل للعميل")
        layout.addWidget(header_frame)

        # Filter bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: #f4f7fb;
                border-radius: 10px;
                border: 1px solid #cdd8e8;
            }
            QLabel { color: #2c3e50; font-size: 12px; font-weight: bold; background: transparent; }
        """)
        card_shadow(filter_frame, blur=10, y=2, alpha=15)
        fl = QHBoxLayout(filter_frame)
        fl.setContentsMargins(20, 14, 20, 14)
        fl.setSpacing(8)

        today = QDate.currentDate()
        first_of_month = QDate(today.year(), today.month(), 1)

        # Customer label + combo (label first = rightmost in RTL)
        cust_lbl = QLabel("👤  العميل:")
        cust_lbl.setFixedWidth(80)
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(200)
        self.customer_combo.setStyleSheet(INPUT_STYLE)
        setup_searchable_combo(self.customer_combo)
        self.customer_combo.lineEdit().setPlaceholderText("ابحث باسم العميل...")

        # Date range
        date_from_lbl = QLabel("من:")
        date_from_lbl.setFixedWidth(30)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(first_of_month)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setStyleSheet(INPUT_STYLE)
        self.date_from.setFixedWidth(150)
        style_calendar(self.date_from)

        date_to_lbl = QLabel("إلى:")
        date_to_lbl.setFixedWidth(30)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(today)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setStyleSheet(INPUT_STYLE)
        self.date_to.setFixedWidth(150)
        style_calendar(self.date_to)

        load_btn = QPushButton("🔍  عرض الحساب")
        load_btn.setStyleSheet(BTN_ADD)
        load_btn.setMinimumWidth(140)
        load_btn.clicked.connect(self._load_account)

        print_btn = QPushButton("🖨  طباعة PDF")
        print_btn.setStyleSheet("""
            QPushButton {
                background: #8e44ad; color: white; border-radius: 8px;
                font-family: Tahoma; font-size: 13px; font-weight: bold;
                padding: 8px 18px; border: none;
            }
            QPushButton:hover { background: #7d3c98; }
            QPushButton:pressed { background: #6c3483; }
        """)
        print_btn.setMinimumWidth(130)
        print_btn.clicked.connect(self._print_account)

        # RTL: first added = rightmost
        fl.addWidget(cust_lbl)
        fl.addWidget(self.customer_combo)
        fl.addSpacing(20)
        fl.addWidget(date_from_lbl)
        fl.addWidget(self.date_from)
        fl.addSpacing(8)
        fl.addWidget(date_to_lbl)
        fl.addWidget(self.date_to)
        fl.addStretch()
        fl.addWidget(load_btn)
        fl.addWidget(print_btn)
        layout.addWidget(filter_frame)

        # Two-column: sales tables | payments
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(6)

        # Left side: sales + returns tables
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(10)

        for attr, title, color, bg in [
            ('vet_sales_table',    'المبيعات — بيطري',        C_PRIMARY, '#f0fff8'),
            ('feed_sales_table',   'المبيعات — أعلاف',         C_ORANGE,  '#fff8f0'),
            ('vet_returns_table',  'مرتجعات البيع — بيطري',   C_DANGER,  '#fff0f0'),
            ('feed_returns_table', 'مرتجعات البيع — أعلاف',   '#8e44ad', '#faf0ff'),
        ]:
            is_sales = 'sales' in attr
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #dce3ec;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(0)

            title_bar = QFrame()
            title_bar.setStyleSheet(f"""
                QFrame {{ background: {bg}; border-radius: 8px 8px 0 0;
                          border-bottom: 2px solid {color}; border-top: none;
                          border-left: none; border-right: none; }}
            """)
            title_bar_layout = QHBoxLayout(title_bar)
            title_bar_layout.setContentsMargins(12, 8, 12, 8)

            lbl = QLabel(title)
            lbl.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
            title_bar_layout.addWidget(lbl)

            count_lbl = QLabel("0 سجل")
            count_lbl.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; border: none;")
            title_bar_layout.addStretch()
            title_bar_layout.addWidget(count_lbl)
            setattr(self, attr + '_count', count_lbl)

            card_layout.addWidget(title_bar)

            t = QTableWidget()
            if is_sales:
                t.setColumnCount(6)
                t.setHorizontalHeaderLabels(["التاريخ", "الإجمالي (ج.م)", "المدفوع (ج.م)", "المتبقي (ج.م)", "نوع الدفع", "الأصناف"])
            else:
                t.setColumnCount(5)
                t.setHorizontalHeaderLabels(["التاريخ", "الإجمالي (ج.م)", "المدفوع (ج.م)", "المتبقي (ج.م)", "نوع الدفع"])
            t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t.setAlternatingRowColors(True)
            t.verticalHeader().hide()
            t.setShowGrid(False)
            t.setFrameShape(QFrame.Shape.NoFrame)
            t.setMaximumHeight(130)
            setattr(self, attr, t)
            card_layout.addWidget(t)

            left_layout.addWidget(card)

        content_splitter.addWidget(left_widget)

        # Right side: payments + summary
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(10)

        pay_lbl = QLabel("الدفعات")
        pay_lbl.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
        pay_lbl.setStyleSheet(f"color: {C_PRIMARY}; background: transparent;")
        right_layout.addWidget(pay_lbl)

        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(3)
        self.payments_table.setHorizontalHeaderLabels(["التاريخ", "المبلغ (ج.م)", "ملاحظات"])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.verticalHeader().hide()
        self.payments_table.setShowGrid(False)
        self.payments_table.setFrameShape(QFrame.Shape.NoFrame)
        right_layout.addWidget(self.payments_table)

        # Summary box
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame { background: #f0faf4; border-radius: 10px; border: 1px solid #a9dfbf; }
        """)
        sl = QVBoxLayout(summary_frame)
        sl.setContentsMargins(14, 12, 14, 12)
        sl.setSpacing(6)

        def _sum_row(label, color, attr_name):
            row = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px; background: transparent;")
            val = QLabel("0.00 ج.م")
            val.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {color}; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            setattr(self, attr_name, val)
            sl.addLayout(row)

        _sum_row("إجمالي المبيعات", C_PRIMARY, 'sum_sales_lbl')
        _sum_row("إجمالي المرتجعات", C_DANGER, 'sum_returns_lbl')
        _sum_row("إجمالي المدفوع", '#16a085', 'sum_paid_lbl')

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #a9dfbf; border: none; max-height: 1px;")
        sl.addWidget(sep)

        _sum_row("الرصيد (عليه)", C_DANGER, 'sum_owed_lbl')

        right_layout.addWidget(summary_frame)
        content_splitter.addWidget(right_widget)
        content_splitter.setSizes([600, 350])

        layout.addWidget(content_splitter)

    def _load_customers(self):
        self.customer_combo.clear()
        for c in db.get_all_customers():
            self.customer_combo.addItem(c['name'], c['id'])

    def _load_account(self):
        cid = self.customer_combo.currentData()
        if cid is None:
            return

        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")

        data = db.get_customer_account(cid, date_from, date_to)
        sales = data['sales']
        returns = data['returns']
        payments = data['payments']

        pay_map = {'cash': 'نقدي', 'credit': 'آجل', 'partial': 'جزئي'}

        def _cell(text, color, align=True, bold=False):
            it = QTableWidgetItem(str(text))
            it.setForeground(QColor(color))
            if align:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bold:
                it.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            return it

        def fill_sales_table(table, attr, items):
            table.setRowCount(len(items))
            getattr(self, attr + '_count').setText(f"{len(items)} سجل")
            for row, s in enumerate(items):
                table.setItem(row, 0, _cell(s['date'], C_TEXT_MED))
                table.setItem(row, 1, _cell(f"{s['total_amount']:.2f}", C_TEXT_DARK, bold=True))
                table.setItem(row, 2, _cell(f"{s.get('paid_amount', 0):.2f}", C_PRIMARY))
                rem = s.get('remaining', 0)
                table.setItem(row, 3, _cell(f"{rem:.2f}", C_DANGER if rem > 0 else C_PRIMARY))
                table.setItem(row, 4, _cell(pay_map.get(s.get('payment_type', 'cash'), ''), C_TEXT_MED))
                summary = s.get('items_summary', '') or ''
                table.setItem(row, 5, _cell(summary, C_TEXT_MED, align=False))
                table.setRowHeight(row, 36)

        def fill_returns_table(table, attr, items):
            table.setRowCount(len(items))
            getattr(self, attr + '_count').setText(f"{len(items)} سجل")
            for row, r in enumerate(items):
                table.setItem(row, 0, _cell(r['date'], C_TEXT_MED))
                table.setItem(row, 1, _cell(f"{r['total_amount']:.2f}", C_DANGER, bold=True))
                for col in [2, 3, 4]:
                    table.setItem(row, col, _cell("—", C_TEXT_MED))
                table.setRowHeight(row, 36)

        vet_sales = [s for s in sales if s.get('invoice_type', 'بيطري') == 'بيطري']
        feed_sales = [s for s in sales if s.get('invoice_type', 'بيطري') == 'أعلاف']
        vet_returns = [r for r in returns if r.get('invoice_type', 'بيطري') == 'بيطري']
        feed_returns = [r for r in returns if r.get('invoice_type', 'بيطري') == 'أعلاف']

        fill_sales_table(self.vet_sales_table, 'vet_sales_table', vet_sales)
        fill_sales_table(self.feed_sales_table, 'feed_sales_table', feed_sales)
        fill_returns_table(self.vet_returns_table, 'vet_returns_table', vet_returns)
        fill_returns_table(self.feed_returns_table, 'feed_returns_table', feed_returns)

        # Payments table
        self.payments_table.setRowCount(len(payments))
        for row, p in enumerate(payments):
            self.payments_table.setItem(row, 0, _cell(p['date'], C_TEXT_MED))
            self.payments_table.setItem(row, 1, _cell(f"{p['amount']:.2f}", C_PRIMARY, bold=True))
            self.payments_table.setItem(row, 2, _cell(p.get('notes', '') or '', C_TEXT_MED))
            self.payments_table.setRowHeight(row, 36)

        # Totals
        total_sales = sum(s['total_amount'] for s in sales)
        total_returns = sum(r['total_amount'] for r in returns)
        total_paid_payments = sum(p['amount'] for p in payments)
        owed = max(0.0, total_sales - total_returns - total_paid_payments)

        self.sum_sales_lbl.setText(f"{total_sales:.2f} ج.م")
        self.sum_returns_lbl.setText(f"{total_returns:.2f} ج.م")
        self.sum_paid_lbl.setText(f"{total_paid_payments:.2f} ج.م")
        self.sum_owed_lbl.setText(f"{owed:.2f} ج.م")
        self.sum_owed_lbl.setStyleSheet(
            f"color: {C_DANGER if owed > 0 else C_PRIMARY}; background: transparent; font-size: 12px; font-weight: bold;"
        )

    def _print_account(self):
        cid = self.customer_combo.currentData()
        if cid is None:
            return
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to = self.date_to.date().toString("yyyy-MM-dd")
        path = pdf_report.generate_customer_account(cid, date_from, date_to)
        if path:
            pdf_report.open_pdf(path)
