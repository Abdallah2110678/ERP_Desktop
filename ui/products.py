from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QMessageBox, QHeaderView, QFrame, QComboBox,
    QSizePolicy, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate, QLocale
from PyQt6.QtGui import QColor, QFont, QPalette
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD, BTN_EDIT, BTN_DELETE, BTN_SECONDARY,
    DIALOG_STYLE, PAGE_STYLE, INPUT_STYLE, card_shadow, style_calendar,
    confirm_delete, show_info, show_warning, show_error,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER, C_ORANGE,
)


def page_header(title, subtitle=""):
    frame = QFrame()
    frame.setStyleSheet("""
        QFrame {
            background-color: white;
            border-radius: 10px;
            border: 1px solid #dce3ec;
        }
    """)
    card_shadow(frame, blur=15, y=3, alpha=18)
    inner = QHBoxLayout(frame)
    inner.setContentsMargins(20, 14, 20, 14)

    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    title_lbl = QLabel(title)
    title_lbl.setFont(QFont("Tahoma", 16, QFont.Weight.Bold))
    title_lbl.setStyleSheet(f"color: {C_TEXT_DARK};")
    text_col.addWidget(title_lbl)
    if subtitle:
        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
        text_col.addWidget(sub_lbl)

    inner.addLayout(text_col)
    inner.addStretch()
    return frame, inner


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("تعديل دواء" if product else "إضافة دواء جديد")
        self.setFixedWidth(480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        # Header strip
        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_PRIMARY}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("تعديل دواء" if self.product else "إضافة دواء جديد")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("مثال: أموكسيسيلين 500 مج")
        form.addRow("اسم الدواء *:", self.name_input)

        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("حبة، علبة، زجاجة، مل، أمبول...")
        form.addRow("الوحدة *:", self.unit_input)

        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0, 999999)
        self.qty_input.setDecimals(2)
        self.qty_input.setSuffix("   وحدة")
        form.addRow("الكمية المتاحة:", self.qty_input)

        self.purchase_price_input = QDoubleSpinBox()
        self.purchase_price_input.setRange(0, 999999)
        self.purchase_price_input.setDecimals(2)
        self.purchase_price_input.setSuffix("   ج.م")
        form.addRow("سعر الشراء:", self.purchase_price_input)

        self.selling_price_input = QDoubleSpinBox()
        self.selling_price_input.setRange(0, 999999)
        self.selling_price_input.setDecimals(2)
        self.selling_price_input.setSuffix("   ج.م")
        form.addRow("سعر البيع:", self.selling_price_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["بيطري", "أعلاف", "نثريات"])
        self.type_combo.setStyleSheet(INPUT_STYLE)
        form.addRow("نوع الصنف:", self.type_combo)

        layout.addLayout(form)

        # Expiry date field — shown for all products (edit & add)
        expiry_row = QHBoxLayout()
        expiry_row.setSpacing(8)

        self._has_expiry_btn = QPushButton("📅  تحديد تاريخ الانتهاء")
        self._has_expiry_btn.setCheckable(True)
        self._has_expiry_btn.setChecked(False)
        self._has_expiry_btn.setFixedHeight(34)
        self._has_expiry_btn.setStyleSheet("""
            QPushButton { border:1.5px solid #cdd5df; border-radius:6px; padding:0 10px;
                font-family:Tahoma; font-size:12px; background:#f4f7fa; color:#7f8c8d; }
            QPushButton:checked { background:#eafaf1; color:#27ae60;
                border-color:#27ae60; font-weight:bold; }
            QPushButton:hover:!checked { background:#eef1f5; }
            QPushButton:checked:hover  { background:#d5f5e3; }
        """)

        _ar_loc = QLocale(QLocale.Language.Arabic, QLocale.Country.Egypt)
        self._expiry_edit = QDateEdit()
        self._expiry_edit.setCalendarPopup(True)
        self._expiry_edit.setLocale(_ar_loc)
        self._expiry_edit.setDisplayFormat("yyyy-MM-dd")
        self._expiry_edit.setDate(QDate.currentDate().addYears(1))
        self._expiry_edit.setMinimumDate(QDate(2000, 1, 1))
        self._expiry_edit.setEnabled(False)
        self._expiry_edit.setStyleSheet("""
            QDateEdit { padding:7px 10px 7px 32px; border:1.5px solid #cdd5df;
                border-radius:6px; font-size:13px; font-family:Tahoma;
                background:#f0f3f7; }
            QDateEdit:enabled { background:white; }
            QDateEdit:enabled:focus { border-color:#27ae60; background:#f0fff4; }
            QDateEdit::drop-down { subcontrol-origin:padding; subcontrol-position:left center;
                width:26px; border:none; background:#27ae60;
                border-top-left-radius:4px; border-bottom-left-radius:4px; }
            QDateEdit:!enabled::drop-down { background:#bdc3c7; }
            QDateEdit::down-arrow { width:10px; height:10px; }
        """)
        # Fusion draws QDateEdit text from palette.windowText(), not the CSS color rule.
        # Set both Text+Base and WindowText+Window for all color groups so dark-mode
        # system palettes cannot bleed white text onto a white background.
        _pal = QPalette()
        for _grp, _txt, _bg in (
            (QPalette.ColorGroup.Active,   QColor("#1a2535"), QColor("#ffffff")),
            (QPalette.ColorGroup.Inactive, QColor("#1a2535"), QColor("#ffffff")),
            (QPalette.ColorGroup.Disabled, QColor("#5d6d7e"), QColor("#f0f3f7")),
        ):
            _pal.setColor(_grp, QPalette.ColorRole.Text,       _txt)
            _pal.setColor(_grp, QPalette.ColorRole.Base,       _bg)
            _pal.setColor(_grp, QPalette.ColorRole.WindowText, _txt)
            _pal.setColor(_grp, QPalette.ColorRole.Window,     _bg)
        self._expiry_edit.setPalette(_pal)
        style_calendar(self._expiry_edit)
        self._has_expiry_btn.toggled.connect(self._expiry_edit.setEnabled)

        expiry_row.addWidget(self._expiry_edit)
        expiry_row.addWidget(self._has_expiry_btn)
        form.addRow("تاريخ الانتهاء:", expiry_row)

        if self.product:
            self.name_input.setText(self.product['name'])
            self.unit_input.setText(self.product['unit'])
            self.qty_input.setValue(self.product['quantity'])
            self.purchase_price_input.setValue(self.product['purchase_price'])
            self.selling_price_input.setValue(self.product['selling_price'])
            ptype = self.product.get('product_type', 'بيطري')
            self.type_combo.setCurrentIndex({"بيطري": 0, "أعلاف": 1, "نثريات": 2, "أخرى": 2}.get(ptype, 0))

            # Pre-populate expiry from existing batches
            expiry_map = db.get_product_nearest_expiries()
            nearest    = expiry_map.get(self.product['id'])
            if nearest:
                self._has_expiry_btn.setChecked(True)
                self._expiry_edit.setDate(QDate.fromString(nearest, "yyyy-MM-dd"))

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
            show_warning(self, "خطأ", "يرجى إدخال اسم الدواء")
            return
        if not self.unit_input.text().strip():
            show_warning(self, "خطأ", "يرجى إدخال وحدة الدواء")
            return
        self.accept()

    def get_data(self):
        expiry = (self._expiry_edit.date().toString("yyyy-MM-dd")
                  if self._has_expiry_btn.isChecked() else None)
        return {
            'name': self.name_input.text().strip(),
            'unit': self.unit_input.text().strip(),
            'quantity': self.qty_input.value(),
            'purchase_price': self.purchase_price_input.value(),
            'selling_price': self.selling_price_input.value(),
            'product_type': self.type_combo.currentText(),
            'expiry_date': expiry,
        }


class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self.load_products()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header_frame, header_inner = page_header(
            "💊  إدارة الأدوية والمنتجات",
            "أضف وعدّل أدوية المخزون مع أسعار الشراء والبيع"
        )
        full_report_btn = QPushButton("🖨  تقرير المخزون الكامل")
        full_report_btn.setStyleSheet("""
            QPushButton { background:#2980b9; color:white; border:none;
                padding:10px 18px; border-radius:7px; font-size:13px;
                font-family:Tahoma; font-weight:bold; }
            QPushButton:hover { background:#2471a3; }
        """)
        full_report_btn.clicked.connect(self._print_full_inventory_report)
        header_inner.addWidget(full_report_btn)

        report_btn = QPushButton("🖨  تقرير المخزون المنخفض")
        report_btn.setStyleSheet("""
            QPushButton { background:#e67e22; color:white; border:none;
                padding:10px 18px; border-radius:7px; font-size:13px;
                font-family:Tahoma; font-weight:bold; }
            QPushButton:hover { background:#d35400; }
        """)
        report_btn.clicked.connect(self._print_low_stock_report)
        header_inner.addWidget(report_btn)

        layout.addWidget(header_frame)

        # Toolbar row (search + count)
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍   ابحث عن دواء بالاسم...")
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.setMaximumWidth(320)
        self.search_input.textChanged.connect(self._search)
        toolbar.addWidget(self.search_input)
        toolbar.addStretch()
        self.count_label = QLabel()
        self.count_label.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
        toolbar.addWidget(self.count_label)
        layout.addLayout(toolbar)

        # Table container
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame { background: white; border-radius: 12px; border: 1px solid #dce3ec; }
        """)
        card_shadow(table_frame)
        table_inner = QVBoxLayout(table_frame)
        table_inner.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "الإجراءات", "سعر البيع (ج.م)", "سعر الشراء (ج.م)", "الكمية", "الوحدة", "النوع", "اسم الدواء", "أقرب تاريخ انتهاء", "id"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 175)
        self.table.setColumnHidden(2, True)
        self.table.setColumnHidden(8, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        table_inner.addWidget(self.table)
        layout.addWidget(table_frame)

    def load_products(self, products=None):
        if products is None:
            products = db.get_all_products()

        from datetime import date as _date, timedelta
        expiry_map  = db.get_product_nearest_expiries()
        today       = _date.today()
        today_str   = today.strftime('%Y-%m-%d')
        warn_cutoff = (today + timedelta(days=90)).strftime('%Y-%m-%d')

        self.table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.table.setItem(row, 8, QTableWidgetItem(str(p['id'])))

            name_item = QTableWidgetItem(p['name'])
            name_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            name_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 6, name_item)

            ptype = p.get('product_type', 'بيطري')
            type_item = QTableWidgetItem(ptype)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_item.setForeground(QColor(C_ORANGE if ptype == 'أعلاف' else ('#2c3e50' if ptype in ('نثريات', 'أخرى') else '#16a085')))
            self.table.setItem(row, 5, type_item)

            unit_item = QTableWidgetItem(p['unit'])
            unit_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 4, unit_item)

            qty = p['quantity']
            qty_item = QTableWidgetItem(f"{qty:.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if qty <= 10:
                qty_item.setForeground(QColor(C_DANGER))
                qty_item.setText(f"⚠  {qty:.2f}")
            else:
                qty_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 3, qty_item)

            pp_item = QTableWidgetItem(f"{p['purchase_price']:.2f}")
            pp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pp_item.setForeground(QColor("#5d6d7e"))
            self.table.setItem(row, 2, pp_item)

            sp_item = QTableWidgetItem(f"{p['selling_price']:.2f}")
            sp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            sp_item.setForeground(QColor(C_PRIMARY))
            sp_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            self.table.setItem(row, 1, sp_item)

            exp_date = expiry_map.get(p['id'])
            if exp_date:
                if exp_date < today_str:
                    exp_text  = f"🔴  {exp_date}"
                    exp_color = C_DANGER
                elif exp_date <= warn_cutoff:
                    exp_text  = f"🟠  {exp_date}"
                    exp_color = C_ORANGE
                else:
                    exp_text  = f"🟢  {exp_date}"
                    exp_color = "#1a7a4a"
            else:
                exp_text  = "—"
                exp_color = C_TEXT_MED
            exp_item = QTableWidgetItem(exp_text)
            exp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            exp_item.setForeground(QColor(exp_color))
            self.table.setItem(row, 7, exp_item)

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(6, 4, 6, 4)
            btn_l.setSpacing(6)

            edit_btn = QPushButton("تعديل")
            edit_btn.setStyleSheet(BTN_EDIT)
            edit_btn.clicked.connect(lambda _, pid=p['id']: self._edit_product(pid))

            del_btn = QPushButton("حذف")
            del_btn.setStyleSheet(BTN_DELETE)
            del_btn.clicked.connect(lambda _, pid=p['id']: self._delete_product(pid))

            btn_l.addWidget(del_btn)
            btn_l.addWidget(edit_btn)
            self.table.setCellWidget(row, 0, btn_w)
            self.table.setRowHeight(row, 54)

        self.count_label.setText(f"عدد الأدوية: {len(products)}")

    def _search(self, query):
        products = db.search_products(query) if query.strip() else db.get_all_products()
        self.load_products(products)

    def _add_product(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.add_product(d['name'], d['unit'], d['quantity'], d['purchase_price'], d['selling_price'], d['product_type'])
            self.load_products()

    def _edit_product(self, pid):
        product = next((p for p in db.get_all_products() if p['id'] == pid), None)
        if not product:
            return
        dlg = ProductDialog(self, product)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.update_product(pid, d['name'], d['unit'], d['quantity'], d['purchase_price'], d['selling_price'], d['product_type'])
            if d.get('expiry_date') is not None:
                db.set_product_expiry(pid, d['expiry_date'], d['quantity'])
            self.load_products()

    def _delete_product(self, pid):
        if confirm_delete(self, "هل أنت متأكد من حذف هذا الدواء؟"):
            db.delete_product(pid)
            self.load_products()

    def _print_low_stock_report(self):
        from ui.notification_bar import LowStockDialog, LOW_THRESHOLD
        products = db.get_low_stock_products(LOW_THRESHOLD)
        if not products:
            show_info(self, "المخزون سليم", "✅  جميع الأدوية لديها كميات كافية في المخزون")
            return
        dlg = LowStockDialog(self, products)
        dlg.exec()

    def _print_full_inventory_report(self):
        products = db.get_all_products()
        if not products:
            show_info(self, "لا توجد بيانات", "لا توجد أدوية مسجلة في المخزون بعد")
            return
        try:
            from pdf_report import generate_inventory_report, open_pdf
            path = generate_inventory_report(products)
            open_pdf(path)
        except Exception as e:
            show_error(self, "خطأ", f"فشل إنشاء ملف PDF:\n{e}")
