from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt
from ui.styles import (
    DIALOG_STYLE, TABLE_STYLE, BTN_SECONDARY,
    C_TEXT_DARK, C_TEXT_MED, C_DANGER,
)

_KINDS = {
    # kind: (title, party label, party field, accent colour, summary bg, summary border)
    'sale':     ("مرتجع البيع",  "العميل", 'customer_name', "#8e44ad", "#f8f0ff", "#e3cdf2"),
    'purchase': ("مرتجع الشراء", "المورد", 'supplier_name', C_DANGER,   "#fff5f5", "#f5cccc"),
}


class ReturnDetailDialog(QDialog):
    """Full bill view of a sale return or a purchase return (same layout as the invoice dialogs)."""

    def __init__(self, ret, items, kind, parent=None):
        super().__init__(parent)
        title, party_lbl, party_field, accent, sum_bg, sum_border = _KINDS[kind]
        self.setWindowTitle(f"تفاصيل {title} # {ret['id']}")
        self.resize(700, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(DIALOG_STYLE + TABLE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ── info strip ────────────────────────────────────────────────────────
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

        ig.addWidget(_col(f"رقم {title}", f"# {ret['id']}", accent))
        ig.addWidget(_col("التاريخ", ret['date']))
        ig.addWidget(_col(party_lbl, ret.get(party_field) or '—'))
        ig.addWidget(_col("نوع", ret.get('invoice_type') or '—'))
        if ret.get('notes'):
            ig.addWidget(_col("ملاحظات", ret['notes']))
        ig.addStretch()
        layout.addWidget(info)

        # ── items table ───────────────────────────────────────────────────────
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
        centre = Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
        for r, item in enumerate(items):
            for c, (val, align) in enumerate([
                (item['product_name'],          Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                (item.get('unit_name') or '—',  centre),
                (f"{item['quantity']:.2f}",     centre),
                (f"{item['unit_price']:.2f}",   centre),
                (f"{item['total']:.2f}",        centre),
            ]):
                it = QTableWidgetItem(val)
                it.setTextAlignment(align)
                tbl.setItem(r, c, it)
            tbl.setRowHeight(r, 40)
        layout.addWidget(tbl)

        # ── total strip ───────────────────────────────────────────────────────
        summary = QFrame()
        summary.setStyleSheet(f"background:{sum_bg}; border-radius:8px; border:1px solid {sum_border};")
        sl = QHBoxLayout(summary)
        sl.setContentsMargins(16, 10, 16, 10)
        sl.setSpacing(6)
        lbl = QLabel("إجمالي المرتجع:")
        lbl.setStyleSheet(f"color: {C_TEXT_MED}; font-size: 12px;")
        val_lbl = QLabel(f"{ret['total_amount']:.2f} ج.م")
        val_lbl.setStyleSheet(f"color: {accent}; font-size: 14px; font-weight: bold; margin-left: 18px;")
        sl.addWidget(lbl)
        sl.addWidget(val_lbl)
        sl.addStretch()
        layout.addWidget(summary)

        btn_row = QHBoxLayout()
        close_btn = QPushButton("إغلاق")
        close_btn.setStyleSheet(BTN_SECONDARY)
        close_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
