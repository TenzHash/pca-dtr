"""schedules.py - schedule rules + undertime / overtime computation engine.

Every schedule is expressed per weekday as four clock times (minutes after midnight):
    (earliest_in, latest_in, earliest_out, latest_out)
A fixed schedule has earliest_in == latest_in and earliest_out == latest_out.
Flexitime: arrive inside [earliest_in, latest_in]; required departure = arrival + 9h
(8h work + 1h lunch), kept inside [earliest_out, latest_out].
"""
from dataclasses import dataclass, field

H = lambda h, m=0: h * 60 + m
LUNCH_MIN = 60
SPAN = H(9)                       # 8 working hours + 1 hour lunch
LUNCH_LO, LUNCH_HI = H(11), H(14, 30)
HALF_CUT = H(12, 30)

SCHEDULES = {
    "provincial": {wd: (H(8), H(8), H(17), H(17)) for wd in range(5)},
    "regional": {0: (H(7, 30), H(8), H(16, 30), H(17)),
                 1: (H(7, 30), H(8, 30), H(16, 30), H(17, 30)),
                 2: (H(7, 30), H(8, 30), H(16, 30), H(17, 30)),
                 3: (H(7, 30), H(8, 30), H(16, 30), H(17, 30)),
                 4: (H(8), H(8, 30), H(17), H(17, 30))},
    "utility": {**{wd: (H(7), H(7), H(16), H(16)) for wd in range(4)},
                4: (H(8), H(8), H(17), H(17))},
}
LABELS = {
    "provincial": "Mon-Fri  8:00 AM - 5:00 PM (fixed)",
    "regional": "Flexitime IN: Mon 7:30-8:00, Tue-Thu 7:30-8:30, Fri 8:00-8:30",
    "utility": "Mon-Thu 7:00 AM - 4:00 PM; Fri 8:00 AM - 5:00 PM",
}
PROVINCES = {"catanduanes", "camarines-norte", "naga", "iriga", "masbate", "sorsogon"}


def schedule_for(office: str, is_utility: bool) -> str:
    if is_utility:
        return "utility"
    return "regional" if office == "regional" else "provincial"


@dataclass
class DayResult:
    day: int
    am_arr: int = None
    am_dep: int = None
    pm_arr: int = None
    pm_dep: int = None
    late: int = 0
    early: int = 0
    excess_lunch: int = 0
    ut: int = 0           # total undertime minutes
    ot: int = 0           # overtime minutes
    kind: str = "work"    # work | saturday | sunday | holiday | absent | nodata | remark
    notes: list = field(default_factory=list)   # printed in Remarks column
    review: list = field(default_factory=list)  # HR review flags (summary sheet)
    present: bool = False
    spans: list = field(default_factory=list)   # [(first_cell, last_cell, text)] merged cells over the 4 time cells
    fill: dict = field(default_factory=dict)    # {cell_index: '#rrggbb'}
    corrected: bool = False   # a manual correction changed this day


def classify(mins):
    """Assign sorted de-duplicated punches to AM/PM arrival/departure slots."""
    r = dict(am_arr=None, am_dep=None, pm_arr=None, pm_dep=None)
    notes, review, auto_lunch, mode = [], [], False, "full"
    n = len(mins)
    if n == 1:
        if mins[0] < H(12):
            r["am_arr"] = mins[0]; mode = "noout"; notes.append("NO TIME-OUT")
        else:
            r["pm_dep"] = mins[0]; mode = "noin"; notes.append("NO TIME-IN")
    elif mins[-1] <= HALF_CUT:
        r["am_arr"], r["am_dep"] = mins[0], mins[-1]; mode = "am"; notes.append("HALF-DAY (AM)")
    elif mins[0] >= HALF_CUT:
        r["pm_arr"], r["pm_dep"] = mins[0], mins[-1]; mode = "pm"; notes.append("HALF-DAY (PM)")
    else:
        r["am_arr"], r["pm_dep"] = mins[0], mins[-1]
        mid = [m for m in mins[1:-1] if LUNCH_LO <= m <= LUNCH_HI]
        extra = [m for m in mins[1:-1] if m not in mid]
        if extra:
            review.append("extra punches ignored: " + ", ".join(f"{m//60:02d}:{m%60:02d}" for m in extra))
        if len(mid) >= 2:
            r["am_dep"], r["pm_arr"] = mid[0], mid[-1]
        elif len(mid) == 1:
            r["am_dep"] = mid[0]; r["pm_arr"] = H(13) if mid[0] <= H(12) else mid[0] + LUNCH_MIN
            auto_lunch = True
        else:
            r["am_dep"], r["pm_arr"] = H(12), H(13); auto_lunch = True
    if mode != "full":
        review.append(notes[0].lower())
    return r, mode, auto_lunch, notes, review


SLOTS = ("am_arr", "am_dep", "pm_arr", "pm_dep")
MODE_NOTE = {"noout": "NO TIME-OUT", "noin": "NO TIME-IN", "am": "HALF-DAY (AM)", "pm": "HALF-DAY (PM)",
             "partial": "INCOMPLETE"}


def reconcile(r):
    """Re-derive the day type from the four slots after a manual correction."""
    a, b, c, e = (r[k] for k in SLOTS)
    if a is None and b is None and c is None and e is None:
        return None
    auto = False
    if a is not None and e is not None:
        if b is None and c is None:
            b, c, auto = H(12), H(13), True
        elif b is None:
            b, auto = c - LUNCH_MIN, True
        elif c is None:
            c, auto = (H(13) if b <= H(12) else b + LUNCH_MIN), True
        mode = "full"
    elif a is not None:
        mode = "am" if (b is not None and c is None) else "noout"
    elif e is not None:
        mode = "pm" if c is not None else "noin"
    else:
        mode = "partial"
    return dict(am_arr=a, am_dep=b, pm_arr=c, pm_dep=e), mode, auto


def compute_day(day: int, date, punches, window, is_off: bool, ot_threshold=0, override=None) -> DayResult:
    """punches: sorted minute list; window: schedule tuple for that weekday (None on rest days);
    is_off: weekend/holiday; override: {slot: minutes or None(blank)} from manual corrections."""
    d = DayResult(day=day)
    if not punches and not override:
        return d
    if punches:
        r, mode, auto_lunch, d.notes, d.review = classify(punches)
    else:
        r, mode, auto_lunch = dict.fromkeys(SLOTS), "full", False
    if override:
        r = dict(r); r.update(override)
        d.corrected = True
        rec = reconcile(r)
        if rec is None:                       # every time cleared -> as if no punches
            return d
        r, mode, auto_lunch = rec
        d.notes = [MODE_NOTE[mode]] if mode in MODE_NOTE else []
        d.review = [x for x in d.review if "punches ignored" in x] + ["manually corrected"]
        if mode in MODE_NOTE:
            d.review.append(MODE_NOTE[mode].lower())
    d.present = True
    d.am_arr, d.am_dep, d.pm_arr, d.pm_dep = r["am_arr"], r["am_dep"], r["pm_arr"], r["pm_dep"]
    if is_off or window is None:
        d.notes = ["REST DAY/HOLIDAY WORK"]
        d.review.append("rest-day/holiday punches")
        return d
    if mode == "partial":
        return d
    in_s, in_e, out_s, out_e = window
    if d.am_arr is not None:
        d.late = max(0, d.am_arr - in_e)
        eff = min(max(d.am_arr, in_s), in_e)
        req_out = min(max(eff + SPAN, out_s), out_e)
    else:
        req_out = out_s
    if mode in ("full", "pm") and d.pm_dep is not None:
        d.early = max(0, req_out - d.pm_dep)
        d.ot = max(0, d.pm_dep - out_e)
        if d.ot < ot_threshold:
            d.ot = 0
    if mode == "full" and not auto_lunch:
        d.excess_lunch = max(0, (d.pm_arr - d.am_dep) - LUNCH_MIN)
    if mode == "am":
        d.early = max(0, H(12) - d.am_dep) + 240           # missing afternoon
    elif mode == "pm":
        d.late = max(0, d.pm_arr - H(13)); d.early += 240  # missing morning
    d.ut = d.late + d.early + d.excess_lunch
    return d


# ---- schedules written as text in the HR roster, e.g. "Mon 7:30AM-8:00AM; T-TH 7:30AM-8:30AM; Fri 8AM-8:30AM"
import re as _re
_DAYMAP = {"M": 0, "MON": 0, "MONDAY": 0, "T": 1, "TUE": 1, "TUES": 1, "TUESDAY": 1, "W": 2, "WED": 2, "WEDNESDAY": 2,
           "TH": 3, "THU": 3, "THURS": 3, "THURSDAY": 3, "F": 4, "FRI": 4, "FRIDAY": 4}
_TIME = r"\d{1,2}(?::\d{2})?\s*[AP]M"


def _tm(x):
    m = _re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s*([AP]M)", x.strip().upper())
    return (int(m[1]) % 12 + (12 if m[3] == "PM" else 0)) * 60 + int(m[2] or 0)


def parse_schedule_text(text):
    """'Monday to Friday (8AM- 5PM)' = fixed in/out. Anything else = time-IN windows per day (out = in + 9h).
    Earliest time-out on Fridays is 5 PM for everyone (flag retreat), as noted in the roster."""
    t = (text or "").upper().replace("\u2013", "-")
    win = {}
    if _re.search(r"MON(DAY)?\s*(TO|-)\s*FRI(DAY)?", t):
        ts = [_tm(x) for x in _re.findall(_TIME, t)]
        if len(ts) == 2:
            win = {wd: (ts[0], ts[0], ts[1], ts[1]) for wd in range(5)}
    else:
        for part in t.split(";"):
            m = _re.match(r"\s*([A-Z]+(?:\s*-\s*[A-Z]+)?)\s+(.*)$", part)
            if not m:
                continue
            toks = [x.strip() for x in m[1].split("-")]
            ts = [_tm(x) for x in _re.findall(_TIME, m[2])]
            if not ts or not all(x in _DAYMAP for x in toks):
                continue
            for wd in range(_DAYMAP[toks[0]], _DAYMAP[toks[-1]] + 1):
                win[wd] = (ts[0], ts[-1], ts[0] + SPAN, ts[-1] + SPAN)
    if 4 in win:
        a, b, c, d = win[4]; c = max(c, H(17)); win[4] = (a, b, c, max(d, c))
    return win or None


def register_schedule(text):
    """Return the schedule key for a roster remark (built-in name when it matches, else a custom entry)."""
    win = parse_schedule_text(text)
    if not win:
        return None
    for name in ("regional", "provincial", "utility"):
        if SCHEDULES[name] == win:
            return name
    key = "txt:" + _re.sub(r"\s+", " ", text.strip())
    SCHEDULES[key] = win; LABELS[key] = _re.sub(r"\s+", " ", text.strip())
    return key


def sched_title(key):
    return {"regional": "Regional", "provincial": "Provincial", "utility": "Utility"}.get(key, "Custom")
