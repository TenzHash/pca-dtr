"""auth.py - sign-in, accounts and permissions for the offline DTR Generator.

Everything lives in two files inside the data folder (never inside the backup zip, so a restore can
not change who is allowed to sign in):
    accounts.json   users with scrambled (PBKDF2) passwords + the hashed admin recovery code
    auth_log.csv    sign-ins, failures, lockouts, account changes (no passwords)

Roles
    admin  everything, every office
    clerk  P.O Clerk: only the offices / stations assigned to her account (see in_scope)
Nobody can change their own DTR (see is_self); the audit log records who made every change.
"""
import csv, datetime as dt, hashlib, hmac, json, math, os, re, secrets, threading, time

from schedules import PROVINCES
from zkparser import norm_key

ITER = 200_000                # PBKDF2 rounds
IDLE_SECONDS = 15 * 60        # automatic sign-out after this long without activity
MAX_FAILS = 5                 # wrong passwords before the account locks
LOCK_SECONDS = 5 * 60         # how long it stays locked
MIN_PASSWORD = 8
ROLES = ("admin", "clerk")
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"        # no 0/O/1/I/L: easy to read out loud
USER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,39}$")
LOG_COLS = ["timestamp", "event", "username", "by", "detail"]


class AuthError(Exception):
    """A problem the person can fix; the message is safe to show on screen."""


def norm_user(u):
    return re.sub(r"\s+", "", str(u or "").strip().lower())


def _now():
    return dt.datetime.now().isoformat(timespec="seconds")


def _norm_id(v):
    s = re.sub(r"\.0$", "", str(v if v is not None else "").strip())
    return s.lstrip("0") or ("0" if s else "")


def _pbkdf2(pw, salt_hex, iters):
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salt_hex), iters).hex()


def _rand(n):
    return "".join(secrets.choice(ALPHABET) for _ in range(n))


def new_temp_password():
    return _rand(10)


def new_recovery_code():
    return "-".join(_rand(4) for _ in range(5))


def _norm_code(c):
    return re.sub(r"[^A-Z0-9]", "", str(c or "").upper())


def check_new_password(pw, username=""):
    pw = pw or ""
    if len(pw) < MIN_PASSWORD:
        raise AuthError(f"The password must be at least {MIN_PASSWORD} characters.")
    if pw.strip().lower() == norm_user(username):
        raise AuthError("The password cannot be the same as the username.")
    if len(set(pw)) < 3:
        raise AuthError("That password is too easy to guess. Use a mix of different characters.")


# ------------------------------------------------------------------ office scoping
_NOISE = {"p", "o", "po", "provincial", "office", "field", "station", "area", "division", "unit"}


def office_key(heading):
    """Roster heading ('SORSOGON P.O', 'REGIONAL OFFICE V') -> short office key ('sorsogon', 'regional')."""
    h = re.sub(r"[^a-z0-9]+", " ", str(heading or "").lower()).strip()
    if not h:
        return ""
    if "regional" in h:
        return "regional"
    for p in sorted(PROVINCES):
        if p.replace("-", " ") in h:
            return p
    toks = [t for t in h.split() if t not in _NOISE]
    return "-".join(toks) or h.replace(" ", "-")


def in_scope(user, info):
    """May this account see the employee whose roster entry is `info` ({} when not in the roster)?
    Admins see everyone. A clerk sees only people whose roster office is one of her offices (and, if the
    account lists stations, whose roster division/station contains one of them). Staff who are not in
    the roster belong to nobody: only admins see them."""
    if user["role"] == "admin":
        return True
    if not info:
        return False
    if office_key(info.get("office", "")) not in set(user.get("offices") or []):
        return False
    stations = [s.lower() for s in (user.get("stations") or []) if s.strip()]
    if stations:
        unit = (info.get("unit") or "").lower()
        return any(s in unit for s in stations)
    return True


def is_self(user, emp, info):
    """Is this employee the person who owns the account? Matched by the linked roster entry and by ID
    number, so a spelling difference between files can not be used to edit your own record."""
    info = info or {}
    rk = user.get("roster_key") or ""
    if rk and (emp.key == rk or norm_key(info.get("name", "")) == rk):
        return True
    mine = _norm_id(user.get("id_no", ""))
    if mine and mine in ({_norm_id(emp.zk_id), _norm_id(info.get("id_no", ""))} - {""}):
        return True
    return False


def operator_label(user):
    return f"{user['display']} ({user['username']})"


def public(u):
    """The account without its password data."""
    out = {k: v for k, v in u.items() if k not in ("salt", "hash", "iter", "fails", "locked_until")}
    out["locked"] = u.get("locked_until", 0) > time.time()
    return out


# ------------------------------------------------------------------ the store
class Auth:
    def __init__(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        self.path = os.path.join(data_dir, "accounts.json")
        self.log_path = os.path.join(data_dir, "auth_log.csv")
        self.lock = threading.RLock()
        self.sessions = {}                      # token -> {username, last}

    # ---- file
    def _load(self):
        if not os.path.exists(self.path):
            return dict(users=[], recovery=None)
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            d.setdefault("users", [])
            return d
        except (OSError, ValueError):
            raise AuthError("The accounts file is damaged. Restore accounts.json from a copy "
                            "(an exported accounts file), or ask the administrator.")

    def _save(self, d):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        os.replace(tmp, self.path)

    def _log(self, event, username="", by="", detail=""):
        try:
            new = not os.path.exists(self.log_path)
            with open(self.log_path, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(LOG_COLS)
                w.writerow([_now(), event, username, by, detail])
        except OSError:
            pass

    def history(self, limit=150):
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        return rows[-limit:][::-1]

    @staticmethod
    def _find(d, uname):
        return next((u for u in d["users"] if u["username"] == uname), None)

    def _active_admins(self, d, ignore=None):
        return [u for u in d["users"] if u["role"] == "admin" and not u.get("disabled") and u["username"] != ignore]

    def _set_pw(self, u, pw, must_change):
        u["salt"] = secrets.token_hex(16)
        u["iter"] = ITER
        u["hash"] = _pbkdf2(pw, u["salt"], ITER)
        u["must_change"] = bool(must_change)
        u["fails"], u["locked_until"] = 0, 0
        u["updated"] = _now()

    @staticmethod
    def _check(pw, u):
        return hmac.compare_digest(_pbkdf2(pw or "", u["salt"], int(u.get("iter", ITER))), u["hash"])

    def _drop_sessions(self, uname, keep=None):
        for t in [t for t, s in self.sessions.items() if s["username"] == uname and t != keep]:
            self.sessions.pop(t, None)

    # ---- first run
    def needs_setup(self):
        with self.lock:
            return not self._load()["users"]

    def first_setup(self, username, display, password):
        with self.lock:
            d = self._load()
            if d["users"]:
                raise AuthError("Setup was already done on this PC.")
            uname = self._valid_username(username)
            check_new_password(password, uname)
            u = dict(username=uname, display=self._valid_display(display, uname), role="admin", offices=[], stations=[],
                     roster_key="", id_no="", disabled=False, created=_now())
            self._set_pw(u, password, False)
            code = new_recovery_code()
            salt = secrets.token_hex(16)
            d["users"].append(u)
            d["recovery"] = dict(salt=salt, hash=_pbkdf2(_norm_code(code), salt, ITER), iter=ITER, fails=0, locked_until=0)
            self._save(d)
            self._log("setup", uname, uname, "first administrator created")
            return public(u), code

    @staticmethod
    def _valid_username(username):
        uname = norm_user(username)
        if not USER_RE.match(uname):
            raise AuthError("The username must be 2 to 40 characters: letters, numbers, dot, dash or underscore.")
        return uname

    @staticmethod
    def _valid_display(display, uname):
        s = re.sub(r"\s+", " ", str(display or "")).strip()
        return s[:80] or uname

    # ---- sign in / out
    def login(self, username, password):
        uname = norm_user(username)
        with self.lock:
            d = self._load()
            u = self._find(d, uname)
            now = time.time()
            if u and u.get("locked_until", 0) > now:
                mins = max(1, math.ceil((u["locked_until"] - now) / 60))
                self._log("login-blocked", uname, detail="account locked")
                raise AuthError(f"Too many wrong passwords. This account is locked for {mins} more minute(s).")
            good = bool(u) and self._check(password, u)
            if not u:                                        # same work for unknown names, so timing tells nothing
                _pbkdf2(password or "", "00" * 16, ITER)
            if not good:
                if u:
                    u["fails"] = u.get("fails", 0) + 1
                    if u["fails"] >= MAX_FAILS:
                        u["fails"], u["locked_until"] = 0, now + LOCK_SECONDS
                        self._log("locked", uname, detail=f"{MAX_FAILS} wrong passwords")
                    self._save(d)
                self._log("login-failed", uname)
                raise AuthError("Wrong username or password.")
            if u.get("disabled"):
                raise AuthError("This account is turned off. Ask an administrator.")
            u["fails"], u["locked_until"] = 0, 0
            self._save(d)
            token = secrets.token_urlsafe(32)
            self.sessions[token] = dict(username=uname, last=now)
            self._log("login", uname)
            return token, public(u)

    def logout(self, token):
        with self.lock:
            s = self.sessions.pop(token, None)
            if s:
                self._log("logout", s["username"])

    def current(self, token):
        """The account behind a session cookie, or None (unknown, expired after 15 idle minutes, turned off)."""
        if not token:
            return None
        with self.lock:
            s = self.sessions.get(token)
            now = time.time()
            if not s or now - s["last"] > IDLE_SECONDS:
                if s:
                    self.sessions.pop(token, None)
                    self._log("auto-signout", s["username"], detail="idle")
                return None
            try:
                u = self._find(self._load(), s["username"])
            except AuthError:
                return None
            if not u or u.get("disabled"):
                self.sessions.pop(token, None)
                return None
            s["last"] = now
            return public(u)

    # ---- passwords
    def change_password(self, username, old, new, token=None):
        with self.lock:
            d = self._load(); u = self._find(d, norm_user(username))
            if not u or not self._check(old, u):
                raise AuthError("The current password is not correct.")
            check_new_password(new, u["username"])
            if new == old:
                raise AuthError("Choose a different password from the current one.")
            self._set_pw(u, new, False)
            self._save(d)
            self._drop_sessions(u["username"], keep=token)
            self._log("password-changed", u["username"], u["username"])

    def reset_password(self, username, by):
        with self.lock:
            d = self._load(); u = self._find(d, norm_user(username))
            if not u:
                raise AuthError("No such account.")
            temp = new_temp_password()
            self._set_pw(u, temp, True)
            self._save(d)
            self._drop_sessions(u["username"])
            self._log("password-reset", u["username"], by)
            return temp

    # ---- recovery code (admins only)
    def recover(self, code, username, new_password):
        with self.lock:
            d = self._load(); rec = d.get("recovery"); now = time.time()
            if not rec:
                raise AuthError("No recovery code is set on this PC.")
            if rec.get("locked_until", 0) > now:
                mins = max(1, math.ceil((rec["locked_until"] - now) / 60))
                raise AuthError(f"Too many wrong codes. Try again in {mins} minute(s).")
            u = self._find(d, norm_user(username))
            ok = hmac.compare_digest(_pbkdf2(_norm_code(code), rec["salt"], int(rec.get("iter", ITER))), rec["hash"])
            if not ok or not u or u["role"] != "admin":
                rec["fails"] = rec.get("fails", 0) + 1
                if rec["fails"] >= MAX_FAILS:
                    rec["fails"], rec["locked_until"] = 0, now + LOCK_SECONDS
                self._save(d)
                self._log("recovery-failed", norm_user(username))
                raise AuthError("The recovery code or the administrator username is not correct.")
            check_new_password(new_password, u["username"])
            self._set_pw(u, new_password, False)
            u["disabled"] = False
            code2 = self._new_recovery(d)                      # a recovery code works once
            self._save(d)
            self._drop_sessions(u["username"])
            self._log("recovery-used", u["username"], u["username"], "password reset with the recovery code")
            return code2

    def _new_recovery(self, d):
        code = new_recovery_code(); salt = secrets.token_hex(16)
        d["recovery"] = dict(salt=salt, hash=_pbkdf2(_norm_code(code), salt, ITER), iter=ITER, fails=0, locked_until=0)
        return code

    def new_recovery_code(self, username, password):
        with self.lock:
            d = self._load(); u = self._find(d, norm_user(username))
            if not u or u["role"] != "admin" or not self._check(password, u):
                raise AuthError("The password is not correct.")
            code = self._new_recovery(d)
            self._save(d)
            self._log("recovery-renewed", u["username"], u["username"])
            return code

    # ---- account management (the caller has already checked the role)
    def list_users(self):
        with self.lock:
            return sorted((public(u) for u in self._load()["users"]), key=lambda u: (u["role"] != "admin", u["display"].lower()))

    @staticmethod
    def _clean_scope(items):
        out = []
        for x in items or []:
            x = re.sub(r"\s+", " ", str(x)).strip().lower() if x is not None else ""
            if x and x not in out:
                out.append(x[:60])
        return out

    def create_user(self, by, username, display, role, offices=(), stations=(), roster_key="", id_no=""):
        with self.lock:
            d = self._load()
            uname = self._valid_username(username)
            if self._find(d, uname):
                raise AuthError("That username is already used on this PC.")
            if role not in ROLES:
                raise AuthError("Choose a role.")
            offices, stations = self._clean_scope(offices), self._clean_scope(stations)
            if role == "clerk" and not offices:
                raise AuthError("Choose at least one office for a P.O Clerk account.")
            u = dict(username=uname, display=self._valid_display(display, uname), role=role, offices=offices if role == "clerk" else [],
                     stations=stations if role == "clerk" else [], roster_key=str(roster_key or ""), id_no=_norm_id(id_no),
                     disabled=False, created=_now())
            temp = new_temp_password()
            self._set_pw(u, temp, True)
            d["users"].append(u)
            self._save(d)
            self._log("account-created", uname, by, f"role={role}")
            return public(u), temp

    def update_user(self, by, username, **ch):
        with self.lock:
            d = self._load(); u = self._find(d, norm_user(username))
            if not u:
                raise AuthError("No such account.")
            before = (u["role"], bool(u.get("disabled")))
            if "role" in ch:
                if ch["role"] not in ROLES:
                    raise AuthError("Choose a role.")
                u["role"] = ch["role"]
            if "display" in ch:
                u["display"] = self._valid_display(ch["display"], u["username"])
            if "offices" in ch:
                u["offices"] = self._clean_scope(ch["offices"])
            if "stations" in ch:
                u["stations"] = self._clean_scope(ch["stations"])
            if "disabled" in ch:
                u["disabled"] = bool(ch["disabled"])
            if u["role"] == "admin":
                u["offices"], u["stations"] = [], []
            elif not u["offices"]:
                raise AuthError("A P.O Clerk account needs at least one office.")
            if (u["role"], bool(u.get("disabled"))) != before and not self._active_admins(d):
                raise AuthError("There must always be at least one active administrator.")
            if (u["role"], bool(u.get("disabled"))) != before and u["username"] == norm_user(by):
                raise AuthError("You cannot change your own role or turn off your own account.")
            u["updated"] = _now()
            self._save(d)
            if u.get("disabled") or u["role"] != before[0]:
                self._drop_sessions(u["username"])
            self._log("account-updated", u["username"], by, ", ".join(f"{k}={ch[k]}" for k in sorted(ch)))
            return public(u)

    def delete_user(self, by, username):
        with self.lock:
            d = self._load(); uname = norm_user(username)
            if uname == norm_user(by):
                raise AuthError("You cannot delete your own account.")
            u = self._find(d, uname)
            if not u:
                raise AuthError("No such account.")
            if u["role"] == "admin" and not self._active_admins(d, ignore=uname):
                raise AuthError("There must always be at least one active administrator.")
            d["users"].remove(u)
            self._save(d)
            self._drop_sessions(uname)
            self._log("account-deleted", uname, by)

    def unlock(self, by, username):
        with self.lock:
            d = self._load(); u = self._find(d, norm_user(username))
            if not u:
                raise AuthError("No such account.")
            u["fails"], u["locked_until"] = 0, 0
            self._save(d)
            self._log("account-unlocked", u["username"], by)

    # ---- moving accounts between PCs (scrambled passwords only)
    def export_users(self, usernames=None):
        with self.lock:
            want = {norm_user(x) for x in usernames} if usernames else None
            users = []
            for u in self._load()["users"]:
                if want is None or u["username"] in want:
                    users.append({k: v for k, v in u.items() if k not in ("fails", "locked_until")})
            return dict(app="pca-dtr-accounts", version=1, exported=_now(), users=users)

    def import_users(self, by, data):
        """Add accounts from an export. An account that already exists is replaced only when the file's copy
        is newer; the account you are signed in as is never replaced."""
        try:
            assert data.get("app") == "pca-dtr-accounts" and isinstance(data["users"], list)
        except Exception:
            raise AuthError("This is not an accounts file exported from the DTR Generator.")
        added, updated, skipped = 0, 0, 0
        with self.lock:
            d = self._load()
            for raw in data["users"]:
                try:
                    uname = self._valid_username(raw["username"])
                    iters = int(raw.get("iter", ITER))
                    assert raw["role"] in ROLES and 10_000 <= iters <= 1_000_000
                    bytes.fromhex(raw["salt"]); assert len(raw["hash"]) == 64; int(raw["hash"], 16)
                except Exception:
                    raise AuthError("The accounts file is damaged or was edited. Nothing was imported.")
                u = dict(username=uname, display=self._valid_display(raw.get("display"), uname), role=raw["role"],
                         offices=self._clean_scope(raw.get("offices")), stations=self._clean_scope(raw.get("stations")),
                         roster_key=str(raw.get("roster_key", "")), id_no=_norm_id(raw.get("id_no", "")),
                         salt=raw["salt"], hash=raw["hash"], iter=iters, must_change=bool(raw.get("must_change")),
                         disabled=bool(raw.get("disabled")), created=str(raw.get("created") or _now()),
                         updated=str(raw.get("updated") or ""), fails=0, locked_until=0)
                if u["role"] == "clerk" and not u["offices"]:
                    raise AuthError(f"The account '{uname}' has no office. Nothing was imported.")
                cur = self._find(d, uname)
                if cur is None:
                    d["users"].append(u); added += 1
                elif uname != norm_user(by) and u["updated"] > cur.get("updated", ""):
                    d["users"][d["users"].index(cur)] = u; updated += 1
                    self._drop_sessions(uname)
                else:
                    skipped += 1
            if not self._active_admins(d):
                raise AuthError("The import would leave no active administrator. Nothing was imported.")
            self._save(d)
            self._log("accounts-imported", by=by, detail=f"added {added}, updated {updated}, skipped {skipped}")
        return dict(added=added, updated=updated, skipped=skipped)
