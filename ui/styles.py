from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect, QMessageBox, QMenu, QSpinBox,
    QToolButton, QAbstractItemView, QCalendarWidget,
    QCompleter, QComboBox,
)
from PyQt6.QtGui import QColor, QPalette, QTextCharFormat
from PyQt6.QtCore import Qt, QObject, QEvent, QDate, QLocale

# ── Color palette ──────────────────────────────────────────────────────────────
C_SIDEBAR        = "#0f1f2e"
C_SIDEBAR_HOVER  = "#162c40"
C_SIDEBAR_ACTIVE = "#1a5c3a"
C_HEADER_BG      = "#16a085"      # teal header strip
C_PAGE_BG        = "#eef1f5"
C_WHITE          = "#ffffff"
C_CARD_BORDER    = "#dce3ec"
C_ROW_ALT        = "#f7f9fb"

C_PRIMARY        = "#27ae60"
C_PRIMARY_DARK   = "#1e8449"
C_INFO           = "#2980b9"
C_INFO_DARK      = "#2471a3"
C_DANGER         = "#e74c3c"
C_DANGER_DARK    = "#c0392b"
C_ORANGE         = "#e67e22"
C_ORANGE_DARK    = "#d35400"
C_PURPLE         = "#8e44ad"
C_PURPLE_DARK    = "#7d3c98"

C_TEXT_DARK      = "#1a2535"
C_TEXT_MED       = "#5d6d7e"
C_TEXT_LIGHT     = "#9aa5b4"

C_TBL_HEADER     = "#1a2535"


def card_shadow(widget, blur=22, y=5, alpha=28):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(y)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


# ── Sidebar ─────────────────────────────────────────────────────────────────────
SIDEBAR_STYLE = f"""
QWidget#sidebar {{
    background-color: {C_SIDEBAR};
}}
QPushButton#nav_btn {{
    background-color: transparent;
    color: #8fa8bf;
    border: none;
    border-right: 3px solid transparent;
    padding: 13px 18px;
    text-align: right;
    font-size: 13px;
    font-family: Tahoma;
    border-radius: 0;
}}
QPushButton#nav_btn:hover {{
    background-color: {C_SIDEBAR_HOVER};
    color: #cde0f0;
}}
QPushButton#nav_btn:checked {{
    background-color: {C_SIDEBAR_ACTIVE};
    color: #ffffff;
    border-right: 4px solid #2ecc71;
    font-weight: bold;
}}
"""

# ── Tables ───────────────────────────────────────────────────────────────────────
TABLE_STYLE = f"""
QTableWidget {{
    background-color: {C_WHITE};
    border: 1px solid {C_CARD_BORDER};
    border-radius: 10px;
    gridline-color: transparent;
    font-size: 13px;
    font-family: Tahoma;
    outline: none;
}}
QTableWidget::item {{
    padding: 9px 12px;
    border-bottom: 1px solid #f0f3f7;
}}
QTableWidget::item:selected {{
    background-color: #d5f5e3;
    color: {C_PRIMARY_DARK};
}}
QTableWidget::item:alternate {{
    background-color: {C_ROW_ALT};
}}
QHeaderView::section {{
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 10px 12px;
    font-size: 12px;
    font-family: Tahoma;
    font-weight: bold;
    border: none;
    border-right: 1px solid #3d5166;
}}
QHeaderView::section:last {{
    border-right: none;
}}
QScrollBar:vertical {{
    background: #f0f3f7; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #bdc3cc; border-radius: 4px; min-height: 30px;
}}
"""

# ── Buttons ───────────────────────────────────────────────────────────────────────
def _btn(bg, hover, text="#fff", padding="10px 22px", font="13px"):
    return f"""
QPushButton {{
    background-color: {bg};
    color: {text};
    border: none;
    padding: {padding};
    border-radius: 7px;
    font-size: {font};
    font-family: Tahoma;
    font-weight: bold;
}}
QPushButton:hover {{ background-color: {hover}; }}
QPushButton:pressed {{ background-color: {hover}; }}
QPushButton:disabled {{ background-color: #ced4da; color: #868e96; }}
"""

BTN_ADD      = _btn(C_PRIMARY,      C_PRIMARY_DARK)
BTN_EDIT     = _btn(C_INFO,         C_INFO_DARK,    padding="7px 15px", font="12px")
BTN_DELETE   = _btn(C_DANGER,       C_DANGER_DARK,  padding="7px 15px", font="12px")
BTN_ORANGE   = _btn(C_ORANGE,       C_ORANGE_DARK)
BTN_PURPLE   = _btn(C_PURPLE,       C_PURPLE_DARK,  padding="7px 12px", font="11px")
BTN_HISTORY  = _btn(C_PURPLE,       C_PURPLE_DARK,  padding="7px 12px", font="11px")
BTN_PAY      = _btn(C_ORANGE,       C_ORANGE_DARK,  padding="7px 12px", font="11px")
BTN_SECONDARY = _btn("#6c757d",     "#5a6268")

# ── Inputs ────────────────────────────────────────────────────────────────────────
INPUT_STYLE = f"""
QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit, QDateEdit {{
    padding: 9px 12px;
    border: 1.5px solid {C_CARD_BORDER};
    border-radius: 7px;
    font-size: 13px;
    font-family: Tahoma;
    background: {C_WHITE};
    color: {C_TEXT_DARK};
    selection-background-color: #d5f5e3;
}}
QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {C_PRIMARY};
    background: #f8fffe;
}}
QLineEdit::placeholder {{ color: {C_TEXT_LIGHT}; }}
QComboBox::drop-down {{
    border: none;
    width: 26px;
    subcontrol-origin: padding;
    subcontrol-position: left center;
    background: #eef1f5;
    border-radius: 0 5px 5px 0;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}
QDateEdit::drop-down {{
    border: none;
    width: 26px;
    subcontrol-origin: padding;
    subcontrol-position: left center;
    background: #eef1f5;
    border-radius: 0 5px 5px 0;
}}
QDateEdit::down-arrow {{
    width: 10px;
    height: 10px;
}}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    width: 22px; border: none; background: #f0f3f7; border-radius: 3px;
}}
QComboBox QAbstractItemView {{
    background: {C_WHITE};
    color: {C_TEXT_DARK};
    border: 1px solid {C_CARD_BORDER};
    border-radius: 6px;
    selection-background-color: {C_PRIMARY};
    selection-color: white;
    font-family: Tahoma;
    font-size: 13px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
    min-height: 28px;
}}
"""

# ── Dialog ────────────────────────────────────────────────────────────────────────
DIALOG_STYLE = f"""
QDialog {{
    background-color: #f4f7fa;
    font-family: Tahoma;
}}
QLabel {{
    font-size: 13px;
    color: {C_TEXT_DARK};
    font-family: Tahoma;
    background: transparent;
}}
""" + INPUT_STYLE

# ── Calendar popup helper ─────────────────────────────────────────────────────
_CALENDAR_CSS = """
    QCalendarWidget { background: white; border: 1px solid #cdd5df; }
    QCalendarWidget QAbstractItemView {
        color: black; background: white;
        alternate-background-color: #f0f3f7;
        selection-background-color: #27ae60; selection-color: white;
        font-family: Tahoma; font-size: 13px; font-weight: bold;
    }
    QCalendarWidget QAbstractItemView:disabled { color: #888888; }
    QCalendarWidget #qt_calendar_navigationbar {
        background: white; border-bottom: 1px solid #cdd5df; padding: 4px;
    }
    QCalendarWidget QToolButton {
        color: black; background: transparent; border: none;
        font-family: Tahoma; font-size: 12px; font-weight: bold; padding: 4px 8px;
    }
    QCalendarWidget QToolButton:hover { background: rgba(0,0,0,0.08); border-radius: 4px; }
    QCalendarWidget QSpinBox {
        color: black; background: white;
        border: 1px solid #cdd5df; border-radius: 3px;
        font-family: Tahoma; font-size: 12px; font-weight: bold; padding: 1px 6px;
        min-width: 46px;
    }
    QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button { width: 0; }
    QCalendarWidget QMenu { color: black; background: white; }
"""

_YEAR_MENU_CSS = (
    "QMenu { color: #1a2535; background: white; font-family: Tahoma; font-size: 12px;"
    " border: 1px solid #cdd5df; padding: 4px 0; }"
    "QMenu::item { padding: 5px 24px; }"
    "QMenu::item:selected { background: #27ae60; color: white; }"
)


def _make_nav_menu(parent):
    """Create a QMenu with an explicit light palette so Fusion dark theme doesn't make text white."""
    menu = QMenu(parent)
    menu.setStyleSheet(_YEAR_MENU_CSS)
    # Fusion draws CE_MenuItem text from palette.windowText(), not from the stylesheet
    # color rule, so we must override the palette explicitly.
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor("white"))
    pal.setColor(QPalette.ColorRole.Base,            QColor("white"))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor("#1a2535"))
    pal.setColor(QPalette.ColorRole.Text,            QColor("#1a2535"))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor("#1a2535"))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor("#27ae60"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    menu.setPalette(pal)
    return menu


class _NavFilter(QObject):
    """Single event filter that handles both the year and month nav buttons."""

    _MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                  "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

    def __init__(self, cal, year_btn, month_btn):
        super().__init__(cal)
        self._cal       = cal
        self._year_btn  = year_btn
        self._month_btn = month_btn

    def eventFilter(self, obj, event):
        if event.type() != QEvent.Type.MouseButtonPress:
            return False
        if obj is self._year_btn:
            return self._show_year_menu()
        if obj is self._month_btn:
            return self._show_month_menu()
        return False

    def _show_year_menu(self):
        cur  = self._cal.yearShown()
        menu = _make_nav_menu(self._cal)
        actions = {}
        for yr in range(2020, 2061):
            a = menu.addAction(str(yr))
            if yr == cur:
                font = a.font(); font.setBold(True); a.setFont(font)
            actions[a] = yr
        pos    = self._year_btn.mapToGlobal(self._year_btn.rect().bottomLeft())
        chosen = menu.exec(pos)
        if chosen and chosen in actions:
            self._cal.setCurrentPage(actions[chosen], self._cal.monthShown())
        return True

    def _show_month_menu(self):
        cur  = self._cal.monthShown()
        menu = _make_nav_menu(self._cal)
        actions = {}
        for i, name in enumerate(self._MONTHS_AR, 1):
            a = menu.addAction(name)
            if i == cur:
                font = a.font(); font.setBold(True); a.setFont(font)
            actions[a] = i
        pos    = self._month_btn.mapToGlobal(self._month_btn.rect().bottomLeft())
        chosen = menu.exec(pos)
        if chosen and chosen in actions:
            self._cal.setCurrentPage(self._cal.yearShown(), actions[chosen])
        return True


class _StyledCalendar(QCalendarWidget):
    """Custom QCalendarWidget — lazy format/palette fix + nav filter install."""

    _COL_WEEKDAY  = QColor("#000000")
    _COL_WEEKEND  = QColor("#000000")
    _COL_SEL_BG   = QColor("#27ae60")
    _COL_TODAY_BG = QColor("#e8f5e9")
    _COL_CELL_BG  = QColor("white")

    def showEvent(self, event):
        super().showEvent(event)
        self._reapply_light_palette()
        self._apply_text_formats()
        self._fix_view_palette()
        self._fix_nav_bar()
        self._install_nav_filter()

    def _reapply_light_palette(self):
        """Re-stamp the light palette every open in case QDateEdit reset it."""
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window,          QColor("white"))
        pal.setColor(QPalette.ColorRole.WindowText,      QColor("black"))
        pal.setColor(QPalette.ColorRole.Base,            QColor("white"))
        pal.setColor(QPalette.ColorRole.AlternateBase,   QColor("#f0f3f7"))
        pal.setColor(QPalette.ColorRole.Text,            QColor("black"))
        pal.setColor(QPalette.ColorRole.Button,          QColor("white"))
        pal.setColor(QPalette.ColorRole.ButtonText,      QColor("black"))
        pal.setColor(QPalette.ColorRole.Highlight,       QColor("#27ae60"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
        self.setPalette(pal)

    def _apply_text_formats(self):
        """setWeekdayTextFormat for all 7 days — called every show so month changes pick it up."""
        wday = QTextCharFormat()
        wday.setForeground(self._COL_WEEKDAY)
        wday.setBackground(self._COL_CELL_BG)

        wend = QTextCharFormat()
        wend.setForeground(self._COL_WEEKEND)
        wend.setBackground(self._COL_CELL_BG)

        for d in (Qt.DayOfWeek.Monday, Qt.DayOfWeek.Tuesday,
                  Qt.DayOfWeek.Wednesday, Qt.DayOfWeek.Thursday,
                  Qt.DayOfWeek.Friday):
            self.setWeekdayTextFormat(d, wday)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, wend)
        self.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, wend)

    def _fix_view_palette(self):
        """Light palette on the view AND its viewport — Fusion paints on the viewport."""
        if getattr(self, '_palette_fixed', False):
            return
        self._palette_fixed = True
        view = self.findChild(QAbstractItemView)
        if not view:
            return
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Base,            self._COL_CELL_BG)
        pal.setColor(QPalette.ColorRole.AlternateBase,   QColor("#f0f3f7"))
        pal.setColor(QPalette.ColorRole.Text,            self._COL_WEEKDAY)
        pal.setColor(QPalette.ColorRole.Window,          self._COL_CELL_BG)
        pal.setColor(QPalette.ColorRole.WindowText,      self._COL_WEEKDAY)
        pal.setColor(QPalette.ColorRole.Highlight,       self._COL_SEL_BG)
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
        view.setPalette(pal)
        view.viewport().setPalette(pal)   # Fusion draws on the viewport, not the view itself

    def _fix_nav_bar(self):
        """Force dark text + light background on nav-bar buttons via both palette and QSS."""
        if getattr(self, '_nav_bar_fixed', False):
            return
        self._nav_bar_fixed = True
        btn_pal = QPalette()
        btn_pal.setColor(QPalette.ColorRole.ButtonText, self._COL_WEEKDAY)
        btn_pal.setColor(QPalette.ColorRole.Window,     self._COL_CELL_BG)
        btn_pal.setColor(QPalette.ColorRole.Button,     self._COL_CELL_BG)
        btn_pal.setColor(QPalette.ColorRole.Text,       self._COL_WEEKDAY)
        btn_pal.setColor(QPalette.ColorRole.WindowText, self._COL_WEEKDAY)
        for btn in self.findChildren(QToolButton):
            btn.setPalette(btn_pal)
            btn.setAutoFillBackground(True)
            btn.setStyleSheet(
                "QToolButton { color: black; background: white;"
                " font-family: Tahoma; font-size: 12px; font-weight: bold;"
                " border: none; padding: 4px 8px; }"
                "QToolButton:hover { background: rgba(0,0,0,0.1); border-radius: 4px; }"
            )

    def _install_nav_filter(self):
        if getattr(self, '_nav_filter', None):
            return
        year_btn  = self.findChild(QToolButton, "qt_calendar_yearbutton")
        month_btn = self.findChild(QToolButton, "qt_calendar_monthbutton")
        if not year_btn:
            _skip = {"qt_calendar_prevmonth", "qt_calendar_nextmonth",
                     "qt_calendar_monthbutton"}
            for btn in self.findChildren(QToolButton):
                if btn.objectName() not in _skip:
                    year_btn = btn
                    break
        if year_btn and month_btn:
            f = _NavFilter(self, year_btn, month_btn)
            year_btn.installEventFilter(f)
            month_btn.installEventFilter(f)
            self._nav_filter = f


def style_calendar(date_edit):
    """Attach a _StyledCalendar to a QDateEdit for reliable cross-theme rendering."""
    ar_locale = QLocale(QLocale.Language.Arabic)
    date_edit.setLocale(ar_locale)
    cal = _StyledCalendar()
    cal.setLocale(ar_locale)
    cal.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    cal.setStyleSheet(_CALENDAR_CSS)
    cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)

    # Apply a full light palette on the calendar widget itself so every
    # child (nav bar, buttons, view, viewport) inherits white bg + black text
    # instead of the app's Fusion dark palette.
    _light = QPalette()
    _light.setColor(QPalette.ColorRole.Window,          QColor("white"))
    _light.setColor(QPalette.ColorRole.WindowText,      QColor("black"))
    _light.setColor(QPalette.ColorRole.Base,            QColor("white"))
    _light.setColor(QPalette.ColorRole.AlternateBase,   QColor("#f0f3f7"))
    _light.setColor(QPalette.ColorRole.Text,            QColor("black"))
    _light.setColor(QPalette.ColorRole.Button,          QColor("white"))
    _light.setColor(QPalette.ColorRole.ButtonText,      QColor("black"))
    _light.setColor(QPalette.ColorRole.Highlight,       QColor("#27ae60"))
    _light.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    cal.setPalette(_light)

    date_edit.setCalendarWidget(cal)


# ── Shared dialog helpers ─────────────────────────────────────────────────────
_BTN_CSS = (
    "padding: 9px 28px; border-radius: 7px; font-size: 13px; "
    "font-family: Tahoma; font-weight: bold; min-width: 90px; border: none; color: white;"
)
_DLG_CSS = """
    QMessageBox {
        background-color: #ffffff;
        font-family: Tahoma;
    }
    QMessageBox QLabel {
        color: #1a2535;
        font-size: 14px;
        font-family: Tahoma;
        background: transparent;
        min-width: 240px;
    }
"""


def _make_dlg(parent, title, message, icon):
    dlg = QMessageBox(parent)
    dlg.setWindowTitle(title)
    dlg.setText(message)
    dlg.setIcon(icon)
    dlg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    dlg.setStyleSheet(_DLG_CSS)
    return dlg


def show_info(parent, title, message):
    """Green OK button."""
    dlg = _make_dlg(parent, title, message, QMessageBox.Icon.Information)
    btn = dlg.addButton("حسناً", QMessageBox.ButtonRole.AcceptRole)
    btn.setStyleSheet(f"background: {C_PRIMARY}; " + _BTN_CSS)
    dlg.exec()


def show_warning(parent, title, message):
    """Orange OK button."""
    dlg = _make_dlg(parent, title, message, QMessageBox.Icon.Warning)
    btn = dlg.addButton("حسناً", QMessageBox.ButtonRole.AcceptRole)
    btn.setStyleSheet(f"background: {C_ORANGE}; " + _BTN_CSS)
    dlg.exec()


def show_error(parent, title, message):
    """Red OK button."""
    dlg = _make_dlg(parent, title, message, QMessageBox.Icon.Critical)
    btn = dlg.addButton("حسناً", QMessageBox.ButtonRole.AcceptRole)
    btn.setStyleSheet(f"background: {C_DANGER}; " + _BTN_CSS)
    dlg.exec()


# ── Confirm delete dialog ─────────────────────────────────────────────────────
def confirm_delete(parent, message="هل أنت متأكد من الحذف؟"):
    """Red delete / gray cancel buttons."""
    dlg = _make_dlg(parent, "تأكيد الحذف", message, QMessageBox.Icon.Question)
    dlg.setStyleSheet(dlg.styleSheet() + """
        QMessageBox {
            background-color: #ffffff;
            font-family: Tahoma;
        }
        QMessageBox QLabel {
            color: #1a2535;
            font-size: 14px;
            font-family: Tahoma;
            background: transparent;
            min-width: 220px;
        }
    """)

    _btn_css = (
        "padding: 9px 28px; border-radius: 7px; font-size: 13px; "
        "font-family: Tahoma; font-weight: bold; min-width: 90px; border: none; color: white;"
    )
    yes_btn = dlg.addButton("نعم، حذف", QMessageBox.ButtonRole.AcceptRole)
    yes_btn.setStyleSheet(f"background: {C_DANGER}; " + _btn_css)

    no_btn = dlg.addButton("إلغاء", QMessageBox.ButtonRole.RejectRole)
    no_btn.setStyleSheet("background: #6c757d; " + _btn_css)

    dlg.setDefaultButton(no_btn)
    dlg.exec()
    return dlg.clickedButton() is yes_btn


# ── Searchable combo helper ───────────────────────────────────────────────────────
def setup_searchable_combo(combo: QComboBox):
    """Attach a type-to-search completer (substring, case-insensitive) to a QComboBox."""
    if not combo.isEditable():
        combo.setEditable(True)
    combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
    completer = QCompleter(combo.model(), combo)
    completer.setFilterMode(Qt.MatchFlag.MatchContains)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    combo.setCompleter(completer)


# ── Page ─────────────────────────────────────────────────────────────────────────
PAGE_STYLE = f"""
QWidget {{
    background-color: {C_PAGE_BG};
    font-family: Tahoma;
}}
QLabel {{
    font-family: Tahoma;
    background: transparent;
}}
"""
