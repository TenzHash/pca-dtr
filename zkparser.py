"""parser.py - ingest ZKTeco 'Attendance Record Report' exports (.xls / .xlsx)

Handles:
  * legacy .xls (via xlrd when installed, otherwise LibreOffice conversion fallback)
  * modern .xlsx, sheet 'Att.log report' or 'Sheet1'
  * concatenated punch strings such as '07:4917:25' (regex \\d{2}:\\d{2})
  * several files covering the same month (e.g. 'June 1-15.xls' + 'Attendance 202606.xls')
"""
import datetime as dt
import glob
import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field

import openpyxl

TIME_RE = re.compile(r"\d{2}:\d{2}")
PERIOD_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s*~\s*(\d{4})-(\d{2})-(\d{2})")
DUP_WINDOW_MIN = 3  # punches closer than this are the same scan (double-tap)


def norm_key(name: str) -> str:
    """'Dela Cruz, Juan A.' and 'DelaCruz,JuanA' -> same key."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def pretty_name(raw: str) -> str:
    """'DelaCruz,JuanA' -> 'DELACRUZ, JUAN A.' (ZKTeco strips spaces)."""
    raw = raw.strip()
    if "," not in raw:
        return raw.upper()
    last, first = raw.split(",", 1)
    first = re.sub(r"(?<=[a-z\.])(?=[A-Z])", " ", first.strip())
    first = re.sub(r"\.(?=[A-Za-z])", ". ", first)
    parts = first.split()
    if len(parts) > 1 and len(parts[-1]) == 1:
        parts[-1] += "."
    return f"{last.strip().upper()}, {' '.join(parts).upper()}"


# --------------------------------------------------------------------- readers
def _clean(v):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return None
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def read_sheets(path: str) -> dict:
    """Return {sheet_name: [row, row, ...]} for .xls or .xlsx."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xls":
        try:
            import xlrd  # legacy reader
            wb = xlrd.open_workbook(path)
            return {s.name: [[_clean(c) for c in s.row_values(r)] for r in range(s.nrows)]
                    for s in wb.sheets()}
        except ImportError:
            soffice = shutil.which("soffice") or shutil.which("libreoffice")
            if not soffice:
                raise RuntimeError("Reading .xls needs 'pip install xlrd' (or LibreOffice).")
            tmp = tempfile.mkdtemp()
            subprocess.run([soffice, "--headless", "--convert-to", "xlsx", "--outdir", tmp, path],
                           check=True, capture_output=True)
            path = os.path.join(tmp, os.path.splitext(os.path.basename(path))[0] + ".xlsx")
    wb = openpyxl.load_workbook(path, data_only=True)
    return {ws.title: [[_clean(c) for c in row] for row in ws.iter_rows(values_only=True)]
            for ws in wb.worksheets}


# --------------------------------------------------------------------- parsing
@dataclass
class Employee:
    key: str
    zk_name: str
    zk_id: str
    punches: dict = field(default_factory=lambda: defaultdict(set))  # date -> {minutes}
    sched: dict = field(default_factory=dict)                        # date -> shift code


@dataclass
class MonthData:
    year: int
    month: int
    employees: dict = field(default_factory=dict)   # key -> Employee
    covered: set = field(default_factory=set)       # dates present in some export
    sched_days: set = field(default_factory=set)    # dates covered by a schedule sheet
    holidays: set = field(default_factory=set)      # weekdays nobody was scheduled


def _period(rows):
    for r in rows[:12]:
        m = PERIOD_RE.search(" ".join(str(c) for c in r if c is not None))
        if m:
            y1, m1, d1, y2, m2, d2 = map(int, m.groups())
            return dt.date(y1, m1, d1), dt.date(y2, m2, d2)
    return None


def _header_map(rows, start):
    """Find the row holding day numbers 1..31 -> {col_index: day_number}."""
    for r in rows[:15]:
        cols = {i: int(v) for i, v in enumerate(r) if isinstance(v, int) and 1 <= v <= 31}
        if len(cols) >= 27:
            return cols
    return {i: i + 1 for i in range(31)}


def _date_for(day, start, end=None):
    """Day-of-month -> real date inside the report period (None if it falls outside)."""
    y, m = (start.year, start.month) if day >= start.day else \
        ((start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1))
    try:
        d = dt.date(y, m, day)
    except ValueError:
        return None
    return d if (end is None or start <= d <= end) else None


def parse_att_log(rows):
    """Yield (id, name, {date: [minutes]}) for every employee block in a sheet."""
    per = _period(rows)
    if not per:
        return None, []
    start, end = per
    cols = _header_map(rows, start)
    out, cur = [], None
    for r in rows:
        txt = [str(c).strip() if c is not None else "" for c in r]
        if "ID:" in txt:
            i = txt.index("ID:")
            emp_id = next((t for t in txt[i + 1:] if t), "")
            name = ""
            if "Name:" in txt:
                j = txt.index("Name:")
                name = next((t for t in txt[j + 1:] if t), "")
            cur = (emp_id, name, defaultdict(list))
            out.append(cur)
        elif cur is not None:
            for ci, v in enumerate(r):
                if v is None or ci not in cols:
                    continue
                times = [int(t[:2]) * 60 + int(t[3:]) for t in TIME_RE.findall(str(v))
                         if int(t[:2]) < 24 and int(t[3:]) < 60]
                if times:
                    d = _date_for(cols[ci], start, end)
                    if d:
                        cur[2][d].extend(times)
    return (start, end), out


def parse_schedule(rows):
    per = _period(rows)
    if not per:
        return None, {}
    start, end = per
    cols = _header_map(rows, start)
    res = {}
    for r in rows:
        if len(r) > 3 and r[1] and r[0] is not None and r[0] != "ID" and isinstance(r[1], str) \
                and "Department" not in r:
            res[norm_key(r[1])] = {_date_for(cols[i], start, end): r[i]
                                   for i in cols if i < len(r) and r[i] is not None
                                   and _date_for(cols[i], start, end)}
    return (start, end), res


def dedupe(mins):
    out = []
    for m in sorted(mins):
        if not out or m - out[-1] >= DUP_WINDOW_MIN:
            out.append(m)
    return out


def load_directory(path: str, log=print):
    """Scan a folder (or a single file) and return {(year, month): MonthData}."""
    files = [path] if os.path.isfile(path) else sorted(
        f for f in glob.glob(os.path.join(path, "*")) if f.lower().endswith((".xls", ".xlsx"))
        and not os.path.basename(f).startswith("~$"))
    months = {}
    for f in files:
        try:
            sheets = read_sheets(f)
        except Exception as e:  # keep going if one file is damaged
            log(f"  ! skipped {os.path.basename(f)}: {e}")
            continue
        for sname, rows in sheets.items():
            per, emps = parse_att_log(rows)
            if per and emps:
                start, end = per
                log(f"  + {os.path.basename(f)} [{sname}] {start}..{end}: {len(emps)} employees")
                for d in range((end - start).days + 1):
                    day = start + dt.timedelta(days=d)
                    months.setdefault((day.year, day.month), MonthData(day.year, day.month)).covered.add(day)
                for emp_id, name, by_date in emps:
                    for d, mins in by_date.items():
                        md = months.setdefault((d.year, d.month), MonthData(d.year, d.month))
                        e = md.employees.setdefault(norm_key(name), Employee(norm_key(name), name, emp_id))
                        e.punches[d].update(mins)
                    # employees with zero punches still get a DTR
                    for (y, m) in {(start.year, start.month), (end.year, end.month)}:
                        md = months.get((y, m))
                        if md:
                            md.employees.setdefault(norm_key(name), Employee(norm_key(name), name, emp_id))
        # schedule sheet(s): shift codes, holidays
        for sname, rows in sheets.items():
            per, sched = parse_schedule(rows) if "chedule" in sname else (None, {})
            if per and sched:
                start, end = per
                weekdays = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
                for day in weekdays:
                    md = months.setdefault((day.year, day.month), MonthData(day.year, day.month))
                    md.sched_days.add(day)
                    if day.weekday() < 5 and not any(s.get(day) for s in sched.values()):
                        md.holidays.add(day)
                for key, by_date in sched.items():
                    for d, code in by_date.items():
                        md = months.get((d.year, d.month))
                        if md and key in md.employees:
                            md.employees[key].sched[d] = code
    return months
