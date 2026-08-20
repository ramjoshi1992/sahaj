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

    # Deliberately NOT adopting this device's earlier sessions. A laptop or a
    # phone is often shared, and claiming everything recorded on it would hand
    # one person another's listening history. Signing in changes what happens
    # from now on, not what happened before.
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
    try:
        rerolls = max(0, min(50, int(d.get("rerolls") or 0)))
    except (TypeError, ValueError):
        rerolls = 0

    with db() as c, c.cursor() as cur:
        cur.execute(
            "INSERT INTO sessions (user_id, device_id, mood, tier, minutes, "
            " plan_seed, texture, bed_offset_db, played_s, completed, rerolls) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (session.get("uid"), device, mood, tier, minutes, seed,
             texture, offset, played, bool(d.get("completed")), rerolls))
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
@signed_in
def stats():
    """
    Signed in only. Sessions saved without an account are recorded against a
    device, but a device is not a person — two people share a laptop — so that
    history is never shown back to anyone. It exists for aggregate counts.
    """
    uid = session.get("uid")
    where, arg = "user_id=%s", uid

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
        # How it usually lands. The texture was here instead, but that is chosen
        # contextually — it would have reported the weather, not the person.
        cur.execute("SELECT r.feeling FROM reflections r "
                    "JOIN sessions s ON s.id = r.session_id "
                    f"WHERE s.{where} GROUP BY r.feeling "
                    "ORDER BY count(*) DESC LIMIT 1", (arg,))
        feeling = (cur.fetchone() or {}).get("feeling")
        cur.execute("SELECT count(*) n FROM reflections r "
                    "JOIN sessions s ON s.id = r.session_id "
                    f"WHERE s.{where}", (arg,))
        reflected = (cur.fetchone() or {}).get("n", 0)
        # for the Sky of Intent grid: weekday and hour of each session
        cur.execute(f"SELECT extract(dow from started_at)::int d, "
                    f"extract(hour from started_at)::int h, mood "
                    f"FROM sessions WHERE {where} "
                    f"AND started_at > now() - interval '7 days'", (arg,))
        grid = [dict(day=r["d"], hour=r["h"], mood=r["mood"]) for r in cur.fetchall()]

        # Which of the seven actually work for this person. The only figure
        # here that could change what someone chooses next time.
        cur.execute("SELECT s.mood, r.feeling, count(*) n "
                    "FROM sessions s JOIN reflections r ON r.session_id = s.id "
                    f"WHERE s.{where} GROUP BY 1,2", (arg,))
        by_mood = {}
        for r in cur.fetchall():
            m = by_mood.setdefault(r["mood"], {"total": 0, "feelings": {}})
            m["total"] += r["n"]
            m["feelings"][r["feeling"]] = r["n"]
        landed = []
        for mood, d in by_mood.items():
            top = max(d["feelings"].items(), key=lambda kv: kv[1])
            landed.append(dict(mood=mood, feeling=top[0], count=top[1],
                               total=d["total"]))
        landed.sort(key=lambda x: -x["total"])

        # asked for, against stayed for
        cur.execute(f"SELECT avg(minutes)::float asked, "
                    f"       avg(played_s)::float / 60 stayed, count(*) n "
                    f"FROM sessions WHERE {where}", (arg,))
        r = cur.fetchone()
        staying = dict(asked=round(r["asked"] or 0, 1),
                       stayed=round(r["stayed"] or 0, 1), n=r["n"])

    return jsonify(sessions=t["n"], listened_s=int(t["s"]), top_mood=mood,
                   usual_minutes=mins, top_feeling=feeling,
                   reflections=reflected, grid=grid,
                   landed=landed, staying=staying)


# ── the owner view ──────────────────────────────────────────

@app.get("/admin/stats")
@signed_in
@owner_only
def admin_stats():
    """
    Two questions, kept apart because they are answered by different numbers.

    Does it work — completion, what people report feeling, which moods deliver
    what they promise, where sessions are abandoned.

    Would anyone pay for it — whether people come back, how often, and whether
    that is holding up week on week. For something used a few times a week,
    weekly return is the honest measure; daily active would flatter nothing.
    """
    days = min(int(request.args.get("days", 7)), 365)
    win = f"now() - interval '{days} days'"
    prev = f"now() - interval '{days * 2} days'"
    out = {"days": days}

    with db() as c, c.cursor() as cur:
        # ── volume, and whether it is moving ──────────────────
        cur.execute(f"SELECT count(*) n, avg(completed::int) done, "
                    f"  percentile_cont(0.5) WITHIN GROUP (ORDER BY minutes) med, "
                    f"  coalesce(sum(played_s),0) secs "
                    f"FROM sessions WHERE started_at > {win}")
        r = cur.fetchone()
        out["sessions"] = r["n"]
        out["completion_rate"] = round(float(r["done"] or 0), 3)
        out["median_minutes"] = float(r["med"] or 0)
        out["hours_played"] = round((r["secs"] or 0) / 3600, 1)

        cur.execute(f"SELECT count(*) n FROM sessions "
                    f"WHERE started_at > {prev} AND started_at <= {win}")
        before = cur.fetchone()["n"]
        out["sessions_prev"] = before
        out["sessions_change"] = (round((out["sessions"] - before) / before, 3)
                                  if before else None)

        # ── would anyone pay for it ───────────────────────────
        # Weekly return, measured only against people who have had the chance:
        # accounts older than the window. Anyone who signed up yesterday cannot
        # have failed to return yet, and counting them would flatter the number.
        cur.execute(f"SELECT count(*) n FROM users WHERE created_at <= {win}")
        eligible = cur.fetchone()["n"]
        cur.execute(f"SELECT count(DISTINCT s.user_id) n FROM sessions s "
                    f"JOIN users u ON u.id = s.user_id "
                    f"WHERE u.created_at <= {win} AND s.started_at > {win}")
        returned = cur.fetchone()["n"]
        out["returning"] = dict(of=eligible, came_back=returned,
                                rate=round(returned / eligible, 3) if eligible else None)

        cur.execute(f"SELECT count(*) n FROM users WHERE created_at > {win}")
        out["new_accounts"] = cur.fetchone()["n"]
        cur.execute("SELECT count(*) n FROM users")
        out["accounts"] = cur.fetchone()["n"]

        # how much people who do come back actually use it
        cur.execute(f"SELECT count(*)::float / nullif(count(DISTINCT "
                    f"  coalesce(user_id::text, device_id)),0) per "
                    f"FROM sessions WHERE started_at > {win}")
        out["sessions_per_person"] = round(float(cur.fetchone()["per"] or 0), 1)

        # signed in against not — how many think it is worth an account
        cur.execute(f"SELECT count(*) FILTER (WHERE user_id IS NOT NULL) named, "
                    f"       count(*) all_n FROM sessions WHERE started_at > {win}")
        r = cur.fetchone()
        out["signed_in_share"] = (round(r["named"] / r["all_n"], 3)
                                  if r["all_n"] else None)

        # eight weeks of volume, for shape rather than a trend line
        cur.execute("SELECT date_trunc('week', started_at)::date wk, count(*) n "
                    "FROM sessions WHERE started_at > now() - interval '8 weeks' "
                    "GROUP BY 1 ORDER BY 1")
        out["weekly"] = [dict(week=r["wk"].isoformat(), n=r["n"])
                         for r in cur.fetchall()]

        # ── does it work ──────────────────────────────────────
        cur.execute(f"SELECT mood, count(*) n FROM sessions "
                    f"WHERE started_at > {win} GROUP BY 1 ORDER BY 2 DESC")
        out["moods"] = cur.fetchall()

        cur.execute(f"SELECT minutes, count(*) n FROM sessions "
                    f"WHERE started_at > {win} GROUP BY 1 ORDER BY 1")
        out["durations"] = cur.fetchall()

        cur.execute(f"SELECT coalesce(texture,'quiet') texture, count(*) n "
                    f"FROM sessions WHERE started_at > {win} "
                    f"GROUP BY 1 ORDER BY 2 DESC")
        out["textures"] = cur.fetchall()

        cur.execute(f"SELECT r.feeling, count(*) n FROM reflections r "
                    f"JOIN sessions s ON s.id=r.session_id "
                    f"WHERE s.started_at > {win} GROUP BY 1 ORDER BY 2 DESC")
        out["feelings"] = cur.fetchall()

        cur.execute(f"SELECT count(*) n, "
                    f"  avg((r.feeling <> 'much the same')::int) shifted "
                    f"FROM reflections r JOIN sessions s ON s.id=r.session_id "
                    f"WHERE s.started_at > {win}")
        r = cur.fetchone()
        out["reflections"] = r["n"]
        out["shift_rate"] = round(float(r["shifted"] or 0), 3) if r["n"] else None

        # the claim the whole thing rests on: does a mood do what it says
        cur.execute(f"SELECT s.mood, "
                    f"  avg((r.feeling <> 'much the same')::int) shifted, "
                    f"  count(*) n FROM sessions s "
                    f"JOIN reflections r ON r.session_id=s.id "
                    f"WHERE s.started_at > {win} GROUP BY 1 ORDER BY 3 DESC")
        out["asked_and_felt"] = [dict(mood=r["mood"], n=r["n"],
                                      shifted=round(float(r["shifted"]), 3))
                                 for r in cur.fetchall()]

        # where people leave, as a fraction of what they asked for
        cur.execute(f"SELECT width_bucket(played_s::float/(minutes*60),0,1,5) b, "
                    f"  count(*) n FROM sessions "
                    f"WHERE completed = false AND started_at > {win} "
                    f"GROUP BY 1 ORDER BY 1")
        out["stopped_at"] = cur.fetchall()

        # ── product health: symptoms, not achievements ────────
        cur.execute(f"SELECT texture, avg((bed_offset_db <> 0)::int) adjusted, "
                    f"  count(*) n FROM sessions "
                    f"WHERE texture IS NOT NULL AND started_at > {win} "
                    f"GROUP BY 1 HAVING count(*) >= 3 ORDER BY 2 DESC")
        out["bed_adjustments"] = [dict(texture=r["texture"], n=r["n"],
                                       adjusted=round(float(r["adjusted"]), 3))
                                  for r in cur.fetchall()]

        cur.execute(f"SELECT mood, avg((rerolls > 0)::int) rerolled, count(*) n "
                    f"FROM sessions WHERE started_at > {win} "
                    f"GROUP BY 1 HAVING count(*) >= 3 ORDER BY 2 DESC")
        out["rerolls"] = [dict(mood=r["mood"], n=r["n"],
                               rerolled=round(float(r["rerolled"]), 3))
                          for r in cur.fetchall()]

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
