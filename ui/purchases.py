from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QDoubleSpinBox, QMessageBox, QHeaderView, QComboBox, QFrame, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate, QLocale
from PyQt6.QtGui import QColor, QFont
import database as db
import pdf_report
from ui.styles import (
    TABLE_STYLE, BTN_EDIT, BTN_SECONDARY, BTN_ORANGE,
    DIALOG_STYLE, PAGE_STYLE, INPUT_STYLE, card_shadow,
    show_info, show_warning, show_error, style_calendar,
    setup_searchable_combo,
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
        setup_searchable_combo(self.supplier_combo)
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
        self.inv_type_combo.addItems(["بيطري", "أعلاف", "نثريات"])
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

        # Due-date row (visible only for credit/partial)
        due_row = QHBoxLayout()
        due_row.setSpacing(8)
        self.due_date_lbl = QLabel("تاريخ السداد:")
        self.due_date_lbl.setStyleSheet(f"color: {C_DANGER}; font-weight: bold;")
        _ar_locale2 = QLocale(QLocale.Language.Arabic, QLocale.Country.Egypt)
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setLocale(_ar_locale2)
        self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.due_date_edit.setDate(QDate.currentDate().addDays(30))
        self.due_date_edit.setMinimumDate(QDate.currentDate())
        self.due_date_edit.setFixedWidth(148)
        self.due_date_edit.setStyleSheet("""
            QDateEdit {
                padding: 8px 10px 8px 34px;
                border: 1.5px solid #e74c3c;
                border-radius: 7px;
                font-size: 13px; font-family: Tahoma;
                background: white; color: #1a2535;
            }
            QDateEdit:focus { border-color: #c0392b; background: #fff5f5; }
            QDateEdit::drop-down {
                subcontrol-origin: padding; subcontrol-position: left center;
                width: 28px; border: none;
                background: #e74c3c;
                border-top-left-radius: 5px; border-bottom-left-radius: 5px;
            }
            QDateEdit::down-arrow { width: 10px; height: 10px; }
        """)
        style_calendar(self.due_date_edit)
        self.due_date_lbl.setVisible(False)
        self.due_date_edit.setVisible(False)
        due_row.addStretch()
        due_row.addWidget(self.due_date_edit)
        due_row.addWidget(self.due_date_lbl)
        layout.addLayout(due_row)

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
        setup_searchable_combo(self.product_combo)

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
        pay = self.pay_type_combo.currentData()
        is_partial = pay == "partial"
        is_deferred = pay in ("credit", "partial")
        self.paid_spin.setVisible(is_partial)
        self.paid_lbl.setVisible(is_partial)
        self.due_date_lbl.setVisible(is_deferred)
        self.due_date_edit.setVisible(is_deferred)

    def _on_product_changed(self, index):
        if 0 <= index < len(self.products_data):
            typed = self.product_combo.currentText().strip()
            p = self.products_data[index]
            if typed == p['name']:
                self.unit_input.setText(p['unit'])
                self.price_spin.setValue(p['purchase_price'])
                self.selling_price_spin.setValue(p['selling_price'])
                self.inv_type_combo.setCurrentText(p.get('product_type') or 'بيطري')

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

        inv_type = self.inv_type_combo.currentText()

        # Create any new products that were typed in and don't exist yet
        for item in self.cart:
            if item.get('is_new') and item['product_id'] is None:
                new_id = db.add_product(
                    item['product_name'],
                    item['unit_name'] or '',
                    0,
                    item['unit_price'],
                    item['selling_price'],
                    inv_type,
                )
                item['product_id'] = new_id
                item['is_new']     = False

        total        = sum(item['total'] for item in self.cart)
        pay_type     = self.pay_type_combo.currentData()
        notes        = self.notes_input.text().strip()

        if pay_type == "cash":
            paid_amount = total
            payment_due_date = None
        elif pay_type == "credit":
            paid_amount = 0.0
            payment_due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        else:
            paid_amount = min(self.paid_spin.value(), total)
            payment_due_date = self.due_date_edit.date().toString("yyyy-MM-dd")

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

        purchase_id = db.create_purchase(supplier_id, supplier_name, self.cart, total, paid_amount, pay_type, notes, inv_type, payment_due_date)
        show_info(self, "تم بنجاح",
            f"✓  تم تسجيل فاتورة الشراء بنجاح\n"
            f"رقم الفاتورة: {purchase_id}\n"
            f"الإجمالي: {total:.2f} ج.م\n"
            "تم تحديث المخزون تلقائياً")
        self.accept()


class PurchaseDetailDialog(QDialog):
    def __init__(self, purchase, items, parent=None):
        super().__init__(parent)
        self._purchase_id = purchase['id']
        self.setWindowTitle(f"تفاصيل فاتورة الشراء # {purchase['id']}")
        self.resize(700, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE + TABLE_STYLE)
        self._build(purchase, items)

    def _build(self, purchase, items):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        type_map = {'cash': 'نقدي', 'credit': 'آجل', 'partial': 'جزئي'}

        info = QFrame()
        info.setStyleSheet("background:#f8f9fa; border-radius:8px; border:1px solid #dce3ec;")
        ig = QHBoxLayout(info)
        ig.setContentsMargins(16, 12, 16, 12)
        ig.setSpacing(28)

        def _col(label, value, color=None):
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(3)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 11px;")
            val = QLabel(value)
            val.setStyleSheet(f"color: {color or C_TEXT_DARK}; font-size: 13px; font-weight: bold;")
            v.addWidget(lbl)
            v.addWidget(val)
            return w

        ig.addWidget(_col("رقم الفاتورة", f"# {purchase['id']}", C_ORANGE))
        ig.addWidget(_col("التاريخ", purchase['date']))
        ig.addWidget(_col("المورد", purchase.get('supplier') or '—'))
        ig.addWidget(_col("نوع", purchase.get('invoice_type', '—')))
        ig.addWidget(_col("الدفع", type_map.get(purchase.get('payment_type', ''), '—')))
        if purchase.get('payment_due_date'):
            ig.addWidget(_col("تاريخ السداد", purchase['payment_due_date']))
        if purchase.get('notes'):
            ig.addWidget(_col("ملاحظات", purchase['notes']))
        ig.addStretch()
        layout.addWidget(info)

        tbl = QTableWidget()
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels(["المنتج", "الوحدة", "الكمية", "سعر الوحدة (ج.م)", "الإجمالي (ج.م)"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.verticalHeader().hide()
        tbl.setShowGrid(False)
        tbl.setFrameShape(QFrame.Shape.NoFrame)
        tbl.setRowCount(len(items))
        for r, item in enumerate(items):
            for c, (val, align) in enumerate([
                (item['product_name'],           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (item.get('unit_name') or '—',   Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
                (f"{item['quantity']:.2f}",       Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
                (f"{item['unit_price']:.2f}",     Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
                (f"{item['total']:.2f}",          Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
            ]):
                it = QTableWidgetItem(val)
                it.setTextAlignment(align)
                tbl.setItem(r, c, it)
            tbl.setRowHeight(r, 40)
        layout.addWidget(tbl)

        summary = QFrame()
        summary.setStyleSheet("background:#fff8f0; border-radius:8px; border:1px solid #f8dfc8;")
        sl = QHBoxLayout(summary)
        sl.setContentsMargins(16, 10, 16, 10)
        sl.setSpacing(6)
        paid = purchase.get('paid_amount') or 0
        remaining = max(0.0, purchase['total_amount'] - paid)
        for label, value, color in [
            ("الإجمالي", f"{purchase['total_amount']:.2f} ج.م", C_TEXT_DARK),
            ("المدفوع",  f"{paid:.2f} ج.م",                     C_ORANGE),
            ("المتبقي",  f"{remaining:.2f} ج.م",                 C_DANGER if remaining > 0 else C_ORANGE),
        ]:
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
            val_lbl = QLabel(value)
            val_lbl.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold; margin-left: 18px;")
            sl.addWidget(lbl)
            sl.addWidget(val_lbl)
        sl.addStretch()
        layout.addWidget(summary)

        btn_row = QHBoxLayout()
        print_btn = QPushButton("🖨️  طباعة الفاتورة")
        print_btn.setStyleSheet(BTN_ORANGE)
        print_btn.clicked.connect(self._print)
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(BTN_SECONDARY)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(print_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _print(self):
        try:
            path = pdf_report.generate_purchase_invoice(self._purchase_id)
            if path:
                pdf_report.open_pdf(path)
        except Exception as e:
            show_error(self, "خطأ", f"تعذّر إنشاء الفاتورة:\n{e}")


class PurchasesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._row_ids = []
        self._purchases_data = {}
        self._setup_ui()
        self.load_purchases()

    def _stat_card(self, parent_layout, title, bg, value_color, icon):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 12px;
                border: 1px solid #dce3ec;
            }}
        """)
        card_shadow(frame, blur=10, y=3, alpha=14)
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(18, 14, 18, 14)
        fl.setSpacing(6)
        hrow = QHBoxLayout()
        hrow.setSpacing(6)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color: {C_TEXT_MED}; font-size: 12px; font-family: Tahoma;"
            " background: transparent; border: none;"
        )
        hrow.addWidget(icon_lbl)
        hrow.addWidget(title_lbl)
        hrow.addStretch()
        fl.addLayout(hrow)
        val_lbl = QLabel("—")
        val_lbl.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color: {value_color}; background: transparent; border: none;")
        fl.addWidget(val_lbl)
        parent_layout.addWidget(frame, 1)
        return val_lbl

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # ── Header card ────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-radius: 12px;
                border: 1px solid #dce3ec;
                border-top: 4px solid {C_ORANGE};
            }}
        """)
        card_shadow(header, blur=15, y=3, alpha=18)
        h_inner = QHBoxLayout(header)
        h_inner.setContentsMargins(20, 16, 20, 16)
        h_inner.setSpacing(14)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        title_lbl = QLabel("📦  المشتريات")
        title_lbl.setFont(QFont("Tahoma", 17, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; background: transparent;")
        sub_lbl = QLabel("سجّل مشترياتك من الموردين — يتم تحديث المخزون تلقائياً")
        sub_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 11px; background: transparent;")
        text_col.addWidget(title_lbl)
        text_col.addWidget(sub_lbl)
        h_inner.addLayout(text_col)
        h_inner.addStretch()

        new_btn = QPushButton("＋  تسجيل شراء جديد")
        new_btn.setStyleSheet(BTN_ORANGE)
        new_btn.clicked.connect(self._new_purchase)
        h_inner.addWidget(new_btn)

        layout.addWidget(header)

        # ── Stats cards ────────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self._lbl_count = self._stat_card(stats_row, "عدد الفواتير",     "#f4f7fa", C_TEXT_DARK, "📋")
        self._lbl_total = self._stat_card(stats_row, "إجمالي المشتريات", "#fff8f0", C_ORANGE,    "🛒")
        self._lbl_paid  = self._stat_card(stats_row, "إجمالي المدفوع",   "#f0fff4", "#27ae60",   "✅")
        self._lbl_debt  = self._stat_card(stats_row, "المتبقي / الديون", "#fff5f5", C_DANGER,    "⚠️")
        layout.addLayout(stats_row)

        # ── Table card with built-in search bar ────────────────────────────────
        self.table_frame = QFrame()
        self.table_frame.setStyleSheet(
            "QFrame { background: white; border-radius: 12px; border: 1px solid #dce3ec; }"
        )
        card_shadow(self.table_frame)
        tl = QVBoxLayout(self.table_frame)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(0)

        search_bar = QFrame()
        search_bar.setStyleSheet(
            "QFrame { background: #f8fafc; border: none;"
            " border-bottom: 1px solid #dce3ec; border-radius: 0; }"
        )
        sb = QHBoxLayout(search_bar)
        sb.setContentsMargins(16, 10, 16, 10)
        sb.setSpacing(10)
        tbl_title = QLabel("الفواتير")
        tbl_title.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        tbl_title.setStyleSheet(f"color: {C_TEXT_DARK}; background: transparent;")
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("🔍  بحث باسم المورد أو رقم الفاتورة...")
        self._search_box.setStyleSheet(INPUT_STYLE)
        self._search_box.setMaximumWidth(320)
        self._search_box.textChanged.connect(self._filter_table)
        sb.addWidget(tbl_title)
        sb.addStretch()
        sb.addWidget(self._search_box)
        tl.addWidget(search_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ملاحظات", "الإجمالي (ج.م)", "المورد", "التاريخ", "تاريخ السداد", "رقم الفاتورة"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 110)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.cellClicked.connect(self._on_row_click)
        tl.addWidget(self.table)

        layout.addWidget(self.table_frame)

    def _filter_table(self, query):
        q = query.strip().lower()
        for row in range(self.table.rowCount()):
            sup_item = self.table.item(row, 2)
            id_item  = self.table.item(row, 5)
            sup = sup_item.text().lower() if sup_item else ""
            inv = id_item.text().lower() if id_item else ""
            self.table.setRowHidden(row, bool(q) and q not in sup and q not in inv)

    def load_purchases(self):
        from datetime import date as _date, timedelta as _td
        today_str = _date.today().isoformat()
        soon_str  = (_date.today() + _td(days=2)).isoformat()

        purchases = db.get_all_purchases()
        self._row_ids = [p['id'] for p in purchases]
        self._purchases_data = {p['id']: p for p in purchases}
        self.table.setRowCount(len(purchases))

        total_amount = 0.0
        total_paid   = 0.0
        total_debt   = 0.0

        for row, p in enumerate(purchases):
            id_item = QTableWidgetItem(f"# {p['id']}")
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            id_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            id_item.setForeground(QColor(C_ORANGE))
            self.table.setItem(row, 5, id_item)

            date_item = QTableWidgetItem(p['date'])
            date_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 3, date_item)

            sup_item = QTableWidgetItem(p['supplier'] or "—")
            sup_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            sup_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 2, sup_item)

            total_item = QTableWidgetItem(f"{p['total_amount']:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            total_item.setForeground(QColor(C_ORANGE))
            total_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            self.table.setItem(row, 1, total_item)

            notes_item = QTableWidgetItem(p.get('notes', '') or "")
            notes_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 0, notes_item)

            due = p.get('payment_due_date')
            remaining = max(0.0, (p.get('total_amount') or 0) - (p.get('paid_amount') or 0))
            if due and remaining > 0:
                if due < today_str:
                    due_color, due_text = C_DANGER, f"متأخر: {due}"
                elif due <= soon_str:
                    due_color, due_text = C_ORANGE, f"قريب: {due}"
                else:
                    due_color, due_text = C_TEXT_MED, due
            else:
                due_color, due_text = C_TEXT_MED, "—"
            due_item = QTableWidgetItem(due_text)
            due_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            due_item.setForeground(QColor(due_color))
            if due and remaining > 0 and due <= soon_str:
                due_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            self.table.setItem(row, 4, due_item)
            self.table.setRowHeight(row, 44)

            total_amount += p['total_amount']
            total_paid   += (p.get('paid_amount') or 0)
            total_debt   += remaining

        self._lbl_count.setText(str(len(purchases)))
        self._lbl_total.setText(f"{total_amount:,.2f} ج.م")
        self._lbl_paid.setText(f"{total_paid:,.2f} ج.م")
        self._lbl_debt.setText(f"{total_debt:,.2f} ج.م")

    def _on_row_click(self, row, _col):
        if 0 <= row < len(self._row_ids):
            self._show_details(self._row_ids[row])

    def _new_purchase(self):
        dlg = NewPurchaseDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_purchases()

    def _show_details(self, purchase_id):
        purchase = self._purchases_data.get(purchase_id)
        if not purchase:
            return
        items = db.get_purchase_items(purchase_id)
        dlg = PurchaseDetailDialog(purchase, items, self)
        dlg.exec()
