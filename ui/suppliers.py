from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QDoubleSpinBox, QHeaderView, QFrame,
    QTabWidget, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont, QPalette
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD, BTN_EDIT, BTN_DELETE, BTN_SECONDARY,
    BTN_HISTORY, BTN_PAY, DIALOG_STYLE, PAGE_STYLE, INPUT_STYLE,
    card_shadow, confirm_delete, show_info, show_warning, show_error, style_calendar,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER, C_ORANGE,
)
from ui.products import page_header

C_TEAL = "#16a085"
C_TEAL_DARK = "#117a65"


class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier=None):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("تعديل مورد" if supplier else "إضافة مورد جديد")
        self.setFixedWidth(410)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_TEAL}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("تعديل المورد" if self.supplier else "إضافة مورد / شركة جديدة")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم الشركة أو المورد")
        self.name_input.setStyleSheet(INPUT_STYLE)
        form.addRow("اسم المورد *:", self.name_input)
        layout.addLayout(form)

        if self.supplier:
            self.name_input.setText(self.supplier['name'])

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
            show_warning(self, "خطأ", "يرجى إدخال اسم المورد")
            return
        self.accept()

    def get_data(self):
        return {'name': self.name_input.text().strip()}


class SupplierPaymentDialog(QDialog):
    def __init__(self, parent, supplier):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("تسجيل دفعة للمورد")
        self.setFixedWidth(380)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_TEAL}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("تسجيل دفعة للمورد")
        title.setFont(QFont("Tahoma", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_DARK};")
        layout.addWidget(title)

        info_box = QFrame()
        debt = self.supplier['total_debt']
        info_box.setStyleSheet(f"""
            QFrame {{
                background: {'#fff8e6' if debt > 0 else '#eafaf1'};
                border-radius: 8px;
                border: 1px solid {'#f4c842' if debt > 0 else '#a9dfbf'};
                padding: 4px;
            }}
        """)
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(4)

        name_lbl = QLabel(f"🏭  {self.supplier['name']}")
        name_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 13px; font-weight: bold;")
        info_layout.addWidget(name_lbl)

        debt_color = C_DANGER if debt > 0 else C_PRIMARY
        debt_lbl = QLabel(f"المبلغ المستحق: {debt:.2f} ج.م")
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
        self.amount_input.setValue(self.supplier['total_debt'] if self.supplier['total_debt'] > 0 else 1)
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
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def get_data(self):
        return {'amount': self.amount_input.value(), 'notes': self.notes_input.text().strip()}


class SupplierHistoryDialog(QDialog):
    def __init__(self, parent, supplier):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("سجل المورد")
        self.resize(760, 540)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE + TABLE_STYLE)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        hdr = QFrame()
        hdr.setStyleSheet("QFrame { background: #1a2535; border-radius: 10px; border: none; }")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(18, 14, 18, 14)

        name_lbl = QLabel(f"🏭  {self.supplier['name']}")
        name_lbl.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: white;")
        hdr_layout.addWidget(name_lbl)
        hdr_layout.addStretch()

        if self.supplier.get('phone'):
            phone_lbl = QLabel(f"📞 {self.supplier['phone']}")
            phone_lbl.setStyleSheet("color: #8fa8bf; font-size: 12px;")
            hdr_layout.addWidget(phone_lbl)

        debt = self.supplier['total_debt']
        debt_color = C_DANGER if debt > 0 else C_PRIMARY
        debt_lbl = QLabel(f"  المستحق: {debt:.2f} ج.م")
        debt_lbl.setFont(QFont("Tahoma", 13, QFont.Weight.Bold))
        debt_lbl.setStyleSheet(f"color: {debt_color}; border: none;")
        hdr_layout.addWidget(debt_lbl)
        layout.addWidget(hdr)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #dce3ec; border-radius: 8px; background: white; }
            QTabBar::tab { padding: 9px 18px; font-family: Tahoma; font-size: 12px; border-radius: 6px 6px 0 0; }
            QTabBar::tab:selected { background: #1a2535; color: white; }
            QTabBar::tab:!selected { background: #f0f2f5; color: #5d6d7e; }
        """)

        # Purchases tab
        p_widget = QWidget()
        p_layout = QVBoxLayout(p_widget)
        p_layout.setContentsMargins(10, 10, 10, 10)
        self.purchases_table = QTableWidget()
        self.purchases_table.setColumnCount(5)
        self.purchases_table.setHorizontalHeaderLabels(
            ["نوع الدفع", "المتبقي (ج.م)", "المدفوع (ج.م)", "الإجمالي (ج.م)", "التاريخ"]
        )
        self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.purchases_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.purchases_table.verticalHeader().hide()
        self.purchases_table.setAlternatingRowColors(True)
        self.purchases_table.setShowGrid(False)
        self.purchases_table.setFrameShape(QFrame.Shape.NoFrame)
        p_layout.addWidget(self.purchases_table)
        tabs.addTab(p_widget, "فواتير الشراء")

        # Payments tab
        pay_widget = QWidget()
        pay_layout = QVBoxLayout(pay_widget)
        pay_layout.setContentsMargins(10, 10, 10, 10)
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(3)
        self.payments_table.setHorizontalHeaderLabels(["ملاحظات", "المبلغ (ج.م)", "التاريخ"])
        self.payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payments_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.payments_table.verticalHeader().hide()
        self.payments_table.setAlternatingRowColors(True)
        self.payments_table.setShowGrid(False)
        self.payments_table.setFrameShape(QFrame.Shape.NoFrame)
        pay_layout.addWidget(self.payments_table)
        tabs.addTab(pay_widget, "سجل المدفوعات")

        layout.addWidget(tabs)

        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(BTN_SECONDARY)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self._load_data()

    def _load_data(self):
        purchases, payments = db.get_supplier_history(self.supplier['id'])
        type_map = {'cash': 'نقدي', 'credit': 'آجل', 'partial': 'جزئي'}

        def _cell(text, color, align=True, bold=False):
            it = QTableWidgetItem(str(text))
            it.setForeground(QColor(color))
            if align:
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if bold:
                it.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            return it

        self.purchases_table.setRowCount(len(purchases))
        for row, p in enumerate(purchases):
            self.purchases_table.setItem(row, 4, _cell(p['date'], C_TEXT_MED))
            total = p.get('total_amount', 0) or 0
            paid = p.get('paid_amount', 0) or 0
            remaining = max(0.0, total - paid)
            self.purchases_table.setItem(row, 3, _cell(f"{total:.2f}", C_TEXT_DARK, bold=True))
            self.purchases_table.setItem(row, 2, _cell(f"{paid:.2f}", C_PRIMARY))
            self.purchases_table.setItem(row, 1, _cell(f"{remaining:.2f}", C_DANGER if remaining > 0 else C_PRIMARY))
            self.purchases_table.setItem(row, 0, _cell(type_map.get(p.get('payment_type', 'cash'), 'نقدي'), C_TEXT_MED))
            self.purchases_table.setRowHeight(row, 42)

        self.payments_table.setRowCount(len(payments))
        for row, p in enumerate(payments):
            self.payments_table.setItem(row, 2, _cell(p['date'], C_TEXT_MED))
            self.payments_table.setItem(row, 1, _cell(f"{p['amount']:.2f}", C_PRIMARY, bold=True))
            self.payments_table.setItem(row, 0, _cell(p.get('notes', ''), C_TEXT_MED))
            self.payments_table.setRowHeight(row, 42)


class SupplierPdfRangeDialog(QDialog):
    def __init__(self, parent, supplier):
        super().__init__(parent)
        self.setWindowTitle("طباعة تقرير المورد PDF")
        self.setFixedWidth(370)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(f"""
            QDialog {{ background: #f4f7fa; font-family: Tahoma; }}
            QLabel {{ font-size: 13px; color: #1a2535; background: transparent; }}
            QDateEdit {{
                padding: 8px 12px; border: 1.5px solid #dce3ec; border-radius: 7px;
                font-size: 13px; font-family: Tahoma; background: white; color: #1a2535;
            }}
            QDateEdit:focus {{ border-color: {C_TEAL}; }}
        """)
        _light = QPalette()
        _light.setColor(QPalette.ColorRole.Window,          QColor("#f4f7fa"))
        _light.setColor(QPalette.ColorRole.WindowText,      QColor("#1a2535"))
        _light.setColor(QPalette.ColorRole.Base,            QColor("#ffffff"))
        _light.setColor(QPalette.ColorRole.Text,            QColor("#1a2535"))
        _light.setColor(QPalette.ColorRole.Button,          QColor("#f4f7fa"))
        _light.setColor(QPalette.ColorRole.ButtonText,      QColor("#1a2535"))
        _light.setColor(QPalette.ColorRole.Highlight,       QColor(C_TEAL))
        _light.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.setPalette(_light)
        self._setup_ui(supplier)

    def _setup_ui(self, supplier):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        strip = QFrame()
        strip.setFixedHeight(6)
        strip.setStyleSheet(f"background: {C_TEAL}; border-radius: 3px; border: none;")
        layout.addWidget(strip)

        title = QLabel("طباعة تقرير المورد PDF")
        title.setFont(QFont("Tahoma", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        sup_lbl = QLabel(f"المورد: {supplier['name']}")
        sup_lbl.setStyleSheet("color: #5d6d7e; font-size: 12px;")
        layout.addWidget(sup_lbl)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        style_calendar(self.date_from)
        form.addRow("من تاريخ:", self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
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
            QPushButton {{ background: {C_TEAL}; color: white; border: none;
                padding: 10px 20px; border-radius: 7px; font-size: 13px;
                font-family: Tahoma; font-weight: bold; }}
            QPushButton:hover {{ background: {C_TEAL_DARK}; }}
        """)
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


class SuppliersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._setup_ui()
        self.load_suppliers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header_frame, header_inner = page_header(
            "🏭  الموردون والشركات",
            "سجّل شركاتك وموردينك وتابع مشترياتك ومدفوعاتك معهم"
        )
        add_btn = QPushButton("＋  إضافة مورد جديد")
        add_btn.setStyleSheet(f"""
            QPushButton {{ background: {C_TEAL}; color: white; border: none;
                padding: 10px 22px; border-radius: 8px; font-size: 13px;
                font-family: Tahoma; font-weight: bold; }}
            QPushButton:hover {{ background: {C_TEAL_DARK}; }}
        """)
        add_btn.clicked.connect(self._add_supplier)
        header_inner.addWidget(add_btn)
        layout.addWidget(header_frame)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍   ابحث عن مورد أو شركة...")
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "الإجراءات", "المستحق (ج.م)", "اسم المورد", "#", "id"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 340)
        self.table.setColumnHidden(4, True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        table_inner.addWidget(self.table)
        layout.addWidget(table_frame)

    def load_suppliers(self, suppliers=None):
        if suppliers is None:
            suppliers = db.get_all_suppliers()

        self.table.setRowCount(len(suppliers))
        for row, s in enumerate(suppliers):
            self.table.setItem(row, 4, QTableWidgetItem(str(s['id'])))

            num_item = QTableWidgetItem(str(row + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            num_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 3, num_item)

            name_item = QTableWidgetItem(s['name'])
            name_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            name_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 2, name_item)

            debt = s['total_debt']
            debt_item = QTableWidgetItem(f"{debt:.2f}")
            debt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if debt > 0:
                debt_item.setForeground(QColor(C_DANGER))
                debt_item.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
            else:
                debt_item.setForeground(QColor(C_PRIMARY))
                debt_item.setText("✓ صفر")
            self.table.setItem(row, 1, debt_item)

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(5, 4, 5, 4)
            btn_l.setSpacing(5)

            history_btn = QPushButton("السجل")
            history_btn.setStyleSheet(BTN_HISTORY)
            history_btn.clicked.connect(lambda _, sid=s['id']: self._view_history(sid))

            pay_btn = QPushButton("دفعة")
            pay_btn.setStyleSheet(BTN_PAY)
            pay_btn.clicked.connect(lambda _, sid=s['id']: self._add_payment(sid))

            edit_btn = QPushButton("تعديل")
            edit_btn.setStyleSheet(BTN_EDIT)
            edit_btn.clicked.connect(lambda _, sid=s['id']: self._edit_supplier(sid))

            del_btn = QPushButton("حذف")
            del_btn.setStyleSheet(BTN_DELETE)
            del_btn.clicked.connect(lambda _, sid=s['id']: self._delete_supplier(sid))

            pdf_btn = QPushButton("🖨 طباعة")
            pdf_btn.setStyleSheet(f"""
                QPushButton {{ background: {C_TEAL}; color: white; border: none;
                    padding: 6px 10px; border-radius: 5px; font-size: 11px; font-family: Tahoma; }}
                QPushButton:hover {{ background: {C_TEAL_DARK}; }}
            """)
            pdf_btn.clicked.connect(lambda _, sid=s['id']: self._print_pdf(sid))

            btn_l.addWidget(del_btn)
            btn_l.addWidget(edit_btn)
            btn_l.addWidget(pay_btn)
            btn_l.addWidget(history_btn)
            btn_l.addWidget(pdf_btn)
            self.table.setCellWidget(row, 0, btn_w)
            self.table.setRowHeight(row, 54)

        total_debt = sum(s['total_debt'] for s in suppliers)
        self.count_label.setText(
            f"عدد الموردين: {len(suppliers)}   |   إجمالي المستحقات: {total_debt:.2f} ج.م"
        )

    def _search(self, query):
        suppliers = db.get_all_suppliers()
        if query.strip():
            q = query.strip().lower()
            suppliers = [s for s in suppliers if q in s['name'].lower()]
        self.load_suppliers(suppliers)

    def _add_supplier(self):
        dlg = SupplierDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.add_supplier(d['name'], '', '')
            self.load_suppliers()

    def _edit_supplier(self, sid):
        supplier = next((s for s in db.get_all_suppliers() if s['id'] == sid), None)
        if not supplier:
            return
        dlg = SupplierDialog(self, supplier)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.update_supplier(sid, d['name'], '', '')
            self.load_suppliers()

    def _delete_supplier(self, sid):
        if confirm_delete(self, "هل أنت متأكد من حذف هذا المورد وجميع بياناته؟"):
            db.delete_supplier(sid)
            self.load_suppliers()

    def _add_payment(self, sid):
        supplier = next((s for s in db.get_all_suppliers() if s['id'] == sid), None)
        if not supplier:
            return
        dlg = SupplierPaymentDialog(self, supplier)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            db.add_supplier_payment(sid, d['amount'], d['notes'])
            self.load_suppliers()
            show_info(self, "تم بنجاح", f"✓  تم تسجيل دفعة {d['amount']:.2f} ج.م للمورد")

    def _view_history(self, sid):
        supplier = next((s for s in db.get_all_suppliers() if s['id'] == sid), None)
        if not supplier:
            return
        SupplierHistoryDialog(self, supplier).exec()

    def _print_pdf(self, sid):
        supplier = next((s for s in db.get_all_suppliers() if s['id'] == sid), None)
        if not supplier:
            return
        dlg = SupplierPdfRangeDialog(self, supplier)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            date_from, date_to = dlg.get_dates()
            try:
                from pdf_report import generate_supplier_statement, open_pdf
                path = generate_supplier_statement(sid, date_from, date_to)
                open_pdf(path)
            except Exception as e:
                show_error(self, "خطأ", f"فشل إنشاء ملف PDF:\n{e}")
