"""
ZenTune | retexture.py
======================
The 14 textures are WAV and total 1,227 MB — storm_2 alone is 313 MB, which
is roughly 28 minutes of audio. A background bed that has to start almost
immediately and run for a whole session cannot be delivered that way.

Textures loop, so they do not need to be long, and they sit at 15% gain
under music, so they do not need to be lossless. This takes a window out of
each one, crossfades the seam so it loops without a join, and writes MP3.

Unlike the music stems, looping genuinely works here: broadband ambience has
no beat grid or melody for a crossfaded seam to violate.

    python retexture.py --textures-root path\\to\\textures          # scan
    python retexture.py --textures-root path\\to\\textures --build  # write mp3s
    python retexture.py --build --upload                           # and push
    python retexture.py --upload --delete-wav                      # tidy R2

Output lands in textures_out/ locally before anything is uploaded.
"""

import argparse, json, os, sys
from pathlib import Path
import numpy as np
import soundfile as sf

NAMES = ["beach_1", "beach_2", "forest_1", "forest_2", "city_1",
         "suburb_1", "suburb_2", "cafe_1", "rain", "storm_1",
         "storm_2", "fireplace_1", "night_1", "river_1"]

BUCKET = "zentune-sessions"
PUBLIC = "https://pub-fefcc3396a88474693cc19e7780eb61f.r2.dev"
OUTDIR = Path("textures_out")
LOOP_S = 150.0        # plenty for a bed nobody is listening to directly

# Where the source is long enough, a longer loop costs a couple of MB and
# halves how often any audible event recurs. Worth it for the textures that
# contain events rather than steady noise: thunder, traffic, speech.
PER_TEXTURE_LOOP = {
    "storm_2": 300.0,     # 31 min of source; thunder claps would recur
    "city_1": 300.0,      # 17.9 min; passing vehicles and voices
    "suburb_1": 300.0,    # 7.2 min
    "river_1": 280.0,     # 5.0 min
    "forest_2": 230.0,    # 4.1 min
    "cafe_1": 220.0,      # 3.9 min; speech fragments are recognisable
    "beach_2": 260.0,     # 4.7 min
    "storm_1": 120.0,     # 2.1 min, already labelled a loop by its source
}
SEAM_S = 4.0          # crossfade length at the loop join
START_FRAC = 0.15     # skip any fade-in at the top of the source


AUDIO = (".wav", ".flac", ".aiff", ".aif", ".mp3", ".ogg", ".m4a")


def find_sources(root: Path):
    """
    Each texture is a folder here, not a file, and a folder may hold several
    candidate recordings. Report them all rather than silently taking one —
    the local rain folder holds a 295MB file while R2 holds an 11.5MB one,
    so 'the biggest' is clearly not what was uploaded before.
    """
    got, missing, choices = {}, [], {}
    for n in NAMES:
        cands = []
        d = root / n
        if d.is_dir():
            cands = sorted(p for p in d.rglob("*") if p.suffix.lower() in AUDIO)
        if not cands:
            cands = sorted(p for p in root.rglob(f"{n}.*") if p.suffix.lower() in AUDIO)
        if not cands:
            cands = sorted(p for p in root.rglob(f"*{n}*")
                           if p.is_file() and p.suffix.lower() in AUDIO)
        if cands:
            # prefer the shortest — these are ambience beds, not master takes
            cands.sort(key=lambda p: p.stat().st_size)
            got[n] = cands[0]
            if len(cands) > 1:
                choices[n] = cands
        else:
            missing.append(n)
    if choices:
        print("folders with more than one candidate "
              "(taking the smallest; pass --pick to override):\n")
        for n, cs in choices.items():
            for i, c in enumerate(cs):
                mark = "  <- using" if i == 0 else ""
                print(f"  {n:<14}{c.name[:44]:<46}"
                      f"{c.stat().st_size/1048576:8.1f}M{mark}")
            print()
    return got, missing


def scan(got, missing):
    print(f"{'texture':<14}{'format':>7}{'rate':>8}{'ch':>4}"
          f"{'duration':>11}{'size':>11}")
    print("-" * 56)
    total = 0
    for n, p in got.items():
        i = sf.info(str(p))
        sz = p.stat().st_size
        total += sz
        print(f"{n:<14}{p.suffix.lstrip('.'):>7}{i.samplerate:>8}{i.channels:>4}"
              f"{i.duration/60:>9.1f}m{sz/1048576:>10.1f}M   {p.name[:34]}")
    print("-" * 56)
    print(f"{'total':<14}{'':>19}{'':>11}{total/1048576:>10.1f}M")
    if missing:
        print(f"\nmissing: {', '.join(missing)}")
    return total


def build_one(path: Path, out: Path, loop_s, seam_s):
    info = sf.info(str(path))
    sr, dur = info.samplerate, info.duration
    want = min(loop_s + seam_s, dur)
    start = min(dur * START_FRAC, max(0.0, dur - want))

    data, _ = sf.read(str(path), start=int(start * sr),
                      stop=int((start + want) * sr), dtype="float32",
                      always_2d=True)
    if data.shape[0] < int(sr * 5):
        return None

    # MP3 only carries 32/44.1/48kHz. Three of these sources are 96k.
    if sr not in (32000, 44100, 48000):
        import librosa
        target = 48000
        data = np.stack([librosa.resample(data[:, c], orig_sr=sr, target_sr=target)
                         for c in range(data.shape[1])], axis=1)
        sr = target

    seam = int(min(seam_s, data.shape[0] / sr / 4) * sr)
    body = data[:-seam] if seam and data.shape[0] > seam * 2 else data

    # Fold the tail back over the head so the wrap-around has no join.
    if seam and body.shape[0] > seam:
        tail = data[-seam:]
        fade_in = np.linspace(0, 1, seam)[:, None]
        body = body.copy()
        body[:seam] = body[:seam] * fade_in + tail * (1 - fade_in)

    peak = float(np.max(np.abs(body))) or 1.0
    body = body / peak * 0.89

    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out), body, sr, format="MP3")
    return body.shape[0] / sr


def build(got, loop_s, seam_s):
    OUTDIR.mkdir(exist_ok=True)
    before = after = 0
    print(f"\nwriting {len(got)} loops to {OUTDIR}/ "
          f"({loop_s:.0f}s body, {seam_s:.0f}s seam)\n")
    for n, p in sorted(got.items()):
        out = OUTDIR / f"{n}.mp3"
        want = PER_TEXTURE_LOOP.get(n, loop_s)
        try:
            secs = build_one(p, out, want, seam_s)
            b, a = p.stat().st_size, out.stat().st_size
            before += b; after += a
            flag = "   SHORT LOOP" if secs < want * 0.8 else ""
            print(f"  {n:<14}{b/1048576:8.1f}M ->{a/1048576:7.2f}M   "
                  f"{secs:5.0f}s loop   {a/b*100:5.1f}%{flag}")
        except Exception as e:
            print(f"  {n:<14}FAILED: {e}")
    print(f"\n  {before/1048576:.0f} MB  ->  {after/1048576:.1f} MB "
          f"({after/before*100:.1f}%)")


def r2():
    try:
        import boto3
    except ImportError:
        sys.exit("boto3 not installed.  pip install boto3")
    for p in [Path(".env"), Path(__file__).resolve().parent / ".env"]:
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break
    a = os.environ.get("R2_ACCOUNT_ID")
    k = os.environ.get("R2_ACCESS_KEY_ID")
    s = os.environ.get("R2_SECRET_ACCESS_KEY")
    if not all([a, k, s]):
        sys.exit("Missing R2 credentials in environment or .env")
    return boto3.client("s3", endpoint_url=f"https://{a}.r2.cloudflarestorage.com",
                        aws_access_key_id=k, aws_secret_access_key=s,
                        region_name="auto")


def upload(delete_wav, only=None):
    files = sorted(OUTDIR.glob("*.mp3"))
    if only:
        files = [f for f in files if f.stem in only]
        if not files:
            sys.exit(f"nothing in {OUTDIR} matching {', '.join(only)}")
    if not files:
        sys.exit(f"nothing in {OUTDIR} — run --build first")
    s3 = r2()
    print(f"\nuploading {len(files)} textures\n")
    for f in files:
        key = f"textures/{f.name}"
        print(f"  {key}", end=" ... ", flush=True)
        s3.upload_file(str(f), BUCKET, key,
                       ExtraArgs={"ContentType": "audio/mpeg"})
        print(f"{f.stat().st_size/1048576:.2f} MB")
    if delete_wav:
        print("\nremoving the WAV originals from R2:")
        for n in (only if only else NAMES):
            key = f"textures/{n}.wav"
            try:
                s3.head_object(Bucket=BUCKET, Key=key)
            except Exception:
                continue
            s3.delete_object(Bucket=BUCKET, Key=key)
            print(f"  deleted {key}")


def relink(lib_path):
    p = Path(lib_path)
    if not p.exists():
        print(f"{lib_path} not found — skipping relink")
        return
    lib = json.loads(p.read_text(encoding="utf-8"))
    tex = lib.get("_textures", {}).get("files", {})
    n = 0
    for name, d in tex.items():
        new = f"{PUBLIC}/textures/{name}.mp3"
        if d.get("url") != new:
            d["url"] = new
            d.pop("bytes", None)
            n += 1
    if tex:
        lib["_textures"]["format"] = "mp3"
        lib["_textures"]["loopSeconds"] = LOOP_S
        p.write_text(json.dumps(lib, indent=1), encoding="utf-8")
        print(f"\nrelinked {n} texture URLs in {lib_path} to .mp3")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--textures-root", default="assets/textures")
    ap.add_argument("--loop", type=float, default=LOOP_S)
    ap.add_argument("--seam", type=float, default=SEAM_S)
    ap.add_argument("--only", default=None,
                    help="comma-separated texture names — rebuild just these")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--delete-wav", action="store_true")
    ap.add_argument("--lib", default="library.json")
    args = ap.parse_args()

    if args.build or not args.upload:
        root = Path(args.textures_root)
        if not root.exists():
            sys.exit(f"textures root not found: {root}\n"
                     f"Point --textures-root at the folder holding the WAVs.")
        got, missing = find_sources(root)
        if not got:
            sys.exit(f"no texture files found under {root}")
        if args.only:
            want = [n.strip() for n in args.only.split(",") if n.strip()]
            unknown = [n for n in want if n not in got]
            if unknown:
                sys.exit(f"not found: {', '.join(unknown)}\n"
                         f"available: {', '.join(sorted(got))}")
            got = {k: v for k, v in got.items() if k in want}
            missing = []
            print(f"(only: {', '.join(want)})\n")
        scan(got, missing)
        if args.build:
            build(got, args.loop, args.seam)
        else:
            print("\nScan only. Re-run with --build to write the loops.")
            return

    if args.upload:
        upload(args.delete_wav,
               [n.strip() for n in args.only.split(',')] if args.only else None)
        relink(args.lib)


if __name__ == "__main__":
    main()
