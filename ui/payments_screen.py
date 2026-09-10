from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDoubleSpinBox,
    QHeaderView, QComboBox, QFrame, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
import database as db
from ui.styles import (
    TABLE_STYLE, BTN_ADD, BTN_DELETE, BTN_SECONDARY,
    PAGE_STYLE, INPUT_STYLE, card_shadow,
    show_info, show_warning, confirm_delete, style_calendar,
    C_TEXT_DARK, C_TEXT_MED, C_PRIMARY, C_DANGER, C_ORANGE,
)
from ui.products import page_header


class PaymentsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(PAGE_STYLE + TABLE_STYLE)
        self._entity_list = []
        self._setup_ui()
        self._load_entities()
        self.load_payments()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        header_frame, _ = page_header("💳  الدفعات", "سجّل وتابع مدفوعات العملاء والموردين")
        layout.addWidget(header_frame)

        # Entry form
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: white; border-radius: 12px; border: 1px solid #dce3ec; }")
        card_shadow(form_frame)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(18, 14, 18, 14)
        form_layout.setSpacing(10)

        # Row 1: entity selector + type badge
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        # RTL: label first = rightmost
        entity_lbl = QLabel("👤  العميل / المورد:")
        entity_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 12px; font-weight: bold;")
        entity_lbl.setFixedWidth(130)

        self.entity_combo = QComboBox()
        self.entity_combo.setMinimumWidth(240)
        self.entity_combo.setStyleSheet(INPUT_STYLE)
        self.entity_combo.currentIndexChanged.connect(self._on_entity_changed)

        self.entity_badge = QLabel()
        self.entity_badge.setFixedWidth(50)
        self.entity_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.entity_badge.setStyleSheet("font-size: 12px; font-weight: bold; border-radius: 6px; padding: 4px 8px;")
        self.entity_badge.hide()

        row1.addWidget(entity_lbl)
        row1.addWidget(self.entity_combo)
        row1.addWidget(self.entity_badge)
        row1.addStretch()

        # Balance chips
        self.balance_against_lbl = QLabel("عليه: 0.00 ج.م")
        self.balance_against_lbl.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        self.balance_against_lbl.setStyleSheet(
            f"color: {C_DANGER}; background: #fff0f0; border-radius: 8px; padding: 4px 12px;"
        )

        self.balance_for_lbl = QLabel("له: 0.00 ج.م")
        self.balance_for_lbl.setFont(QFont("Tahoma", 12, QFont.Weight.Bold))
        self.balance_for_lbl.setStyleSheet(
            f"color: {C_PRIMARY}; background: #f0fff8; border-radius: 8px; padding: 4px 12px;"
        )

        row1.addWidget(self.balance_against_lbl)
        row1.addSpacing(8)
        row1.addWidget(self.balance_for_lbl)
        form_layout.addLayout(row1)

        # Row 2: date + amount + notes
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        # RTL: label first = rightmost
        date_lbl = QLabel("📅  التاريخ:")
        date_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 12px; font-weight: bold;")
        date_lbl.setFixedWidth(80)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setStyleSheet(INPUT_STYLE)
        self.date_edit.setFixedWidth(155)
        style_calendar(self.date_edit)

        amount_lbl = QLabel("💰  المبلغ:")
        amount_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 12px; font-weight: bold;")
        amount_lbl.setFixedWidth(70)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 9999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSuffix(" ج.م")
        self.amount_spin.setStyleSheet(INPUT_STYLE)
        self.amount_spin.setFixedWidth(160)

        notes_lbl = QLabel("ملاحظات:")
        notes_lbl.setStyleSheet(f"color: {C_TEXT_DARK}; font-size: 12px; font-weight: bold;")
        notes_lbl.setFixedWidth(65)
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات (اختياري)")
        self.notes_input.setStyleSheet(INPUT_STYLE)

        row2.addWidget(date_lbl)
        row2.addWidget(self.date_edit)
        row2.addSpacing(12)
        row2.addWidget(amount_lbl)
        row2.addWidget(self.amount_spin)
        row2.addSpacing(12)
        row2.addWidget(notes_lbl)
        row2.addWidget(self.notes_input)
        form_layout.addLayout(row2)

        # Row 3: buttons
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        add_btn = QPushButton("➕  إضافة دفعة")
        add_btn.setStyleSheet(BTN_ADD)
        add_btn.clicked.connect(self._add_payment)

        show_all_btn = QPushButton("عرض الكل")
        show_all_btn.setStyleSheet(BTN_SECONDARY)
        show_all_btn.clicked.connect(self.load_payments)

        row3.addWidget(add_btn)
        row3.addWidget(show_all_btn)
        row3.addStretch()
        form_layout.addLayout(row3)

        layout.addWidget(form_frame)

        # Payments table
        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { background: white; border-radius: 12px; border: 1px solid #dce3ec; }")
        card_shadow(table_frame)
        tl = QVBoxLayout(table_frame)
        tl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "حذف", "النوع", "القيمة (ج.م)", "التاريخ", "ملاحظات", "العميل / المورد"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 65)
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

    def _load_entities(self):
        customers = db.get_all_customers()
        suppliers = db.get_all_suppliers()
        self._entity_list = []

        self.entity_combo.blockSignals(True)
        self.entity_combo.clear()
        self.entity_combo.addItem("-- اختر عميل أو مورد --", None)

        for c in customers:
            self._entity_list.append({'id': c['id'], 'name': c['name'], 'type': 'customer', 'debt': c['total_debt']})
            self.entity_combo.addItem(f"👤 {c['name']}", ('customer', c['id']))

        for s in suppliers:
            self._entity_list.append({'id': s['id'], 'name': s['name'], 'type': 'supplier', 'debt': s['total_debt']})
            self.entity_combo.addItem(f"🏭 {s['name']}", ('supplier', s['id']))

        self.entity_combo.blockSignals(False)

    def _on_entity_changed(self, index):
        data = self.entity_combo.currentData()
        if not data:
            self.entity_badge.hide()
            self.balance_against_lbl.setText("عليه: 0.00 ج.م")
            self.balance_for_lbl.setText("له: 0.00 ج.م")
            self.balance_against_lbl.setStyleSheet(
                f"color: {C_DANGER}; background: #fff0f0; border-radius: 8px; padding: 4px 12px;"
            )
            self.balance_for_lbl.setStyleSheet(
                f"color: {C_PRIMARY}; background: #f0fff8; border-radius: 8px; padding: 4px 12px;"
            )
            return

        etype, eid = data
        entity = next((e for e in self._entity_list if e['id'] == eid and e['type'] == etype), None)
        if not entity:
            return

        debt = entity['debt']
        self.entity_badge.show()
        if etype == 'customer':
            self.entity_badge.setText("عميل")
            self.entity_badge.setStyleSheet(
                "color: white; background: #8e44ad; border-radius: 6px; padding: 4px 8px; font-size: 11px; font-weight: bold;"
            )
            self.balance_against_lbl.setText(f"عليه: {debt:.2f} ج.م")
            self.balance_against_lbl.setStyleSheet(
                f"color: {C_DANGER}; background: #fff0f0; border-radius: 8px; padding: 4px 12px; font-size: 13px; font-weight: bold;"
            )
            self.balance_for_lbl.setText("له: 0.00 ج.م")
            self.balance_for_lbl.setStyleSheet(
                f"color: {C_TEXT_MED}; background: #f5f5f5; border-radius: 8px; padding: 4px 12px; font-size: 13px; font-weight: bold;"
            )
        else:
            self.entity_badge.setText("مورد")
            self.entity_badge.setStyleSheet(
                "color: white; background: #16a085; border-radius: 6px; padding: 4px 8px; font-size: 11px; font-weight: bold;"
            )
            self.balance_against_lbl.setText("عليه: 0.00 ج.م")
            self.balance_against_lbl.setStyleSheet(
                f"color: {C_TEXT_MED}; background: #f5f5f5; border-radius: 8px; padding: 4px 12px; font-size: 13px; font-weight: bold;"
            )
            self.balance_for_lbl.setText(f"له: {debt:.2f} ج.م")
            self.balance_for_lbl.setStyleSheet(
                f"color: {C_PRIMARY}; background: #f0fff8; border-radius: 8px; padding: 4px 12px; font-size: 13px; font-weight: bold;"
            )

    def _add_payment(self):
        data = self.entity_combo.currentData()
        if not data:
            show_warning(self, "خطأ", "يرجى اختيار عميل أو مورد")
            return
        amount = self.amount_spin.value()
        if amount <= 0:
            show_warning(self, "خطأ", "يرجى إدخال مبلغ أكبر من صفر")
            return

        etype, eid = data
        notes = self.notes_input.text().strip()
        date = self.date_edit.date().toString("yyyy-MM-dd")

        if etype == 'customer':
            db.add_payment(eid, amount, notes, date)
        else:
            db.add_supplier_payment(eid, amount, notes, date)

        entity = next((e for e in self._entity_list if e['id'] == eid and e['type'] == etype), None)
        name = entity['name'] if entity else ""
        show_info(self, "تم", f"✓ تم تسجيل دفعة {amount:.2f} ج.م لـ {name}")

        self.amount_spin.setValue(0)
        self.notes_input.clear()
        self._load_entities()
        # Restore selection
        self.entity_combo.setCurrentIndex(0)
        self.load_payments()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_entities()

    def load_payments(self):
        payments = db.get_all_payments_combined()
        self.table.setRowCount(len(payments))

        for row, p in enumerate(payments):
            name_item = QTableWidgetItem(p.get('entity_name', ''))
            name_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            name_item.setForeground(QColor(C_TEXT_DARK))
            self.table.setItem(row, 5, name_item)

            notes_item = QTableWidgetItem(p.get('notes', '') or '')
            notes_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 4, notes_item)

            date_item = QTableWidgetItem(p['date'])
            date_item.setForeground(QColor(C_TEXT_MED))
            self.table.setItem(row, 3, date_item)

            amount_item = QTableWidgetItem(f"{p['amount']:.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            amount_item.setForeground(QColor(C_PRIMARY))
            amount_item.setFont(QFont("Tahoma", 11, QFont.Weight.Bold))
            self.table.setItem(row, 2, amount_item)

            etype_label = "عميل" if p['entity_type'] == 'customer' else "مورد"
            type_item = QTableWidgetItem(etype_label)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            type_item.setForeground(QColor("#8e44ad" if p['entity_type'] == 'customer' else "#16a085"))
            self.table.setItem(row, 1, type_item)

            del_btn = QPushButton("🗑")
            del_btn.setStyleSheet(f"background: {C_DANGER}; color: white; border: none; border-radius: 4px; font-size: 14px;")
            pid = p['id']
            ptype = p['entity_type']
            del_btn.clicked.connect(lambda _, i=pid, t=ptype: self._delete_payment(i, t))
            self.table.setCellWidget(row, 0, del_btn)
            self.table.setRowHeight(row, 44)

        total = sum(p['amount'] for p in payments)
        self.count_label.setText(
            f"عدد الدفعات: {len(payments)}   |   إجمالي المدفوعات: {total:.2f} ج.م"
        )

    def _delete_payment(self, pid, ptype):
        if confirm_delete(self, "هل أنت متأكد من حذف هذه الدفعة؟"):
            if ptype == 'customer':
                db.delete_payment(pid)
            else:
                db.delete_supplier_payment(pid)
            self._load_entities()
            self.load_payments()
