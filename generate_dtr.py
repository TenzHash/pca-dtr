#!/usr/bin/env python3
"""Biometric DTR & CSC Form No. 48 generator.

  python generate_dtr.py --input Attendance --office regional --month 2026-08
  python generate_dtr.py --input Attendance --office sorsogon --roster Biometrics.xlsx --individual
"""
import argparse, calendar, csv, datetime as dt, os, re, sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zkparser import load_directory, dedupe, norm_key, pretty_name
from schedules import SCHEDULES, LABELS, PROVINCES, schedule_for, compute_day, DayResult, sched_title
from form48 import new_canvas, draw_page
from roster import load_roster, lookup, sec_label

OFFICES = {"regional"} | PROVINCES


def load_remarks(path):
    """CSV: employee,date,remark   (date = YYYY-MM-DD or YYYY-MM-DD:YYYY-MM-DD; employee '*' = everyone)"""
    rules = []
    if path and os.path.exists(path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                a, _, b = row["date"].strip().partition(":")
                d1 = dt.date.fromisoformat(a); d2 = dt.date.fromisoformat(b or a)
                rules.append((row["employee"].strip(), d1, d2, row["remark"].strip()))
    return rules


def remarks_for(rules, key, date):
    return [r for who, d1, d2, r in rules if d1 <= date <= d2 and (who == "*" or norm_key(who) in key)]


def parse_spans(s):
    out = []
    for p in (s or "").split("|"):
        rng, _, t = p.partition(":")
        a, _, b = rng.partition("-")
        if a.isdigit() and b.isdigit() and t:
            out.append((int(a), int(b), t))
    return out


def parse_fill(s):
    return {int(k): v for k, _, v in (x.partition(":") for x in (s or "").split(",")) if k.isdigit() and v}


def ser_spans(sp): return "|".join(f"{a}-{b}:{t}" for a, b, t in sp)
def ser_fill(fl): return ",".join(f"{k}:{v}" for k, v in sorted(fl.items()))


def build_month(md, emp, sched_name, rules, args):
    ndays = calendar.monthrange(md.year, md.month)[1]
    results = []
    for dd in range(1, ndays + 1):
        date = dt.date(md.year, md.month, dd)
        wd = date.weekday()
        user = remarks_for(rules, emp.key, date)
        mins = dedupe(emp.punches.get(date, []))
        holiday = date in md.holidays or date in args.holiday_set
        off = wd >= 5 or holiday
        res = compute_day(dd, date, mins, SCHEDULES[sched_name].get(wd), off, args.ot_threshold,
                          getattr(args, 'overrides', {}).get((emp.key, date)))
        code = emp.sched.get(date)
        if code in (25, 26):
            user.append({25: "LEAVE", 26: "OFFICIAL BUSINESS / OUT"}[code])
        po = getattr(args, 'post', {}).get((emp.key, date), {})
        if res.present:
            res.notes = user + res.notes
        else:
            if date not in md.covered:
                res.kind = "nodata"
            elif wd == 5: res.kind = "saturday"
            elif wd == 6: res.kind = "sunday"
            elif holiday: res.kind = "holiday"
            elif user: res.kind, res.notes = "remark", user
            else:
                res.kind = "absent"; res.review.append("no punches on a working day")
        if po:
            res.corrected = True
            if "remark" in po:
                res.notes = [po["remark"]] if po["remark"] else []
                if not res.present:
                    res.kind = "remark"
            if "merge" in po:
                res.spans = parse_spans(po["merge"])
                cov = {i for a, b, t in res.spans for i in range(a, b + 1)}
                if res.present and {0, 1} <= cov and "HALF-DAY (PM)" in res.notes or res.present and {2, 3} <= cov and "HALF-DAY (AM)" in res.notes:
                    res.ut = max(0, res.ut - 240)        # the covered half is excused (leave / OB)
                if not res.present and cov >= {0, 1, 2, 3} and res.kind == "absent":
                    res.kind = "remark"
            if "fill" in po:
                res.fill = parse_fill(po["fill"])
            if "ut" in po:
                res.ut = po["ut"]
            if "ot" in po:
                res.ot = po["ot"]
            if res.kind == "absent" and po:
                res.kind = "remark" if "remark" in po else res.kind
        results.append(res)
    return results


def auto_holidays(md, log=print):
    """Holidays come from what people actually did, not from the device's schedule sheet:
    a weekday nobody punched on is a holiday / suspension; a weekday the sheet left blank
    but most staff worked is a normal working day."""
    n = len(md.employees)
    if n < 10:
        return
    for day in sorted(md.covered):
        if day.weekday() >= 5:
            continue
        who = sum(1 for e in md.employees.values() if e.punches.get(day))
        if day not in md.holidays and who <= max(1, 0.05 * n):
            md.holidays.add(day)
            log(f"    auto-detected holiday/no-work day {day} ({who}/{n} punched)")
        elif day in md.holidays and who >= 0.2 * n:
            md.holidays.discard(day)
            log(f"    {day} was blank in the schedule sheet but {who}/{n} worked - treated as a working day")


def summarize(results):
    work = [r for r in results if r.present]
    return dict(days_present=len(work), absences=sum(r.kind == "absent" for r in results),
                late_count=sum(r.late > 0 for r in work), ut=sum(r.ut for r in results),
                ot=sum(r.ot for r in results), review=sum(bool(r.review) for r in results),
                corrected=sum(r.corrected for r in results))


def write_summary(path, rows, detail):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Summary"
    head = ["Employee", "Schedule", "Days Present", "Absences", "Times Late", "Undertime (h:mm)",
            "Undertime (min)", "Overtime (h:mm)", "Overtime (min)", "Days to Review", "Manual Corrections", "ID No.", "Office", "Division / Station", "Supervisor"]
    ws.append(head)
    for r in rows:
        ws.append([r["name"], r["sched"], r["days_present"], r["absences"], r["late_count"],
                   f"{r['ut']//60}:{r['ut']%60:02d}", r["ut"], f"{r['ot']//60}:{r['ot']%60:02d}", r["ot"], r["review"], r["corrected"], r.get("id_no", ""), r.get("office", ""), r.get("division", ""), r.get("supervisor", "")])
    ws2 = wb.create_sheet("Daily Detail")
    ws2.append(["Employee", "Date", "Day", "AM In", "AM Out", "PM In", "PM Out", "Late (min)",
                "Early Out (min)", "Excess Lunch (min)", "Undertime (min)", "Overtime (min)", "Remarks", "Review Flag", "Manually Corrected"])
    f = lambda m: "" if m is None else f"{m//60:02d}:{m%60:02d}"
    for name, date, d in detail:
        label = {"saturday": "SATURDAY", "sunday": "SUNDAY", "holiday": "HOLIDAY", "absent": "ABSENT"}.get(d.kind, "")
        ws2.append([name, date, date.strftime("%a"), f(d.am_arr), f(d.am_dep), f(d.pm_arr), f(d.pm_dep),
                    d.late, d.early, d.excess_lunch, d.ut, d.ot, "; ".join(d.notes) or label, "; ".join(d.review), "YES" if d.corrected else ""])
    for sh in (ws, ws2):
        for c in sh[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F4E78")
            c.alignment = Alignment(wrap_text=True, horizontal="center")
        for col in sh.columns:
            sh.column_dimensions[col[0].column_letter].width = max(12, min(40, max(len(str(c.value or "")) for c in col) + 2))
        sh.freeze_panes = "A2"
    wb.save(path)


def office_label(office):
    return "Regional Office" if office == "regional" else f"{office.replace('-', ' ').title()} Provincial Office"


def process_month(md, emps, office, roster, util_keys, rules, holiday_set, ot_threshold=0, overrides=None, post=None, defaults=None):
    """Compute every employee's month. Returns a list of dicts (shared by CLI and web app)."""
    class A: pass
    a = A(); a.holiday_set = holiday_set; a.ot_threshold = ot_threshold; a.overrides = overrides or {}; a.post = post or {}
    items, dflt = [], defaults or {}
    for e in emps:
        info = lookup(roster, e)
        name = pretty_name(info["name"]) if info else pretty_name(e.zk_name)
        sname = "utility" if e.key in util_keys else (info.get("sched") or schedule_for(office, False))
        res = build_month(md, e, sname, rules, a)
        olab = sec_label(info.get("office")) or office_label(office)
        div = info.get("unit") or dflt.get("division", "")
        sup = (info.get("supervisor") or dflt.get("supervisor", "")).upper()
        s = summarize(res); s.update(name=name, sched=sched_title(sname), id_no=info.get("id_no") or e.zk_id, office=olab,
                                     division=div, supervisor=sup)
        items.append(dict(emp=e, name=name, sname=sname, res=res, summary=s, office_label=olab, id_no=s["id_no"],
                          division=div, supervisor=sup, sup_roster=bool(info.get("supervisor"))))
    return items


def render_pdf(target, items, year, month, office, in_charge="", layout="two", inc_sig=None):
    c = new_canvas(target)
    for it in items:
        draw_page(c, copies=2 if layout == "two" else 1, name=it["name"], year=year, month=month, days=it["res"],
                  office_label=it.get("office_label") or office_label(office), id_no=it.get("id_no", ""), sched_label=LABELS[it["sname"]], in_charge=(it.get("supervisor") or in_charge),
                  division=it.get("division", ""),
                  note=it.get("note", ""), sig_emp=it.get("sig"), sig_inc=inc_sig)
    c.save()


def month_employees(md, roster, employee=None):
    emps = sorted(md.employees.values(), key=lambda e: pretty_name(lookup(roster, e).get("name", e.zk_name)))
    return [e for e in emps if not employee or norm_key(employee) in e.key]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default="Attendance", help="folder (or file) of ZKTeco exports")
    ap.add_argument("--office", default="regional", choices=sorted(OFFICES))
    ap.add_argument("--month", help="YYYY-MM (default: every month found)")
    ap.add_argument("--employee", help="only employees whose name contains this text")
    ap.add_argument("--roster", help="HR roster .xlsx (full names + utility-worker detection)")
    ap.add_argument("--utility", default="", help="comma-separated names to treat as utility workers")
    ap.add_argument("--remarks", help="CSV of Leave / Official Business / Travel remarks")
    ap.add_argument("--holidays", default="", help="extra holidays, comma-separated YYYY-MM-DD")
    ap.add_argument("--in-charge", default="", help="supervisor name used when the roster has none")
    ap.add_argument("--division", default="", help="division / station used when the roster has none")
    ap.add_argument("--ot-threshold", type=int, default=0, help="ignore overtime shorter than N minutes")
    ap.add_argument("--layout", default="two", choices=["two", "one"], help="two copies side by side (default) or one")
    ap.add_argument("--individual", action="store_true", help="also write one PDF per employee")
    ap.add_argument("--out", default="output")
    args = ap.parse_args()
    args.holiday_set = {dt.date.fromisoformat(x) for x in args.holidays.split(",") if x.strip()}

    print(f"Scanning {args.input} ...")
    months = load_directory(args.input)
    if not months:
        sys.exit("No attendance data found.")
    roster = load_roster(args.roster) if args.roster else {}
    util_keys = {norm_key(x) for x in args.utility.split(",") if x.strip()}
    rules = load_remarks(args.remarks)
    os.makedirs(args.out, exist_ok=True)
    for (y, m) in sorted(months):
        if args.month and f"{y}-{m:02d}" != args.month:
            continue
        md = months[(y, m)]
        auto_holidays(md)
        emps = month_employees(md, roster, args.employee)
        if not emps:
            continue
        items = process_month(md, emps, args.office, roster, util_keys, rules, args.holiday_set, args.ot_threshold, None, None, dict(division=args.division, supervisor=args.in_charge))
        tag = f"DTR_{args.office}_{y}-{m:02d}"
        render_pdf(os.path.join(args.out, tag + ".pdf"), items, y, m, args.office, args.in_charge, args.layout)
        if args.individual:
            os.makedirs(os.path.join(args.out, "individual"), exist_ok=True)
            for it in items:
                render_pdf(os.path.join(args.out, "individual", f"{tag}_{it['emp'].key}.pdf"), [it], y, m, args.office, args.in_charge, args.layout)
        detail = [(it["name"], dt.date(y, m, r.day), r) for it in items for r in it["res"] if r.kind != "nodata"]
        write_summary(os.path.join(args.out, tag + "_summary.xlsx"), [it["summary"] for it in items], detail)
        print(f"{y}-{m:02d}: {len(items)} DTRs -> {args.out}/{tag}.pdf (+ summary xlsx)")


if __name__ == "__main__":
    main()
