"""
ZenTune | stem_analyser.py
===========================
Finds the best 30-second conditioning anchor in any audio stem.

Used in two ways:
  1. Standalone — analyse a single stem and print results
  2. As a module — imported by the generation pipeline

The anchor is the 30-second window with the highest combined score of:
  - Energy (RMS)       — how full and present the music is
  - Brightness         — spectral centroid, captures harmonic richness
  - Note density       — onset count, captures musical activity

All three normalised and weighted equally.

Standalone usage:
    python stem_analyser.py path/to/stem.mp3
    python stem_analyser.py path/to/stem.mp3 --window 20   (20s anchor)
    python stem_analyser.py assets/stems/happy/ --batch     (analyse folder)

Module usage:
    from stem_analyser import find_anchor
    anchor = find_anchor("path/to/stem.mp3")
    # returns { "start_s": 110, "end_s": 140, "score": 9.09, "duration_s": 174.0 }
"""

import argparse, json
from pathlib import Path

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# CORE ANALYSIS
# ─────────────────────────────────────────────────────────────

def find_anchor(
    audio_path: str | Path,
    window_s: int = 30,
    hop_s: int = 5,
) -> dict:
    """
    Finds the best conditioning anchor window in an audio file.

    Parameters
    ----------
    audio_path : path to any .mp3 / .wav file
    window_s   : anchor window length in seconds (default 30)
    hop_s      : step between candidate windows in seconds (default 5)

    Returns
    -------
    {
        "start_s"    : int,    # anchor start in seconds
        "end_s"      : int,    # anchor end in seconds
        "score"      : float,  # composite quality score
        "duration_s" : float,  # total audio duration
        "top3"       : [...],  # top 3 windows for reference
    }
    """
    if not LIBROSA_AVAILABLE:
        raise ImportError("Run: pip install librosa")

    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")

    y, sr = librosa.load(str(path), sr=None, mono=True)
    duration_s = len(y) / sr
    window_samples = int(window_s * sr)
    hop_samples    = int(hop_s * sr)

    # Global normalisation baselines
    global_rms    = float(np.sqrt(np.mean(y ** 2))) or 1e-8
    global_bright = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))) or 1e-8

    candidates = []
    for start_sample in range(0, len(y) - window_samples, hop_samples):
        seg = y[start_sample : start_sample + window_samples]
        if len(seg) < window_samples:
            break

        energy    = float(np.sqrt(np.mean(seg ** 2)))
        brightness= float(np.mean(librosa.feature.spectral_centroid(y=seg, sr=sr)))
        n_onsets  = len(librosa.onset.onset_detect(y=seg, sr=sr))

        # Normalise each dimension against global baseline
        e_norm = energy     / global_rms
        b_norm = brightness / global_bright
        o_norm = n_onsets   / max(window_s * 2, 1)   # onsets per second baseline

        score = (e_norm + b_norm + o_norm) / 3.0
        start_s = int(start_sample / sr)
        candidates.append({
            "start_s"   : start_s,
            "end_s"     : start_s + window_s,
            "score"     : round(score, 3),
            "energy"    : round(e_norm, 3),
            "brightness": round(b_norm, 3),
            "activity"  : round(o_norm, 3),
        })

    if not candidates:
        # Very short file — use whole thing
        return {
            "start_s": 0,
            "end_s": int(duration_s),
            "score": 0.0,
            "duration_s": round(duration_s, 1),
            "top3": [],
        }

    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]

    return {
        "start_s"    : best["start_s"],
        "end_s"      : best["end_s"],
        "score"      : best["score"],
        "duration_s" : round(duration_s, 1),
        "top3"       : candidates[:3],
        "file"       : str(path),
    }


def analyse_folder(
    folder: str | Path,
    window_s: int = 30,
    manifest_path: str | Path = None,
) -> dict:
    """
    Analyses every .mp3 in a folder tree and returns / saves a manifest.

    Manifest structure:
    {
        "stems/happy/core/00.mp3": { "start_s": 110, "end_s": 140, ... },
        ...
    }
    """
    folder = Path(folder)
    files  = sorted(folder.rglob("*.mp3"))
    print(f"Analysing {len(files)} stems in {folder}...\n")

    manifest = {}
    for i, f in enumerate(files):
        rel = str(f.relative_to(folder.parent) if folder.parent else f)
        try:
            result = find_anchor(f, window_s=window_s)
            manifest[rel] = {
                "start_s"    : result["start_s"],
                "end_s"      : result["end_s"],
                "score"      : result["score"],
                "duration_s" : result["duration_s"],
            }
            print(f"  [{i+1}/{len(files)}] {f.name}")
            print(f"    Anchor : {result['start_s']}s – {result['end_s']}s  "
                  f"(score: {result['score']:.3f}, "
                  f"duration: {result['duration_s']}s)")
            for j, t in enumerate(result["top3"][:3]):
                marker = " ← BEST" if j == 0 else ""
                print(f"    Top {j+1}  : {t['start_s']}s–{t['end_s']}s  "
                      f"E:{t['energy']:.2f} B:{t['brightness']:.2f} "
                      f"A:{t['activity']:.2f}{marker}")
            print()
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")
            manifest[rel] = {"error": str(e)}

    if manifest_path:
        out = Path(manifest_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Manifest saved: {out}")

    return manifest


# ─────────────────────────────────────────────────────────────
# STANDALONE CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Find the best conditioning anchor in a stem or folder of stems"
    )
    parser.add_argument("path", help="Path to .mp3 file or folder")
    parser.add_argument("--window",   type=int, default=30,
                        help="Anchor window length in seconds (default: 30)")
    parser.add_argument("--batch",    action="store_true",
                        help="Analyse all .mp3 files in the folder recursively")
    parser.add_argument("--manifest", default=None,
                        help="Save batch results to this JSON file")
    args = parser.parse_args()

    if not LIBROSA_AVAILABLE:
        print("Install librosa first:  pip install librosa")
        return

    target = Path(args.path)

    if args.batch or target.is_dir():
        analyse_folder(target, window_s=args.window,
                       manifest_path=args.manifest or "stem_anchors.json")
    else:
        result = find_anchor(target, window_s=args.window)
        print(f"\nFile     : {target.name}")
        print(f"Duration : {result['duration_s']}s")
        print(f"\nBest anchor ({args.window}s window):")
        print(f"  Start  : {result['start_s']}s  ({result['start_s']//60}:"
              f"{result['start_s']%60:02d})")
        print(f"  End    : {result['end_s']}s  ({result['end_s']//60}:"
              f"{result['end_s']%60:02d})")
        print(f"  Score  : {result['score']:.3f}")
        print(f"\nTop 3 candidates:")
        for i, t in enumerate(result["top3"]):
            marker = " ← recommended" if i == 0 else ""
            print(f"  {i+1}. {t['start_s']}s–{t['end_s']}s  "
                  f"(energy:{t['energy']:.2f} "
                  f"brightness:{t['brightness']:.2f} "
                  f"activity:{t['activity']:.2f}){marker}")
        print(f"\nUse in test_hybrid.py:")
        print(f"  --ref-start {result['start_s']} "
              f"--ref-end {result['end_s']}")


if __name__ == "__main__":
    main()
