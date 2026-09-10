from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QDoubleSpinBox, QMessageBox, QHeaderView, QComboBox, QFrame,
    QCompleter,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD, BTN_EDIT, BTN_SECONDARY, BTN_ORANGE,
    DIALOG_STYLE, PAGE_STYLE, INPUT_STYLE, card_shadow,
    show_info, show_warning, show_error,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER, C_ORANGE,
)
from ui.products import page_header


class NewSaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إنشاء فاتورة بيع جديدة")
        self.resize(860, 650)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE + TABLE_STYLE)
        self.cart = []
        self._pay_type_idx = 0
        self._setup_ui()
        self._load_customers()
        self._load_products()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        # Title strip
        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_PRIMARY}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("🛒  فاتورة بيع جديدة")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        # Customer row with search
        cust_row = QHBoxLayout()
        cust_row.setSpacing(8)

        cust_lbl = QLabel("العميل:")
        cust_lbl.setFixedWidth(60)

        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("🔍  ابحث باسم العميل أو اتركه فارغاً للنقدي...")
        self.customer_search.setStyleSheet(INPUT_STYLE)
        self.customer_search.setMinimumWidth(300)

        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(240)
        self.customer_combo.setStyleSheet(INPUT_STYLE)

        self.customer_search.textChanged.connect(self._filter_customers)

        cust_row.addWidget(self.customer_combo)
        cust_row.addWidget(self.customer_search)
        cust_row.addWidget(cust_lbl)
        cust_row.addStretch()
        layout.addLayout(cust_row)

        # Options row: payment type + invoice type (right under customer)
        options_row = QHBoxLayout()
        options_row.setSpacing(10)

        _PAY_BTN_STYLES = [
            ("💵  نقدي", "#27ae60", "#1e8449", "#f0fff4", "#27ae60"),
            ("📋  آجل",  "#e67e22", "#d35400", "#fff7f0", "#e67e22"),
        ]

        def _pay_btn_style(bg, hover, bg_off, border_off, is_on):
            if is_on:
                return (f"QPushButton {{ background: {bg}; color: white; border: none; "
                        f"padding: 7px 18px; border-radius: 7px; "
                        f"font-size: 12px; font-family: Tahoma; font-weight: bold; }}"
                        f"QPushButton:hover {{ background: {hover}; }}")
            else:
                return (f"QPushButton {{ background: {bg_off}; color: {border_off}; "
                        f"border: 2px solid {border_off}; padding: 6px 17px; border-radius: 7px; "
                        f"font-size: 12px; font-family: Tahoma; font-weight: bold; }}"
                        f"QPushButton:hover {{ background: {bg}20; }}")

        self._pay_btns = []
        pay_btns_h = QHBoxLayout()
        pay_btns_h.setSpacing(6)
        for i, (text, bg, hover, bg_off, border_off) in enumerate(_PAY_BTN_STYLES):
            btn = QPushButton(text)
            btn.setStyleSheet(_pay_btn_style(bg, hover, bg_off, border_off, i == 0))
            btn.clicked.connect(lambda _, idx=i: self._select_pay_type(idx))
            pay_btns_h.addWidget(btn)
            self._pay_btns.append(btn)

        pay_lbl_top = QLabel("نوع الدفع:")
        pay_lbl_top.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 12px; font-weight: bold;")

        self.invoice_type = QComboBox()
        self.invoice_type.addItems(["بيطري", "أعلاف"])
        self.invoice_type.setStyleSheet(INPUT_STYLE)
        self.invoice_type.setFixedWidth(120)
        inv_lbl_top = QLabel("نوع الفاتورة:")
        inv_lbl_top.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 12px; font-weight: bold;")

        options_row.addWidget(pay_lbl_top)
        options_row.addLayout(pay_btns_h)
        options_row.addSpacing(28)
        options_row.addWidget(inv_lbl_top)
        options_row.addWidget(self.invoice_type)
        options_row.addStretch()
        layout.addLayout(options_row)

        # Product add row
        prod_frame = QFrame()
        prod_frame.setStyleSheet("""
            QFrame { background: #f4f7fa; border-radius: 8px; border: 1px solid #dce3ec; }
        """)
        pl = QVBoxLayout(prod_frame)
        pl.setContentsMargins(12, 10, 12, 10)
        pl.setSpacing(8)

        # Row 1: drug name + unit (auto-filled, editable)
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(220)
        self.product_combo.setStyleSheet(INPUT_STYLE)
        self.product_combo.setEditable(True)
        self.product_combo.lineEdit().setPlaceholderText("اكتب اسم الدواء...")
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)

        self.unit_input = QLineEdit()
        self.unit_input.setFixedWidth(110)
        self.unit_input.setPlaceholderText("الوحدة")
        self.unit_input.setStyleSheet(INPUT_STYLE)

        self.stock_label = QLabel()
        self.stock_label.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 11px; background: transparent;")

        row1.addWidget(self.product_combo)
        row1.addWidget(QLabel("الدواء:"))
        row1.addSpacing(16)
        row1.addWidget(self.unit_input)
        row1.addWidget(QLabel("الوحدة:"))
        row1.addStretch()
        row1.addWidget(self.stock_label)
        pl.addLayout(row1)

        # Row 2: quantity + price + add button
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 99999)
        self.qty_spin.setDecimals(2)
        self.qty_spin.setValue(1)
        self.qty_spin.setFixedWidth(100)
        self.qty_spin.setStyleSheet(INPUT_STYLE)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" ج.م")
        self.price_spin.setFixedWidth(130)
        self.price_spin.setStyleSheet(INPUT_STYLE)

        add_item_btn = QPushButton("➕  إضافة للفاتورة")
        add_item_btn.setStyleSheet(BTN_ADD.replace("padding: 10px 22px;", "padding: 8px 18px;"))
        add_item_btn.clicked.connect(self._add_to_cart)

        row2.addWidget(self.qty_spin)
        row2.addWidget(QLabel("الكمية:"))
        row2.addSpacing(16)
        row2.addWidget(self.price_spin)
        row2.addWidget(QLabel("السعر:"))
        row2.addStretch()
        row2.addWidget(add_item_btn)
        pl.addLayout(row2)

        layout.addWidget(prod_frame)

        # Cart label
        cart_lbl = QLabel("الأصناف في الفاتورة:")
        cart_lbl.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        cart_lbl.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(cart_lbl)

        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["حذف","الإجمالي (ج.م)","السعر (ج.م)","الكمية","اسم الدواء"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.cart_table.setColumnWidth(0, 65)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cart_table.verticalHeader().hide()
        self.cart_table.setMaximumHeight(190)
        self.cart_table.setShowGrid(False)
        self.cart_table.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.cart_table)

        # Payment panel
        pay_frame = QFrame()
        pay_frame.setStyleSheet("""
            QFrame { background: #f0faf4; border-radius: 10px; border: 1px solid #a9dfbf; }
        """)
        pay_layout = QHBoxLayout(pay_frame)
        pay_layout.setContentsMargins(16, 12, 16, 12)
        pay_layout.setSpacing(18)

        def _block(label, widget, bold_widget=False):
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(widget)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 11px;")
            col.addWidget(lbl)
            return col

        self.total_label = QLabel("0.00 ج.م")
        self.total_label.setFont(QFont("Tahoma", 17, QFont.Weight.Bold))
        self.total_label.setStyleSheet(f"color: {C_TEXT_DARK}; background: transparent;")

        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setSuffix(" ج.م")
        self.paid_spin.setStyleSheet(INPUT_STYLE + "QDoubleSpinBox { font-size: 14px; }")
        self.paid_spin.valueChanged.connect(self._update_remaining)

        self.remaining_label = QLabel("0.00 ج.م")
        self.remaining_label.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        self.remaining_label.setStyleSheet(f"color: {C_PRIMARY}; background: transparent;")

        def vline():
            l = QFrame()
            l.setFrameShape(QFrame.Shape.VLine)
            l.setStyleSheet("color: #a9dfbf;")
            return l

        pay_layout.addLayout(_block("الإجمالي", self.total_label))
        pay_layout.addWidget(vline())
        pay_layout.addLayout(_block("المبلغ المدفوع", self.paid_spin))
        pay_layout.addWidget(vline())
        pay_layout.addLayout(_block("المتبقي (دين)", self.remaining_label))
        layout.addWidget(pay_frame)

        # Notes
        notes_row = QHBoxLayout()
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات على الفاتورة (اختياري)")
        self.notes_input.setStyleSheet(INPUT_STYLE)
        notes_row.addWidget(self.notes_input)
        notes_row.addWidget(QLabel("ملاحظات:"))
        layout.addLayout(notes_row)

        # Action buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton("✓  تأكيد الفاتورة")
        confirm_btn.setStyleSheet(BTN_ADD)
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self._confirm_sale)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def _load_customers(self):
        self._all_customers = db.get_all_customers()
        self._populate_customer_combo(self._all_customers)

    def _populate_customer_combo(self, customers):
        self.customer_combo.blockSignals(True)
        self.customer_combo.clear()
        self.customer_combo.addItem("عميل نقدي (بدون حساب)", None)
        for c in customers:
            debt_str = f"  —  رصيد: {c['total_debt']:.2f} ج.م" if c['total_debt'] != 0 else ""
            self.customer_combo.addItem(f"{c['name']}{debt_str}", c['id'])
        self.customer_combo.blockSignals(False)

    def _filter_customers(self, query):
        q = query.strip().lower()
        if not q:
            self._populate_customer_combo(self._all_customers)
        else:
            filtered = [c for c in self._all_customers if q in c['name'].lower()]
            self._populate_customer_combo(filtered)
            if filtered:
                self.customer_combo.setCurrentIndex(1)

    def _load_products(self):
        self.products_data = db.get_all_products()
        self.product_combo.clear()
        for p in self.products_data:
            self.product_combo.addItem(p['name'], p['id'])

    def _on_product_changed(self, index):
        if 0 <= index < len(self.products_data):
            p = self.products_data[index]
            self.unit_input.setText(p['unit'])
            self.price_spin.setValue(p['selling_price'])
            self.stock_label.setText(f"المتاح: {p['quantity']:.2f} {p['unit']}")

    def _select_pay_type(self, idx):
        self._pay_type_idx = idx
        _STYLES = [
            ("#27ae60", "#1e8449", "#f0fff4", "#27ae60"),
            ("#e67e22", "#d35400", "#fff7f0", "#e67e22"),
        ]
        for i, btn in enumerate(self._pay_btns):
            bg, hover, bg_off, border_off = _STYLES[i]
            if i == idx:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {bg}; color: white; border: none; "
                    f"padding: 7px 18px; border-radius: 7px; "
                    f"font-size: 12px; font-family: Tahoma; font-weight: bold; }}"
                    f"QPushButton:hover {{ background: {hover}; }}")
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {bg_off}; color: {border_off}; "
                    f"border: 2px solid {border_off}; padding: 6px 17px; border-radius: 7px; "
                    f"font-size: 12px; font-family: Tahoma; font-weight: bold; }}"
                    f"QPushButton:hover {{ background: {bg}20; }}")
        self._on_payment_type_changed(idx)

    def _on_payment_type_changed(self, index):
        total = sum(item['total'] for item in self.cart)
        if index == 0:
            self.paid_spin.setValue(total)
        elif index == 1:
            self.paid_spin.setValue(0)

    def _add_to_cart(self):
        idx = self.product_combo.currentIndex()
        if idx < 0 or idx >= len(self.products_data):
            show_warning(self, "خطأ", "يرجى اختيار دواء من القائمة")
            return
        product   = self.products_data[idx]
        unit_name = self.unit_input.text().strip() or product['unit']
        qty   = self.qty_spin.value()
        price = self.price_spin.value()

        if qty <= 0:
            show_warning(self, "خطأ", "الكمية يجب أن تكون أكبر من صفر")
            return
        if qty > product['quantity']:
            show_warning(self, "تحذير",
                f"الكمية المتاحة فقط {product['quantity']:.2f} {product['unit']}")
            return

        for item in self.cart:
            if item['product_id'] == product['id']:
                item['quantity'] += qty
                item['total'] = round(item['quantity'] * item['unit_price'], 2)
                self._refresh_cart(); self._update_total(); return

        self.cart.append({
            'product_id':   product['id'],
            'product_name': product['name'],
            'unit_name':    unit_name,
            'quantity':     qty,
            'unit_price':   price,
            'total':        round(qty * price, 2),
        })
        self._refresh_cart(); self._update_total()

    def _refresh_cart(self):
        self.cart_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            display = f"{item['product_name']}  ({item.get('unit_name', '')})"
            name_item = QTableWidgetItem(display)
            name_item.setForeground(QColor(C_TEXT_DARK))
            name_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            self.cart_table.setItem(row, 4, name_item)

            for col, val, clr in [
                (3, f"{item['quantity']:.2f}",  C_TEXT_DARK),
                (2, f"{item['unit_price']:.2f}", C_TEXT_MED),
                (1, f"{item['total']:.2f}",      C_PRIMARY),
            ]:
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setForeground(QColor(clr))
                if col == 1:
                    it.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
                self.cart_table.setItem(row, col, it)

            del_btn = QPushButton("🗑")
            del_btn.setStyleSheet(f"background:{C_DANGER}; color:white; border:none; border-radius:4px; font-size:14px;")
            del_btn.clicked.connect(lambda _, r=row: self._remove_from_cart(r))
            self.cart_table.setCellWidget(row, 0, del_btn)
            self.cart_table.setRowHeight(row, 40)

    def _remove_from_cart(self, row):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self._refresh_cart(); self._update_total()

    def _update_total(self):
        total = sum(item['total'] for item in self.cart)
        self.total_label.setText(f"{total:.2f} ج.م")
        if self._pay_type_idx == 0:
            self.paid_spin.setValue(total)
        elif self._pay_type_idx == 1:
            self.paid_spin.setValue(0)
        self._update_remaining()

    def _update_remaining(self):
        total     = sum(item['total'] for item in self.cart)
        remaining = max(0, total - self.paid_spin.value())
        self.remaining_label.setText(f"{remaining:.2f} ج.م")
        self.remaining_label.setStyleSheet(
            f"color: {C_DANGER if remaining > 0 else C_PRIMARY}; "
            "font-size: 14px; font-weight: bold; background: transparent;"
        )

    def _confirm_sale(self):
        if not self.cart:
            show_warning(self, "خطأ", "يرجى إضافة دواء واحد على الأقل")
            return
        total     = sum(item['total'] for item in self.cart)
        paid      = self.paid_spin.value()
        remaining = max(0, total - paid)
        cid       = self.customer_combo.currentData()
        cname     = self.customer_combo.currentText().split("   —")[0]

        if remaining > 0 and cid is None:
            show_warning(self, "تحذير",
                "لتسجيل دين على حساب عميل يجب اختيار عميل مسجل من القائمة")
            return

        type_map    = {0: 'cash', 1: 'credit'}
        pay_type    = type_map[self._pay_type_idx]
        inv_type    = self.invoice_type.currentText()
        notes       = self.notes_input.text().strip()

        sale_id = db.create_sale(cid, cname, self.cart, total, paid, pay_type, notes, inv_type)
        show_info(self, "تم بنجاح",
            f"✓  تم تسجيل الفاتورة بنجاح\n"
            f"رقم الفاتورة: {sale_id}\n"
            f"الإجمالي: {total:.2f} ج.م\n"
            f"المدفوع: {paid:.2f} ج.م\n"
            f"المتبقي: {remaining:.2f} ج.م")
        self.accept()


class SalesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self.load_sales()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header_frame, header_inner = page_header(
            "🛒  سجل المبيعات",
            "جميع فواتير البيع النقدية والآجلة"
        )
        new_btn = QPushButton("＋  فاتورة بيع جديدة")
        new_btn.setStyleSheet(BTN_ADD)
        new_btn.clicked.connect(self._new_sale)
        header_inner.addWidget(new_btn)
        layout.addWidget(header_frame)

        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background:white; border-radius:12px; border:1px solid #dce3ec; }")
        card_shadow(table_frame)
        tl = QVBoxLayout(table_frame)
        tl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "الإجراءات", "نوع الدفع", "المتبقي (ج.م)", "المدفوع (ج.م)", "الإجمالي (ج.م)", "العميل", "التاريخ", "رقم الفاتورة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(7, 100)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        tl.addWidget(self.table)
        layout.addWidget(table_frame)

        self.count_label = QLabel()
        self.count_label.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
        layout.addWidget(self.count_label)

    def load_sales(self):
        sales = db.get_all_sales()
        type_map = {'cash': 'نقدي', 'credit': 'آجل', 'partial': 'جزئي'}
        self.table.setRowCount(len(sales))

        for row, s in enumerate(sales):
            id_item = QTableWidgetItem(f"# {s['id']}")
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            id_item.setForeground(QColor(C_PRIMARY))
            self.table.setItem(row, 7, id_item)

            date_item = QTableWidgetItem(s['date'])
            date_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 6, date_item)

            name_item = QTableWidgetItem(s['customer_name'])
            name_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            name_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 5, name_item)

            for col, val, clr in [
                (4, f"{s['total_amount']:.2f}", C_TEXT_DARK),
                (3, f"{s['paid_amount']:.2f}",  C_PRIMARY),
                (2, f"{s['remaining']:.2f}",    C_DANGER if s['remaining'] > 0 else C_PRIMARY),
            ]:
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setForeground(QColor(clr))
                self.table.setItem(row, col, it)

            type_item = QTableWidgetItem(type_map.get(s['payment_type'], ''))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 1, type_item)

            det_btn = QPushButton("التفاصيل")
            det_btn.setStyleSheet(BTN_EDIT)
            det_btn.clicked.connect(lambda _, sid=s['id']: self._show_details(sid))
            btn_w = QWidget()
            bl = QHBoxLayout(btn_w)
            bl.setContentsMargins(5, 4, 5, 4)
            bl.addWidget(det_btn)
            self.table.setCellWidget(row, 0, btn_w)
            self.table.setRowHeight(row, 50)

        total_amount = sum(s['total_amount'] for s in sales)
        self.count_label.setText(
            f"عدد الفواتير: {len(sales)}   |   إجمالي المبيعات: {total_amount:.2f} ج.م"
        )

    def _new_sale(self):
        dlg = NewSaleDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_sales()

    def _show_details(self, sale_id):
        items = db.get_sale_items(sale_id)
        msg = f"تفاصيل الفاتورة رقم {sale_id}:\n\n"
        for item in items:
            msg += f"•  {item['product_name']}   ×{item['quantity']:.2f}   @{item['unit_price']:.2f} ج.م  =  {item['total']:.2f} ج.م\n"
        show_info(self, "تفاصيل الفاتورة", msg)
