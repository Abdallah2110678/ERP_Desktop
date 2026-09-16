"""
Arabic PDF report generator — optimised for black & white printing.
Uses reportlab + arabic_reshaper + python-bidi for proper RTL rendering.
"""
import os
import tempfile
from pathlib import Path
from datetime import datetime

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

import arabic_reshaper
from bidi.algorithm import get_display

import database as db
from config import PHARMACY_NAME, PHARMACY_SUBTITLE

# ── Font registration ──────────────────────────────────────────────────────────
_FONTS_DIR = Path("C:/Windows/Fonts")

def _reg(name, filename):
    path = _FONTS_DIR / filename
    if path.exists():
        pdfmetrics.registerFont(TTFont(name, str(path)))
        return True
    return False

if not _reg("Ar", "tahoma.ttf"):
    _reg("Ar", "arial.ttf")
if not _reg("ArBold", "tahomabd.ttf"):
    _reg("ArBold", "arialbd.ttf")

# ── B&W colour palette ────────────────────────────────────────────────────────
BLACK      = colors.black
WHITE      = colors.white
DARK_GRAY  = colors.HexColor("#1a1a1a")
MID_GRAY   = colors.HexColor("#555555")
LIGHT_GRAY = colors.HexColor("#e8e8e8")
RULE_GRAY  = colors.HexColor("#aaaaaa")

# ── Page constants ─────────────────────────────────────────────────────────────
W, H  = A4           # 595 x 842 pt
ML    = 40           # left margin
MR    = W - ML       # right edge = 555 pt
TW    = MR - ML      # usable width = 515 pt
MT    = H - 40       # top start y
ROW_H = 22           # data row height
HDR_H = 22           # header row height

# ── Arabic helpers ─────────────────────────────────────────────────────────────
def _ar(text: str) -> str:
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

def _rtext(c, text, x, y, font="Ar", size=11):
    c.setFont(font, size);  c.setFillColor(BLACK)
    c.drawRightString(x, y, _ar(text))

def _ctext(c, text, x, y, font="Ar", size=11, color=None):
    c.setFont(font, size);  c.setFillColor(color or BLACK)
    c.drawCentredString(x, y, _ar(text))

def _ltext(c, text, x, y, font="Ar", size=11):
    c.setFont(font, size);  c.setFillColor(BLACK)
    c.drawString(x, y, _ar(text))

def _hline(c, y, x1=None, x2=None, width=0.6, dashed=False):
    c.setStrokeColor(RULE_GRAY);  c.setLineWidth(width)
    c.setDash(3, 3) if dashed else c.setDash()
    c.line(x1 if x1 is not None else ML, y,
           x2 if x2 is not None else MR, y)
    c.setDash()

def _col_xs(widths):
    xs, x = [], ML
    for w in widths:
        xs.append(x);  x += w
    return xs


# ── Page header ────────────────────────────────────────────────────────────────
def _draw_page_header(c, report_title: str, subtitle: str = "") -> float:
    c.setFillColor(DARK_GRAY)
    c.rect(0, H - 86, W, 86, fill=1, stroke=0)

    c.setFont("ArBold", 18);  c.setFillColor(WHITE)
    c.drawCentredString(W / 2, H - 34, _ar(PHARMACY_NAME))

    c.setFont("Ar", 10);  c.setFillColor(colors.HexColor("#cccccc"))
    c.drawCentredString(W / 2, H - 52, _ar(PHARMACY_SUBTITLE))

    c.setStrokeColor(WHITE);  c.setLineWidth(0.5)
    c.line(ML, H - 60, MR, H - 60)

    c.setFont("ArBold", 12);  c.setFillColor(WHITE)
    c.drawCentredString(W / 2, H - 74, _ar(report_title))

    y = H - 96
    if subtitle:
        c.setFont("Ar", 9);  c.setFillColor(MID_GRAY)
        c.drawCentredString(W / 2, y, _ar(subtitle))
        y -= 14
    _hline(c, y, width=1.2)
    return y - 14


# ── Table header row ───────────────────────────────────────────────────────────
def _draw_table_header(c, y, headers, col_xs, col_widths):
    """Black background, white bold text. Returns y position after the row."""
    top = y + 4
    bot = y + 4 - HDR_H
    c.setFillColor(DARK_GRAY)
    c.rect(ML, bot, TW, HDR_H, fill=1, stroke=0)

    c.setFillColor(WHITE)
    for (text, align), cx, cw in zip(headers, col_xs, col_widths):
        c.setFont("ArBold", 9)
        text_y = bot + 6
        if align == "r":
            c.drawRightString(cx + cw - 5, text_y, _ar(text))
        elif align == "c":
            c.drawCentredString(cx + cw / 2, text_y, _ar(text))
        else:
            c.drawString(cx + 5, text_y, _ar(text))

    # Vertical column separators
    c.setStrokeColor(colors.HexColor("#555555"));  c.setLineWidth(0.4)
    x = ML
    for cw in col_widths[:-1]:
        x += cw
        c.line(x, bot, x, top)

    return y - HDR_H - 2


# ── Data row ──────────────────────────────────────────────────────────────────
def _draw_row(c, y, row_data, col_xs, col_widths,
              shaded=False, bold_cols=None, size=9.5):
    bold_cols = bold_cols or set()
    top = y + 4
    bot = y + 4 - ROW_H
    text_y = bot + 6

    if shaded:
        c.setFillColor(LIGHT_GRAY)
        c.rect(ML, bot, TW, ROW_H, fill=1, stroke=0)

    # Outer border
    c.setStrokeColor(RULE_GRAY);  c.setLineWidth(0.5)
    c.rect(ML, bot, TW, ROW_H, fill=0, stroke=1)

    c.setFillColor(BLACK)
    for i, ((text, align), cx, cw) in enumerate(zip(row_data, col_xs, col_widths)):
        font = "ArBold" if i in bold_cols else "Ar"
        c.setFont(font, size)
        if align == "r":
            c.drawRightString(cx + cw - 5, text_y, _ar(text))
        elif align == "c":
            c.drawCentredString(cx + cw / 2, text_y, _ar(text))
        else:
            c.drawString(cx + 5, text_y, _ar(text))

    # Vertical column separators
    c.setStrokeColor(RULE_GRAY);  c.setLineWidth(0.4)
    x = ML
    for cw in col_widths[:-1]:
        x += cw
        c.line(x, bot, x, top)


# ── Page footer ───────────────────────────────────────────────────────────────
def _draw_footer(c, label: str):
    _hline(c, 36, width=0.6)
    c.setFont("Ar", 8);  c.setFillColor(MID_GRAY)
    c.drawCentredString(W / 2, 24,
        _ar(f"{PHARMACY_NAME}  —  {label}  —  {datetime.now().strftime('%Y-%m-%d')}"))


def _maybe_new_page(c, y, threshold, footer_label, hdr_fn=None):
    if y < threshold:
        _draw_footer(c, footer_label)
        c.showPage()
        y = MT
        if hdr_fn:
            y = hdr_fn(c)
    return y


PAY_MAP_AR = {'cash': 'نقدي', 'credit': 'آجل', 'partial': 'جزئي'}


def _draw_return_block(c, y, ret_date, items, total_amount, footer_label):
    """Draw one return block: items table with date column → total footer."""
    ICW  = [75, 85, 55, 50, 85, 165]   # Σ = 515
    ICX  = _col_xs(ICW)
    IHDR = [("الاجمالي ج.م", "c"), ("سعر الوحدة", "c"),
            ("الكمية", "c"), ("الوحدة", "c"),
            ("التاريخ", "c"), ("اسم الصنف", "r")]
    y = _draw_table_header(c, y, IHDR, ICX, ICW)

    if items:
        for i, it in enumerate(items):
            y = _maybe_new_page(c, y, 80, footer_label)
            row = [
                (f"{it['total']:.2f}",               "c"),
                (f"{it['unit_price']:.2f}",           "c"),
                (f"{it['quantity']:.2f}",             "c"),
                (str(it.get('unit_name', '') or ''),  "c"),
                (str(ret_date),                       "c"),
                (str(it.get('product_name', '')),     "r"),
            ]
            _draw_row(c, y, row, ICX, ICW, shaded=(i % 2 == 0), size=9)
            y -= ROW_H
    else:
        row = [("—", "c"), ("—", "c"), ("—", "c"), ("—", "c"),
               (str(ret_date), "c"), ("لا توجد أصناف", "r")]
        _draw_row(c, y, row, ICX, ICW, shaded=True, size=9)
        y -= ROW_H

    y = _maybe_new_page(c, y, 50, footer_label)
    SFTR_H = 20
    c.setFillColor(colors.HexColor("#d5d8dc"))
    c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.6)
    c.rect(ML, y + 4 - SFTR_H, TW, SFTR_H, fill=1, stroke=1)
    c.setFillColor(BLACK);  c.setFont("ArBold", 9)
    c.drawRightString(MR - 8, y + 4 - SFTR_H + 6,
                      _ar(f"اجمالي المرتجع: {total_amount:.2f} ج.م"))
    y -= SFTR_H + 8
    return y


def _draw_invoice_block(c, y, inv_date, items, total_amount, paid_amount,
                        remaining, pay_type, footer_label):
    """
    Draw one invoice block: items table (name|date|unit|qty|price|total)
    → summary footer row. Returns updated y.
    """
    # ── items table ───────────────────────────────────────────────────────────
    # cols L→R: الإجمالي | سعر الوحدة | الكمية | الوحدة | التاريخ | اسم الصنف
    ICW  = [75, 85, 55, 50, 85, 165]   # Σ = 515
    ICX  = _col_xs(ICW)
    IHDR = [("الاجمالي ج.م", "c"), ("سعر الوحدة", "c"),
            ("الكمية", "c"), ("الوحدة", "c"),
            ("التاريخ", "c"), ("اسم الصنف", "r")]
    y = _draw_table_header(c, y, IHDR, ICX, ICW)

    if items:
        for i, it in enumerate(items):
            y = _maybe_new_page(c, y, 80, footer_label)
            row = [
                (f"{it['total']:.2f}",               "c"),
                (f"{it['unit_price']:.2f}",           "c"),
                (f"{it['quantity']:.2f}",             "c"),
                (str(it.get('unit_name', '') or ''),  "c"),
                (str(inv_date),                       "c"),
                (str(it.get('product_name', '')),     "r"),
            ]
            _draw_row(c, y, row, ICX, ICW, shaded=(i % 2 == 0), size=9)
            y -= ROW_H
    else:
        row = [("—", "c"), ("—", "c"), ("—", "c"), ("—", "c"),
               (str(inv_date), "c"), ("لا توجد أصناف", "r")]
        _draw_row(c, y, row, ICX, ICW, shaded=True, size=9)
        y -= ROW_H

    # ── summary footer ────────────────────────────────────────────────────────
    y = _maybe_new_page(c, y, 50, footer_label)
    SFTR_H = 20
    c.setFillColor(colors.HexColor("#d5d8dc"))
    c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.6)
    c.rect(ML, y + 4 - SFTR_H, TW, SFTR_H, fill=1, stroke=1)
    rem_text = f"{remaining:.2f} *" if remaining > 0 else f"{remaining:.2f}"
    text_y = y + 4 - SFTR_H + 6
    c.setFillColor(BLACK)
    c.setFont("ArBold", 9)
    c.drawRightString(MR - 8,   text_y, _ar(f"الاجمالي: {total_amount:.2f} ج.م"))
    c.setFont("Ar", 9)
    c.drawCentredString(ML + 310, text_y, _ar(f"المدفوع: {paid_amount:.2f} ج.م"))
    c.drawCentredString(ML + 180, text_y, _ar(f"المتبقي: {rem_text} ج.م"))
    c.drawString(ML + 8,        text_y, _ar(PAY_MAP_AR.get(pay_type or 'cash', '')))

    y -= SFTR_H + 8
    return y


# =============================================================================
# 1.  Customer statement
# =============================================================================
def generate_customer_statement(customer_id: int, date_from: str, date_to: str) -> str:
    customers = db.get_all_customers()
    customer  = next((cu for cu in customers if cu['id'] == customer_id), None)
    if not customer:
        raise ValueError("العميل غير موجود")

    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    sales = [dict(r) for r in conn.execute(
        "SELECT * FROM sales WHERE customer_id=? AND date BETWEEN ? AND ? ORDER BY date",
        (customer_id, date_from, date_to)).fetchall()]
    payments = [dict(r) for r in conn.execute(
        "SELECT * FROM payments WHERE customer_id=? AND date BETWEEN ? AND ? ORDER BY date",
        (customer_id, date_from, date_to)).fetchall()]
    conn.close()

    total_sales    = sum(s['total_amount'] for s in sales)
    total_paid     = sum(s['paid_amount']  for s in sales)
    total_payments = sum(p['amount']       for p in payments)
    remaining_debt = max(0.0, total_sales - total_paid - total_payments)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        prefix=f"statement_{customer['name'].replace(' ', '_')}_",
        delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    subtitle = (f"الفترة: {date_from}  الى  {date_to}"
                f"   |   طبع: {datetime.now().strftime('%Y-%m-%d')}")
    y = _draw_page_header(c, "كشف حساب عميل", subtitle)

    # Customer info box
    box_h = 50
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _rtext(c, f"الاسم :  {customer['name']}",              MR - 8, y - 14, "ArBold", 11)
    _rtext(c, f"الهاتف :  {customer.get('phone') or '—'}", MR - 8, y - 30, "Ar",     10)
    _ltext(c, f"الرصيد الكلي :  {remaining_debt:.2f} ج.م", ML + 8, y - 14, "ArBold", 11)
    y -= box_h + 16

    # Sales — one invoice block per sale
    if sales:
        _rtext(c, "فواتير البيع", MR, y, "ArBold", 12)
        y -= 8;  _hline(c, y, width=0.8);  y -= 10

        for s in sales:
            y = _maybe_new_page(c, y, 120, "كشف حساب عميل")
            sale_items = db.get_sale_items(s['id'])
            y = _draw_invoice_block(c, y, s['date'], sale_items,
                                    s['total_amount'], s['paid_amount'],
                                    s['remaining'], s['payment_type'],
                                    "كشف حساب عميل")

        _rtext(c,
               f"اجمالي الفواتير: {total_sales:.2f}    |    اجمالي المدفوع: {total_paid:.2f}  ج.م",
               MR, y, "ArBold", 10)
        y -= 22

    # Payments table
    if payments:
        _rtext(c, "سجل المدفوعات", MR, y, "ArBold", 12)
        y -= 8;  _hline(c, y, width=0.8);  y -= 14

        PCW  = [295, 115, 105]   # ملاحظات | المبلغ | التاريخ  = 515
        PCX  = _col_xs(PCW)
        PHDR = [("ملاحظات", "r"), ("المبلغ ج.م", "c"), ("التاريخ", "c")]
        y = _draw_table_header(c, y, PHDR, PCX, PCW)

        for i, p in enumerate(payments):
            prow = [
                (p.get('notes', ''), "r"),
                (f"{p['amount']:.2f}", "c"),
                (p['date'], "c"),
            ]
            _draw_row(c, y, prow, PCX, PCW, shaded=(i % 2 == 0), bold_cols={1})
            y -= ROW_H
            y = _maybe_new_page(c, y, 90, "كشف حساب عميل")

        y -= 4
        _rtext(c, f"اجمالي المدفوعات في الفترة: {total_payments:.2f} ج.م",
               MR, y, "ArBold", 10)
        y -= 22

    # Summary box
    y = _maybe_new_page(c, y, 145, "كشف حساب عميل")
    y -= 8;  _hline(c, y, width=1.2);  y -= 14

    sum_h = 68
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - sum_h, TW, sum_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _ctext(c, "ملخص الحساب", W / 2, y - 14, "ArBold", 13)
    _rtext(c, f"اجمالي الفواتير في الفترة :             {total_sales:.2f} ج.م",
           MR - 10, y - 30, "Ar", 10.5)
    _rtext(c, f"اجمالي المدفوعات في الفترة :           {total_payments:.2f} ج.م",
           MR - 10, y - 46, "Ar", 10.5)
    _rtext(c, f"الرصيد الكلي المتبقي على العميل :   {remaining_debt:.2f} ج.م",
           MR - 10, y - 62, "ArBold", 11)

    c.setFont("Ar", 8);  c.setFillColor(MID_GRAY)
    c.drawString(ML + 4, y - sum_h - 12,
                 _ar("* القيم المعلمة بـ (*) تشير الى مبالغ متبقية غير مدفوعة"))

    _draw_footer(c, "كشف حساب عميل")
    c.save()
    return tmp.name


# =============================================================================
# 2.  Customer account (matches the حساب العميل page: 4-section layout)
# =============================================================================
def generate_customer_account(customer_id: int, date_from: str, date_to: str) -> str:
    customers = db.get_all_customers()
    customer  = next((cu for cu in customers if cu['id'] == customer_id), None)
    if not customer:
        return None

    data     = db.get_customer_account(customer_id, date_from, date_to)
    sales    = data['sales']
    returns  = data['returns']
    payments = data['payments']

    vet_sales     = [s for s in sales   if s.get('invoice_type', 'بيطري') == 'بيطري']
    feed_sales    = [s for s in sales   if s.get('invoice_type', 'بيطري') == 'أعلاف']
    other_sales   = [s for s in sales   if s.get('invoice_type', 'بيطري') in ('نثريات', 'أخرى')]
    vet_returns   = [r for r in returns if r.get('invoice_type', 'بيطري') == 'بيطري']
    feed_returns  = [r for r in returns if r.get('invoice_type', 'بيطري') == 'أعلاف']
    other_returns = [r for r in returns if r.get('invoice_type', 'بيطري') in ('نثريات', 'أخرى')]

    total_sales    = sum(s['total_amount'] for s in sales)
    total_returns  = sum(r['total_amount'] for r in returns)
    total_payments = sum(p['amount'] for p in payments)
    owed           = max(0.0, total_sales - total_returns - total_payments)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        prefix=f"account_{customer['name'].replace(' ', '_')}_",
        delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    subtitle = (f"الفترة: {date_from}  الى  {date_to}"
                f"   |   طبع: {datetime.now().strftime('%Y-%m-%d')}")
    y = _draw_page_header(c, "كشف حساب العميل", subtitle)

    # Customer info box
    box_h = 36
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _rtext(c, f"العميل :  {customer['name']}", MR - 8, y - 14, "ArBold", 11)
    _ltext(c, f"المستحق في الفترة :  {owed:.2f} ج.م", ML + 8, y - 14, "ArBold", 11)
    y -= box_h + 14

    def _sales_section(title, items):
        nonlocal y
        if not items:
            return
        _rtext(c, title, MR, y, "ArBold", 11)
        y -= 6;  _hline(c, y, width=0.7);  y -= 10
        for s in items:
            y = _maybe_new_page(c, y, 120, "كشف حساب العميل")
            sale_items = db.get_sale_items(s['id'])
            y = _draw_invoice_block(c, y, s['date'], sale_items,
                                    s['total_amount'], s.get('paid_amount', 0),
                                    s.get('remaining', 0), s.get('payment_type', 'cash'),
                                    "كشف حساب العميل")
        y -= 6

    def _returns_section(title, items):
        nonlocal y
        if not items:
            return
        _rtext(c, title, MR, y, "ArBold", 11)
        y -= 6;  _hline(c, y, width=0.7);  y -= 10
        for r in items:
            y = _maybe_new_page(c, y, 120, "كشف حساب العميل")
            return_items = db.get_sale_return_items(r['id'])
            y = _draw_return_block(c, y, r['date'], return_items,
                                   r['total_amount'], "كشف حساب العميل")
        y -= 6

    _sales_section("مبيعات بيطري", vet_sales)
    _sales_section("مبيعات أعلاف", feed_sales)
    _sales_section("مبيعات نثريات", other_sales)
    _returns_section("مرتجعات بيطري", vet_returns)
    _returns_section("مرتجعات أعلاف", feed_returns)
    _returns_section("مرتجعات نثريات", other_returns)

    # Payments table
    if payments:
        _rtext(c, "الدفعات", MR, y, "ArBold", 11)
        y -= 6;  _hline(c, y, width=0.7);  y -= 12

        PCW  = [295, 115, 105]
        PCX  = _col_xs(PCW)
        PHDR = [("ملاحظات", "r"), ("المبلغ ج.م", "c"), ("التاريخ", "c")]
        y = _draw_table_header(c, y, PHDR, PCX, PCW)
        for i, p in enumerate(payments):
            prow = [
                (p.get('notes', '') or '', "r"),
                (f"{p['amount']:.2f}", "c"),
                (p['date'], "c"),
            ]
            _draw_row(c, y, prow, PCX, PCW, shaded=(i % 2 == 0), bold_cols={1})
            y -= ROW_H
            y = _maybe_new_page(c, y, 90, "كشف حساب العميل")
        y -= 6

    # Summary box
    y = _maybe_new_page(c, y, 120, "كشف حساب العميل")
    y -= 8;  _hline(c, y, width=1.2);  y -= 14
    sum_h = 82
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - sum_h, TW, sum_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _ctext(c, "ملخص الحساب", W / 2, y - 14, "ArBold", 13)
    _rtext(c, f"اجمالي المبيعات :          {total_sales:.2f} ج.م",  MR - 10, y - 30, "Ar", 10.5)
    _rtext(c, f"اجمالي المرتجعات :         {total_returns:.2f} ج.م", MR - 10, y - 46, "Ar", 10.5)
    _rtext(c, f"اجمالي الدفعات :              {total_payments:.2f} ج.م", MR - 10, y - 62, "Ar", 10.5)
    _rtext(c, f"الرصيد (عليه) :               {owed:.2f} ج.م",       MR - 10, y - 78, "ArBold", 11)

    _draw_footer(c, "كشف حساب العميل")
    c.save()
    return tmp.name


# =============================================================================
# 3.  Low-stock report
# =============================================================================
def generate_low_stock_report(products: list, threshold: int = 10) -> str:
    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf", prefix="low_stock_report_", delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    subtitle = (f"الحد الادنى: {threshold} وحدة   |   "
                f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}")
    y = _draw_page_header(c, "تقرير المنتجات ذات المخزون المنخفض", subtitle)

    critical = [p for p in products if p['quantity'] <= 5]
    low      = [p for p in products if 5 < p['quantity'] <= threshold]

    box_h = 50
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.6)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _rtext(c, f"اجمالي المنتجات المنخفضة:  {len(products)} منتج",          MR - 8, y - 14, "ArBold", 11)
    _rtext(c, f"(!)  حرج — اقل من 5 وحدات:  {len(critical)} منتج",         MR - 8, y - 30, "ArBold", 10)
    _rtext(c, f"(v)  منخفض — من 5 الى {threshold} وحدة:  {len(low)} منتج", MR - 8, y - 46, "Ar",     10)
    y -= box_h + 16

    if not products:
        _ctext(c, "لا توجد منتجات ذات مخزون منخفض حاليا", W / 2, y - 20, "ArBold", 12)
        _draw_footer(c, "تقرير المخزون المنخفض")
        c.save()
        return tmp.name

    # Columns L→R: الحالة | سعر البيع | سعر الشراء | الكمية | الوحدة | اسم الدواء
    CW  = [72, 82, 82, 72, 57, 150]   # = 515
    CX  = _col_xs(CW)
    HDR = [("الحالة", "c"), ("سعر البيع ج.م", "c"), ("سعر الشراء ج.م", "c"),
           ("الكمية", "c"), ("الوحدة", "c"), ("اسم الدواء", "r")]

    def _rehdr(cv):
        return _draw_table_header(cv, MT - 10, HDR, CX, CW) - 2

    y = _draw_table_header(c, y, HDR, CX, CW)

    for i, p in enumerate(products):
        is_crit = p['quantity'] <= 5
        status  = "(!) حرج" if is_crit else "(v) منخفض"
        row = [
            (status,                       "c"),
            (f"{p['selling_price']:.2f}",  "c"),
            (f"{p['purchase_price']:.2f}", "c"),
            (f"{p['quantity']:.2f}",       "c"),
            (p['unit'],                    "c"),
            (p['name'],                    "r"),
        ]
        bold = {0, 3, 5} if is_crit else {0}
        _draw_row(c, y, row, CX, CW, shaded=(i % 2 == 0), bold_cols=bold)
        y -= ROW_H
        y = _maybe_new_page(c, y, 80, "تقرير المخزون المنخفض", _rehdr)

    y -= 10
    _hline(c, y, width=0.5, dashed=True);  y -= 14
    c.setFont("Ar", 8.5);  c.setFillColor(MID_GRAY)
    c.drawString(ML, y,
                 _ar(f"(!) حرج: الكمية اقل من 5     (v) منخفض: الكمية بين 5 و {threshold} وحدة"))

    _draw_footer(c, "تقرير المخزون المنخفض")
    c.save()
    return tmp.name


# =============================================================================
# 3.  Full inventory report
# =============================================================================
def generate_inventory_report(products: list) -> str:
    from datetime import date as _dt
    CRIT = 10   # matches notification_bar.CRIT_THRESHOLD
    LOW  = 30   # matches notification_bar.LOW_THRESHOLD

    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf", prefix="inventory_report_", delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    subtitle = (f"اجمالي الادوية: {len(products)}   |   "
                f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}")
    y = _draw_page_header(c, "تقرير المخزون الكامل", subtitle)

    low_count  = sum(1 for p in products if CRIT < p['quantity'] <= LOW)
    crit_count = sum(1 for p in products if p['quantity'] <= CRIT)
    total_val  = sum(p['quantity'] * p['purchase_price'] for p in products)

    # fetch nearest expiry per product
    expiry_map = db.get_product_nearest_expiries()
    today_str  = _dt.today().strftime('%Y-%m-%d')

    box_h = 50
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.6)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _rtext(c, f"اجمالي قيمة المخزون (بسعر الشراء):  {total_val:.2f} ج.م",       MR - 8, y - 14, "ArBold", 11)
    _rtext(c, f"(!)  منتجات حرجة (اقل من {CRIT} وحدات):  {crit_count}",          MR - 8, y - 30, "ArBold", 10)
    _rtext(c, f"(v)  منتجات منخفضة ({CRIT} الى {LOW} وحدات):  {low_count}",      MR - 8, y - 46, "Ar",     10)
    y -= box_h + 16

    # Columns L→R: سعر البيع | سعر الشراء | الكمية | الوحدة | أقرب تاريخ انتهاء | اسم الدواء
    CW  = [80, 80, 75, 65, 100, 115]   # Σ = 515
    CX  = _col_xs(CW)
    HDR = [("سعر البيع", "c"), ("سعر الشراء", "c"),
           ("الكمية", "c"), ("الوحدة", "c"),
           ("تاريخ الانتهاء", "c"), ("اسم الدواء", "r")]

    def _rehdr(cv):
        return _draw_table_header(cv, MT - 10, HDR, CX, CW) - 2

    y = _draw_table_header(c, y, HDR, CX, CW)

    for i, p in enumerate(products):
        is_crit = p['quantity'] <= CRIT
        is_low  = CRIT < p['quantity'] <= LOW

        qty_lbl = (f"(!){p['quantity']:.2f}" if is_crit
                   else f"(v){p['quantity']:.2f}" if is_low
                   else f"{p['quantity']:.2f}")

        exp = expiry_map.get(p['id'])
        if exp:
            exp_lbl = f"* {exp}" if exp < today_str else exp
        else:
            exp_lbl = "—"

        row = [
            (f"{p['selling_price']:.2f}",  "c"),
            (f"{p['purchase_price']:.2f}", "c"),
            (qty_lbl,                      "c"),
            (p['unit'],                    "c"),
            (exp_lbl,                      "c"),
            (p['name'],                    "r"),
        ]
        bold = {2, 5} if is_crit else ({2} if is_low else {5})
        _draw_row(c, y, row, CX, CW, shaded=(i % 2 == 0), bold_cols=bold)
        y -= ROW_H
        y = _maybe_new_page(c, y, 80, "تقرير المخزون الكامل", _rehdr)

    y -= 10
    _hline(c, y, width=0.5, dashed=True);  y -= 14
    c.setFont("Ar", 8.5);  c.setFillColor(MID_GRAY)
    c.drawString(ML, y, _ar(
        f"(!) حرج: اقل من {CRIT} وحدات     "
        f"(v) منخفض: من {CRIT} الى {LOW} وحدات     "
        f"* تاريخ منتهي الصلاحية"))

    _draw_footer(c, "تقرير المخزون الكامل")
    c.save()
    return tmp.name


# =============================================================================
# 4.  Supplier statement
# =============================================================================
def generate_supplier_statement(supplier_id: int, date_from: str, date_to: str) -> str:
    suppliers = db.get_all_suppliers()
    supplier  = next((s for s in suppliers if s['id'] == supplier_id), None)
    if not supplier:
        raise ValueError("المورد غير موجود")

    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    purchases = [dict(r) for r in conn.execute(
        "SELECT * FROM purchases WHERE supplier_id=? AND date BETWEEN ? AND ? ORDER BY date",
        (supplier_id, date_from, date_to)).fetchall()]
    payments = [dict(r) for r in conn.execute(
        "SELECT * FROM supplier_payments WHERE supplier_id=? AND date BETWEEN ? AND ? ORDER BY date",
        (supplier_id, date_from, date_to)).fetchall()]
    conn.close()

    total_purchases  = sum(p['total_amount'] for p in purchases)
    total_paid_inv   = sum(p.get('paid_amount') or 0 for p in purchases)
    total_payments   = sum(p['amount'] for p in payments)
    remaining_debt   = max(0.0, total_purchases - total_paid_inv - total_payments)

    from datetime import date as _date, timedelta as _td
    today_str = _date.today().isoformat()
    due_invoices = [
        p for p in purchases
        if p.get('payment_due_date') and
           max(0.0, p['total_amount'] - (p.get('paid_amount') or 0)) > 0
    ]
    total_due_amount = sum(
        max(0.0, p['total_amount'] - (p.get('paid_amount') or 0))
        for p in due_invoices
    )

    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        prefix=f"supplier_{supplier['name'].replace(' ', '_')}_",
        delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    subtitle = (f"الفترة: {date_from}  الى  {date_to}"
                f"   |   طبع: {datetime.now().strftime('%Y-%m-%d')}")
    y = _draw_page_header(c, "كشف حساب مورد", subtitle)

    # Supplier info box
    box_h = 50
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _rtext(c, f"الاسم :  {supplier['name']}",               MR - 8, y - 14, "ArBold", 11)
    _rtext(c, f"الهاتف :  {supplier.get('phone') or '—'}",  MR - 8, y - 30, "Ar",     10)
    _ltext(c, f"المستحق في الفترة :  {remaining_debt:.2f} ج.م", ML + 8, y - 14, "ArBold", 11)
    y -= box_h + 16

    # Purchases — one invoice block per purchase
    if purchases:
        _rtext(c, "فواتير الشراء", MR, y, "ArBold", 12)
        y -= 8;  _hline(c, y, width=0.8);  y -= 10

        for p in purchases:
            y = _maybe_new_page(c, y, 120, "كشف حساب مورد")
            paid_amt = p.get('paid_amount') or 0
            rem = max(0.0, p['total_amount'] - paid_amt)
            purchase_items = db.get_purchase_items(p['id'])
            y = _draw_invoice_block(c, y, p['date'], purchase_items,
                                    p['total_amount'], paid_amt, rem,
                                    p.get('payment_type', 'cash'),
                                    "كشف حساب مورد")
            if p.get('payment_due_date') and rem > 0:
                due = p['payment_due_date']
                label = f"  تاريخ السداد: {due}"
                if due < today_str:
                    label += "  *** متأخر ***"
                _rtext(c, label, MR, y, "ArBold", 9)
                y -= 14

        _rtext(c,
               f"اجمالي الفواتير: {total_purchases:.2f}    |    اجمالي المدفوع: {total_paid_inv:.2f}  ج.م",
               MR, y, "ArBold", 10)
        y -= 22

    # Due payments section
    if due_invoices:
        y = _maybe_new_page(c, y, 100, "كشف حساب مورد")
        _rtext(c, "المبالغ المستحقة بتواريخ السداد", MR, y, "ArBold", 12)
        y -= 8;  _hline(c, y, width=0.8);  y -= 14

        DCW  = [200, 120, 105]
        DCX  = _col_xs(DCW)
        DHDR = [("المتبقي ج.م", "c"), ("تاريخ السداد", "c"), ("رقم الفاتورة", "c")]
        y = _draw_table_header(c, y, DHDR, DCX, DCW)

        for i, p in enumerate(sorted(due_invoices, key=lambda x: x.get('payment_due_date', ''))):
            rem = max(0.0, p['total_amount'] - (p.get('paid_amount') or 0))
            due = p['payment_due_date']
            status = "متأخر" if due < today_str else due
            drow = [
                (f"{rem:.2f}", "c"),
                (status, "c"),
                (f"# {p['id']}", "c"),
            ]
            _draw_row(c, y, drow, DCX, DCW, shaded=(i % 2 == 0), bold_cols={0})
            y -= ROW_H
            y = _maybe_new_page(c, y, 90, "كشف حساب مورد")

        y -= 4
        _rtext(c, f"اجمالي المستحق بتواريخ السداد: {total_due_amount:.2f} ج.م",
               MR, y, "ArBold", 10)
        y -= 22

    # Payments table
    if payments:
        _rtext(c, "سجل المدفوعات للمورد", MR, y, "ArBold", 12)
        y -= 8;  _hline(c, y, width=0.8);  y -= 14

        PCW  = [295, 115, 105]
        PCX  = _col_xs(PCW)
        PHDR = [("ملاحظات", "r"), ("المبلغ ج.م", "c"), ("التاريخ", "c")]
        y = _draw_table_header(c, y, PHDR, PCX, PCW)

        for i, p in enumerate(payments):
            prow = [
                (p.get('notes', ''), "r"),
                (f"{p['amount']:.2f}", "c"),
                (p['date'], "c"),
            ]
            _draw_row(c, y, prow, PCX, PCW, shaded=(i % 2 == 0), bold_cols={1})
            y -= ROW_H
            y = _maybe_new_page(c, y, 90, "كشف حساب مورد")

        y -= 4
        _rtext(c, f"اجمالي المدفوعات في الفترة: {total_payments:.2f} ج.م",
               MR, y, "ArBold", 10)
        y -= 22

    # Summary box
    y = _maybe_new_page(c, y, 145, "كشف حساب مورد")
    y -= 8;  _hline(c, y, width=1.2);  y -= 14

    sum_h = 84 if due_invoices else 68
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - sum_h, TW, sum_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _ctext(c, "ملخص حساب المورد", W / 2, y - 14, "ArBold", 13)
    _rtext(c, f"اجمالي فواتير الشراء في الفترة :     {total_purchases:.2f} ج.م",
           MR - 10, y - 30, "Ar", 10.5)
    _rtext(c, f"اجمالي المدفوعات في الفترة :           {total_payments:.2f} ج.م",
           MR - 10, y - 46, "Ar", 10.5)
    _rtext(c, f"المستحق الكلي للمورد :                    {remaining_debt:.2f} ج.م",
           MR - 10, y - 62, "ArBold", 11)
    if due_invoices:
        _rtext(c, f"اجمالي المبالغ المستحقة بتواريخ السداد :  {total_due_amount:.2f} ج.م",
               MR - 10, y - 78, "ArBold", 11)

    c.setFont("Ar", 8);  c.setFillColor(MID_GRAY)
    c.drawString(ML + 4, y - sum_h - 12,
                 _ar("* القيم المعلمة بـ (*) تشير الى مبالغ متبقية غير مدفوعة"))

    _draw_footer(c, "كشف حساب مورد")
    c.save()
    return tmp.name


# =============================================================================
# 5.  Product report
# =============================================================================
def generate_product_report(product_id: int, date_from: str, date_to: str) -> str:
    from datetime import date as _dt, timedelta

    data = db.get_product_report(product_id, date_from, date_to)
    if not data:
        return None

    product          = data['product']
    purchases        = data['purchases']
    sales            = data['sales']
    sale_returns     = data['sale_returns']
    purchase_returns = data['purchase_returns']
    batches          = data['batches']

    today_str = _dt.today().strftime('%Y-%m-%d')
    warn_str  = (_dt.today() + timedelta(days=90)).strftime('%Y-%m-%d')

    total_purch_qty  = sum(r['quantity'] for r in purchases)
    total_purch_cost = sum(r['total']    for r in purchases)
    total_sales_qty  = sum(r['quantity'] for r in sales)
    total_sales_rev  = sum(r['total']    for r in sales)
    total_sr_qty     = sum(r['quantity'] for r in sale_returns)
    total_pr_qty     = sum(r['quantity'] for r in purchase_returns)
    net_profit       = total_sales_rev - (total_sales_qty * product['purchase_price'])

    safe_name = product['name'].replace(' ', '_')[:20]
    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf", prefix=f"product_{safe_name}_", delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    FOOTER = "تقرير الصنف"
    subtitle = (f"الفترة: {date_from}  الى  {date_to}"
                f"   |   طبع: {datetime.now().strftime('%Y-%m-%d')}")
    y = _draw_page_header(c, f"تقرير الصنف: {product['name']}", subtitle)

    # ── Product info box ──────────────────────────────────────────────────────
    box_h = 64
    c.setFillColor(LIGHT_GRAY); c.setStrokeColor(DARK_GRAY); c.setLineWidth(0.8)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _rtext(c, f"اسم الصنف:  {product['name']}", MR - 8, y - 14, "ArBold", 11)
    _rtext(c, f"النوع:  {product.get('product_type', '—')}   |   الوحدة:  {product['unit']}", MR - 8, y - 30, "Ar", 10)
    _rtext(c, f"سعر الشراء:  {product['purchase_price']:.2f} ج.م   |   سعر البيع:  {product['selling_price']:.2f} ج.م", MR - 8, y - 46, "Ar", 10)
    unit = product.get('unit') or 'وحدة'
    _ltext(c, f"الكمية الحالية:  {product['quantity']:.2f} {unit}", ML + 8, y - 14, "ArBold", 11)
    y -= box_h + 16

    # ── Shared columns for purchases / sales / returns ────────────────────────
    TXW = [70, 75, 55, 50, 120, 145]   # total | price | qty | unit | name | date  Σ=515
    TXX = _col_xs(TXW)

    def _transaction_section(title, items, name_hdr, name_key):
        nonlocal y
        _rtext(c, title, MR, y, "ArBold", 12)
        y -= 8;  _hline(c, y, width=0.8);  y -= 10
        HDR = [("الإجمالي ج.م", "c"), ("سعر الوحدة", "c"), ("الكمية", "c"),
               ("الوحدة", "c"), (name_hdr, "c"), ("التاريخ", "c")]
        y = _draw_table_header(c, y, HDR, TXX, TXW)
        if items:
            for i, it in enumerate(items):
                y = _maybe_new_page(c, y, 80, FOOTER)
                row = [
                    (f"{it['total']:.2f}",                 "c"),
                    (f"{it['unit_price']:.2f}",            "c"),
                    (f"{it['quantity']:.2f}",              "c"),
                    (str(it.get('unit_name', '') or ''),   "c"),
                    (str(it.get(name_key, '')  or ''),     "c"),
                    (str(it['date']),                      "c"),
                ]
                _draw_row(c, y, row, TXX, TXW, shaded=(i % 2 == 0), size=9)
                y -= ROW_H
        else:
            empty = [("—", "c")] * 6
            _draw_row(c, y, empty, TXX, TXW, shaded=True, size=9)
            y -= ROW_H
        y -= 10

    _transaction_section("المشتريات",       purchases,        "المورد",  "supplier_name")
    y = _maybe_new_page(c, y, 120, FOOTER)
    _transaction_section("المبيعات",        sales,            "العميل",  "customer_name")

    if sale_returns:
        y = _maybe_new_page(c, y, 120, FOOTER)
        _transaction_section("مرتجعات البيع",   sale_returns,     "العميل",  "customer_name")

    if purchase_returns:
        y = _maybe_new_page(c, y, 120, FOOTER)
        _transaction_section("مرتجعات الشراء",  purchase_returns, "المورد",  "supplier_name")

    # ── Active batches ────────────────────────────────────────────────────────
    if batches:
        y = _maybe_new_page(c, y, 120, FOOTER)
        _rtext(c, "الدفعات الحالية في المخزون", MR, y, "ArBold", 12)
        y -= 8;  _hline(c, y, width=0.8);  y -= 10

        BCW  = [130, 95, 95, 195]   # expiry | price | qty | purchase_date  Σ=515
        BCX  = _col_xs(BCW)
        BHDR = [("تاريخ الانتهاء", "c"), ("سعر الشراء ج.م", "c"),
                ("الكمية المتبقية", "c"), ("تاريخ الشراء", "c")]
        y = _draw_table_header(c, y, BHDR, BCX, BCW)

        for i, b in enumerate(batches):
            y = _maybe_new_page(c, y, 80, FOOTER)
            exp = b.get('expiry_date')
            if exp:
                exp_lbl = f"* {exp}" if exp < today_str else exp
            else:
                exp_lbl = "—"
            row = [
                (exp_lbl,                                    "c"),
                (f"{b['purchase_price']:.2f}",               "c"),
                (f"{b['quantity']:.2f}",                     "c"),
                (str(b.get('purchase_date', '') or '—'),     "c"),
            ]
            _draw_row(c, y, row, BCX, BCW, shaded=(i % 2 == 0), size=9)
            y -= ROW_H
        y -= 8

    # ── Summary box ───────────────────────────────────────────────────────────
    y = _maybe_new_page(c, y, 170, FOOTER)
    y -= 8;  _hline(c, y, width=1.2);  y -= 14

    sum_h = 148
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - sum_h, TW, sum_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _ctext(c, "ملخص الصنف", W / 2, y - 14, "ArBold", 13)
    unit = product.get('unit') or 'وحدة'
    _rtext(c, f"إجمالي الكمية المشتراة (في الفترة):    {total_purch_qty:.2f} {unit}",  MR - 10, y - 30,  "Ar", 10)
    _rtext(c, f"إجمالي تكلفة المشتريات:                 {total_purch_cost:.2f} ج.م", MR - 10, y - 46,  "Ar", 10)
    _rtext(c, f"إجمالي الكمية المباعة (في الفترة):      {total_sales_qty:.2f} {unit}",  MR - 10, y - 62,  "Ar", 10)
    _rtext(c, f"إجمالي إيرادات المبيعات:                {total_sales_rev:.2f} ج.م",  MR - 10, y - 78,  "Ar", 10)
    _rtext(c, f"مرتجعات البيع (الكمية):                 {total_sr_qty:.2f} {unit}",    MR - 10, y - 94,  "Ar", 10)
    _rtext(c, f"مرتجعات الشراء (الكمية):                {total_pr_qty:.2f} {unit}",    MR - 10, y - 110, "Ar", 10)
    _rtext(c, f"الكمية الحالية في المخزون:              {product['quantity']:.2f} {unit}", MR - 10, y - 126, "ArBold", 11)
    _rtext(c, f"الربح التقديري:                          {net_profit:.2f} ج.م",       MR - 10, y - 142, "ArBold", 11)

    c.setFont("Ar", 8);  c.setFillColor(MID_GRAY)
    notes = []
    if batches:
        notes.append("* تاريخ انتهاء الصلاحية المعلم بـ (*) منتهٍ بالفعل")
    notes.append("الربح التقديري محسوب على أساس سعر الشراء الحالي")
    c.drawString(ML + 4, y - sum_h - 12, _ar("   |   ".join(notes)))

    _draw_footer(c, FOOTER)
    c.save()
    return tmp.name


# =============================================================================
# 6.  Single sale invoice
# =============================================================================
def generate_sale_invoice(sale_id: int) -> str:
    sale  = db.get_sale(sale_id)
    if not sale:
        return None
    items = db.get_sale_items(sale_id)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf", prefix=f"sale_invoice_{sale_id}_", delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    subtitle = f"فاتورة رقم  # {sale_id}   —   {sale['date']}"
    y = _draw_page_header(c, "فاتورة بيع", subtitle)

    # Info box
    box_h = 52
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    _rtext(c, f"العميل :  {sale['customer_name']}", MR - 8, y - 14, "ArBold", 11)
    pay_ar = PAY_MAP_AR.get(sale.get('payment_type', ''), '—')
    inv_type = sale.get('invoice_type', '—') or '—'
    _ltext(c, f"نوع الفاتورة :  {inv_type}   |   طريقة الدفع :  {pay_ar}", ML + 8, y - 14, "Ar", 10)
    _rtext(c, f"الإجمالي :  {sale['total_amount']:.2f} ج.م   |   المدفوع :  {sale.get('paid_amount', 0):.2f} ج.م   |   المتبقي :  {sale.get('remaining', 0):.2f} ج.م",
           MR - 8, y - 30, "Ar", 10)
    if sale.get('notes'):
        _rtext(c, f"ملاحظات :  {sale['notes']}", MR - 8, y - 46, "Ar", 9.5)
    y -= box_h + 14

    y = _draw_invoice_block(c, y, sale['date'], items,
                            sale['total_amount'], sale.get('paid_amount', 0),
                            sale.get('remaining', 0), sale.get('payment_type', 'cash'),
                            "فاتورة بيع")

    _draw_footer(c, "فاتورة بيع")
    c.save()
    return tmp.name


# =============================================================================
# 7.  Single purchase invoice
# =============================================================================
def generate_purchase_invoice(purchase_id: int) -> str:
    purchase = db.get_purchase(purchase_id)
    if not purchase:
        return None
    items = db.get_purchase_items(purchase_id)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".pdf", prefix=f"purchase_invoice_{purchase_id}_", delete=False)
    tmp.close()
    c = rl_canvas.Canvas(tmp.name, pagesize=A4)

    subtitle = f"فاتورة رقم  # {purchase_id}   —   {purchase['date']}"
    y = _draw_page_header(c, "فاتورة شراء", subtitle)

    # Info box
    box_h = 52
    c.setFillColor(LIGHT_GRAY);  c.setStrokeColor(DARK_GRAY);  c.setLineWidth(0.8)
    c.rect(ML, y - box_h, TW, box_h, fill=1, stroke=1)
    c.setFillColor(BLACK)
    supplier = purchase.get('supplier') or '—'
    _rtext(c, f"المورد :  {supplier}", MR - 8, y - 14, "ArBold", 11)
    pay_ar   = PAY_MAP_AR.get(purchase.get('payment_type', ''), '—')
    inv_type = purchase.get('invoice_type', '—') or '—'
    _ltext(c, f"نوع الفاتورة :  {inv_type}   |   طريقة الدفع :  {pay_ar}", ML + 8, y - 14, "Ar", 10)
    paid      = purchase.get('paid_amount') or 0
    remaining = max(0.0, purchase['total_amount'] - paid)
    _rtext(c, f"الإجمالي :  {purchase['total_amount']:.2f} ج.م   |   المدفوع :  {paid:.2f} ج.م   |   المتبقي :  {remaining:.2f} ج.م",
           MR - 8, y - 30, "Ar", 10)
    due = purchase.get('payment_due_date')
    if due:
        _ltext(c, f"تاريخ السداد :  {due}", ML + 8, y - 30, "Ar", 10)
    if purchase.get('notes'):
        _rtext(c, f"ملاحظات :  {purchase['notes']}", MR - 8, y - 46, "Ar", 9.5)
    y -= box_h + 14

    pay_type = purchase.get('payment_type', 'cash')
    y = _draw_invoice_block(c, y, purchase['date'], items,
                            purchase['total_amount'], paid, remaining,
                            pay_type, "فاتورة شراء")

    _draw_footer(c, "فاتورة شراء")
    c.save()
    return tmp.name


# ── Open PDF ──────────────────────────────────────────────────────────────────
def open_pdf(path: str):
    os.startfile(path)
