"""roster.py - HR roster in the PCA_Flexitime.xlsx format.

Sheets 'Regular' and 'Non-Regular'. Office headings (REGIONAL OFFICE V, SORSOGON P.O ...) sit on their own rows.
Each person's schedule is the REMARKS text. An optional 'ID NO.' column (biometric ID) is used when the name does not match. Only name, position, office, schedule and ID are read."""
import re
import openpyxl
from zkparser import norm_key
from schedules import register_schedule


class Roster(dict):
    by_id = {}


def _norm_id(v):
    s = re.sub(r"\.0$", "", str(v if v is not None else "").strip())
    return s.lstrip("0") or ("0" if s else "")


def _clean(v):
    return re.sub(r"\s+", " ", str(v if v is not None else "")).strip()


def sec_label(section):
    return (section or "").title().replace("P.O", "P.O.").replace("P.O..", "P.O.") if section else ""


def _find(h, *pats, exclude=()):
    for i, x in enumerate(h):
        u = x.upper()
        if any(re.search(p, u) for p in pats) and not any(re.search(p, u) for p in exclude):
            return i


def load_roster(path):
    """Columns are found by their headings, so an ID column (ID NO., EMPLOYEE ID, BIOMETRIC ID ...) is read
    wherever it is placed, and files without one still load."""
    out, by_id = Roster(), {}
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    for sh in wb.sheetnames:
        if sh.strip().lower() not in ("regular", "non-regular"):
            continue
        office, cat, cols = "", "Regular" if sh.strip().lower() == "regular" else "", None
        for row in wb[sh].iter_rows(values_only=True):
            c = [_clean(x) for x in row] + [""] * 12
            if cols is None:                                   # header row
                n = _find(c, r"NAME")
                if n is not None:
                    cols = dict(name=n, position=_find(c, r"POSITION", r"FUNCTION"),
                                unit=_find(c, r"DIVISION", r"PLACE OF ASSIGNMENT", r"STATION"), sup=_find(c, r"SUPERVISOR"),
                                rem=_find(c, r"REMARK", r"NOTE"),
                                id=_find(c, r"\bID\b", r"BIOMETRIC", r"EMPLOYEE NO", r"EMP\.? ?NO", exclude=(r"ITEM",)))
                continue
            g = lambda k: c[cols[k]] if cols[k] is not None else ""
            if not g("name"):
                if c[0] and not g("position") and not g("unit"):   # a heading row: category or office
                    if c[0].upper() in ("CONTRACT OF SERVICE", "JOB ORDER PERSONNEL"):
                        cat = c[0].title()
                    else:
                        office = c[0]
                continue                                       # vacant item
            e = dict(name=g("name"), position=g("position"), unit=g("unit"), supervisor=g("sup"), remarks=g("rem"),
                     item=c[0], office=office, category=cat, id_no=_norm_id(g("id")), sched=register_schedule(g("rem")))
            out[norm_key(e["name"])] = e
            if e["id_no"]:
                by_id[e["id_no"]] = e
    out.by_id = by_id
    return out


def lookup(roster, emp):
    """Roster entry for an attendance employee: by ID number first, then by name."""
    if not roster:
        return {}
    e = roster.get(emp.key)                      # name first: IDs can be reused by a later person in older months
    if e is None and getattr(roster, "by_id", None):
        e = roster.by_id.get(_norm_id(emp.zk_id))
    return e or {}
