"""
ZenTune | upload_seeds.py
=========================
Puts the Lyria seed tracks on R2 alongside the conditioned stems.

Under the family architecture the seeds are primary content, not source
material: each one opens and closes its own movement. Nothing is retired —
intros, outros and core/04 are all family middles now — so this is purely
additive. 189 stems + 63 seeds = 252 objects.

Runs in scan mode by default and touches nothing. Look at what it found,
then re-run with --upload.

    python upload_seeds.py                          # scan and report only
    python upload_seeds.py --upload                 # push to R2
    python upload_seeds.py --verify                 # HEAD every expected key
    python upload_seeds.py --set-cors               # apply a CORS policy
    python upload_seeds.py --manifest seeds.json    # write URL manifest

Credentials (same as archive_extra_stems.py used):
    set R2_ACCOUNT_ID=...
    set R2_ACCESS_KEY_ID=...
    set R2_SECRET_ACCESS_KEY=...
"""

import argparse, json, os, re, sys
from pathlib import Path

BUCKET = "zentune-sessions"
PUBLIC = "https://pub-fefcc3396a88474693cc19e7780eb61f.r2.dev"
PREFIX = "seeds"
MOODS = ["happy", "kickstart", "unmotivated", "focus",
         "anxious", "socially-drained", "sleepy"]
TIERS = ["energetic", "balanced", "mellow"]

# Origins the browser will fetch audio from. decodeAudioData needs CORS.
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://ramjoshi1992.github.io",
]


def parse_path(p: Path, root: Path):
    """
    Work out (mood, tier, seed_letter) from a path, whatever the layout.
    Handles .../<mood>/<tier>/seed_a.mp3 and .../<mood>/<tier>_seed_a.mp3
    and filenames like 'anxious_mellow_seed_a.mp3'.
    """
    parts = [x.lower() for x in p.relative_to(root).parts]
    blob = "/".join(parts)

    mood = next((m for m in MOODS if m in blob), None)
    tier = next((t for t in TIERS if t in blob), None)
    m = re.search(r"seed[ _\-]?([abc])\b", blob)
    letter = m.group(1).upper() if m else None
    if letter is None:
        m = re.search(r"[ _\-]([abc])\.mp3$", blob)
        letter = m.group(1).upper() if m else None
    return mood, tier, letter


def scan(root: Path):
    # Seeds sit alongside the phase folders inside each mood/tier directory,
    # so point this at assets/stems and match on the filename rather than
    # walking all 189 conditioned stems as well.
    files = sorted(root.rglob("seed_*.mp3")) or sorted(root.rglob("*seed*.mp3"))
    if not files:
        files = sorted(root.rglob("*.mp3"))
    found, bad = {}, []
    for f in files:
        mood, tier, letter = parse_path(f, root)
        if not (mood and tier and letter):
            bad.append((f, mood, tier, letter))
            continue
        found[(mood, tier, letter)] = f
    return found, bad, files


def report(found, bad, files, root):
    print(f"scanned {root}  —  {len(files)} mp3 files, {len(found)} parsed\n")
    for mood in MOODS:
        row = []
        for tier in TIERS:
            got = "".join(l if (mood, tier, l) in found else "." for l in "ABC")
            row.append(f"{tier[:4]}:{got}")
        print(f"  {mood:<18}" + "   ".join(row))
    missing = [(m, t, l) for m in MOODS for t in TIERS for l in "ABC"
               if (m, t, l) not in found]
    print(f"\n  parsed {len(found)} of 63 expected")
    if missing:
        print(f"  MISSING {len(missing)}:")
        for m, t, l in missing[:15]:
            print(f"    {m}/{t}/seed_{l.lower()}")
        if len(missing) > 15:
            print(f"    ... and {len(missing)-15} more")
    if bad:
        print(f"\n  {len(bad)} files could not be parsed:")
        for f, m, t, l in bad[:10]:
            print(f"    {f.name}   mood={m} tier={t} seed={l}")
        print("  (rename them, or tell me the layout and I'll fix the parser)")


def key_for(mood, tier, letter):
    return f"{PREFIX}/{mood}/{tier}/seed_{letter.lower()}.mp3"


# Credential names vary between projects, so accept the usual variants
# rather than insisting on one spelling.
ALIASES = {
    "account": ["R2_ACCOUNT_ID", "CLOUDFLARE_ACCOUNT_ID", "CF_ACCOUNT_ID",
                "ACCOUNT_ID", "R2_ACCOUNT"],
    "key":     ["R2_ACCESS_KEY_ID", "R2_ACCESS_KEY", "CLOUDFLARE_ACCESS_KEY_ID",
                "AWS_ACCESS_KEY_ID", "R2_KEY_ID"],
    "secret":  ["R2_SECRET_ACCESS_KEY", "R2_SECRET_KEY", "CLOUDFLARE_SECRET_ACCESS_KEY",
                "AWS_SECRET_ACCESS_KEY", "R2_SECRET"],
}


def load_dotenv():
    """
    Python does not read .env by itself. Look beside the script and in the
    working directory, and fold anything found into the environment without
    overwriting variables that are already set.
    """
    seen = []
    for p in [Path(".env"), Path(__file__).resolve().parent / ".env"]:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            seen.append(k)
            os.environ.setdefault(k, v)
        print(f"  read {p}  ({len(seen)} keys)")
        break
    return seen


def pick(kind):
    for name in ALIASES[kind]:
        v = os.environ.get(name)
        if v:
            return v, name
    return None, None


def client():
    try:
        import boto3
    except ImportError:
        sys.exit("boto3 not installed.  pip install boto3")

    found = load_dotenv()
    acct, n1 = pick("account")
    akid, n2 = pick("key")
    sec, n3 = pick("secret")

    if not all([acct, akid, sec]):
        print("\nCould not assemble R2 credentials.")
        print(f"  account id : {n1 or 'NOT FOUND'}")
        print(f"  access key : {n2 or 'NOT FOUND'}")
        print(f"  secret     : {n3 or 'NOT FOUND'}")
        if found:
            print("\n  Keys present in .env (names only, no values):")
            for k in found:
                print(f"    {k}")
            print("\n  If yours are named differently, tell me the names "
                  "and I'll add them to ALIASES.")
        else:
            print("\n  No .env found beside the script or in the working "
                  "directory.")
        sys.exit(1)

    print(f"  credentials: {n1} / {n2} / {n3}")
    return boto3.client("s3",
                        endpoint_url=f"https://{acct}.r2.cloudflarestorage.com",
                        aws_access_key_id=akid, aws_secret_access_key=sec,
                        region_name="auto")


def upload(found, force):
    s3 = client()
    existing = set()
    if not force:
        tok = None
        while True:
            kw = dict(Bucket=BUCKET, Prefix=PREFIX + "/")
            if tok:
                kw["ContinuationToken"] = tok
            r = s3.list_objects_v2(**kw)
            existing |= {o["Key"] for o in r.get("Contents", [])}
            if not r.get("IsTruncated"):
                break
            tok = r.get("NextContinuationToken")
        print(f"{len(existing)} objects already under {PREFIX}/\n")

    ok = skip = fail = 0
    for i, ((mood, tier, letter), path) in enumerate(sorted(found.items()), 1):
        k = key_for(mood, tier, letter)
        if k in existing:
            skip += 1
            continue
        print(f"  [{i}/{len(found)}] {k}", end=" ... ", flush=True)
        try:
            s3.upload_file(str(path), BUCKET, k,
                           ExtraArgs={"ContentType": "audio/mpeg"})
            print(f"{path.stat().st_size/1048576:.1f} MB")
            ok += 1
        except Exception as e:
            print(f"FAILED: {e}")
            fail += 1
    print(f"\nuploaded {ok}, skipped {skip} already present, failed {fail}")
    return fail == 0


def verify():
    s3 = client()
    missing = []
    for m in MOODS:
        for t in TIERS:
            for l in "ABC":
                k = key_for(m, t, l)
                try:
                    s3.head_object(Bucket=BUCKET, Key=k)
                except Exception:
                    missing.append(k)
    print(f"verified {63-len(missing)}/63 seed objects present on R2")
    for k in missing:
        print(f"  MISSING {k}")
    return not missing


def set_cors():
    """
    decodeAudioData fetches audio cross-origin, which the browser blocks
    without these headers. This is the piece we never confirmed was in place.
    """
    s3 = client()
    rules = {"CORSRules": [{
        "AllowedOrigins": CORS_ORIGINS,
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedHeaders": ["*"],
        "ExposeHeaders": ["Content-Length", "Content-Range"],
        "MaxAgeSeconds": 3600,
    }]}
    s3.put_bucket_cors(Bucket=BUCKET, CORSConfiguration=rules)
    print("CORS policy applied for:")
    for o in CORS_ORIGINS:
        print(f"  {o}")
    try:
        got = s3.get_bucket_cors(Bucket=BUCKET)
        print("\nread back:", json.dumps(got.get("CORSRules"), indent=1))
    except Exception as e:
        print(f"(could not read back: {e})")


def write_manifest(found, out):
    man = {f"{m}/{t}/seed_{l.lower()}": f"{PUBLIC}/{key_for(m,t,l)}"
           for (m, t, l) in sorted(found)}
    Path(out).write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(f"wrote {out}  ({len(man)} entries)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-root", default="assets/seeds")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="re-upload even if the key already exists")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--set-cors", action="store_true")
    ap.add_argument("--manifest", default=None)
    args = ap.parse_args()

    if args.set_cors:
        set_cors()
        if not (args.upload or args.verify or args.manifest):
            return
    if args.verify:
        verify()
        return

    root = Path(args.seeds_root)
    if not root.exists():
        print(f"seeds root not found: {root}")
        print("Try --seeds-root with the folder holding the Lyria seeds.")
        return
    found, bad, files = scan(root)
    report(found, bad, files, root)

    if args.manifest:
        write_manifest(found, args.manifest)
    if args.upload:
        if len(found) < 63:
            print("\nRefusing to upload a partial set — "
                  "fix the missing/unparsed files first, or pass --force.")
            if not args.force:
                return
        print()
        upload(found, args.force)
        print()
        verify()
    else:
        print("\nScan only. Re-run with --upload when the table looks right.")


if __name__ == "__main__":
    main()
