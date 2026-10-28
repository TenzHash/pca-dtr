"""End-to-end check of the web app:  python test_app.py <folder with ZKTeco exports> [roster.xlsx]"""
import os, shutil, sys, tempfile
tmp = tempfile.mkdtemp(); os.environ["DTR_DATA"] = tmp
import app as A
c = A.app.test_client()
assert c.post("/api/setup", json={"username": "tester", "display": "HR Tester", "password": "Test-Pass-123"}).status_code == 200   # sign in (first run)
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
# manual correction + audit trail
c.post("/api/settings", json={"office": "regional", "operator": "HR Tester"})
day = next(r for r in c.get(f"/api/employee/{ym}/{k}").json["rows"] if r["kind"] == "absent")["date"]
bad = c.post("/api/correct", json={"ym": ym, "key": k, "date": day, "edits": {"am_in": "08:00"}, "reason": ""}); assert bad.status_code == 400
bad = c.post("/api/correct", json={"ym": ym, "key": k, "date": day, "edits": {"am_in": "8am"}, "reason": "x"}); assert bad.status_code == 400
ok = c.post("/api/correct", json={"ym": ym, "key": k, "date": day, "edits": {"am_in": "08:00", "pm_out": "17:00"}, "reason": "Forgot to punch"}).json; assert ok["changed"] == 2
row = next(r for r in c.get(f"/api/employee/{ym}/{k}").json["rows"] if r["date"] == day); assert row["corrected"] and row["pm_out"] == "17:00" and set(row["ov"]) == {"am_in", "pm_out"}
log = c.get(f"/api/audit?ym={ym}&key={k}").json; assert len(log) == 2 and log[0]["operator"] == "HR Tester (tester)" and log[0]["reason"] == "Forgot to punch"
assert c.get(f"/pdf/{ym}/{k}").status_code == 200 and c.get("/audit.csv").status_code == 200
assert c.post("/api/correct/revert", json={"ym": ym, "key": k, "date": day}).json["changed"] == 2
row = next(r for r in c.get(f"/api/employee/{ym}/{k}").json["rows"] if r["date"] == day); assert not row["corrected"] and row["kind"] == "absent"
print("corrections + audit trail OK;", len(c.get(f"/api/audit?ym={ym}&key={k}").json), "log rows")
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
cells = [{"date": day, "field": "am_in", "value": ""}, {"date": day, "field": "am_out", "value": ""}, {"date": day, "field": "merge", "value": "0-1:OFFICIAL BUSINESS"}, {"date": day, "field": "fill", "value": "2:#ffe699,7:#c6efce"}, {"date": day, "field": "remark", "value": "see memo"}]
assert c.post("/api/cells", json={"ym": ym, "key": k, "cells": cells}).json["changed"] >= 3
row = next(r for r in c.get(f"/api/employee/{ym}/{k}").json["rows"] if r["date"] == day)
assert row["spans"] == [[0, 1, "OFFICIAL BUSINESS", 0]] and row["fill"] == {"2": "#ffe699", "7": "#c6efce"} and row["note"] == "see memo"
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
print("web app OK; outputs saved:", os.listdir(os.path.join(tmp, "output")))
