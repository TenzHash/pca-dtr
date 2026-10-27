"""app.py - local web app for the DTR generator (runs offline on each office PC).

    python app.py            # opens http://127.0.0.1:5810 in the browser
All data lives in a 'DTR_Data' folder next to the program (attendance files, roster,
remarks, settings, generated PDFs), so an office can back it up by copying one folder.
"""
import csv, datetime as dt, getpass, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, threading, urllib.error, urllib.parse, urllib.request, webbrowser, zipfile

from flask import Flask, abort, jsonify, request, send_file

BASE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from zkparser import load_directory, norm_key
from roster import load_roster
from schedules import PROVINCES
import generate_dtr as G
from version import VERSION

def _data_dir():
    """Dev/portable: DTR_Data beside the program. Installed .exe: Documents\\DTR Generator (always writable)."""
    if os.environ.get("DTR_DATA"):
        return os.environ["DTR_DATA"]
    portable = os.path.join(BASE, "DTR_Data")
    if not getattr(sys, "frozen", False) or os.path.isdir(portable):
        return portable
    return os.path.join(os.path.expanduser("~"), "Documents", "DTR Generator")


DATA = _data_dir()
ATT, OUT = os.path.join(DATA, "Attendance"), os.path.join(DATA, "output")
SETTINGS, REMARKS, ROSTER, AUDIT = (os.path.join(DATA, x) for x in ("settings.json", "remarks.csv", "roster.xlsx", "audit_log.csv"))
for d in (ATT, OUT):
    os.makedirs(d, exist_ok=True)

DEFAULTS = dict(office="regional", in_charge="", ot_threshold=0, holidays=[], utility="", operator="", layout="two", theme="", update_source="", division="")
OFFICES = ["regional"] + sorted(PROVINCES)
app = Flask(__name__)
_lock = threading.Lock()
_alock = threading.Lock()
_cache = {"sig": None, "months": {}, "roster": {}, "roster_sig": None}


# ------------------------------------------------------------------ storage
def settings():
    s = dict(DEFAULTS)
    if os.path.exists(SETTINGS):
        s.update(json.load(open(SETTINGS, encoding="utf-8")))
    return s


def files():
    return sorted(f for f in os.listdir(ATT) if f.lower().endswith((".xls", ".xlsx")) and not f.startswith("~$"))


def data():
    """Parsed attendance, re-read only when the folder contents change."""
    with _lock:
        sig = tuple((f, os.path.getmtime(os.path.join(ATT, f)), os.path.getsize(os.path.join(ATT, f))) for f in files())
        if sig != _cache["sig"]:
            months = load_directory(ATT, log=lambda *a: None)
            for md in months.values():
                G.auto_holidays(md, log=lambda *a: None)
            _cache.update(sig=sig, months=months)
        rsig = os.path.getmtime(ROSTER) if os.path.exists(ROSTER) else None
        if rsig != _cache["roster_sig"]:
            _cache.update(roster_sig=rsig, roster=load_roster(ROSTER) if rsig else {})
        return _cache["months"], _cache["roster"]


def read_remarks():
    if not os.path.exists(REMARKS):
        return []
    with open(REMARKS, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_remarks(rows):
    with open(REMARKS, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["employee", "date", "remark"]); w.writeheader(); w.writerows(rows)


def month_items(ym, only=None):
    months, roster = data()
    try:
        y, m = map(int, ym.split("-"))
    except ValueError:
        abort(404)
    md = months.get((y, m)) or abort(404)
    s = settings()
    extra = {dt.date.fromisoformat(h) for h in s["holidays"]}
    util = {norm_key(x) for x in s["utility"].split(",") if x.strip()}
    emps = G.month_employees(md, roster)
    if only:
        emps = [e for e in emps if e.key == only] or abort(404)
    rules = G.load_remarks(REMARKS)
    slots, post, notes = load_overrides()
    items = G.process_month(md, emps, s["office"], roster, util, rules, extra, int(s["ot_threshold"] or 0), slots, post, dict(division=s["division"], supervisor=s["in_charge"]))
    for it in items:
        it["note"] = notes.get((it["emp"].key, ym), "")
        it["sig"] = sig_path("emp", it["emp"].key)
    return md, items, s


SIG = os.path.join(DATA, "signatures")


def sig_path(kind, key=""):
    n = "incharge" if kind == "incharge" else "emp_" + re.sub(r"[^a-z]", "", key)
    for ext in ("png", "jpg"):
        p = os.path.join(SIG, f"{n}.{ext}")
        if os.path.exists(p):
            return p


def _sig_clear(kind, key):
    p = sig_path(kind, key)
    while p:
        os.remove(p); p = sig_path(kind, key)


@app.post("/api/signature")
def sig_upload():
    kind, key, f = request.form.get("kind", "emp"), request.form.get("key", ""), request.files.get("file")
    ext = os.path.splitext(f.filename or "")[1].lower().lstrip(".") if f else ""
    if ext not in ("png", "jpg", "jpeg"):
        return jsonify(error="Use a PNG or JPG image."), 400
    os.makedirs(SIG, exist_ok=True); _sig_clear(kind, key)
    n = "incharge" if kind == "incharge" else "emp_" + re.sub(r"[^a-z]", "", key)
    f.save(os.path.join(SIG, f"{n}.{'png' if ext == 'png' else 'jpg'}"))
    return jsonify(ok=True)


@app.post("/api/signature/delete")
def sig_delete():
    _sig_clear(request.json.get("kind", "emp"), request.json.get("key", ""))
    return jsonify(ok=True)


@app.get("/sig/<kind>/<key>")
def sig_get(kind, key):
    p = sig_path(kind, key)
    return send_file(p) if p else abort(404)


# ------------------------------------------------------------------ backup / restore
KEEP = ("Attendance", "signatures", "settings.json", "remarks.csv", "roster.xlsx", "audit_log.csv")


def make_backup_zip(target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(dict(app="pca-dtr", version=VERSION, created=dt.datetime.now().isoformat(timespec="seconds"))))
        for name in KEEP:
            p = os.path.join(DATA, name)
            if os.path.isfile(p):
                z.write(p, name)
            elif os.path.isdir(p):
                for root, _, fs in os.walk(p):
                    for f in fs:
                        fp = os.path.join(root, f); z.write(fp, os.path.relpath(fp, DATA))


def auto_backup():
    """One automatic backup per day in DATA/backups (last 10 kept)."""
    if not any(os.path.exists(os.path.join(DATA, n)) for n in KEEP):
        return
    d = os.path.join(DATA, "backups"); os.makedirs(d, exist_ok=True)
    t = os.path.join(d, f"auto_{dt.date.today():%Y%m%d}.zip")
    if not os.path.exists(t):
        make_backup_zip(t)
    for old in sorted(f for f in os.listdir(d) if f.endswith(".zip"))[:-10]:
        os.remove(os.path.join(d, old))


@app.get("/backup")
def backup():
    buf = io.BytesIO(); make_backup_zip(buf); buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"DTR_Backup_{dt.datetime.now():%Y%m%d_%H%M}.zip")


@app.post("/api/restore")
def restore():
    f = request.files.get("file")
    try:
        z = zipfile.ZipFile(f.stream)
        if json.loads(z.read("manifest.json")).get("app") != "pca-dtr":
            raise ValueError
    except Exception:
        return jsonify(error="This is not a DTR Generator backup file."), 400
    names = [n for n in z.namelist() if n != "manifest.json" and not n.endswith("/")]
    if any(n.startswith(("/", "..")) or ".." in n.split("/") or n.split("/")[0] not in KEEP for n in names):
        return jsonify(error="The backup contains unexpected files and was not restored."), 400
    os.makedirs(os.path.join(DATA, "backups"), exist_ok=True)
    make_backup_zip(os.path.join(DATA, "backups", f"before_restore_{dt.datetime.now():%Y%m%d_%H%M%S}.zip"))
    for n in KEEP:                                     # replace, not merge
        p = os.path.join(DATA, n)
        shutil.rmtree(p) if os.path.isdir(p) else (os.remove(p) if os.path.exists(p) else None)
    for n in names:
        dest = os.path.join(DATA, *n.split("/")); os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as out:
            out.write(z.read(n))
    os.makedirs(ATT, exist_ok=True); _cache.update(sig=None, roster_sig=None)
    return jsonify(ok=True, files=len(names))


# ------------------------------------------------------------------ updates
def _default_source():
    """Location baked into the installer (update_source.txt), so office staff never type anything."""
    try:
        for ln in open(os.path.join(BASE, "update_source.txt"), encoding="utf-8-sig"):
            if ln.strip() and not ln.lstrip().startswith("#"):
                return ln.strip()
    except OSError:
        pass
    return ""


def _update_info():
    src = settings().get("update_source", "").strip() or _default_source()
    base = dict(configured=bool(src), current=VERSION, available=False)
    if not src:
        return base
    try:
        web = src.lower().startswith("http")
        if web:
            with urllib.request.urlopen(src, timeout=8) as r:
                m = json.loads(r.read().decode("utf-8-sig"))
            inst = urllib.parse.urljoin(src, m["file"])
        else:
            p = src if src.lower().endswith(".json") else os.path.join(src, "latest.json")
            m = json.load(open(p, encoding="utf-8-sig")); inst = os.path.join(os.path.dirname(p), m["file"])
        newer = tuple(map(int, m["version"].split("."))) > tuple(map(int, VERSION.split(".")))
        return dict(base, latest=m["version"], available=newer, installer=inst, sha256=str(m.get("sha256", "")).lower())
    except urllib.error.HTTPError as e:
        return dict(base, error=f"HTTP {e.code}", code=e.code)
    except Exception as e:
        return dict(base, error=f"Could not read the update source: {e}")


@app.get("/api/update/check")
def update_check():
    i = _update_info(); i.pop("installer", None); i.pop("sha256", None)
    return jsonify(i)


@app.post("/api/update/install")
def update_install():
    if not getattr(sys, "frozen", False):
        return jsonify(error="Updates can only be installed from the installed program."), 400
    i = _update_info()
    if not i.get("available") or len(i.get("sha256", "")) != 64:
        return jsonify(error="No verified update is available."), 400
    dest = os.path.join(tempfile.mkdtemp(prefix="DTR_Update_"), "DTR_Generator_Setup.exe")
    try:
        if i["installer"].lower().startswith("http"):
            urllib.request.urlretrieve(i["installer"], dest)
        else:
            shutil.copy(i["installer"], dest)
    except Exception as e:
        return jsonify(error=f"Download failed: {e}"), 400
    if hashlib.sha256(open(dest, "rb").read()).hexdigest() != i["sha256"]:
        os.remove(dest)
        return jsonify(error="The downloaded update failed its integrity check and was not installed."), 400
    auto_backup()
    subprocess.Popen([dest, "/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS", "/NOCANCEL"], creationflags=0x00000008)
    threading.Timer(1.5, lambda: os._exit(0)).start()
    return jsonify(ok=True)


# ------------------------------------------------------------------ API
@app.get("/api/state")
def state():
    months, roster = data()
    return jsonify(version=VERSION, settings=settings(), files=files(), offices=OFFICES, roster=bool(roster),
                   months=[f"{y}-{m:02d}" for (y, m) in sorted(months)], remarks=read_remarks())


@app.post("/api/settings")
def save_settings():
    s = settings(); s.update({k: v for k, v in request.json.items() if k in DEFAULTS})
    if s["office"] not in OFFICES:
        abort(400)
    json.dump(s, open(SETTINGS, "w", encoding="utf-8"), indent=2)
    return jsonify(ok=True)


@app.post("/api/upload")
def upload():
    kind = request.form.get("kind", "attendance")
    for f in request.files.getlist("files"):
        name = os.path.basename(f.filename)
        if kind == "roster":
            f.save(ROSTER)
        elif name.lower().endswith((".xls", ".xlsx")):
            f.save(os.path.join(ATT, name))
    return jsonify(ok=True)


@app.post("/api/delete_file")
def delete_file():
    p = os.path.join(ATT, os.path.basename(request.json["name"]))
    if os.path.exists(p):
        os.remove(p)
    return jsonify(ok=True)


@app.get("/api/month/<ym>")
def month(ym):
    md, items, s = month_items(ym)
    return jsonify(holidays=sorted(d.isoformat() for d in md.holidays), office=s["office"],
                   employees=[dict(key=i["emp"].key, **i["summary"]) for i in items])


@app.get("/api/employee/<ym>/<key>")
def employee(ym, key):
    md, items, s = month_items(ym, key)
    it = items[0]; f = fmt_hm
    sl, po, notes = load_overrides()
    ovd = {d: [ui for ui, s_ in UI2SLOT.items() if s_ in v] for (k2, d), v in sl.items() if k2 == key}
    for (k2, d), v in po.items():
        if k2 == key:
            ovd.setdefault(d, []).extend(v)
    rows = []
    for r in it["res"]:
        if r.kind == "nodata":
            continue
        date = dt.date(md.year, md.month, r.day)
        rows.append(dict(date=date.isoformat(), dow=date.strftime("%a"), am_in=f(r.am_arr), am_out=f(r.am_dep),
                         pm_in=f(r.pm_arr), pm_out=f(r.pm_dep), ut=r.ut, ot=r.ot, kind=r.kind, corrected=r.corrected, fill=r.fill,
                         spans=[[x, y, t, 0] for x, y, t in r.spans] or ([[0, 3, "; ".join(r.notes), 1]] if r.kind == "remark" else []),
                         ov=ovd.get(date, []),
                         note="; ".join(r.notes), review="; ".join(r.review)))
    return jsonify(name=it["name"], sched=it["summary"]["sched"], rows=rows, note=notes.get((key, ym), ""), office=s["office"], id_no=it["id_no"], office_label=it["office_label"], division=it["division"], supervisor=it["supervisor"], sup_roster=it["sup_roster"],
                   sig_emp=bool(sig_path("emp", key)), sig_inc=bool(sig_path("incharge")))


@app.post("/api/remarks")
def add_remark():
    j = request.json
    rows = read_remarks()
    if not j.get("remark", "").strip() or not j.get("start"):
        abort(400)
    d = j["start"] + (":" + j["end"] if j.get("end") and j["end"] != j["start"] else "")
    rows.append(dict(employee=j.get("employee") or "*", date=d, remark=j["remark"].strip().upper()))
    write_remarks(rows)
    return jsonify(ok=True)


@app.post("/api/remarks/delete")
def del_remark():
    rows = read_remarks(); i = int(request.json["index"])
    if 0 <= i < len(rows):
        rows.pop(i); write_remarks(rows)
    return jsonify(ok=True)



# ------------------------------------------------------------------ manual corrections + audit trail
UI2SLOT = {"am_in": "am_arr", "am_out": "am_dep", "pm_in": "pm_arr", "pm_out": "pm_dep"}
AUDIT_COLS = ["timestamp", "operator", "employee_key", "employee", "date", "field", "old", "new", "reason"]
REVERT = "__REVERT__"


def audit_rows():
    if not os.path.exists(AUDIT):
        return []
    with open(AUDIT, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def audit_append(rows):
    with _alock:
        new = not os.path.exists(AUDIT)
        with open(AUDIT, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=AUDIT_COLS)
            if new:
                w.writeheader()
            w.writerows(rows)


def parse_hm(s):
    s = (s or "").strip()
    if not s:
        return None
    m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", s)
    if not m:
        raise ValueError(f"'{s}' is not a valid time. Use 24-hour HH:MM, e.g. 17:05.")
    return int(m.group(1)) * 60 + int(m.group(2))


def fmt_hm(v):
    return "" if v is None else f"{v // 60:02d}:{v % 60:02d}"


POST_FIELDS = ("ut", "ot", "remark", "merge", "fill")


def load_overrides():
    """Latest audit entry per (employee, date, field) wins; a revert removes the override.
    Returns (time-slot overrides, ut/ot/remark overrides, monthly notes)."""
    slots, post, notes = {}, {}, {}
    for r in audit_rows():
        f, k = r["field"], (r["employee_key"], dt.date.fromisoformat(r["date"]))
        if f == "month_note":
            notes[(r["employee_key"], r["date"][:7])] = r["new"]
        elif f in UI2SLOT:
            if r["new"] == REVERT:
                slots.get(k, {}).pop(UI2SLOT[f], None)
            else:
                slots.setdefault(k, {})[UI2SLOT[f]] = parse_hm(r["new"])
        elif f in POST_FIELDS:
            if r["new"] == REVERT:
                post.get(k, {}).pop(f, None)
            else:
                post.setdefault(k, {})[f] = int(r["new"] or 0) if f in ("ut", "ot") else r["new"]
    return ({k: v for k, v in slots.items() if v}, {k: v for k, v in post.items() if v}, notes)


def operator_name():
    return settings().get("operator", "").strip() or getpass.getuser()


@app.post("/api/correct")
def correct():
    j = request.json
    reason = (j.get("reason") or "").strip()
    if not reason:
        return jsonify(error="A reason is required for every correction."), 400
    md, items, s = month_items(j["ym"], j["key"])
    it = items[0]
    r = it["res"][int(j["date"][8:]) - 1]
    cur = dict(am_in=r.am_arr, am_out=r.am_dep, pm_in=r.pm_arr, pm_out=r.pm_dep)
    ts = dt.datetime.now().isoformat(timespec="seconds"); rows = []
    try:
        for ui, val in j["edits"].items():
            if ui not in UI2SLOT:
                continue
            new = parse_hm(val)
            if new != cur[ui]:
                rows.append(dict(timestamp=ts, operator=operator_name(), employee_key=j["key"], employee=it["name"],
                                 date=j["date"], field=ui, old=fmt_hm(cur[ui]), new=fmt_hm(new), reason=reason))
    except ValueError as e:
        return jsonify(error=str(e)), 400
    if rows:
        audit_append(rows)
    return jsonify(ok=True, changed=len(rows))


@app.post("/api/cells")
def cells():
    """Excel-style edits: [{date, field, value}] for time cells, ut / ot (minutes), remark, month_note."""
    j = request.json
    reason = (j.get("reason") or "").strip() or "Manual edit"
    md, items, s = month_items(j["ym"], j["key"])
    it = items[0]; ts = dt.datetime.now().isoformat(timespec="seconds"); rows = []
    try:
        for c in j["cells"]:
            f, date, val = c["field"], c.get("date") or f"{j['ym']}-01", str(c.get("value", "")).strip()
            if f == "month_note":
                old = ""
            else:
                r = it["res"][int(date[8:]) - 1]
                old = {"am_in": fmt_hm(r.am_arr), "am_out": fmt_hm(r.am_dep), "pm_in": fmt_hm(r.pm_arr),
                       "pm_out": fmt_hm(r.pm_dep), "ut": str(r.ut), "ot": str(r.ot), "remark": "; ".join(r.notes),
                       "merge": G.ser_spans(r.spans), "fill": G.ser_fill(r.fill)}[f]
                if f in UI2SLOT:
                    val = fmt_hm(parse_hm(val))
                elif f in ("merge", "fill"):
                    val = val.replace("\n", " ")
                elif f in ("ut", "ot"):
                    val = str(max(0, int(float(val or 0))))
            if val != old:
                rows.append(dict(timestamp=ts, operator=operator_name(), employee_key=j["key"], employee=it["name"],
                                 date=date, field=f, old=old, new=val, reason=reason))
    except (ValueError, KeyError) as e:
        return jsonify(error=str(e)), 400
    if rows:
        audit_append(rows)
    return jsonify(ok=True, changed=len(rows))


@app.post("/api/correct/revert")
def revert():
    j = request.json
    k = (j["key"], dt.date.fromisoformat(j["date"]))
    ov = load_overrides()[0].get(k, {}); pov = load_overrides()[1].get(k, {})
    md, items, s = month_items(j["ym"], j["key"])
    it = items[0]; r = it["res"][int(j["date"][8:]) - 1]
    cur = dict(am_arr=r.am_arr, am_dep=r.am_dep, pm_arr=r.pm_arr, pm_dep=r.pm_dep)
    ts = dt.datetime.now().isoformat(timespec="seconds")
    rows = [dict(timestamp=ts, operator=operator_name(), employee_key=j["key"], employee=it["name"], date=j["date"],
                 field=ui, old=fmt_hm(cur[slot]), new=REVERT,
                 reason=(j.get("reason") or "").strip() or "Reverted to biometric record")
            for ui, slot in UI2SLOT.items() if slot in ov]
    rows += [dict(timestamp=ts, operator=operator_name(), employee_key=j["key"], employee=it["name"], date=j["date"],
                  field=f, old="", new=REVERT, reason="Reverted to biometric record") for f in pov]
    if rows:
        audit_append(rows)
    return jsonify(ok=True, changed=len(rows))


@app.get("/api/audit")
def audit():
    key, ym = request.args.get("key"), request.args.get("ym", "")
    rows = [r for r in audit_rows() if (not key or r["employee_key"] == key) and r["date"].startswith(ym)]
    return jsonify(rows[::-1])


@app.get("/audit.csv")
def audit_csv():
    if not os.path.exists(AUDIT):
        audit_append([])
    return send_file(AUDIT, as_attachment=True, download_name="audit_log.csv")


# ------------------------------------------------------------------ downloads
def _pdf(ym, key=None, download=False):
    md, items, s = month_items(ym, key)
    buf = io.BytesIO()
    G.render_pdf(buf, items, md.year, md.month, s["office"], s["in_charge"], request.args.get("layout") or s["layout"], sig_path("incharge"))
    buf.seek(0)
    name = f"DTR_{s['office']}_{ym}" + (f"_{key}" if key else "") + ".pdf"
    if not key:
        open(os.path.join(OUT, name), "wb").write(buf.getvalue())      # keep a copy for the office records
    return send_file(buf, mimetype="application/pdf", download_name=name, as_attachment=download)


@app.get("/pdf/<ym>")
def pdf_all(ym): return _pdf(ym, download=True)


@app.get("/pdf/<ym>/<key>")
def pdf_one(ym, key): return _pdf(ym, key, download=request.args.get("download") == "1")


@app.get("/xlsx/<ym>")
def xlsx(ym):
    md, items, s = month_items(ym)
    path = os.path.join(OUT, f"DTR_{s['office']}_{ym}_summary.xlsx")
    detail = [(i["name"], dt.date(md.year, md.month, r.day), r) for i in items for r in i["res"] if r.kind != "nodata"]
    G.write_summary(path, [i["summary"] for i in items], detail)
    return send_file(path, as_attachment=True)


@app.get("/zip/<ym>")
def zip_individual(ym):
    md, items, s = month_items(ym)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for it in items:
            one = io.BytesIO()
            G.render_pdf(one, [it], md.year, md.month, s["office"], s["in_charge"], s["layout"], sig_path("incharge"))
            z.writestr(f"{it['name'].replace(',', '').replace('.', '')}.pdf", one.getvalue())
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"DTR_{s['office']}_{ym}_individual.zip")


@app.get("/")
def index():
    return PAGE


from ui import PAGE  # noqa: E402  (HTML kept in its own file)


def main(port=5810):
    auto_backup()
    url = f"http://127.0.0.1:{port}"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"DTR Generator running at {url}  (close this window to stop)")
    app.run(host="127.0.0.1", port=port, threaded=True)


if __name__ == "__main__":
    main()
