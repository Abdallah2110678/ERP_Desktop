"""
Generates the application icon in memory using QPainter — a cute cartoon chicken.
No external image files required — call get_app_icon() and pass to setWindowIcon().
"""
from PyQt6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QPolygon, QIcon
from PyQt6.QtCore import Qt, QPoint, QRect


def _draw_icon(size: int) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    s  = size
    cx = s // 2

    # ── Sky-blue rounded background ───────────────────────────────────────────
    pad = max(1, s // 20)
    r   = s // 5
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("#e8f4fc")))
    p.drawRoundedRect(pad, pad, s - 2 * pad, s - 2 * pad, r, r)

    # ── Scale helper: all coords as fractions of s ────────────────────────────
    def f(v): return int(v * s)

    # ── Body (fat yellow ellipse, lower-centre) ───────────────────────────────
    bx = f(0.18); by = f(0.46)
    bw = f(0.64); bh = f(0.38)
    p.setBrush(QBrush(QColor("#f5c542")))
    p.setPen(QPen(QColor("#c8952a"), max(1, s // 48)))
    p.drawEllipse(bx, by, bw, bh)

    # ── Left wing (darker teardrop, behind body) ──────────────────────────────
    p.setBrush(QBrush(QColor("#e0a f00".replace(" ", ""))))   # fallback colour
    p.setBrush(QBrush(QColor("#e8b030")))
    p.setPen(QPen(QColor("#c8952a"), max(1, s // 48)))
    wing_pts = QPolygon([
        QPoint(f(0.14), f(0.52)),
        QPoint(f(0.04), f(0.62)),
        QPoint(f(0.06), f(0.78)),
        QPoint(f(0.20), f(0.72)),
        QPoint(f(0.22), f(0.58)),
    ])
    p.drawPolygon(wing_pts)

    # ── Right wing ────────────────────────────────────────────────────────────
    wing_pts2 = QPolygon([
        QPoint(f(0.86), f(0.52)),
        QPoint(f(0.96), f(0.62)),
        QPoint(f(0.94), f(0.78)),
        QPoint(f(0.80), f(0.72)),
        QPoint(f(0.78), f(0.58)),
    ])
    p.drawPolygon(wing_pts2)

    # ── Body again on top of wings ────────────────────────────────────────────
    p.setBrush(QBrush(QColor("#f5c542")))
    p.setPen(QPen(QColor("#c8952a"), max(1, s // 48)))
    p.drawEllipse(bx, by, bw, bh)

    # ── Tail feathers (fan of rounded rects, back-right) ─────────────────────
    p.setBrush(QBrush(QColor("#e8b030")))
    tail_pts = QPolygon([
        QPoint(f(0.70), f(0.50)),
        QPoint(f(0.90), f(0.30)),
        QPoint(f(0.95), f(0.38)),
        QPoint(f(0.80), f(0.56)),
    ])
    p.drawPolygon(tail_pts)
    tail_pts2 = QPolygon([
        QPoint(f(0.68), f(0.52)),
        QPoint(f(0.94), f(0.46)),
        QPoint(f(0.96), f(0.55)),
        QPoint(f(0.76), f(0.60)),
    ])
    p.drawPolygon(tail_pts2)

    # ── Head (round yellow circle) ────────────────────────────────────────────
    hr = f(0.20)
    hx = cx - hr
    hy = f(0.10)
    p.setBrush(QBrush(QColor("#f5c542")))
    p.setPen(QPen(QColor("#c8952a"), max(1, s // 48)))
    p.drawEllipse(hx, hy, hr * 2, hr * 2)

    # ── Comb (three red bumps on top of head) ────────────────────────────────
    comb_r = max(2, f(0.07))
    p.setBrush(QBrush(QColor("#e74c3c")))
    p.setPen(QPen(QColor("#c0392b"), max(1, s // 60)))
    for dx in (-f(0.07), 0, f(0.07)):
        p.drawEllipse(QPoint(cx + dx, hy - comb_r // 2), comb_r, comb_r)

    # ── Wattle (red teardrop under beak) ─────────────────────────────────────
    p.setBrush(QBrush(QColor("#e74c3c")))
    p.setPen(Qt.PenStyle.NoPen)
    wr = max(2, f(0.05))
    p.drawEllipse(QPoint(cx + f(0.16), hy + hr + f(0.04)), wr, int(wr * 1.4))

    # ── Beak (small orange triangle) ─────────────────────────────────────────
    p.setBrush(QBrush(QColor("#e67e22")))
    p.setPen(QPen(QColor("#d35400"), max(1, s // 60)))
    beak = QPolygon([
        QPoint(cx + hr - f(0.02), hy + hr - f(0.04)),
        QPoint(cx + hr + f(0.16), hy + hr + f(0.02)),
        QPoint(cx + hr - f(0.02), hy + hr + f(0.08)),
    ])
    p.drawPolygon(beak)

    # ── Eye (white + black pupil) ─────────────────────────────────────────────
    er = max(2, f(0.055))
    ex = cx + f(0.08)
    ey = hy + f(0.08)
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPoint(ex, ey), er, er)
    p.setBrush(QBrush(QColor("#1a1a2e")))
    p.drawEllipse(QPoint(ex + max(1, er // 4), ey), max(1, er // 2), max(1, er // 2))

    # ── Legs & feet ───────────────────────────────────────────────────────────
    leg_w  = max(2, s // 28)
    leg_col = QColor("#e67e22")
    p.setPen(QPen(leg_col, leg_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    # left leg
    p.drawLine(QPoint(cx - f(0.10), f(0.82)), QPoint(cx - f(0.10), f(0.92)))
    # right leg
    p.drawLine(QPoint(cx + f(0.10), f(0.82)), QPoint(cx + f(0.10), f(0.92)))

    # toes (three lines per foot)
    toe_w = max(1, s // 40)
    p.setPen(QPen(leg_col, toe_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for foot_x in (cx - f(0.10), cx + f(0.10)):
        foot_y = f(0.92)
        p.drawLine(QPoint(foot_x, foot_y), QPoint(foot_x - f(0.10), foot_y + f(0.06)))
        p.drawLine(QPoint(foot_x, foot_y), QPoint(foot_x,            foot_y + f(0.07)))
        p.drawLine(QPoint(foot_x, foot_y), QPoint(foot_x + f(0.10), foot_y + f(0.06)))

    p.end()
    return pix


def get_app_icon() -> QIcon:
    """Return a QIcon built from multiple sizes for crisp rendering at any scale."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_draw_icon(size))
    return icon
