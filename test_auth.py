"""Checks for sign-in, roles, office scoping and the self-edit rule.   python test_auth.py
Builds a made-up roster and attendance file in a temporary folder (no real data needed)."""
import io, json, os, re, tempfile, time

tmp = tempfile.mkdtemp(); os.environ["DTR_DATA"] = tmp
import openpyxl
import app as APP
import auth as A

PEOPLE = [  # name, roster office heading, division/station, id
    ("SANTOS, ANA", "SORSOGON P.O", "OPERATIONS", "101"),
    ("REYES, BEN", "SORSOGON P.O", "OPERATIONS", "102"),
    ("CRUZ, CARL", "MASBATE P.O", "OPERATIONS", "103"),
    ("LIM, DINA", "REGIONAL OFFICE V", "FINANCE", "104"),
    ("ALBAY, ALMA", "CATANDUANES P.O", "ALBAY FIELD STATION", "105"),
    ("CATAN, CELSO", "CATANDUANES P.O", "CATANDUANES STATION", "106"),
]
STRANGER = ("NOROSTER, NIDA", "900")           # punches but is not in the roster


def build_files():
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Attendance Record"
    ws.append(["Attendance Record Report"]); ws.append(["Att. Time", "2026-08-01 ~ 2026-08-31"])
    ws.append(list(range(1, 32)))
    for name, idn in [(p[0].replace(" ", ""), p[3]) for p in PEOPLE] + [(STRANGER[0].replace(" ", ""), STRANGER[1])]:
        ws.append(["ID:", idn, None, "Name:", name])
        row = [None] * 31
        for d in (3, 4, 5, 6, 7):
            row[d - 1] = "08:00 17:00"
        ws.append(row)
    att = os.path.join(tmp, "att.xlsx"); wb.save(att)
    wr = openpyxl.Workbook(); w = wr.active; w.title = "Regular"
    w.append(["ITEM", "NAME", "POSITION", "DIVISION", "SUPERVISOR", "ID NO.", "REMARKS"])
    cur = None
    for i, (n, off, unit, idn) in enumerate(PEOPLE, 1):
        if off != cur:
            w.append([off]); cur = off
        w.append([i, n, "CLERK", unit, "BOSS, B.", idn, ""])
    ros = os.path.join(tmp, "roster.xlsx"); wr.save(ros)
    return att, ros


def ok(r, code=200):
    assert r.status_code == code, (r.status_code, r.get_data(as_text=True)[:200])
    return r.json if r.is_json else None


def client():
    return APP.app.test_client()


def login(c, u, p, code=200):
    return ok(c.post("/api/login", json={"username": u, "password": p}), code)


def names(c, ym="2026-08"):
    return sorted(e["name"] for e in ok(c.get(f"/api/month/{ym}"))["employees"])


# ---------------------------------------------------------------- first run, sign-in required
adm = client()
assert adm.get("/api/me").json == {"setup": True}
for url in ("/api/state", "/api/month/2026-08", "/backup", "/audit.csv", "/pdf/2026-08"):
    assert adm.get(url).status_code == 401, url
assert adm.post("/api/upload", data={}).status_code == 401
assert adm.get("/").status_code == 200                       # the page itself holds no data
ok(adm.post("/api/setup", json={"username": "admin1", "display": "Ana Admin", "password": "short"}), 400)
ok(adm.post("/api/setup", json={"username": "admin1", "display": "Ana Admin", "password": "admin1"}), 400)
r = ok(adm.post("/api/setup", json={"username": "Admin1", "display": "Rina Admin", "password": "Correct-Horse-1"}))
assert re.fullmatch(r"([A-Z2-9]{4}-){4}[A-Z2-9]{4}", r["recovery"]) and r["user"]["role"] == "admin"
RECOVERY = r["recovery"]
ok(client().post("/api/setup", json={"username": "x1", "display": "X", "password": "Correct-Horse-2"}), 400)   # only once
acc = open(os.path.join(tmp, "accounts.json"), encoding="utf-8").read()
assert "Correct-Horse-1" not in acc and RECOVERY not in acc and "pbkdf2" not in acc.lower() and '"hash"' in acc
print("setup + sign-in required OK")

att, ros = build_files()
for f, kind in ((att, "attendance"), (ros, "roster")):
    with open(f, "rb") as fh:
        ok(adm.post("/api/upload", data={"files": (fh, os.path.basename(f)), "kind": kind}, content_type="multipart/form-data"))
assert len(names(adm)) == 7                                   # admins see everyone
em = {e["name"]: e for e in ok(adm.get("/api/month/2026-08"))["employees"]}
assert [n for n, e in em.items() if e["unassigned"]] == ["NOROSTER, NIDA"], "staff missing from the roster are listed apart"
print("admin sees all, roster-less staff flagged OK")

# ---------------------------------------------------------------- accounts and temporary passwords
pe = {p["name"]: p for p in ok(adm.get("/api/accounts"))["people"]}
assert pe["SANTOS, ANA"]["office"] == "sorsogon" and pe["LIM, DINA"]["office"] == "regional" and pe["ALBAY, ALMA"]["office"] == "catanduanes"
def mk(c, **kw):
    return ok(c.post("/api/accounts/create", json=kw))
t1 = mk(adm, username="101", display="Ana Santos", role="clerk", offices=["sorsogon"], roster_key="santosana", id_no="101")
t2 = mk(adm, username="102", display="Ben Reyes", role="clerk", offices=["sorsogon"], roster_key="reyesben", id_no="102")
t3 = mk(adm, username="alma", display="Alma Albay", role="clerk", offices=["catanduanes"], stations=["albay"])
ok(adm.post("/api/accounts/create", json=dict(username="bad", display="B", role="clerk", offices=[])), 400)     # a clerk needs an office
ok(adm.post("/api/accounts/create", json=dict(username="101", display="dup", role="clerk", offices=["x"])), 400)
assert len(t1["temp"]) == 10 and t1["temp"] != t2["temp"]
ana = client()
login(ana, "101", "wrong", 400)
login(ana, "101", t1["temp"])
assert ana.get("/api/state").status_code == 403, "must choose a new password first"
ok(ana.post("/api/password", json={"old": t1["temp"], "new": "abc"}), 400)
ok(ana.post("/api/password", json={"old": "nope", "new": "Another-Pass-9"}), 400)
ok(ana.post("/api/password", json={"old": t1["temp"], "new": "Another-Pass-9"}))
assert ana.get("/api/state").status_code == 200
print("accounts, temporary password, forced change OK")

# ---------------------------------------------------------------- office scoping for a clerk
assert names(ana) == ["REYES, BEN", "SANTOS, ANA"], names(ana)
k_cruz = "cruzcarl"; k_reyes = "reyesben"; k_santos = "santosana"
assert ana.get(f"/api/employee/2026-08/{k_cruz}").status_code == 404
assert ana.get(f"/pdf/2026-08/{k_cruz}").status_code == 404
assert ana.get("/pdf/2026-08").status_code == 200 and ana.get("/zip/2026-08").status_code == 200 and ana.get("/xlsx/2026-08").status_code == 200
ok(ana.post("/api/correct", json={"ym": "2026-08", "key": k_cruz, "date": "2026-08-03", "edits": {"am_in": "08:01"}, "reason": "x"}), 403)
ok(ana.post("/api/cells", json={"ym": "2026-08", "key": "norosternida", "cells": [{"date": "2026-08-03", "field": "ot", "value": "5"}]}), 403)
ok(ana.post("/api/remarks", json={"employee": k_cruz, "start": "2026-08-10", "remark": "leave"}), 403)
ok(ana.post("/api/remarks", json={"employee": "*", "start": "2026-08-10", "remark": "holiday"}), 403)
for url in ("/backup", "/audit.csv", "/api/accounts", "/accounts.json", "/api/update/check", "/api/accounts/history"):
    assert ana.get(url).status_code == 403, url
ok(ana.post("/api/restore", data={}, content_type="multipart/form-data"), 403)
ok(ana.post("/api/delete_file", json={"name": "att.xlsx"}), 403)
ok(ana.post("/api/upload", data={"files": (io.BytesIO(b"x"), "r.xlsx"), "kind": "roster"}, content_type="multipart/form-data"), 403)
ok(ana.post("/api/signature", data={"kind": "incharge", "key": "x", "file": (io.BytesIO(b"x"), "s.png")}, content_type="multipart/form-data"), 403)
ok(ana.post("/api/accounts/create", json=dict(username="evil", display="E", role="admin")), 403)
ok(ana.post("/api/settings", json={"office": "naga", "theme": "dark", "update_source": "http://evil"}))
st = ana.get("/api/state").json; assert st["settings"]["theme"] == "dark" and st["settings"]["office"] == "regional", "clerk may only change theme / layout"
assert "update_source" not in st["settings"]
print("clerk scoping + admin-only areas OK")

# ---------------------------------------------------------------- nobody edits their own record; others can
ok(ana.post("/api/cells", json={"ym": "2026-08", "key": k_santos, "cells": [{"date": "2026-08-03", "field": "ot", "value": "5"}]}), 403)
ok(ana.post("/api/correct", json={"ym": "2026-08", "key": k_santos, "date": "2026-08-03", "edits": {"am_in": "08:01"}, "reason": "x"}), 403)
ok(ana.post("/api/remarks", json={"employee": k_santos, "start": "2026-08-10", "remark": "leave"}), 403)
assert ana.get(f"/api/employee/2026-08/{k_santos}").json["own"] is True        # she can still view / print it
assert ana.get(f"/pdf/2026-08/{k_santos}").status_code == 200
ok(ana.post("/api/cells", json={"ym": "2026-08", "key": k_reyes, "reason": "Forgot to punch", "cells": [{"date": "2026-08-03", "field": "ot", "value": "5"}]}))
ok(ana.post("/api/remarks", json={"employee": k_reyes, "start": "2026-08-10", "remark": "leave"}))
ben = client(); login(ben, "102", t2["temp"]); ok(ben.post("/api/password", json={"old": t2["temp"], "new": "Another-Pass-8"}))
ok(ben.post("/api/cells", json={"ym": "2026-08", "key": k_reyes, "cells": [{"date": "2026-08-04", "field": "ot", "value": "5"}]}), 403)
ok(ben.post("/api/cells", json={"ym": "2026-08", "key": k_santos, "reason": "ben edits ana", "cells": [{"date": "2026-08-04", "field": "ot", "value": "7"}]}))
# the admin who owns a roster entry is blocked too
adm2 = mk(adm, username="lim", display="Dina Lim", role="admin", roster_key="limdina", id_no="104")
dina = client(); login(dina, "lim", adm2["temp"]); ok(dina.post("/api/password", json={"old": adm2["temp"], "new": "Another-Pass-7"}))
ok(dina.post("/api/cells", json={"ym": "2026-08", "key": "limdina", "cells": [{"date": "2026-08-03", "field": "ot", "value": "5"}]}), 403)
ok(dina.post("/api/cells", json={"ym": "2026-08", "key": k_cruz, "cells": [{"date": "2026-08-03", "field": "ot", "value": "5"}]}))
ok(adm.post("/api/cells", json={"ym": "2026-08", "key": "limdina", "cells": [{"date": "2026-08-03", "field": "ot", "value": "5"}]}))     # the other admin may
# audit: who made the change is the signed-in account, not a typed name
adm.post("/api/settings", json={"operator": "Someone Else"})
rows = ok(adm.get("/api/audit?ym=&key="))
assert {r["operator"] for r in rows} == {"Ana Santos (101)", "Ben Reyes (102)", "Dina Lim (lim)", "Rina Admin (admin1)"}, {r["operator"] for r in rows}
mine = ok(ana.get("/api/audit?ym=&key="))
assert mine and all(r["operator"] == "Ana Santos (101)" for r in mine), "a clerk sees only her own audit entries"
print("self-edit block + audit identity OK")

# ---------------------------------------------------------------- stations (Albay vs Catanduanes)
alma = client(); login(alma, "alma", t3["temp"]); ok(alma.post("/api/password", json={"old": t3["temp"], "new": "Another-Pass-6"}))
assert names(alma) == ["ALBAY, ALMA"], names(alma)
ok(adm.post("/api/accounts/update", json={"username": "alma", "stations": []}))
assert names(alma) == ["ALBAY, ALMA", "CATAN, CELSO"]
print("station filter OK")

# ---------------------------------------------------------------- lockout and idle timeout
x = client()
for _ in range(4):
    login(x, "102", "wrong-wrong", 400)
msg = login(x, "102", "wrong-wrong", 400)["error"]
assert "Wrong" in msg
msg = login(x, "102", "Another-Pass-8", 400)["error"]; assert "locked" in msg, msg           # right password, still locked
APP.AUTH.lock.acquire(); d = APP.AUTH._load(); [u.update(locked_until=time.time() - 1) for u in d["users"]]; APP.AUTH._save(d); APP.AUTH.lock.release()
login(x, "102", "Another-Pass-8")
assert LOCK_OK if (LOCK_OK := A.LOCK_SECONDS == 300 and A.MAX_FAILS == 5 and A.IDLE_SECONDS == 900) else False
tok = next(iter(APP.AUTH.sessions))
for t in APP.AUTH.sessions: APP.AUTH.sessions[t]["last"] -= A.IDLE_SECONDS + 5
assert ana.get("/api/state").status_code == 401, "signed out after 15 idle minutes"
login(ana, "101", "Another-Pass-9"); assert ana.get("/api/state").status_code == 200
ana.post("/api/logout"); assert ana.get("/api/state").status_code == 401
print("lockout + idle timeout OK")

# ---------------------------------------------------------------- admin management guards
login(adm, "admin1", "Correct-Horse-1")
ok(adm.post("/api/accounts/update", json={"username": "admin1", "role": "clerk", "offices": ["naga"]}), 400)
ok(adm.post("/api/accounts/delete", json={"username": "admin1"}), 400)
ok(adm.post("/api/accounts/update", json={"username": "admin1", "disabled": True}), 400)
ok(adm.post("/api/accounts/update", json={"username": "lim", "disabled": True}))
dd = client(); login(dd, "lim", "Another-Pass-7", 400)
ok(adm.post("/api/accounts/update", json={"username": "lim", "disabled": False}))
tmp_pw = ok(adm.post("/api/accounts/reset", json={"username": "102"}))["temp"]
assert ben.get("/api/state").status_code == 401, "reset signs the person out"
login(client(), "102", tmp_pw)
print("admin guards + reset OK")

# ---------------------------------------------------------------- recovery code
r = client()
ok(r.post("/api/recover", json={"code": "AAAA-BBBB-CCCC-DDDD-EEEE", "username": "admin1", "password": "Brand-New-Pass-1"}), 400)
ok(r.post("/api/recover", json={"code": RECOVERY, "username": "102", "password": "Brand-New-Pass-1"}), 400)       # clerks can't use it
new_code = ok(r.post("/api/recover", json={"code": RECOVERY.lower(), "username": "admin1", "password": "Brand-New-Pass-1"}))["recovery"]
assert new_code != RECOVERY
ok(client().post("/api/recover", json={"code": RECOVERY, "username": "admin1", "password": "Brand-New-Pass-2"}), 400)  # works once
login(client(), "admin1", "Brand-New-Pass-1")
print("recovery code OK")

# ---------------------------------------------------------------- move accounts to another PC
login(adm, "admin1", "Brand-New-Pass-1")
exp = adm.get("/accounts.json?users=101,lim")
blob = json.loads(exp.data)
assert {u["username"] for u in blob["users"]} == {"101", "lim"} and all("salt" in u and "hash" in u for u in blob["users"])
other = A.Auth(tempfile.mkdtemp())
other.first_setup("rootadmin", "Root", "Root-Pass-123")
print("import:", other.import_users("rootadmin", blob))
assert {u["username"] for u in other.list_users()} == {"rootadmin", "101", "lim"}
tk, u = other.login("101", "Another-Pass-9"); assert u["role"] == "clerk"
assert other.import_users("rootadmin", blob)["skipped"] == 2
for bad in ({"app": "x"}, {"app": "pca-dtr-accounts", "users": [{"username": "a1", "role": "admin", "salt": "zz", "hash": "1"}]}):
    try: other.import_users("rootadmin", bad); raise SystemExit("bad import accepted")
    except A.AuthError: pass
ok(adm.post("/api/accounts/import", data={"file": (io.BytesIO(exp.data), "a.json")}, content_type="multipart/form-data"))
ok(adm.post("/api/accounts/import", data={"file": (io.BytesIO(b"nope"), "a.json")}, content_type="multipart/form-data"), 400)
# backups never carry accounts, and a restore leaves them alone
bk = adm.get("/backup"); import zipfile
assert not any("accounts" in n or "auth_log" in n for n in zipfile.ZipFile(io.BytesIO(bk.data)).namelist())
ok(adm.post("/api/restore", data={"file": (io.BytesIO(bk.data), "b.zip")}, content_type="multipart/form-data"))
login(client(), "101", "Another-Pass-9")
hist = ok(adm.get("/api/accounts/history")); assert any(h["event"] == "locked" for h in hist) and "Another-Pass" not in json.dumps(hist)
print("export / import, backup isolation, sign-in history OK")
print("ALL AUTH CHECKS PASSED")
