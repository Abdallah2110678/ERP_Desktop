from datetime import date as _dt, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFrame, QDateEdit, QSplitter,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD,
    PAGE_STYLE, INPUT_STYLE, card_shadow, style_calendar, setup_searchable_combo,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER, C_ORANGE, C_PURPLE,
)
from ui.products import page_header
import pdf_report

C_TEAL = '#16a085'


class ProductReportPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self._load_products()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        hdr, _ = page_header("📋  تقرير الصنف", "حركة الشراء والبيع والمرتجعات والمخزون لصنف محدد")
        layout.addWidget(hdr)

        layout.addWidget(self._build_filter_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([600, 380])
        layout.addWidget(splitter)

    def _build_filter_bar(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #f4f7fb;
                border-radius: 10px;
                border: 1px solid #cdd8e8;
            }
            QLabel { color: #2c3e50; font-size: 12px; font-weight: bold; background: transparent; }
        """)
        card_shadow(frame, blur=10, y=2, alpha=15)
        fl = QHBoxLayout(frame)
        fl.setContentsMargins(20, 14, 20, 14)
        fl.setSpacing(8)

        today = QDate.currentDate()
        first_of_year = QDate(today.year(), 1, 1)

        prod_lbl = QLabel("💊  الصنف:")
        prod_lbl.setFixedWidth(80)
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(230)
        self.product_combo.setStyleSheet(INPUT_STYLE)
        setup_searchable_combo(self.product_combo)
        self.product_combo.lineEdit().setPlaceholderText("ابحث باسم الصنف...")

        from_lbl = QLabel("من:")
        from_lbl.setFixedWidth(30)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(first_of_year)
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setStyleSheet(INPUT_STYLE)
        self.date_from.setFixedWidth(150)
        style_calendar(self.date_from)

        to_lbl = QLabel("إلى:")
        to_lbl.setFixedWidth(30)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(today)
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setStyleSheet(INPUT_STYLE)
        self.date_to.setFixedWidth(150)
        style_calendar(self.date_to)

        view_btn = QPushButton("🔍  عرض التقرير")
        view_btn.setStyleSheet(BTN_ADD)
        view_btn.setMinimumWidth(145)
        view_btn.clicked.connect(self._load_report)

        print_btn = QPushButton("🖨  طباعة PDF")
        print_btn.setStyleSheet("""
            QPushButton {
                background: #8e44ad; color: white; border-radius: 8px;
                font-family: Tahoma; font-size: 13px; font-weight: bold;
                padding: 8px 18px; border: none;
            }
            QPushButton:hover   { background: #7d3c98; }
            QPushButton:pressed { background: #6c3483; }
        """)
        print_btn.setMinimumWidth(130)
        print_btn.clicked.connect(self._print_report)

        fl.addWidget(prod_lbl)
        fl.addWidget(self.product_combo)
        fl.addSpacing(20)
        fl.addWidget(from_lbl)
        fl.addWidget(self.date_from)
        fl.addSpacing(8)
        fl.addWidget(to_lbl)
        fl.addWidget(self.date_to)
        fl.addStretch()
        fl.addWidget(view_btn)
        fl.addWidget(print_btn)
        return frame

    def _build_left_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(10)

        specs = [
            ('purchases_table', 'المشتريات', C_PRIMARY, '#f0fff8',
             ["التاريخ", "المورد", "الكمية", "سعر الشراء (ج.م)", "الإجمالي (ج.م)"], 160),
            ('sales_table', 'المبيعات', C_ORANGE, '#fff8f0',
             ["التاريخ", "العميل", "الكمية", "سعر البيع (ج.م)", "الإجمالي (ج.م)"], 160),
        ]
        for attr, title, color, bg, headers, max_h in specs:
            layout.addWidget(self._make_table_card(attr, title, color, bg, headers, max_h))
        return widget

    def _build_right_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(10)

        specs = [
            ('sale_returns_table', 'مرتجعات البيع', C_DANGER, '#fff0f0',
             ["التاريخ", "العميل", "الكمية", "الإجمالي (ج.م)"], 110),
            ('purchase_returns_table', 'مرتجعات الشراء', C_PURPLE, '#faf0ff',
             ["التاريخ", "المورد", "الكمية", "الإجمالي (ج.م)"], 110),
            ('batches_table', 'الدفعات الحالية في المخزون', C_TEAL, '#f0faf7',
             ["تاريخ الشراء", "الكمية المتبقية", "سعر الشراء", "تاريخ الانتهاء"], 110),
        ]
        for attr, title, color, bg, headers, max_h in specs:
            layout.addWidget(self._make_table_card(attr, title, color, bg, headers, max_h,
                                                   batches_note=('batches' in attr)))

        layout.addWidget(self._build_summary_box())
        layout.addStretch()
        return widget

    def _make_table_card(self, attr, title, color, bg, headers, max_h, batches_note=False):
        card = QFrame()
        card.setStyleSheet("QFrame { background: white; border-radius: 8px; border: 1px solid #dce3ec; }")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        title_bar = QFrame()
        title_bar.setStyleSheet(f"""
            QFrame {{ background: {bg}; border-radius: 8px 8px 0 0;
                      border-bottom: 2px solid {color};
                      border-top: none; border-left: none; border-right: none; }}
        """)
        tbl = QHBoxLayout(title_bar)
        tbl.setContentsMargins(12, 8, 12, 8)

        lbl = QLabel(title)
        lbl.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        tbl.addWidget(lbl)
        tbl.addStretch()

        if batches_note:
            note = QLabel("(المخزون الحالي — بدون تصفية بالتاريخ)")
            note.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent; border: none;")
            tbl.addWidget(note)
        else:
            cnt = QLabel("0 سجل")
            cnt.setStyleSheet(f"color: {color}; font-size: 11px; background: transparent; border: none;")
            tbl.addWidget(cnt)
            setattr(self, attr + '_count', cnt)

        cl.addWidget(title_bar)

        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().hide()
        t.setShowGrid(False)
        t.setFrameShape(QFrame.Shape.NoFrame)
        t.setMaximumHeight(max_h)
        setattr(self, attr, t)
        cl.addWidget(t)
        return card

    def _build_summary_box(self):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background: #f0faf4; border-radius: 10px; border: 1px solid #a9dfbf; }
        """)
        sl = QVBoxLayout(frame)
        sl.setContentsMargins(14, 12, 14, 12)
        sl.setSpacing(6)

        def _row(label, color, attr_name):
            row = QHBoxLayout()
            lbl = QLabel(label + ":")
            lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px; background: transparent;")
            val = QLabel("—")
            val.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            val.setStyleSheet(f"color: {color}; background: transparent;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            setattr(self, attr_name, val)
            sl.addLayout(row)

        _row("إجمالي الكمية المشتراة", C_PRIMARY,    'sum_purch_qty_lbl')
        _row("إجمالي تكلفة الشراء",   C_PRIMARY,    'sum_purch_cost_lbl')
        _row("إجمالي الكمية المباعة", C_ORANGE,     'sum_sales_qty_lbl')
        _row("إجمالي إيرادات البيع",  C_ORANGE,     'sum_sales_rev_lbl')

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #a9dfbf; border: none; max-height: 1px;")
        sl.addWidget(sep)

        _row("الكمية في المخزون الآن", C_TEXT_DARK, 'sum_stock_qty_lbl')
        _row("الربح التقديري",         C_TEAL,      'sum_profit_lbl')
        return frame

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_products(self):
        self.product_combo.clear()
        for p in db.get_all_products():
            self.product_combo.addItem(p['name'], p['id'])

    def _load_report(self):
        pid = self.product_combo.currentData()
        if pid is None:
            return

        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to   = self.date_to.date().toString("yyyy-MM-dd")
        data = db.get_product_report(pid, date_from, date_to)
        if not data:
            return

        today_str = _dt.today().strftime('%Y-%m-%d')
        warn_str  = (_dt.today() + timedelta(days=90)).strftime('%Y-%m-%d')

        def _cell(text, color=C_TEXT_DARK, align=True, bold=False):
            it = QTableWidgetItem(str(text))
            it.setForeground(QColor(color))
            if align:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bold:
                it.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            return it

        # Purchases
        rows = data['purchases']
        self.purchases_table.setRowCount(len(rows))
        self.purchases_table_count.setText(f"{len(rows)} سجل")
        for i, r in enumerate(rows):
            self.purchases_table.setItem(i, 0, _cell(r['date'],                            C_TEXT_MED))
            self.purchases_table.setItem(i, 1, _cell(r.get('supplier_name') or '—',        C_TEXT_MED, align=False))
            self.purchases_table.setItem(i, 2, _cell(f"{r['quantity']:.2f}",               C_TEXT_DARK, bold=True))
            self.purchases_table.setItem(i, 3, _cell(f"{r['unit_price']:.2f}",             C_PRIMARY))
            self.purchases_table.setItem(i, 4, _cell(f"{r['total']:.2f}",                  C_TEXT_DARK, bold=True))
            self.purchases_table.setRowHeight(i, 34)

        # Sales
        rows = data['sales']
        self.sales_table.setRowCount(len(rows))
        self.sales_table_count.setText(f"{len(rows)} سجل")
        for i, r in enumerate(rows):
            self.sales_table.setItem(i, 0, _cell(r['date'],                               C_TEXT_MED))
            self.sales_table.setItem(i, 1, _cell(r.get('customer_name') or '—',           C_TEXT_MED, align=False))
            self.sales_table.setItem(i, 2, _cell(f"{r['quantity']:.2f}",                  C_TEXT_DARK, bold=True))
            self.sales_table.setItem(i, 3, _cell(f"{r['unit_price']:.2f}",                C_ORANGE))
            self.sales_table.setItem(i, 4, _cell(f"{r['total']:.2f}",                     C_TEXT_DARK, bold=True))
            self.sales_table.setRowHeight(i, 34)

        # Sale returns
        rows = data['sale_returns']
        self.sale_returns_table.setRowCount(len(rows))
        self.sale_returns_table_count.setText(f"{len(rows)} سجل")
        for i, r in enumerate(rows):
            self.sale_returns_table.setItem(i, 0, _cell(r['date'],                        C_TEXT_MED))
            self.sale_returns_table.setItem(i, 1, _cell(r.get('customer_name') or '—',    C_TEXT_MED, align=False))
            self.sale_returns_table.setItem(i, 2, _cell(f"{r['quantity']:.2f}",           C_DANGER, bold=True))
            self.sale_returns_table.setItem(i, 3, _cell(f"{r['total']:.2f}",              C_DANGER))
            self.sale_returns_table.setRowHeight(i, 34)

        # Purchase returns
        rows = data['purchase_returns']
        self.purchase_returns_table.setRowCount(len(rows))
        self.purchase_returns_table_count.setText(f"{len(rows)} سجل")
        for i, r in enumerate(rows):
            self.purchase_returns_table.setItem(i, 0, _cell(r['date'],                    C_TEXT_MED))
            self.purchase_returns_table.setItem(i, 1, _cell(r.get('supplier_name') or '—', C_TEXT_MED, align=False))
            self.purchase_returns_table.setItem(i, 2, _cell(f"{r['quantity']:.2f}",       C_PURPLE, bold=True))
            self.purchase_returns_table.setItem(i, 3, _cell(f"{r['total']:.2f}",          C_PURPLE))
            self.purchase_returns_table.setRowHeight(i, 34)

        # Active batches (no date filter)
        batches = data['batches']
        self.batches_table.setRowCount(len(batches))
        for i, b in enumerate(batches):
            exp_raw = b.get('expiry_date')
            if exp_raw:
                if exp_raw < today_str:
                    exp_display, exp_color = f"⚠ {exp_raw}", C_DANGER
                elif exp_raw <= warn_str:
                    exp_display, exp_color = exp_raw, C_ORANGE
                else:
                    exp_display, exp_color = exp_raw, C_TEAL
            else:
                exp_display, exp_color = '—', C_TEXT_MED

            self.batches_table.setItem(i, 0, _cell(str(b.get('purchase_date') or '—'),   C_TEXT_MED))
            self.batches_table.setItem(i, 1, _cell(f"{b['quantity']:.2f}",               C_TEXT_DARK, bold=True))
            self.batches_table.setItem(i, 2, _cell(f"{b['purchase_price']:.2f}",         C_PRIMARY))
            self.batches_table.setItem(i, 3, _cell(exp_display,                          exp_color,
                                                    bold=(exp_color == C_DANGER)))
            self.batches_table.setRowHeight(i, 34)

        # Summary
        product       = data['product']
        purch_qty     = sum(r['quantity'] for r in data['purchases'])
        purch_cost    = sum(r['total']    for r in data['purchases'])
        sales_qty     = sum(r['quantity'] for r in data['sales'])
        sales_rev     = sum(r['total']    for r in data['sales'])
        net_profit    = sales_rev - (sales_qty * product['purchase_price'])

        unit = product.get('unit') or 'وحدة'
        self.sum_purch_qty_lbl.setText(f"{purch_qty:.2f} {unit}")
        self.sum_purch_cost_lbl.setText(f"{purch_cost:.2f} ج.م")
        self.sum_sales_qty_lbl.setText(f"{sales_qty:.2f} {unit}")
        self.sum_sales_rev_lbl.setText(f"{sales_rev:.2f} ج.م")
        self.sum_stock_qty_lbl.setText(f"{product['quantity']:.2f} {unit}")
        self.sum_profit_lbl.setText(f"{net_profit:.2f} ج.م")
        profit_color = C_TEAL if net_profit >= 0 else C_DANGER
        self.sum_profit_lbl.setStyleSheet(
            f"color: {profit_color}; background: transparent; font-size: 12px; font-weight: bold;"
        )

    def _print_report(self):
        pid = self.product_combo.currentData()
        if pid is None:
            return
        date_from = self.date_from.date().toString("yyyy-MM-dd")
        date_to   = self.date_to.date().toString("yyyy-MM-dd")
        path = pdf_report.generate_product_report(pid, date_from, date_to)
        if path:
            pdf_report.open_pdf(path)
