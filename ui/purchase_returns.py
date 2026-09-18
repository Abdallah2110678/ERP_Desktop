from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QDoubleSpinBox, QHeaderView, QComboBox, QFrame, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_EDIT, BTN_SECONDARY, BTN_ORANGE,
    DIALOG_STYLE, PAGE_STYLE, INPUT_STYLE, card_shadow, style_calendar,
    show_info, show_warning, setup_searchable_combo,
    C_TEXT_DARK, C_TEXT_MED, C_DANGER, C_ORANGE,
)
from ui.products import page_header


class NewPurchaseReturnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تسجيل مرتجع شراء")
        self.resize(820, 580)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE + TABLE_STYLE)
        self.cart = []
        self._suppliers = []
        self._setup_ui()
        self._load_products()
        self._load_suppliers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_DANGER}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("↩  تسجيل مرتجع شراء")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        # Supplier + invoice type row
        sup_row = QHBoxLayout()
        sup_row.setSpacing(8)
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.supplier_combo.setMinimumWidth(220)
        self.supplier_combo.setStyleSheet(INPUT_STYLE)
        self.supplier_combo.lineEdit().setPlaceholderText("اختر مورداً...")
        setup_searchable_combo(self.supplier_combo)
        sup_row.addWidget(self.supplier_combo)
        sup_row.addWidget(QLabel("المورد:"))
        sup_row.addSpacing(16)

        self.inv_type_combo = QComboBox()
        self.inv_type_combo.addItems(["بيطري", "أعلاف", "نثريات"])
        self.inv_type_combo.setStyleSheet(INPUT_STYLE)
        self.inv_type_combo.setFixedWidth(110)
        sup_row.addWidget(self.inv_type_combo)
        sup_row.addWidget(QLabel("نوع الفاتورة:"))
        sup_row.addSpacing(20)

        date_lbl = QLabel("التاريخ:")
        date_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 12px; font-weight: bold;")
        self.ret_date = QDateEdit()
        self.ret_date.setCalendarPopup(True)
        self.ret_date.setDate(QDate.currentDate())
        self.ret_date.setDisplayFormat("yyyy-MM-dd")
        self.ret_date.setStyleSheet(INPUT_STYLE)
        self.ret_date.setFixedWidth(150)
        style_calendar(self.ret_date)
        sup_row.addWidget(date_lbl)
        sup_row.addWidget(self.ret_date)
        sup_row.addStretch()
        layout.addLayout(sup_row)

        # Product entry
        prod_frame = QFrame()
        prod_frame.setStyleSheet("QFrame { background:#f4f7fa; border-radius:8px; border:1px solid #dce3ec; }")
        pl = QVBoxLayout(prod_frame)
        pl.setContentsMargins(12, 10, 12, 10)
        pl.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(220)
        self.product_combo.setStyleSheet(INPUT_STYLE)
        self.product_combo.setEditable(True)
        self.product_combo.lineEdit().setPlaceholderText("اكتب اسم الصنف...")
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)
        setup_searchable_combo(self.product_combo)

        self.unit_input = QLineEdit()
        self.unit_input.setFixedWidth(110)
        self.unit_input.setPlaceholderText("الوحدة")
        self.unit_input.setStyleSheet(INPUT_STYLE)

        row1.addWidget(self.product_combo)
        row1.addWidget(QLabel("الصنف:"))
        row1.addSpacing(16)
        row1.addWidget(self.unit_input)
        row1.addWidget(QLabel("الوحدة:"))
        row1.addStretch()
        pl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 999999)
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

        add_btn = QPushButton("➕  إضافة")
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: {C_DANGER}; color: white; border: none;
                padding: 8px 18px; border-radius: 7px; font-family: Tahoma; font-size: 13px; font-weight: bold; }}
            QPushButton:hover {{ background: #c0392b; }}
        """)
        add_btn.clicked.connect(self._add_item)

        row2.addWidget(self.qty_spin)
        row2.addWidget(QLabel("الكمية:"))
        row2.addSpacing(10)
        row2.addWidget(self.price_spin)
        row2.addWidget(QLabel("سعر الشراء:"))
        row2.addStretch()
        row2.addWidget(add_btn)
        pl.addLayout(row2)
        layout.addWidget(prod_frame)

        items_lbl = QLabel("الأصناف المرتجعة:")
        items_lbl.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        items_lbl.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(items_lbl)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["حذف", "الإجمالي (ج.م)", "سعر الشراء (ج.م)", "الكمية", "الصنف"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.items_table.setColumnWidth(0, 65)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.verticalHeader().hide()
        self.items_table.setMaximumHeight(180)
        self.items_table.setShowGrid(False)
        self.items_table.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.items_table)

        total_row = QHBoxLayout()
        total_row.addStretch()
        total_lbl = QLabel("إجمالي المرتجع:")
        total_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 13px;")
        self.total_label = QLabel("0.00 ج.م")
        self.total_label.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        self.total_label.setStyleSheet(f"color: {C_DANGER};")
        total_row.addWidget(self.total_label)
        total_row.addWidget(total_lbl)
        layout.addLayout(total_row)

        notes_row = QHBoxLayout()
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        self.notes_input.setStyleSheet(INPUT_STYLE)
        notes_row.addWidget(self.notes_input)
        notes_row.addWidget(QLabel("ملاحظات:"))
        layout.addLayout(notes_row)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton("✓  تأكيد المرتجع")
        confirm_btn.setStyleSheet(f"""
            QPushButton {{ background: {C_DANGER}; color: white; border: none;
                padding: 10px 22px; border-radius: 8px; font-family: Tahoma; font-size: 13px; font-weight: bold; }}
            QPushButton:hover {{ background: #c0392b; }}
        """)
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def _load_products(self):
        self.products_data = db.get_all_products()
        self.product_combo.clear()
        for p in self.products_data:
            self.product_combo.addItem(p['name'], p['id'])

    def _load_suppliers(self):
        self._suppliers = db.get_all_suppliers()
        self.supplier_combo.clear()
        self.supplier_combo.addItem("", None)
        for s in self._suppliers:
            self.supplier_combo.addItem(s['name'], s['id'])

    def _on_product_changed(self, index):
        if 0 <= index < len(self.products_data):
            p = self.products_data[index]
            self.unit_input.setText(p['unit'])
            self.price_spin.setValue(p['purchase_price'])
            self.inv_type_combo.setCurrentText(p.get('product_type') or 'بيطري')

    def _add_item(self):
        idx = self.product_combo.currentIndex()
        typed_name = self.product_combo.currentText().strip()
        unit_name = self.unit_input.text().strip()
        qty = self.qty_spin.value()
        price = self.price_spin.value()

        if not typed_name:
            show_warning(self, "خطأ", "يرجى إدخال اسم الصنف")
            return
        if qty <= 0:
            show_warning(self, "خطأ", "الكمية يجب أن تكون أكبر من صفر")
            return

        if 0 <= idx < len(self.products_data):
            product = self.products_data[idx]
            product_id = product['id']
            name = product['name']
            unit_name = unit_name or product['unit']
        else:
            product_id = None
            name = typed_name

        for item in self.cart:
            if item['product_id'] is not None and item['product_id'] == product_id:
                item['quantity'] += qty
                item['unit_price'] = price
                item['total'] = round(item['quantity'] * price, 2)
                self._refresh_table()
                self._update_total()
                return

        self.cart.append({
            'product_id': product_id,
            'product_name': name,
            'unit_name': unit_name,
            'quantity': qty,
            'unit_price': price,
            'total': round(qty * price, 2),
        })
        self._refresh_table()
        self._update_total()

    def _refresh_table(self):
        self.items_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            display = f"{item['product_name']}  ({item.get('unit_name', '')})"
            name_item = QTableWidgetItem(display)
            name_item.setForeground(QColor(C_TEXT_DARK))
            name_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            self.items_table.setItem(row, 4, name_item)
            for col, val, clr in [
                (3, f"{item['quantity']:.2f}", C_TEXT_DARK),
                (2, f"{item['unit_price']:.2f}", C_TEXT_MED),
                (1, f"{item['total']:.2f}", C_DANGER),
            ]:
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setForeground(QColor(clr))
                if col == 1:
                    it.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
                self.items_table.setItem(row, col, it)

            del_btn = QPushButton("🗑")
            del_btn.setStyleSheet(f"background:{C_DANGER}; color:white; border:none; border-radius:4px; font-size:14px;")
            del_btn.clicked.connect(lambda _, r=row: self._remove_item(r))
            self.items_table.setCellWidget(row, 0, del_btn)
            self.items_table.setRowHeight(row, 40)

    def _remove_item(self, row):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self._refresh_table()
            self._update_total()

    def _update_total(self):
        total = sum(item['total'] for item in self.cart)
        self.total_label.setText(f"{total:.2f} ج.م")

    def _confirm(self):
        if not self.cart:
            show_warning(self, "خطأ", "يرجى إضافة صنف واحد على الأقل")
            return

        total = sum(item['total'] for item in self.cart)
        inv_type = self.inv_type_combo.currentText()
        notes = self.notes_input.text().strip()

        supplier_id = None
        supplier_name = ""
        idx = self.supplier_combo.currentIndex()
        typed = self.supplier_combo.currentText().strip()
        if idx > 0 and idx - 1 < len(self._suppliers):
            sid = self.supplier_combo.currentData()
            if sid:
                supplier_id = sid
                supplier_name = self._suppliers[idx - 1]['name']
        elif typed:
            supplier_name = typed

        _d = self.ret_date.date()
        ret_date = f"{_d.year()}-{_d.month():02d}-{_d.day():02d}"
        db.create_purchase_return(supplier_id, supplier_name, self.cart, total, inv_type, notes, date=ret_date)
        show_info(self, "تم بنجاح",
                  f"✓  تم تسجيل مرتجع الشراء بنجاح\n"
                  f"الإجمالي: {total:.2f} ج.م\n"
                  "تم تحديث المخزون تلقائياً")
        self.accept()


class PurchaseReturnsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self.load_returns()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header_frame, header_inner = page_header(
            "↩  مرتجعات الشراء",
            "سجّل المرتجعات التي أعدتها للموردين"
        )
        new_btn = QPushButton("＋  تسجيل مرتجع شراء")
        new_btn.setStyleSheet(f"""
            QPushButton {{ background: {C_DANGER}; color: white; border: none;
                padding: 10px 22px; border-radius: 8px; font-size: 13px;
                font-family: Tahoma; font-weight: bold; }}
            QPushButton:hover {{ background: #c0392b; }}
        """)
        new_btn.clicked.connect(self._new_return)
        header_inner.addWidget(new_btn)
        layout.addWidget(header_frame)

        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background:white; border-radius:12px; border:1px solid #dce3ec; }")
        card_shadow(table_frame)
        tl = QVBoxLayout(table_frame)
        tl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "الإجراءات", "نوع الفاتورة", "الإجمالي (ج.م)", "المورد", "التاريخ"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 120)
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

    def load_returns(self):
        returns = db.get_all_purchase_returns()
        self.table.setRowCount(len(returns))
        for row, r in enumerate(returns):
            date_item = QTableWidgetItem(r['date'])
            date_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 4, date_item)

            sup_item = QTableWidgetItem(r.get('supplier_name', '') or "—")
            sup_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            sup_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 3, sup_item)

            total_item = QTableWidgetItem(f"{r['total_amount']:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            total_item.setForeground(QColor(C_DANGER))
            total_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            self.table.setItem(row, 2, total_item)

            inv_type_item = QTableWidgetItem(r.get('invoice_type', 'بيطري'))
            inv_type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            inv_type_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 1, inv_type_item)

            det_btn = QPushButton("التفاصيل")
            det_btn.setStyleSheet(BTN_EDIT)
            det_btn.clicked.connect(lambda _, rid=r['id']: self._show_details(rid))
            btn_w = QWidget()
            bl = QHBoxLayout(btn_w)
            bl.setContentsMargins(5, 4, 5, 4)
            bl.addWidget(det_btn)
            self.table.setCellWidget(row, 0, btn_w)
            self.table.setRowHeight(row, 50)

        total = sum(r['total_amount'] for r in returns)
        self.count_label.setText(f"عدد المرتجعات: {len(returns)}   |   إجمالي المرتجعات: {total:.2f} ج.م")

    def _new_return(self):
        dlg = NewPurchaseReturnDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_returns()

    def _show_details(self, return_id):
        items = db.get_purchase_return_items(return_id)
        msg = f"تفاصيل مرتجع الشراء رقم {return_id}:\n\n"
        for item in items:
            msg += f"•  {item['product_name']}   ×{item['quantity']:.2f}   @{item['unit_price']:.2f} ج.م  =  {item['total']:.2f} ج.م\n"
        from ui.styles import show_info
        show_info(self, "تفاصيل المرتجع", msg)
