"""
Lull | app.py
=============
The whole backend. Four things: accounts, saving a session, saving a
reflection, and reading stats.

It is deliberately off the critical path. A session starts, plays and ends
without ever reaching this server — the plan is built in the browser from a
static library, the audio comes from R2, the weather from Open-Meteo. This is
only called to record what happened, which is why Render's free tier spinning
down after fifteen minutes does not matter.

A session is written ONCE, when it ends, whether it finished or was stopped.
Creating a row at the start would leave orphans behind everyone who wandered
off, and abandonment is something the owner view needs to see rather than
something to lose.

Environment (set these in Render, never in the repo):
    NEON_DATABASE_URL   postgres connection string
    SECRET_KEY          flask session signing
    OWNER_HANDLE        which account may read /admin/stats
    ALLOWED_ORIGINS     comma-separated, e.g. https://you.github.io
"""

import os, re
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
    # The frontend is on github.io and this is on onrender.com — a different
    # site entirely, so the session cookie has to be explicitly cross-site.
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=90),
)

ORIGINS = [o.strip() for o in
           os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
           if o.strip()]
CORS(app, origins=ORIGINS, supports_credentials=True)

DB_URL = os.environ.get("NEON_DATABASE_URL")
OWNER = os.environ.get("OWNER_HANDLE", "")

MOODS = {"happy", "kickstart", "unmotivated", "focus",
         "anxious", "socially-drained", "sleepy"}
TIERS = {"energetic", "balanced", "mellow"}
MINUTES = {10, 20, 30, 45}
FEELINGS = {"settled", "lighter", "clearer", "much the same"}


def db():
    if not DB_URL:
        raise RuntimeError("NEON_DATABASE_URL is not set")
    return psycopg.connect(DB_URL, row_factory=dict_row)


def signed_in(f):
    @wraps(f)
    def inner(*a, **kw):
        if not session.get("uid"):
            return jsonify(error="sign in first"), 401
        return f(*a, **kw)
    return inner


def owner_only(f):
    @wraps(f)
    def inner(*a, **kw):
        if not OWNER or session.get("handle") != OWNER:
            return jsonify(error="not found"), 404      # don't advertise it
        return f(*a, **kw)
    return inner


# ── accounts ────────────────────────────────────────────────
# Optional throughout. The app works signed out; an account only makes
# history follow you between devices.

@app.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    handle = (d.get("handle") or "").strip().lower()
    pw = d.get("password") or ""
    if not re.fullmatch(r"[a-z0-9_.-]{3,32}", handle):
        return jsonify(error="Handles are 3-32 characters: letters, numbers, "
                             "dot, dash or underscore."), 400
    if len(pw) < 8:
        return jsonify(error="Passwords need at least 8 characters."), 400
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE handle=%s", (handle,))
        if cur.fetchone():
            return jsonify(error="That handle is taken."), 409
        cur.execute(
            "INSERT INTO users (handle, password_hash) VALUES (%s,%s) "
            "RETURNING id, handle, created_at",
            (handle, generate_password_hash(pw)))
        u = cur.fetchone()
    session.permanent = True
    session["uid"], session["handle"] = u["id"], u["handle"]
    return jsonify(handle=u["handle"], since=u["created_at"].isoformat()), 201


@app.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    handle = (d.get("handle") or "").strip().lower()
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT id, handle, password_hash, created_at "
                    "FROM users WHERE handle=%s", (handle,))
        u = cur.fetchone()
    if not u or not check_password_hash(u["password_hash"], d.get("password") or ""):
        return jsonify(error="That handle and password don't match."), 401
    session.permanent = True
    session["uid"], session["handle"] = u["id"], u["handle"]

    # adopt anything saved on this device before signing in
    dev = (d.get("device_id") or "").strip()
    if dev:
        with db() as c, c.cursor() as cur:
            cur.execute("UPDATE sessions SET user_id=%s "
                        "WHERE device_id=%s AND user_id IS NULL",
                        (u["id"], dev))
    return jsonify(handle=u["handle"], since=u["created_at"].isoformat())


@app.post("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/me")
def me():
    if not session.get("uid"):
        return jsonify(handle=None)
    return jsonify(handle=session.get("handle"))


# ── sessions ────────────────────────────────────────────────

@app.post("/sessions")
def save_session():
    """
    Written once, when a session ends. mood, tier, minutes and plan_seed
    reproduce the entire arrangement later, so nothing about the plan is kept.
    Accepts a beacon on tab close, hence the lenient body parsing.
    """
    d = request.get_json(silent=True, force=True) or {}
    mood, tier = d.get("mood"), d.get("tier")
    if mood not in MOODS or tier not in TIERS:
        return jsonify(error="unknown mood or tier"), 400
    try:
        minutes = int(d.get("minutes"))
        seed = int(d.get("plan_seed"))
        played = max(0, int(d.get("played_s") or 0))
    except (TypeError, ValueError):
        return jsonify(error="minutes, plan_seed and played_s must be numbers"), 400
    if minutes not in MINUTES:
        return jsonify(error="minutes must be 10, 20, 30 or 45"), 400

    texture = d.get("texture") or None          # null is a real choice: quiet
    offset = float(d.get("bed_offset_db") or 0)
    device = (d.get("device_id") or "")[:64] or None

    with db() as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO sessions (user_id, device_id, mood, tier, minutes, "
            " plan_seed, texture, bed_offset_db, played_s, completed) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (session.get("uid"), device, mood, tier, minutes, seed,
             texture, offset, played, bool(d.get("completed"))))
        sid = cur.fetchone()["id"]
    return jsonify(session_id=sid), 201


@app.post("/sessions/<int:sid>/reflection")
def save_reflection(sid):
    d = request.get_json(silent=True) or {}
    feeling = d.get("feeling")
    if feeling not in FEELINGS:
        return jsonify(error="unknown feeling"), 400
    with db() as c, c.cursor() as cur:
        cur.execute("SELECT 1 FROM sessions WHERE id=%s", (sid,))
        if not cur.fetchone():
            return jsonify(error="no such session"), 404
        cur.execute("INSERT INTO reflections (session_id, feeling) VALUES (%s,%s)",
                    (sid, feeling))
    return jsonify(ok=True), 201


# ── your own history ────────────────────────────────────────

@app.get("/stats")
def stats():
    """Works signed in (by account) or signed out (by device)."""
    uid, dev = session.get("uid"), request.args.get("device_id")
    if uid:
        where, arg = "user_id=%s", uid
    elif dev:
        where, arg = "device_id=%s AND user_id IS NULL", dev
    else:
        return jsonify(sessions=0, listened_s=0, top_mood=None,
                       usual_minutes=None, top_texture=None)

    with db() as c, c.cursor() as cur:
        cur.execute(f"SELECT count(*) n, coalesce(sum(played_s),0) s "
                    f"FROM sessions WHERE {where}", (arg,))
        t = cur.fetchone()
        cur.execute(f"SELECT mood FROM sessions WHERE {where} "
                    f"GROUP BY mood ORDER BY count(*) DESC LIMIT 1", (arg,))
        mood = (cur.fetchone() or {}).get("mood")
        cur.execute(f"SELECT minutes FROM sessions WHERE {where} "
                    f"GROUP BY minutes ORDER BY count(*) DESC LIMIT 1", (arg,))
        mins = (cur.fetchone() or {}).get("minutes")
        cur.execute(f"SELECT coalesce(texture,'quiet') t FROM sessions "
                    f"WHERE {where} GROUP BY 1 ORDER BY count(*) DESC LIMIT 1", (arg,))
        tex = (cur.fetchone() or {}).get("t")
        # for the Sky of Intent grid: weekday and hour of each session
        cur.execute(f"SELECT extract(dow from started_at)::int d, "
                    f"extract(hour from started_at)::int h, mood "
                    f"FROM sessions WHERE {where} "
                    f"AND started_at > now() - interval '7 days'", (arg,))
        grid = [dict(day=r["d"], hour=r["h"], mood=r["mood"]) for r in cur.fetchall()]

    return jsonify(sessions=t["n"], listened_s=int(t["s"]), top_mood=mood,
                   usual_minutes=mins, top_texture=tex, grid=grid)


# ── the owner view ──────────────────────────────────────────

@app.get("/admin/stats")
@signed_in
@owner_only
def admin_stats():
    days = min(int(request.args.get("days", 7)), 365)
    since = f"now() - interval '{days} days'"
    out = {}
    with db() as c, c.cursor() as cur:
        cur.execute(f"SELECT count(*) n, avg(completed::int) done, "
                    f"       percentile_cont(0.5) WITHIN GROUP (ORDER BY minutes) med "
                    f"FROM sessions WHERE started_at > {since}")
        r = cur.fetchone()
        out["sessions"] = r["n"]
        out["completion_rate"] = round(float(r["done"] or 0), 3)
        out["median_minutes"] = float(r["med"] or 0)

        cur.execute(f"SELECT mood, count(*) n FROM sessions "
                    f"WHERE started_at > {since} GROUP BY 1 ORDER BY 2 DESC")
        out["moods"] = cur.fetchall()

        cur.execute(f"SELECT coalesce(texture,'quiet') texture, count(*) n "
                    f"FROM sessions WHERE started_at > {since} "
                    f"GROUP BY 1 ORDER BY 2 DESC")
        out["textures"] = cur.fetchall()

        # calibration health — the number to watch. If people are adjusting,
        # the measurement is wrong, not their taste.
        cur.execute(f"SELECT texture, avg((bed_offset_db <> 0)::int) adjusted, "
                    f"       count(*) n FROM sessions "
                    f"WHERE texture IS NOT NULL AND started_at > {since} "
                    f"GROUP BY 1 ORDER BY 2 DESC")
        out["bed_adjustments"] = cur.fetchall()

        cur.execute(f"SELECT r.feeling, count(*) n FROM reflections r "
                    f"JOIN sessions s ON s.id=r.session_id "
                    f"WHERE s.started_at > {since} GROUP BY 1 ORDER BY 2 DESC")
        out["feelings"] = cur.fetchall()

        # asked, and felt — does a mood do what its phrase promises
        cur.execute(f"SELECT s.mood, "
                    f"  avg((r.feeling <> 'much the same')::int) shifted, "
                    f"  count(*) n FROM sessions s "
                    f"JOIN reflections r ON r.session_id=s.id "
                    f"WHERE s.started_at > {since} GROUP BY 1 ORDER BY 3 DESC")
        out["asked_and_felt"] = cur.fetchall()

        # how far in people stop, as a fraction of what they asked for
        cur.execute(f"SELECT width_bucket(played_s::float/(minutes*60), 0, 1, 5) b, "
                    f"       count(*) n FROM sessions "
                    f"WHERE completed = false AND started_at > {since} "
                    f"GROUP BY 1 ORDER BY 1")
        out["stopped_at"] = cur.fetchall()
    return jsonify(out)


@app.get("/health")
def health():
    try:
        with db() as c, c.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify(ok=True, db=True)
    except Exception as e:
        return jsonify(ok=False, db=False, error=str(e)[:200]), 503


if __name__ == "__main__":
    app.run(debug=True, port=5000)
