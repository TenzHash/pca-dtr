"""Quick rule checks:  python tests.py"""
from schedules import SCHEDULES, compute_day, H
import datetime as dt

def run(office, wd, punches):
    return compute_day(1, dt.date(2026, 8, 3 + wd), sorted(punches), SCHEDULES[office][wd], False)

# provincial fixed 8-5
r = run("provincial", 0, [H(8, 20), H(17, 45)]);  assert (r.late, r.ut, r.ot) == (20, 20, 45)
r = run("provincial", 2, [H(7, 50), H(16, 40)]);  assert (r.late, r.ut, r.ot) == (0, 20, 0)
# regional flexitime
r = run("regional", 0, [H(7, 20), H(16, 30)]);    assert (r.ut, r.ot) == (0, 0)      # early bird, Mon 7:30 in/4:30 out
r = run("regional", 0, [H(8, 10), H(17, 0)]);     assert (r.late, r.ut) == (10, 10)  # Mon latest in 8:00
r = run("regional", 1, [H(8, 25), H(17, 25)]);    assert (r.ut, r.ot) == (0, 0)      # Tue in 8:25 -> out 5:25 pm exactly
r = run("regional", 1, [H(8, 25), H(17, 0)]);     assert r.early == 25               # must stay until 5:25 pm
r = run("regional", 4, [H(8, 40), H(17, 45)]);    assert (r.late, r.ot) == (10, 15)  # Fri latest in 8:30, out end 5:30
# utility
r = run("utility", 1, [H(7, 10), H(16, 0)]);      assert (r.late, r.ut) == (10, 10)
r = run("utility", 4, [H(8, 0), H(17, 30)]);      assert r.ot == 30
# incomplete / half-day
r = run("provincial", 3, [H(8, 5)]);              assert "NO TIME-OUT" in r.notes and r.ut == 5
r = run("provincial", 3, [H(8, 0), H(12, 1)]);    assert r.ut == 240
r = run("provincial", 3, [H(8, 0), H(12, 5), H(13, 30), H(17, 0)]); assert r.excess_lunch == 25
# manual corrections
r = compute_day(1, dt.date(2026, 8, 6), [H(8, 5)], SCHEDULES["provincial"][3], False, 0, {"pm_dep": H(17, 0)})
assert r.corrected and r.notes == [] and (r.late, r.ut, r.ot) == (5, 5, 0) and r.am_dep == H(12)   # fixed missing time-out
r = compute_day(1, dt.date(2026, 8, 6), [], SCHEDULES["provincial"][3], False, 0, {"am_arr": H(8), "pm_dep": H(17)})
assert r.present and r.ut == 0                                                                       # whole day entered by hand
r = compute_day(1, dt.date(2026, 8, 6), [H(8), H(17)], SCHEDULES["provincial"][3], False, 0, dict.fromkeys(("am_arr", "am_dep", "pm_arr", "pm_dep")))
assert not r.present                                                                                 # all times cleared
from schedules import parse_schedule_text, register_schedule
assert register_schedule("Monday to Friday (8AM- 5PM)") == "provincial"
assert register_schedule("Mon 7:30AM-8:00AM; T-TH 7:30AM-8:30AM; Fri 8AM-8:30AM") == "regional"
k = register_schedule("Mon-Thu 7AM- 8AM; Friday 8AM"); w = SCHEDULES[k]
assert k.startswith("txt:") and w[0] == (H(7), H(8), H(16), H(17)) and w[4] == (H(8), H(8), H(17), H(17)) and set(w) == {0, 1, 2, 3, 4}
assert parse_schedule_text("whatever") is None
import openpyxl, tempfile, os
from roster import load_roster, lookup
from zkparser import Employee
for hdr, idv in ((["ITEM NO", "NAME OF INCUMBENT", "ID NO.", "POSITION TITLE", "DIVISION/ PROVINCE", "SUPERVISOR", "REMARKS"], "0012"),
                 (["NO", "NAME", "POSITION", "STATION", "Supervisor", "REMARKS", "Employee ID"], 12.0)):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Regular"; ws.append(hdr); ws.append(["REGIONAL OFFICE V"])
    row = {"ITEM NO": "1-1", "NO": 1, "NAME OF INCUMBENT": "Dela Cruz, Juan A.", "NAME": "Dela Cruz, Juan A.", "ID NO.": idv, "Employee ID": idv,
           "POSITION TITLE": "Clerk", "POSITION": "Clerk", "DIVISION/ PROVINCE": "Admin Unit", "STATION": "Admin Unit", "SUPERVISOR": "A. BOSS", "Supervisor": "A. BOSS",
           "REMARKS": "Monday to Friday (8AM- 5PM)"}
    ws.append([row[h] for h in hdr]); p = os.path.join(tempfile.mkdtemp(), "r.xlsx"); wb.save(p)
    R = load_roster(p); e = lookup(R, Employee("x", "Somebody,Else", "12"))     # found by ID although the name differs
    assert e["name"] == "Dela Cruz, Juan A." and e["unit"] == "Admin Unit" and e["supervisor"] == "A. BOSS" and e["office"] == "REGIONAL OFFICE V" and e["sched"] == "provincial"
no_id = openpyxl.Workbook(); ws = no_id.active; ws.title = "Regular"; ws.append(["ITEM NO", "NAME OF INCUMBENT", "POSITION TITLE", "DIVISION", "SUPERVISOR", "REMARKS"]); ws.append(["1", "A, B.", "x", "y", "z", ""])
p = os.path.join(tempfile.mkdtemp(), "n.xlsx"); no_id.save(p); assert load_roster(p).by_id == {} and len(load_roster(p)) == 1
print("all rule checks passed")
