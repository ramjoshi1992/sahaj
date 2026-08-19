"""
ZenTune | calibrate_textures.py
===============================
Measures the properties the bed-level model needs, and writes them into
library.json. Run once; the model reads the numbers at runtime.

A flat "textures at 15%" fails because 15% of what is not comparable between
files. rain is dense broadband; fireplace_1 is sparse crackle with a high
crest factor; night_1 is narrow and high. At the same nominal level they sit
in completely different places perceptually.

Measured per texture:
  bands       energy in 8 octave bands, normalised — where the texture lives
  loudnessDb  90th percentile of 200ms RMS. A high percentile over short
              windows, because for a bed sitting under music what you notice
              is the part that pokes through, not the average. The first pass
              used the 75th over 400ms and read fireplace_1 at -40dB, which
              then demanded above-unity gain to reach a sensible level.
  crestDb     95th percentile over median of 50ms RMS. How much it pokes
              above its own average, which is what makes it noticeable.

Measured per group:
  bands           the same 8-band profile, aggregated over its pieces after
                  the per-piece gain trim
  musicLoudnessDb the group's own level on the same scale

The model then places the texture a fixed depth below the music's energy in
the texture's own bands, rather than below the music overall. See bedlevel.js.

    python calibrate_textures.py                 # textures + all groups
    python calibrate_textures.py --quick         # 6 pieces per group
"""

import argparse, json, sys
from pathlib import Path
import numpy as np
import librosa
from scipy.signal import bilinear, lfilter
import warnings
warnings.filterwarnings("ignore")


def k_weight(y, sr):
    """
    ITU-R BS.1770 K-weighting: a high shelf plus a high-pass, which is the
    broadcast standard for comparing the perceived level of different
    programme material.

    Without it, raw energy piles up below 90Hz in almost everything — the
    first calibration run had storm_2 reading 93% sub-90Hz, which describes
    rumble rather than what a thunderstorm sounds like. The ear is around
    20dB less sensitive at 60Hz than at 1kHz, so measuring unweighted made
    the band overlap depend on content neither the music nor the texture is
    really about.
    """
    # stage 1: high-frequency shelf (head/torso response)
    f0, G, Q = 1681.97, 3.99984, 0.7071752
    K = np.tan(np.pi * f0 / sr)
    Vh = np.power(10.0, G / 20.0)
    Vb = np.power(Vh, 0.499666774)
    a0 = 1.0 + K / Q + K * K
    b = np.array([(Vh + Vb * K / Q + K * K) / a0,
                  2.0 * (K * K - Vh) / a0,
                  (Vh - Vb * K / Q + K * K) / a0])
    a = np.array([1.0,
                  2.0 * (K * K - 1.0) / a0,
                  (1.0 - K / Q + K * K) / a0])
    y = lfilter(b, a, y)

    # stage 2: high-pass
    f0, Q = 38.13547087, 0.5003270373
    K = np.tan(np.pi * f0 / sr)
    a0 = 1.0 + K / Q + K * K
    b = np.array([1.0, -2.0, 1.0])
    a = np.array([1.0,
                  2.0 * (K * K - 1.0) / a0,
                  (1.0 - K / Q + K * K) / a0])
    return lfilter(b, a, y)

SR = 22050
EDGES = [0, 90, 180, 355, 710, 1400, 2800, 5600, 11025]   # 8 octave-ish bands
LABELS = ["<90", "90-180", "180-355", "355-710", "710-1.4k",
          "1.4-2.8k", "2.8-5.6k", ">5.6k"]

# What the session screen calls each one. A place, not a filename — the user
# is somewhere, they are not choosing an asset.
#
# Two rules, both learned by getting them wrong first. No verbs: someone lying
# in bed with city streets playing is not walking anywhere. And no claims about
# the listener's world that we cannot know — a season ("summer night") or a
# terrain ("mountain stream") can simply be false for them. Describe the sound.
# Absence of a texture is "quiet", which says what you hear rather than what
# has been switched off.
DISPLAY = {
    "beach_1":     "quiet shoreline",
    "beach_2":     "open coast",
    "forest_1":    "among the trees",
    "forest_2":    "woodland birds",
    "city_1":      "city streets",
    "suburb_1":    "quiet street",
    "suburb_2":    "side streets",
    "cafe_1":      "corner caf\u00e9",
    "rain":        "rain outside",
    "storm_1":     "distant thunder",
    "storm_2":     "storm outside",
    "fireplace_1": "by the fire",
    "night_1":     "night crickets",
    "river_1":     "by the river",
}
NO_TEXTURE_LABEL = "quiet"


def band_profile(y, sr):
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=1024)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    out = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        m = (freqs >= lo) & (freqs < hi)
        out.append(float(S[m].sum()) if m.any() else 0.0)
    total = sum(out) or 1.0
    return [round(v / total, 5) for v in out]


def short_rms(y, sr, win_s):
    w = max(1, int(win_s * sr))
    n = len(y) // w
    if n < 2:
        return np.array([np.sqrt(np.mean(y ** 2))])
    return np.sqrt(np.mean(y[:n * w].reshape(n, w) ** 2, axis=1))


def db(v):
    return round(float(20 * np.log10(max(v, 1e-7))), 2)


def measure_texture(path):
    y, sr = librosa.load(str(path), sr=SR, mono=True)
    y = k_weight(y, sr)
    e200 = short_rms(y, sr, 0.200)
    e050 = short_rms(y, sr, 0.050)
    med = float(np.median(e050)) or 1e-7
    return dict(
        bands=band_profile(y, sr),
        loudnessDb=db(float(np.percentile(e200, 90))),
        crestDb=round(float(20 * np.log10(float(np.percentile(e050, 95)) / med)), 2),
        durationS=round(len(y) / sr, 1),
    )


def measure_group(lib, key, root, quick):
    g = lib[key]
    mood, tier = key.split("/")
    picks = []
    for fam in ("A", "B", "C"):
        f = g["families"].get(fam)
        if not f:
            continue
        members = ([f["seed"]] if f["seed"] else []) + f["mids"]
        picks += members[:2] if quick else members

    acc = np.zeros(len(LABELS))
    levels, used = [], 0
    for piece in picks:
        if piece.startswith("seed_"):
            p = root / mood / tier / f"{piece}.mp3"
        else:
            ph, idx = piece.split("/")
            p = root / mood / tier / ph / f"{idx}.mp3"
        if not p.exists():
            continue
        y, sr = librosa.load(str(p), sr=SR, mono=True)
        gain = g["pieces"][piece].get("gain", 1.0)
        y = k_weight(y * gain, sr)
        acc += np.array(band_profile(y, sr))
        levels.append(float(np.percentile(short_rms(y, sr, 0.200), 90)))
        used += 1
    if not used:
        return None
    acc /= acc.sum() or 1.0
    return dict(bands=[round(float(v), 5) for v in acc],
                musicLoudnessDb=db(float(np.median(levels))),
                measuredFrom=used)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", default="library.json")
    ap.add_argument("--textures-dir", default="textures_out")
    ap.add_argument("--stems-root", default="assets/stems")
    ap.add_argument("--only", default=None,
                    help="comma-separated texture names — re-measure just these "
                         "and leave the group music profiles alone")
    ap.add_argument("--skip-groups", action="store_true",
                    help="textures only; the music has not changed")
    ap.add_argument("--quick", action="store_true",
                    help="sample 2 pieces per family instead of all 4")
    args = ap.parse_args()

    libp = Path(args.lib)
    if not libp.exists():
        sys.exit(f"{args.lib} not found — run build_library.py first")
    lib = json.loads(libp.read_text(encoding="utf-8"))

    tdir = Path(args.textures_dir)
    if not tdir.exists():
        sys.exit(f"{tdir} not found — run retexture.py --build first")

    only = [n.strip() for n in args.only.split(",")] if args.only else None
    if only:
        print(f"(only: {', '.join(only)} — group music profiles left as they are)\n")

    print("=== textures ===")
    print(f"{'texture':<14}{'label':<20}{'loud dB':>9}{'crest dB':>10}{'dur':>7}   dominant bands")
    tex = lib.setdefault("_textures", {}).setdefault("files", {})
    for f in sorted(tdir.glob("*.mp3")):
        name = f.stem
        if only and name not in only:
            continue
        m = measure_texture(f)
        entry = tex.setdefault(name, {})
        entry.update(m)
        entry["label"] = DISPLAY.get(name, name.replace("_", " "))
        top = np.argsort(m["bands"])[::-1][:2]
        print(f"{name:<14}{entry['label']:<20}{m['loudnessDb']:>9}{m['crestDb']:>10}{m['durationS']:>7.0f}"
              f"   {LABELS[top[0]]} ({m['bands'][top[0]]*100:.0f}%), "
              f"{LABELS[top[1]]} ({m['bands'][top[1]]*100:.0f}%)")
    lib["_textures"]["bandLabels"] = LABELS
    lib["_textures"]["weighting"] = "BS.1770 K"
    lib["_textures"]["noneLabel"] = NO_TEXTURE_LABEL

    if only or args.skip_groups:
        libp.write_text(json.dumps(lib, indent=1), encoding="utf-8")
        print(f"\nwrote {args.lib} — textures only, groups untouched")
        louds = [t["loudnessDb"] for t in tex.values() if "loudnessDb" in t]
        if louds:
            print(f"texture loudness spread : {max(louds)-min(louds):.1f} dB")
        return

    print("\n=== groups ===")
    root = Path(args.stems_root)
    keys = sorted(k for k in lib if not k.startswith("_"))
    for i, key in enumerate(keys, 1):
        print(f"  [{i}/{len(keys)}] {key}", end=" ... ", flush=True)
        r = measure_group(lib, key, root, args.quick)
        if not r:
            print("no local files")
            continue
        lib[key]["music"] = r
        top = np.argsort(r["bands"])[::-1][:2]
        print(f"{r['musicLoudnessDb']:>7} dB   {LABELS[top[0]]} "
              f"({r['bands'][top[0]]*100:.0f}%), {LABELS[top[1]]} "
              f"({r['bands'][top[1]]*100:.0f}%)   from {r['measuredFrom']} pieces")

    libp.write_text(json.dumps(lib, indent=1), encoding="utf-8")
    print(f"\nwrote {args.lib}  ({libp.stat().st_size/1024:.0f} KB)")

    # a quick look at how far apart the textures actually are
    louds = [t["loudnessDb"] for t in tex.values() if "loudnessDb" in t]
    crests = [t["crestDb"] for t in tex.values() if "crestDb" in t]
    if louds:
        print(f"\ntexture loudness spread : {max(louds)-min(louds):.1f} dB "
              f"({min(louds)} to {max(louds)})")
        print(f"texture crest spread    : {max(crests)-min(crests):.1f} dB "
              f"({min(crests)} to {max(crests)})")
        print("\nThat spread is what a single fixed percentage was ignoring.")


if __name__ == "__main__":
    main()
