"""auth.py - accounts for the DTR Generator. Only salted password hashes are stored, never passwords.

Roles: 'admin' (everything) and 'clerk' (P.O Clerk: only the staff of their own office). Accounts live in
DATA/users.json on each PC; they can be exported from one PC and imported on another."""
import datetime as dt
import json
import os
import re
import secrets
import threading
import time

from werkzeug.security import check_password_hash, generate_password_hash

MAX_FAILS, LOCK_SECS, IDLE_SECS, MIN_PW = 5, 300, 900, 8
_PW = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
_RC = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_lk = threading.RLock()
_USER = re.compile(r"^[a-z0-9._-]{3,30}$")


def temp_password():
    return "".join(secrets.choice(_PW) for _ in range(10))


def _now():
    return dt.datetime.now().isoformat(timespec="seconds")


def hash_pw(p):
    return generate_password_hash(p, method="pbkdf2:sha256:200000")


def policy(pw, username=""):
    if len(pw or "") < MIN_PW:
        raise ValueError(f"The password must be at least {MIN_PW} characters.")
    if pw.lower() == (username or "").lower():
        raise ValueError("The password cannot be the same as the username.")


class Accounts:
    def __init__(self, path):
        self.path = path

    # ---- storage
    def _read(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            d = {}
        return {"users": d.get("users", []), "recovery_hash": d.get("recovery_hash", ""),
                "rec_fails": d.get("rec_fails", 0), "rec_locked": d.get("rec_locked", 0)}

    def _write(self, d):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        os.replace(tmp, self.path)

    def has_users(self):
        return bool(self._read()["users"])

    def list(self):
        return self._read()["users"]

    def get(self, username):
        u = (username or "").strip().lower()
        return next((x for x in self._read()["users"] if x["username"] == u), None)

    def _admins_left(self, users, skip=None):
        return sum(1 for x in users if x["role"] == "admin" and x.get("active", True) and x["username"] != skip)

    # ---- accounts
    def create(self, username, name, role, office="", keywords="", links=(), password=None, must_change=True):
        username = (username or "").strip().lower()
        if not _USER.match(username):
            raise ValueError("Username: 3-30 letters, numbers, dot, dash or underscore.")
        if not (name or "").strip():
            raise ValueError("Enter the person's full name.")
        if role not in ("admin", "clerk"):
            raise ValueError("Choose a role.")
        if role == "clerk" and not (office or "").strip():
            raise ValueError("A P.O Clerk account needs an office.")
        policy(password, username)
        with _lk:
            d = self._read()
            if any(x["username"] == username for x in d["users"]):
                raise ValueError("That username is already taken.")
            u = dict(username=username, name=name.strip(), role=role, office=(office or "").strip() if role == "clerk" else "",
                     keywords=(keywords or "").strip(), links=list(dict.fromkeys(links)), pw=hash_pw(password),
                     must_change=must_change, active=True, failed=0, locked_until=0, updated_at=_now())
            d["users"].append(u)
            self._write(d)
            return u

    def verify(self, username, password):
        """-> (user, None) or (None, message). Locks an account for 5 minutes after 5 wrong passwords."""
        with _lk:
            d = self._read()
            u = next((x for x in d["users"] if x["username"] == (username or "").strip().lower()), None)
            if not u or not u.get("active", True):
                check_password_hash(hash_pw("x"), password or "")        # same time as a real check
                return None, "Incorrect username or password."
            if u.get("locked_until", 0) > time.time():
                return None, f"Too many wrong attempts. Try again in {int((u['locked_until'] - time.time()) // 60) + 1} minute(s)."
            if check_password_hash(u["pw"], password or ""):
                u["failed"] = 0
                self._write(d)
                return u, None
            u["failed"] = u.get("failed", 0) + 1
            if u["failed"] >= MAX_FAILS:
                u["failed"], u["locked_until"] = 0, time.time() + LOCK_SECS
            self._write(d)
            return None, "Incorrect username or password."

    def set_password(self, username, new, must_change=False):
        policy(new, username)
        with _lk:
            d = self._read()
            u = next(x for x in d["users"] if x["username"] == username)
            u.update(pw=hash_pw(new), must_change=must_change, failed=0, locked_until=0, updated_at=_now())
            self._write(d)

    def reset(self, username):
        t = temp_password()
        self.set_password(username, t, must_change=True)
        return t

    def update(self, username, **f):
        with _lk:
            d = self._read()
            u = next((x for x in d["users"] if x["username"] == username), None)
            if not u:
                raise ValueError("Account not found.")
            new = dict(u, **{k: v for k, v in f.items() if k in ("name", "role", "office", "keywords", "links", "active")})
            if new["role"] not in ("admin", "clerk") or (new["role"] == "clerk" and not new["office"].strip()):
                raise ValueError("A P.O Clerk account needs an office.")
            if new["role"] != "admin" or not new.get("active", True):
                if u["role"] == "admin" and self._admins_left(d["users"], skip=username) == 0:
                    raise ValueError("At least one active administrator must remain.")
            if new["role"] == "admin":
                new["office"] = ""
            u.update(new, updated_at=_now())
            self._write(d)
            return u

    def delete(self, username):
        with _lk:
            d = self._read()
            u = next((x for x in d["users"] if x["username"] == username), None)
            if u and u["role"] == "admin" and self._admins_left(d["users"], skip=username) == 0:
                raise ValueError("At least one active administrator must remain.")
            d["users"] = [x for x in d["users"] if x["username"] != username]
            self._write(d)

    # ---- one-time recovery code (kept sealed by the Regional Office)
    def new_recovery(self):
        code = "-".join("".join(secrets.choice(_RC) for _ in range(4)) for _ in range(4))
        with _lk:
            d = self._read()
            d.update(recovery_hash=hash_pw(code), rec_fails=0, rec_locked=0)
            self._write(d)
        return code

    def recover(self, username, code, new_password):
        """Admin forgot the password: the recovery code sets a new one and issues a fresh code."""
        with _lk:
            d = self._read()
            if d["rec_locked"] > time.time():
                raise ValueError("Too many wrong codes. Try again in a few minutes.")
            u = next((x for x in d["users"] if x["username"] == (username or "").strip().lower() and x["role"] == "admin"), None)
            if not u or not d["recovery_hash"] or not check_password_hash(d["recovery_hash"], (code or "").strip().upper()):
                d["rec_fails"] += 1
                if d["rec_fails"] >= MAX_FAILS:
                    d["rec_fails"], d["rec_locked"] = 0, time.time() + LOCK_SECS
                self._write(d)
                raise ValueError("The username or recovery code is not correct.")
        self.set_password(u["username"], new_password)
        return self.new_recovery()

    # ---- move accounts between PCs
    def export(self):
        return {"app": "pca-dtr-accounts", "exported": _now(), "users": self._read()["users"]}

    def import_(self, data):
        if data.get("app") != "pca-dtr-accounts":
            raise ValueError("This is not an accounts file from the DTR Generator.")
        added = updated = 0
        with _lk:
            d = self._read()
            for n in data.get("users", []):
                if not (_USER.match(n.get("username", "")) and n.get("role") in ("admin", "clerk") and n.get("pw")):
                    continue
                cur = next((x for x in d["users"] if x["username"] == n["username"]), None)
                if cur is None:
                    d["users"].append(dict(n, failed=0, locked_until=0)); added += 1
                elif n.get("updated_at", "") > cur.get("updated_at", ""):
                    cur.update(n, failed=0, locked_until=0); updated += 1
            self._write(d)
        return added, updated
