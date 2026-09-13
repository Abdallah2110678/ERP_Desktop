from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QDoubleSpinBox, QMessageBox, QHeaderView, QComboBox, QFrame, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate, QLocale
from PyQt6.QtGui import QColor, QFont
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_EDIT, BTN_SECONDARY, BTN_ORANGE,
    DIALOG_STYLE, PAGE_STYLE, INPUT_STYLE, card_shadow,
    show_info, show_warning, show_error, style_calendar,
    C_TEXT_DARK, C_TEXT_MED, C_DANGER, C_ORANGE,
)
from ui.products import page_header


class NewPurchaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تسجيل فاتورة شراء جديدة")
        self.resize(820, 620)
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
        strip.setStyleSheet(f"background: {C_ORANGE}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("📦  تسجيل فاتورة شراء")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        # Supplier row
        sup_row = QHBoxLayout()
        sup_row.setSpacing(8)
        self.supplier_combo = QComboBox()
        self.supplier_combo.setEditable(True)
        self.supplier_combo.setMinimumWidth(220)
        self.supplier_combo.setStyleSheet(INPUT_STYLE)
        self.supplier_combo.lineEdit().setPlaceholderText("اختر مورداً أو اكتب اسماً جديداً...")
        sup_row.addWidget(self.supplier_combo)
        sup_row.addWidget(QLabel("المورد:"))
        sup_row.addSpacing(20)

        pay_type_lbl = QLabel("نوع الدفع:")
        self.pay_type_combo = QComboBox()
        self.pay_type_combo.addItem("نقدي", "cash")
        self.pay_type_combo.addItem("آجل (دين)", "credit")
        self.pay_type_combo.addItem("دفع جزئي", "partial")
        self.pay_type_combo.setStyleSheet(INPUT_STYLE)
        self.pay_type_combo.setFixedWidth(140)
        self.pay_type_combo.currentIndexChanged.connect(self._on_pay_type_changed)
        sup_row.addWidget(self.pay_type_combo)
        sup_row.addWidget(pay_type_lbl)
        sup_row.addSpacing(12)

        inv_type_lbl = QLabel("نوع الفاتورة:")
        self.inv_type_combo = QComboBox()
        self.inv_type_combo.addItems(["بيطري", "أعلاف", "أخرى"])
        self.inv_type_combo.setStyleSheet(INPUT_STYLE)
        self.inv_type_combo.setFixedWidth(110)
        sup_row.addWidget(self.inv_type_combo)
        sup_row.addWidget(inv_type_lbl)
        sup_row.addSpacing(20)

        self.paid_lbl = QLabel("المدفوع:")
        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setSuffix(" ج.م")
        self.paid_spin.setFixedWidth(130)
        self.paid_spin.setStyleSheet(INPUT_STYLE)
        self.paid_spin.setVisible(False)
        self.paid_lbl.setVisible(False)
        sup_row.addWidget(self.paid_spin)
        sup_row.addWidget(self.paid_lbl)
        sup_row.addStretch()
        layout.addLayout(sup_row)

        # Product add rows
        prod_frame = QFrame()
        prod_frame.setStyleSheet("QFrame { background:#f4f7fa; border-radius:8px; border:1px solid #dce3ec; }")
        pl = QVBoxLayout(prod_frame)
        pl.setContentsMargins(12, 10, 12, 10)
        pl.setSpacing(8)

        # Row 1: drug name + unit (editable)
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(220)
        self.product_combo.setStyleSheet(INPUT_STYLE)
        self.product_combo.setEditable(True)
        self.product_combo.lineEdit().setPlaceholderText("اكتب اسم الدواء أو اختره من القائمة...")
        self.product_combo.currentIndexChanged.connect(self._on_product_changed)

        self.unit_input = QLineEdit()
        self.unit_input.setFixedWidth(110)
        self.unit_input.setPlaceholderText("الوحدة")
        self.unit_input.setStyleSheet(INPUT_STYLE)

        self.has_expiry_cb = QPushButton("📅  تاريخ الانتهاء")
        self.has_expiry_cb.setCheckable(True)
        self.has_expiry_cb.setChecked(False)
        self.has_expiry_cb.setFixedHeight(36)
        self.has_expiry_cb.setStyleSheet("""
            QPushButton {
                border: 1.5px solid #cdd5df; border-radius: 7px;
                padding: 0 12px; font-family: Tahoma; font-size: 12px;
                background: #f4f7fa; color: #7f8c8d;
            }
            QPushButton:checked {
                background: #eafaf1; color: #27ae60;
                border-color: #27ae60; font-weight: bold;
            }
            QPushButton:hover:!checked { background: #eef1f5; }
            QPushButton:checked:hover  { background: #d5f5e3; }
        """)

        _ar_locale = QLocale(QLocale.Language.Arabic, QLocale.Country.Egypt)
        self.expiry_edit = QDateEdit()
        self.expiry_edit.setCalendarPopup(True)
        self.expiry_edit.setLocale(_ar_locale)
        self.expiry_edit.setDisplayFormat("yyyy-MM-dd")
        self.expiry_edit.setFixedWidth(148)
        self.expiry_edit.setDate(QDate.currentDate().addYears(1))
        self.expiry_edit.setMinimumDate(QDate.currentDate())
        self.expiry_edit.setEnabled(False)
        self.expiry_edit.setStyleSheet("""
            QDateEdit {
                padding: 8px 10px 8px 34px;
                border: 1.5px solid #cdd5df;
                border-radius: 7px;
                font-size: 13px; font-family: Tahoma;
                background: #f0f3f7; color: #8a99a8;
            }
            QDateEdit:enabled { background: white; color: #1a2535; }
            QDateEdit:enabled:focus { border-color: #27ae60; background: #f0fff4; }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: left center;
                width: 28px; border: none;
                background: #27ae60;
                border-top-left-radius: 5px;
                border-bottom-left-radius: 5px;
            }
            QDateEdit:!enabled::drop-down { background: #bdc3c7; }
            QDateEdit::down-arrow { width: 10px; height: 10px; }
        """)
        cal = self.expiry_edit.calendarWidget()
        if cal:
            cal.setLocale(_ar_locale)
            cal.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        style_calendar(self.expiry_edit)
        self.has_expiry_cb.toggled.connect(self.expiry_edit.setEnabled)

        row1.addWidget(self.product_combo)
        row1.addWidget(QLabel("الدواء:"))
        row1.addSpacing(12)
        row1.addWidget(self.unit_input)
        row1.addWidget(QLabel("الوحدة:"))
        row1.addSpacing(12)
        row1.addWidget(self.expiry_edit)
        row1.addWidget(self.has_expiry_cb)
        row1.addStretch()
        pl.addLayout(row1)

        # Row 2: qty + purchase price + selling price + add button
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

        self.selling_price_spin = QDoubleSpinBox()
        self.selling_price_spin.setRange(0, 999999)
        self.selling_price_spin.setDecimals(2)
        self.selling_price_spin.setSuffix(" ج.م")
        self.selling_price_spin.setFixedWidth(130)
        self.selling_price_spin.setStyleSheet(INPUT_STYLE)

        add_btn = QPushButton("➕  إضافة")
        add_btn.setStyleSheet(BTN_ORANGE.replace("padding: 10px 22px;", "padding: 8px 18px;"))
        add_btn.clicked.connect(self._add_item)

        row2.addWidget(self.qty_spin)
        row2.addWidget(QLabel("الكمية:"))
        row2.addSpacing(10)
        row2.addWidget(self.price_spin)
        row2.addWidget(QLabel("سعر الشراء:"))
        row2.addSpacing(10)
        row2.addWidget(self.selling_price_spin)
        row2.addWidget(QLabel("سعر البيع:"))
        row2.addStretch()
        row2.addWidget(add_btn)
        pl.addLayout(row2)

        layout.addWidget(prod_frame)

        items_lbl = QLabel("الأصناف المشتراة:")
        items_lbl.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        items_lbl.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(items_lbl)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["حذف","الإجمالي (ج.م)","سعر الشراء (ج.م)","الكمية","تاريخ الانتهاء","اسم الدواء"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.items_table.setColumnWidth(0, 65)
        self.items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.items_table.verticalHeader().hide()
        self.items_table.setMaximumHeight(190)
        self.items_table.setShowGrid(False)
        self.items_table.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.items_table)

        # Total row
        total_row = QHBoxLayout()
        total_row.addStretch()
        total_lbl = QLabel("إجمالي الفاتورة:")
        total_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 13px;")
        self.total_label = QLabel("0.00 ج.م")
        self.total_label.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
        self.total_label.setStyleSheet(f"color: {C_ORANGE};")
        total_row.addWidget(self.total_label)
        total_row.addWidget(total_lbl)
        layout.addLayout(total_row)

        # Notes
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
        confirm_btn = QPushButton("✓  تأكيد الشراء")
        confirm_btn.setStyleSheet(BTN_ORANGE)
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self._confirm_purchase)
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

    def _on_pay_type_changed(self, index):
        is_partial = self.pay_type_combo.currentData() == "partial"
        self.paid_spin.setVisible(is_partial)
        self.paid_lbl.setVisible(is_partial)

    def _on_product_changed(self, index):
        if 0 <= index < len(self.products_data):
            typed = self.product_combo.currentText().strip()
            p = self.products_data[index]
            if typed == p['name']:
                self.unit_input.setText(p['unit'])
                self.price_spin.setValue(p['purchase_price'])
                self.selling_price_spin.setValue(p['selling_price'])

    def _add_item(self):
        idx           = self.product_combo.currentIndex()
        typed_name    = self.product_combo.currentText().strip()
        unit_name     = self.unit_input.text().strip()
        qty           = self.qty_spin.value()
        price         = self.price_spin.value()
        selling_price = self.selling_price_spin.value()

        if not typed_name:
            show_warning(self, "خطأ", "يرجى إدخال اسم الدواء")
            return
        if qty <= 0:
            show_warning(self, "خطأ", "الكمية يجب أن تكون أكبر من صفر")
            return

        expiry_date = self.expiry_edit.date().toString("yyyy-MM-dd") if self.has_expiry_cb.isChecked() else None

        existing = (
            0 <= idx < len(self.products_data)
            and typed_name == self.products_data[idx]['name']
        )
        if existing:
            product    = self.products_data[idx]
            product_id = product['id']
            name       = product['name']
            unit_name  = unit_name or product['unit']
        else:
            product_id = None
            name       = typed_name

        # Each add = its own batch entry (no merging), so FIFO works correctly
        self.cart.append({
            'product_id':    product_id,
            'product_name':  name,
            'unit_name':     unit_name,
            'quantity':      qty,
            'unit_price':    price,
            'selling_price': selling_price,
            'total':         round(qty * price, 2),
            'expiry_date':   expiry_date,
            'is_new':        product_id is None,
        })
        self._refresh_table(); self._update_total()

    def _refresh_table(self):
        self.items_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            display = f"{item['product_name']}  ({item.get('unit_name', '')})"
            name_item = QTableWidgetItem(display)
            name_item.setForeground(QColor(C_TEXT_DARK))
            name_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            self.items_table.setItem(row, 5, name_item)

            for col, val, clr in [
                (3, f"{item['quantity']:.2f}",   C_TEXT_DARK),
                (2, f"{item['unit_price']:.2f}",  C_TEXT_MED),
                (1, f"{item['total']:.2f}",        C_ORANGE),
            ]:
                it = QTableWidgetItem(val)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setForeground(QColor(clr))
                if col == 1:
                    it.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
                self.items_table.setItem(row, col, it)

            exp = item.get('expiry_date') or '—'
            exp_item = QTableWidgetItem(exp)
            exp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            exp_item.setForeground(QColor(C_DANGER if exp != '—' else C_TEXT_MED))
            self.items_table.setItem(row, 4, exp_item)

            del_btn = QPushButton("🗑")
            del_btn.setStyleSheet(f"background:{C_DANGER}; color:white; border:none; border-radius:4px; font-size:14px;")
            del_btn.clicked.connect(lambda _, r=row: self._remove_item(r))
            self.items_table.setCellWidget(row, 0, del_btn)
            self.items_table.setRowHeight(row, 40)

    def _remove_item(self, row):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self._refresh_table(); self._update_total()

    def _update_total(self):
        total = sum(item['total'] for item in self.cart)
        self.total_label.setText(f"{total:.2f} ج.م")

    def _confirm_purchase(self):
        if not self.cart:
            show_warning(self, "خطأ", "يرجى إضافة صنف واحد على الأقل")
            return

        # Create any new products that were typed in and don't exist yet
        for item in self.cart:
            if item.get('is_new') and item['product_id'] is None:
                new_id = db.add_product(
                    item['product_name'],
                    item['unit_name'] or '',
                    0,
                    item['unit_price'],
                    item['selling_price'],
                )
                item['product_id'] = new_id
                item['is_new']     = False

        total        = sum(item['total'] for item in self.cart)
        pay_type     = self.pay_type_combo.currentData()
        notes        = self.notes_input.text().strip()

        if pay_type == "cash":
            paid_amount = total
        elif pay_type == "credit":
            paid_amount = 0.0
        else:
            paid_amount = min(self.paid_spin.value(), total)

        # Resolve supplier — create a new one if a name was typed but not yet in the list
        supplier_id   = None
        supplier_name = ""
        idx = self.supplier_combo.currentIndex()
        typed = self.supplier_combo.currentText().strip()
        if idx > 0:
            sid = self.supplier_combo.currentData()
            if sid:
                supplier_id   = sid
                supplier_name = self.supplier_combo.itemText(idx)
        if supplier_id is None and typed:
            supplier_name = typed
            supplier_id   = db.add_supplier(typed, '', '')

        inv_type = self.inv_type_combo.currentText()
        purchase_id = db.create_purchase(supplier_id, supplier_name, self.cart, total, paid_amount, pay_type, notes, inv_type)
        show_info(self, "تم بنجاح",
            f"✓  تم تسجيل فاتورة الشراء بنجاح\n"
            f"رقم الفاتورة: {purchase_id}\n"
            f"الإجمالي: {total:.2f} ج.م\n"
            "تم تحديث المخزون تلقائياً")
        self.accept()


class PurchasesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self.load_purchases()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header_frame, header_inner = page_header(
            "📦  سجل المشتريات",
            "سجّل مشترياتك من الموردين وتحديث المخزون يتم تلقائياً"
        )
        new_btn = QPushButton("＋  تسجيل شراء جديد")
        new_btn.setStyleSheet(BTN_ORANGE)
        new_btn.clicked.connect(self._new_purchase)
        header_inner.addWidget(new_btn)
        layout.addWidget(header_frame)

        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background:white; border-radius:12px; border:1px solid #dce3ec; }")
        card_shadow(table_frame)
        tl = QVBoxLayout(table_frame)
        tl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "الإجراءات", "ملاحظات", "الإجمالي (ج.م)", "المورد", "التاريخ", "رقم الفاتورة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(5, 100)
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

    def load_purchases(self):
        purchases = db.get_all_purchases()
        self.table.setRowCount(len(purchases))

        for row, p in enumerate(purchases):
            id_item = QTableWidgetItem(f"# {p['id']}")
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            id_item.setForeground(QColor(C_ORANGE))
            self.table.setItem(row, 5, id_item)

            date_item = QTableWidgetItem(p['date'])
            date_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 4, date_item)

            sup_item = QTableWidgetItem(p['supplier'] or "—")
            sup_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            sup_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 3, sup_item)

            total_item = QTableWidgetItem(f"{p['total_amount']:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            total_item.setForeground(QColor(C_ORANGE))
            total_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            self.table.setItem(row, 2, total_item)

            notes_item = QTableWidgetItem(p.get('notes', '') or "")
            notes_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 1, notes_item)

            det_btn = QPushButton("التفاصيل")
            det_btn.setStyleSheet(BTN_EDIT)
            det_btn.clicked.connect(lambda _, pid=p['id']: self._show_details(pid))
            btn_w = QWidget()
            bl = QHBoxLayout(btn_w)
            bl.setContentsMargins(5, 4, 5, 4)
            bl.addWidget(det_btn)
            self.table.setCellWidget(row, 0, btn_w)
            self.table.setRowHeight(row, 50)

        total_amount = sum(p['total_amount'] for p in purchases)
        self.count_label.setText(
            f"عدد الفواتير: {len(purchases)}   |   إجمالي المشتريات: {total_amount:.2f} ج.م"
        )

    def _new_purchase(self):
        dlg = NewPurchaseDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_purchases()

    def _show_details(self, purchase_id):
        items = db.get_purchase_items(purchase_id)
        msg = f"تفاصيل فاتورة الشراء رقم {purchase_id}:\n\n"
        for item in items:
            msg += f"•  {item['product_name']}   ×{item['quantity']:.2f}   @{item['unit_price']:.2f} ج.م  =  {item['total']:.2f} ج.م\n"
        show_info(self, "تفاصيل الشراء", msg)
