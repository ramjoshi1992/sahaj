"""
Lull | check_licences.py
=======================
Reads the Freesound sound ID out of each texture's original filename, asks the
API what licence it carries, and writes a credits file.

Freesound filenames start with the sound ID — 376795__amholma__gentle-waves.wav
is sound 376795 — so nothing needs transcribing by hand.

Why it matters: CC0 is free rein, CC-BY needs attribution, and CC-BY-NC cannot
be used if the app ever charges for anything. Sampling+ is a retired licence
that Creative Commons withdrew as too hard to interpret, so treat it as unusable
rather than reason about it. Attribution survives our processing — the loops are
trimmed, crossfaded and re-encoded, but they are still derivative works.

Needs a free API token: https://freesound.org/apiv2/apply
Put it in .env as FREESOUND_TOKEN=..., or pass --token.

    python check_licences.py --textures-root assets\\textures
    python check_licences.py --textures-root assets\\textures --write-library
"""

import argparse, json, os, re, sys, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API = "https://freesound.org/apiv2/sounds/{id}/?fields=id,name,username,license,url,duration&token={t}"

# How each licence sits with a product that might one day charge. The API
# returns licences as URL fragments — "by-nc/4.0/", "zero/1.0/" — not display
# names, so match on those. Order matters: "by-nc" contains "by".
VERDICT = [
    ("publicdomain/zero", "ok",    "CC0 — no obligations, no credit needed"),
    ("licenses/zero",     "ok",    "CC0 — no obligations, no credit needed"),
    ("by-nc-sa",          "block", "NonCommercial — unusable if the app charges"),
    ("by-nc",             "block", "NonCommercial — unusable if the app charges"),
    ("sampling+",         "block", "retired licence, ambiguous — replace"),
    ("by-sa",             "check", "ShareAlike — check what it obliges"),
    ("by",                "ok",    "CC-BY — usable, must credit"),
]


def load_env():
    for p in (Path(".env"), Path(__file__).resolve().parent / ".env"):
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            return


def find_ids(root: Path):
    """Texture folder name -> (sound id, original filename)."""
    out, unmatched = {}, []
    for f in sorted(root.rglob("*")):
        if f.suffix.lower() not in (".wav", ".flac", ".aiff", ".aif", ".mp3", ".ogg"):
            continue
        texture = f.parent.name if f.parent != root else f.stem
        m = re.match(r"^(\d{4,8})__", f.name)
        if m:
            out[texture] = (int(m.group(1)), f.name)
        else:
            unmatched.append((texture, f.name))
    return out, unmatched


def lookup(sound_id, token):
    req = Request(API.format(id=sound_id, t=token),
                  headers={"User-Agent": "Lull/1.0"})
    try:
        with urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        return {"error": f"{e.code} {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def verdict_for(lic):
    l = (lic or "").lower()
    for frag, state, why in VERDICT:
        if frag in l:
            return (state, why)
    return ("check", "unrecognised — check by hand")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--textures-root", default="assets/textures")
    ap.add_argument("--token", default=None)
    ap.add_argument("--out", default="credits.json")
    ap.add_argument("--lib", default="library.json")
    ap.add_argument("--write-library", action="store_true",
                    help="fold licence and credit into library.json _textures")
    args = ap.parse_args()

    load_env()
    token = args.token or os.environ.get("FREESOUND_TOKEN")
    if not token:
        sys.exit("No API token. Get one free at https://freesound.org/apiv2/apply\n"
                 "then add FREESOUND_TOKEN=... to .env, or pass --token.")

    root = Path(args.textures_root)
    if not root.exists():
        sys.exit(f"not found: {root}")

    found, unmatched = find_ids(root)
    if not found:
        sys.exit(f"No Freesound IDs in any filename under {root}. "
                 "Files may have been renamed — check the attribution page at "
                 "https://freesound.org/home/attribution/ instead.")

    print(f"{len(found)} textures with a sound ID\n")
    print(f"{'texture':<14}{'id':>8}  {'licence':<32}{'user':<18}verdict")
    print("-" * 92)

    credits, blocked, failed = {}, [], []
    for texture, (sid, fname) in sorted(found.items()):
        d = lookup(sid, token)
        time.sleep(0.4)                      # free tier allows 60/min
        if "error" in d:
            print(f"{texture:<14}{sid:>8}  {'—':<32}{'—':<18}{d['error']}")
            failed.append(texture)
            continue
        lic = d.get("license", "")
        l = (lic or "").lower()
        short = ("CC0" if "zero" in l else
                 "CC-BY-NC-SA" if "by-nc-sa" in l else
                 "CC-BY-NC" if "by-nc" in l else
                 "CC-BY-SA" if "by-sa" in l else
                 "CC-BY" if "/by" in l or l.startswith("by") else
                 "Sampling+" if "sampling" in l else lic)
        state, why = verdict_for(lic)
        mark = {"ok": "ok", "block": "REPLACE", "check": "check"}[state]
        print(f"{texture:<14}{sid:>8}  {short[:31]:<32}{d.get('username','?')[:17]:<18}{mark}  {why}")
        if state == "block":
            blocked.append((texture, d.get("username"), short))
        credits[texture] = {
            "id": sid, "name": d.get("name"), "username": d.get("username"),
            "license": lic, "url": d.get("url"),
            "attribution": f'"{d.get("name")}" by {d.get("username")} '
                           f'({d.get("url")}) licensed under {short}',
            "usable": state != "block",
        }

    if unmatched:
        print(f"\n{len(unmatched)} files with no ID in the filename:")
        for t, f in unmatched:
            print(f"  {t}: {f}")

    Path(args.out).write_text(json.dumps(credits, indent=1), encoding="utf-8")
    print(f"\nwrote {args.out}")

    if blocked:
        print(f"\n{len(blocked)} MUST BE REPLACED if the app ever charges:")
        for t, u, l in blocked:
            print(f"  {t:<14}by {u} — {l}")
        print("\n  Replacing one means rebuilding its loop, re-measuring it and "
              "re-uploading, since the bed level is calibrated per file.")
    else:
        print("\nNothing blocks a paid launch. Credit still required for anything "
              "that is not CC0.")

    print("\n--- credits block ---")
    for t in sorted(credits):
        if "zero" not in (credits[t]["license"] or "").lower():
            print("  " + credits[t]["attribution"])

    if args.write_library:
        p = Path(args.lib)
        if not p.exists():
            print(f"\n{args.lib} not found — skipping")
            return
        lib = json.loads(p.read_text(encoding="utf-8"))
        files = lib.setdefault("_textures", {}).setdefault("files", {})
        for t, c in credits.items():
            if t in files:
                files[t]["license"] = c["license"]
                files[t]["credit"] = c["attribution"]
        p.write_text(json.dumps(lib, indent=1), encoding="utf-8")
        print(f"\nfolded licence and credit into {args.lib} — "
              "the credits screen can read them from there")


if __name__ == "__main__":
    main()
