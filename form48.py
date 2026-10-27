"""form48.py - CSC Form No. 48 on blank 8.5x11 portrait paper, one or two copies side by side."""
import calendar
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

COLS = [.38, .72, .72, .72, .72, .52, .52, .70, 2.30]      # Day, AM in/out, PM in/out, UT h/m, OT, Remarks (inches @ full width)
ROW = 0.198 * inch


def fmt(m, pm=False):
    if m is None:
        return ""
    h, mm = divmod(m, 60)
    return f"{h - 12 if pm and h > 12 else h}:{mm:02d}"


def hhmm(m):
    return f"{m // 60}:{m % 60:02d}" if m else ""


def new_canvas(path):
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle("Daily Time Record - CSC Form No. 48")
    return c


def draw_dtr(c, name, year, month, days, office_label, sched_label, in_charge="", note="", sig_emp=None, sig_inc=None, id_no="", division="",
             x0=0.6 * inch, w=7.3 * inch):
    k = w / (7.3 * inch)
    fs = lambda n: max(4.8, n * (0.55 + 0.45 * k))
    XS = [x0]
    for cw in COLS:
        XS.append(XS[-1] + cw * inch * k)
    mid = x0 + w / 2

    def txt(x, y, s, size=8, font="Helvetica", align="l", maxw=None):
        c.setFont(font, fs(size))
        while maxw and len(s) > 1 and stringWidth(s, font, fs(size)) > maxw:
            s = s[:-1]
        {"l": c.drawString, "c": c.drawCentredString, "r": c.drawRightString}[align](x, y, s)

    y = letter[1] - 0.5 * inch
    txt(x0, y, "Civil Service Form No. 48", 8); txt(x0 + w, y, office_label, 8, align="r")
    y -= 0.25 * inch; txt(mid, y, "DAILY TIME RECORD", 15, "Helvetica-Bold", "c")
    y -= 0.15 * inch; txt(mid, y, "-----o0o-----", 8, align="c")
    y -= 0.3 * inch; txt(mid, y + 3, name, 11, "Helvetica-Bold", "c", w - 0.4 * inch * k)
    c.line(x0 + 0.5 * inch * k, y, x0 + w - 0.5 * inch * k, y); txt(mid, y - 9, "(Name)", 7.5, align="c")
    if division:
        txt(x0 + 2, y - 9, division, 6.5, maxw=w * 0.33)
    if id_no:
        txt(x0 + w, y - 9, f"ID No. {id_no}", 7, align="r")
    y -= 0.28 * inch; txt(x0 + 0.1 * inch, y, "For the month of", 9)
    txt(x0 + w * 0.5, y, f"{calendar.month_name[month].upper()} {year}", 10, "Helvetica-Bold", "c")
    c.line(x0 + w * 0.3, y - 2, x0 + w - 0.1 * inch, y - 2)
    y -= 0.19 * inch; txt(x0 + 0.1 * inch, y, "Official hours for arrival and departure:", 7.5)
    y -= 0.11 * inch; txt(x0 + 0.1 * inch, y, sched_label, 7.5, maxw=w - 0.2 * inch)
    y -= 0.11 * inch

    top, hh = y, ROW * 1.9
    c.setLineWidth(0.8); c.rect(x0, top - hh, w, hh); c.setLineWidth(0.5)
    txt((XS[0] + XS[1]) / 2, top - hh / 2 - 3, "Day", 8, "Helvetica-Bold", "c")
    for a, b, t in ((1, 3, "A.M."), (3, 5, "P.M."), (5, 7, "Undertime")):
        txt((XS[a] + XS[b]) / 2, top - ROW * .62, t, 8, "Helvetica-Bold", "c")
    txt((XS[7] + XS[8]) / 2, top - hh / 2 - 3, "Overtime", 5.6, "Helvetica-Bold", "c")
    txt((XS[8] + XS[9]) / 2, top - hh / 2 - 3, "Remarks", 8, "Helvetica-Bold", "c")
    for i, t in enumerate(("Arrival", "Departure", "Arrival", "Departure", "Hours", "Minutes"), start=1):
        txt((XS[i] + XS[i + 1]) / 2, top - hh + 4, t, 6.2, align="c")
    for i in (1, 3, 5, 7, 8):
        c.line(XS[i], top - hh, XS[i], top)
    for i in (2, 4, 6):
        c.line(XS[i], top - hh, XS[i], top - ROW)
    c.line(XS[1], top - ROW, XS[7], top - ROW)

    ry, tot_ut, tot_ot = top - hh, 0, 0
    by_day, nd = {d.day: d for d in days}, calendar.monthrange(year, month)[1]
    for dd in range(1, 32):
        d = by_day.get(dd)
        sp = list(d.spans) if d else []
        if d and not sp and not d.present and d.kind in ("saturday", "sunday", "holiday", "absent", "remark"):
            lab = {"saturday": "SATURDAY", "sunday": "SUNDAY", "holiday": "HOLIDAY", "absent": "ABSENT"}.get(d.kind) \
                or (d.notes[0].upper() if d.notes else "")
            sp = [(0, 3, lab)]
        cov = {i for a, b, t in sp for i in range(a, b + 1)}
        inner = {i for a, b, t in sp for i in range(a + 2, b + 2)}        # cell borders hidden inside merged cells
        if d:
            fills = dict(d.fill)
            if d.kind in ("saturday", "sunday", "holiday") and not d.present:
                for i in range(4):
                    fills.setdefault(i, "#eeeeee")
            for ci, col in fills.items():
                c.setFillColor(HexColor(col)); c.rect(XS[ci + 1], ry - ROW, XS[ci + 2] - XS[ci + 1], ROW, fill=1, stroke=0)
            c.setFillGray(0)
        c.rect(x0, ry - ROW, w, ROW)
        for i in range(1, 9):
            if i not in inner:
                c.line(XS[i], ry - ROW, XS[i], ry)
        base = ry - ROW + 5
        txt((XS[0] + XS[1]) / 2, base, str(dd) if dd <= nd else "", 8, align="c")
        if d:
            for i, (v, pm) in enumerate(((d.am_arr, 0), (d.am_dep, 0), (d.pm_arr, 1), (d.pm_dep, 1))):
                if i not in cov:
                    txt((XS[i + 1] + XS[i + 2]) / 2, base, fmt(v, pm), 8, align="c")
            for a, b, t in sp:
                txt((XS[a + 1] + XS[b + 2]) / 2, base, t, 7.5, "Helvetica-Bold", "c", XS[b + 2] - XS[a + 1] - 4)
            if d.ut:
                txt((XS[5] + XS[6]) / 2, base, str(d.ut // 60) if d.ut >= 60 else "", 8, align="c")
                txt((XS[6] + XS[7]) / 2, base, str(d.ut % 60) if d.ut % 60 else "", 8, align="c")
            txt((XS[7] + XS[8]) / 2, base, hhmm(d.ot), 7.5, align="c")
            txt(XS[8] + 2, base, "; ".join(d.notes) if d.present or d.kind != "remark" or d.spans else "", 6.8, maxw=XS[9] - XS[8] - 3)
            tot_ut += d.ut; tot_ot += d.ot
        ry -= ROW
    th = ROW * 1.1
    c.rect(x0, ry - th, w, th)
    for i in (5, 6, 7, 8):
        c.line(XS[i], ry - th, XS[i], ry)
    txt(x0 + 4, ry - ROW * .75, "TOTAL", 8.5, "Helvetica-Bold")
    txt((XS[5] + XS[6]) / 2, ry - ROW * .75, str(tot_ut // 60), 8.5, "Helvetica-Bold", "c")
    txt((XS[6] + XS[7]) / 2, ry - ROW * .75, str(tot_ut % 60), 8.5, "Helvetica-Bold", "c")
    txt((XS[7] + XS[8]) / 2, ry - ROW * .75, hhmm(tot_ot) or "0:00", 7.5, "Helvetica-Bold", "c")
    ry -= th
    nh = 0.34 * inch                                   # monthly note box
    c.rect(x0, ry - nh, w, nh); txt(x0 + 3, ry - 8, "MONTHLY NOTE:", 6.5, "Helvetica-Bold")
    words, line, ly = (note or "").split(), "", ry - 17
    for wd in words:
        if stringWidth(line + " " + wd, "Helvetica", fs(7)) > w - 8 and line:
            txt(x0 + 3, ly, line.strip(), 7); line, ly = "", ly - 8
        line += " " + wd
    if line:
        txt(x0 + 3, ly, line.strip(), 7)
    ry -= nh + 0.15 * inch
    txt(x0, ry, "I CERTIFY on my honor that the above is a true and correct report of the hours of work performed,", 7.5, maxw=w)
    txt(x0, ry - 10, "record of which was made daily at the time of arrival at and departure from office.", 7.5, maxw=w)
    from reportlab.lib.utils import ImageReader

    def sig_block(img, nm, cap):
        xc = x0 + w * 0.71
        if img:
            try:
                iw, ih = ImageReader(img).getSize(); s = min(0.36 * inch / ih, w * 0.5 / iw)
                c.drawImage(img, xc - iw * s / 2, ry + 1, iw * s, ih * s, mask="auto")
            except Exception:
                pass
        c.line(x0 + w * 0.42, ry, x0 + w, ry)
        txt(xc, ry - 8, nm, 7.5, "Helvetica-Bold", "c", w * 0.55); txt(xc, ry - 15, cap, 6, align="c")

    ry -= 0.42 * inch; sig_block(sig_emp, name, "(Signature over printed name)")
    ry -= 0.26 * inch; txt(x0, ry, "VERIFIED as to the prescribed office hours.", 7.5, maxw=w)
    ry -= 0.42 * inch; sig_block(sig_inc, in_charge or "", "(In Charge)")
    return tot_ut, tot_ot


def draw_page(c, copies=2, **kw):
    """One page: 'copies' identical DTRs (2 = side by side like the printed Form 48 sheet)."""
    if copies == 2:
        W = 3.75 * inch
        for x in (0.35 * inch, 0.35 * inch + W + 0.3 * inch):
            draw_dtr(c, x0=x, w=W, **kw)
    else:
        draw_dtr(c, **kw)
    c.setFont("Helvetica-Oblique", 5.5); c.setFillGray(.45)
    c.drawString(0.35 * inch, 0.2 * inch, "Computed from ZKTeco biometric logs. UT = late arrival + early departure + excess lunch; "
                 "OT = departure past the latest official out-time.")
    c.setFillGray(0); c.showPage()
