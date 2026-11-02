"""End-to-end check of the web app:  python test_app.py <folder with ZKTeco exports> [roster.xlsx]"""
import os, shutil, sys, tempfile
tmp = tempfile.mkdtemp(); os.environ["DTR_DATA"] = tmp
import app as A
c = A.app.test_client()
c.post("/api/settings", json={"operator": "Admin, Test A."})
src = sys.argv[1]
for f in sorted(os.listdir(src)):
    if f.lower().endswith((".xls", ".xlsx")):
        with open(os.path.join(src, f), "rb") as fh:
            assert c.post("/api/upload", data={"files": (fh, f)}, content_type="multipart/form-data").status_code == 200
if len(sys.argv) > 2:
    with open(sys.argv[2], "rb") as fh:
        c.post("/api/upload", data={"files": (fh, "r.xlsx"), "kind": "roster"}, content_type="multipart/form-data")
st = c.get("/api/state").json; print("months:", st["months"], "roster:", st["roster"])
ym = "2026-08"
m = c.get(f"/api/month/{ym}").json; print(len(m["employees"]), "employees; holidays", m["holidays"])
k = max(m["employees"], key=lambda e: e["absences"])["key"]
assert c.post("/api/remarks", json={"employee": k, "start": "2026-08-05", "end": "2026-08-06", "remark": "leave"}).status_code == 200
e = c.get(f"/api/employee/{ym}/{k}").json
print([r["note"] or r["kind"] for r in e["rows"] if r["date"] in ("2026-08-05", "2026-08-06")])
assert c.post("/api/settings", json={"office": "sorsogon", "in_charge": "J. DELA CRUZ"}).status_code == 200
for url, mt in ((f"/pdf/{ym}", "pdf"), (f"/pdf/{ym}/{k}", "pdf"), (f"/xlsx/{ym}", "sheet"), (f"/zip/{ym}", "zip")):
    r = c.get(url); assert r.status_code == 200 and len(r.data) > 1000, url; print(url, len(r.data), "bytes")
# biometric times are read-only (server side)
day = next(r["date"] for r in c.get(f"/api/employee/{ym}/{k}").json["rows"] if r["kind"] == "absent")
assert c.post("/api/correct", json={"ym": ym, "key": k, "date": day, "edits": {"am_in": "08:00"}, "reason": "x"}).status_code == 400
r = c.post("/api/cells", json={"ym": ym, "key": k, "cells": [{"date": day, "field": "am_in", "value": "08:00"}]}); assert r.status_code == 400 and r.json["code"] == "readonly"
assert next(x for x in c.get(f"/api/employee/{ym}/{k}").json["rows"] if x["date"] == day)["kind"] == "absent"
# a holiday typed for everyone is a real holiday: people who punched that day get holiday work, not a late/half-day workday
hd = "2026-08-21"; assert c.post("/api/remarks", json={"employee": "*", "start": hd, "remark": "Ninoy Aquino Day"}).status_code == 200
rows = [next(x for x in c.get(f"/api/employee/{ym}/{e['key']}").json["rows"] if x["date"] == hd) for e in all_emps[:30]] if False else None
for e in c.get(f"/api/month/{ym}").json["employees"]:
    row = next(x for x in c.get(f"/api/employee/{ym}/{e['key']}").json["rows"] if x["date"] == hd)
    assert row["kind"] == "holiday" and row["ut"] == 0 and "NINOY AQUINO DAY" in row["note"], row
c.post("/api/remarks/delete", json={"index": len(c.get("/api/state").json["remarks"]) - 1})
print("read-only times + holiday for everyone OK")
# Excel-style cell edits
cells = [{"date": day, "field": "ut", "value": "75"}, {"date": day, "field": "ot", "value": "30"}, {"date": day, "field": "remark", "value": "Field work"}, {"field": "month_note", "value": "Seminar on Aug 5"}]
assert c.post("/api/cells", json={"ym": ym, "key": k, "cells": cells}).json["changed"] == 4
e = c.get(f"/api/employee/{ym}/{k}").json; row = next(r for r in e["rows"] if r["date"] == day)
assert row["ut"] == 75 and row["ot"] == 30 and row["note"] == "Field work" and e["note"] == "Seminar on Aug 5" and {"ut", "ot", "remark"} <= set(row["ov"])
assert c.get(f"/pdf/{ym}/{k}").status_code == 200 and c.post("/api/cells", json={"ym": ym, "key": k, "cells": [{"date": day, "field": "ot", "value": "x"}]}).status_code == 400
assert c.post("/api/correct/revert", json={"ym": ym, "key": k, "date": day}).json["changed"] == 3
print("cell editing OK")
assert "attachment" in c.get(f"/pdf/{ym}/{k}?download=1").headers["Content-Disposition"] and "attachment" not in c.get(f"/pdf/{ym}/{k}").headers.get("Content-Disposition", "")
print("single-employee export OK")
import io
from PIL import Image
def png():
    b = io.BytesIO(); Image.new("RGBA", (200, 80), (0, 0, 120, 255)).save(b, "PNG"); b.seek(0); return b
assert c.post("/api/signature", data={"kind": "emp", "key": k, "file": (png(), "s.png")}, content_type="multipart/form-data").status_code == 200
assert c.post("/api/signature", data={"kind": "incharge", "key": "x", "file": (png(), "s.png")}, content_type="multipart/form-data").status_code == 200
e = c.get(f"/api/employee/{ym}/{k}").json; assert e["sig_emp"] and e["sig_inc"] and c.get(f"/sig/emp/{k}").status_code == 200
for lay in ("one", "two"): r = c.get(f"/pdf/{ym}/{k}?layout={lay}"); assert r.status_code == 200 and r.data[:4] == b"%PDF"
assert c.post("/api/settings", json={"theme": "dark"}).status_code == 200 and c.get("/api/state").json["settings"]["theme"] == "dark"
c.post("/api/signature/delete", json={"kind": "emp", "key": k}); assert not c.get(f"/api/employee/{ym}/{k}").json["sig_emp"]
print("signatures, layouts, theme OK")
cells = [{"date": day, "field": "merge", "value": "0-1:OFFICIAL BUSINESS"}, {"date": day, "field": "fill", "value": "2:#ffe699,6:#c6efce"}, {"date": day, "field": "remark", "value": "see memo"}]
assert c.post("/api/cells", json={"ym": ym, "key": k, "cells": cells}).json["changed"] >= 3
row = next(r for r in c.get(f"/api/employee/{ym}/{k}").json["rows"] if r["date"] == day)
assert row["spans"] == [[0, 1, "OFFICIAL BUSINESS", 0]] and row["fill"] == {"2": "#ffe699", "6": "#c6efce"} and row["note"] == "see memo"
assert c.get(f"/pdf/{ym}/{k}").status_code == 200
assert c.post("/api/correct/revert", json={"ym": ym, "key": k, "date": day}).status_code == 200
row = next(r for r in c.get(f"/api/employee/{ym}/{k}").json["rows"] if r["date"] == day); assert row["spans"] == [] and row["fill"] == {}
print("partial merge, fill, editable remarks OK")
import zipfile, json as _j
bk = c.get("/backup"); assert bk.status_code == 200 and "manifest.json" in zipfile.ZipFile(io.BytesIO(bk.data)).namelist()
n_before = len(c.get("/api/state").json["files"]); c.post("/api/delete_file", json={"name": c.get("/api/state").json["files"][0]})
r = c.post("/api/restore", data={"file": (io.BytesIO(bk.data), "b.zip")}, content_type="multipart/form-data").json
assert r["ok"] and len(c.get("/api/state").json["files"]) == n_before and c.get(f"/api/month/{ym}").status_code == 200
assert c.post("/api/restore", data={"file": (io.BytesIO(b"nope"), "x.zip")}, content_type="multipart/form-data").status_code == 400
evil = io.BytesIO(); zz = zipfile.ZipFile(evil, "w"); zz.writestr("manifest.json", _j.dumps({"app": "pca-dtr"})); zz.writestr("../evil.txt", "x"); zz.close(); evil.seek(0)
assert c.post("/api/restore", data={"file": (evil, "e.zip")}, content_type="multipart/form-data").status_code == 400
print("backup / restore OK")
srcdir = os.path.join(tmp, "share"); os.makedirs(srcdir); open(os.path.join(srcdir, "latest.json"), "w").write(_j.dumps({"version": "9.9.9", "file": "S.exe", "sha256": "0" * 64}))
c.post("/api/settings", json={"update_source": srcdir}); u = c.get("/api/update/check").json
assert u["available"] and u["latest"] == "9.9.9" and c.post("/api/update/install").status_code == 400
c.post("/api/settings", json={"update_source": ""}); print("update check OK")
c.post("/api/settings", json={"division": "Regional Technical Unit", "in_charge": "A. SUPERVISOR"})
e = c.get(f"/api/employee/{ym}/{k}").json; assert "division" in e and "supervisor" in e and e["office_label"]
assert c.get(f"/pdf/{ym}/{k}").status_code == 200
print("division / supervisor OK")
assert c.get("/").status_code == 200 and c.get("/api/month/1999-01").status_code == 404
# ---------------- no login: everything is open
assert c.get("/api/state").status_code == 200 and c.get("/api/me").status_code == 404 and c.get("/api/users").status_code == 404
print("no login OK")
r = c.post("/api/settings", json={"holidays": ["2026-8-20", "08/24/2026", "Aug 25, 2026", "tomorrow", "2026-02-30"]}).json
assert r["invalid"] == ["tomorrow", "2026-02-30"], r
assert c.get("/api/state").json["settings"]["holidays"] == ["2026-08-20", "2026-08-24", "2026-08-25"]
hm_ = c.get(f"/api/month/{ym}").json["holidays"]; assert {"2026-08-20", "2026-08-24", "2026-08-25"} <= set(h[:10] for h in hm_), hm_
c.post("/api/remarks", json={"employee": "*", "start": "2026-08-26", "end": "2026-08-27", "remark": "Typhoon"})
hm_ = c.get(f"/api/month/{ym}").json["holidays"]; assert "2026-08-26 (TYPHOON)" in hm_ and "2026-08-27 (TYPHOON)" in hm_, hm_
c.post("/api/remarks/delete", json={"index": len(c.get("/api/state").json["remarks"]) - 1}); c.post("/api/settings", json={"holidays": []})
print("holiday settings + list OK")
print("web app OK; outputs saved:", os.listdir(os.path.join(tmp, "output")))
