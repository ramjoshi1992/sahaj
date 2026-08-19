"""
ZenTune | generate_mood.py  v2
================================
End-to-end pipeline for one mood using 3 Lyria seeds per tier.

For each context tier (energetic / balanced / mellow):
  1. Generate 3 Lyria seeds (3 different musical interpretations)
  2. Analyse each seed → find best 30s anchor (different window per seed)
  3. Upload each seed to ElevenLabs → get song_id
  4. Generate 3 pieces per seed (9 total per tier):
       Seed A → intro/00, core/00, core/01   (best anchor)
       Seed B → intro/01, core/02, core/03   (second anchor)
       Seed C → core/04,  outro/00, outro/01 (third anchor)
  5. Core pieces trimmed by 10s to remove ElevenLabs fade-out
  6. Upload all pieces to R2, save to manifest

Resumable — skips files already on disk and in manifest.

Usage:
    python generate_mood.py --mood happy
    python generate_mood.py --mood kickstart
    python generate_mood.py --mood focus --tier balanced
    python generate_mood.py --mood happy --dry-run
"""

import os, sys, base64, json, time, argparse, warnings, io
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────
STEMS_DIR      = Path("assets/stems")
MANIFEST       = Path("stem_manifest.json")
CHUNK_MAX_MS   = 120000   # ElevenLabs 2-min chunk limit
CORE_TRIM_MS   = 10000    # trim last 10s off core pieces (removes auto fade-out)
SEEDS_PER_TIER = 3

TIERS = ["energetic", "balanced", "mellow"]

# 3 seeds × 3 pieces each = 9 pieces per tier
# Seed A → intro/00, core/00, core/01
# Seed B → intro/01, core/02, core/03
# Seed C → core/04,  outro/00, outro/01
SEED_PLAN = [
    [("intro", 0), ("core", 0), ("core", 1)],   # Seed A
    [("intro", 1), ("core", 2), ("core", 3)],   # Seed B
    [("core",  4), ("outro",0), ("outro", 1)],  # Seed C
]

# Phase-specific ElevenLabs style modifiers
PHASE_POSITIVE = {
    "intro": ["gentle opening", "sparse", "inviting", "building slowly"],
    "core" : ["sustained energy throughout", "no fade out", "continuous",
              "open ended", "loop ready", "maintains momentum"],
    "outro": ["gentle resolution", "winding down", "peaceful conclusion"],
}
PHASE_NEGATIVE = {
    "intro": ["loud", "busy", "full arrangement", "peak energy"],
    "core" : ["fade out", "ending", "resolution", "outro",
              "conclusion", "wind down", "fading"],
    "outro": ["energetic", "building", "rising", "loud"],
}


# ── Imports ───────────────────────────────────────────────────
def check_imports():
    missing = []
    for pkg, name in [("google.genai","google-genai"),
                      ("elevenlabs","elevenlabs"),
                      ("boto3","boto3"),
                      ("librosa","librosa"),
                      ("pydub","pydub")]:
        try: __import__(pkg)
        except ImportError: missing.append(name)
    if missing:
        print(f"Install: pip install {' '.join(missing)}"); sys.exit(1)

check_imports()

from google import genai as google_genai
from elevenlabs import ElevenLabs
from elevenlabs.types import (
    CompositionPlan, GenerationChunkInput, AudioRefChunk, TimeRange
)
import boto3
from stem_analyser import find_anchor
from prompt_library import LYRIA_PROMPTS, ELEVENLABS_CONFIG


# ── Clients ───────────────────────────────────────────────────
def get_lyria_client():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key: print("Set GEMINI_API_KEY in .env"); sys.exit(1)
    return google_genai.Client(api_key=key)

def get_el_client():
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key: print("Set ELEVENLABS_API_KEY in .env"); sys.exit(1)
    return ElevenLabs(api_key=key)

def get_r2():
    for v in ["R2_ACCOUNT_ID","R2_ACCESS_KEY_ID","R2_SECRET_ACCESS_KEY"]:
        if not os.getenv(v): print(f"Set {v} in .env"); sys.exit(1)
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


# ── Lyria ─────────────────────────────────────────────────────
def generate_lyria_seed(client, prompt: str, max_retries: int = 5) -> bytes:
    for attempt in range(1, max_retries + 1):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                response = client.models.generate_content(
                    model="lyria-3-pro-preview",
                    contents=prompt,
                )
            if not response.candidates:
                raise ValueError("No candidates in Lyria response")
            content = response.candidates[0].content
            if content is None:
                raise ValueError("Lyria content is None (transient error)")
            for part in content.parts:
                inline = getattr(part, "inline_data", None)
                if inline:
                    data = getattr(inline, "data", None)
                    if data:
                        return base64.b64decode(data) if isinstance(data, str) else bytes(data)
            raise ValueError("No audio in Lyria response parts")
        except Exception as e:
            if attempt < max_retries:
                wait = min(15 * (2 ** (attempt - 1)), 120)  # 15s, 30s, 60s, 120s
                print(f"    Attempt {attempt} failed: {e}  — retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise RuntimeError(f"Lyria failed after {max_retries} attempts: {e}")


# ── ElevenLabs ────────────────────────────────────────────────
def generate_el_piece(
    client, song_id: str,
    ref_start_ms: int, ref_end_ms: int,
    mood: str, phase: str,
) -> bytes:
    cfg      = ELEVENLABS_CONFIG[mood]
    pos_tags = cfg["style_tags"] + PHASE_POSITIVE[phase]
    neg_tags = cfg["negative_styles"] + PHASE_NEGATIVE[phase]

    plan = CompositionPlan(chunks=[
        GenerationChunkInput(
            text=cfg["style_text"],
            duration_ms=CHUNK_MAX_MS,
            positive_styles=pos_tags,
            negative_styles=neg_tags,
            context_adherence="high",
            conditioning_ref=AudioRefChunk(
                song_id=song_id,
                range=TimeRange(start_ms=ref_start_ms, end_ms=ref_end_ms),
            ),
            condition_strength=(
                "high"   if phase in ("intro", "outro")
                else "medium"   # core: more creative latitude for variety
            ),
        )
    ])

    stream      = client.music.stream(composition_plan=plan, model_id="music_v2")
    audio_bytes = b"".join(stream)

    # Trim fade-out from core pieces
    if phase == "core" and CORE_TRIM_MS > 0:
        try:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
            seg = seg[:-CORE_TRIM_MS]
            buf = io.BytesIO()
            seg.export(buf, format="mp3", bitrate="192k")
            audio_bytes = buf.getvalue()
        except Exception as e:
            print(f"    Warning: trim failed ({e}) — using untrimmed")

    return audio_bytes


# ── R2 ────────────────────────────────────────────────────────
def upload_r2(r2, local_path: Path, r2_key: str) -> str:
    bucket = os.getenv("R2_BUCKET_NAME", "zentune-sessions")
    domain = os.getenv("R2_PUBLIC_DOMAIN", "").rstrip("/")
    r2.upload_file(
        Filename=str(local_path),
        Bucket=bucket,
        Key=r2_key,
        ExtraArgs={"ContentType": "audio/mpeg"},
    )
    return f"{domain}/{r2_key}"


# ── Manifest ──────────────────────────────────────────────────
def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}

def save_manifest(data: dict):
    MANIFEST.write_text(json.dumps(data, indent=2))


# ── Main pipeline ─────────────────────────────────────────────
def process_mood(mood: str, tiers: list, dry_run: bool):
    if mood not in LYRIA_PROMPTS:
        print(f"Unknown mood '{mood}'. Options: {list(LYRIA_PROMPTS.keys())}")
        sys.exit(1)

    total_pieces = SEEDS_PER_TIER * len(SEED_PLAN[0]) * len(tiers)
    print(f"\n{'='*60}")
    print(f"  MOOD: {mood.upper()}")
    print(f"  Tiers: {tiers}")
    print(f"  Seeds per tier: {SEEDS_PER_TIER}")
    print(f"  Pieces per tier: {SEEDS_PER_TIER * len(SEED_PLAN[0])} "
          f"(3 seeds × 3 pieces each)")
    print(f"  Total: {total_pieces} pieces")
    print(f"{'='*60}\n")

    if dry_run:
        print("[DRY RUN] No API calls will be made.\n")

    lyria_client = None if dry_run else get_lyria_client()
    el_client    = None if dry_run else get_el_client()
    r2_client    = None if dry_run else get_r2()
    manifest     = load_manifest()

    for tier in tiers:
        print(f"\n── Tier: {tier} ──────────────────────────────────")
        tier_dir = STEMS_DIR / mood / tier
        tier_dir.mkdir(parents=True, exist_ok=True)

        for seed_idx, pieces in enumerate(SEED_PLAN):
            seed_label = chr(65 + seed_idx)  # A, B, C
            seed_path  = tier_dir / f"seed_{seed_label.lower()}.mp3"

            print(f"\n  ── Seed {seed_label} ──")

            # ── Step 1: Generate Lyria seed ───────────────────
            print(f"  [1/3] Lyria seed {seed_label}")
            if seed_path.exists():
                print(f"    ✓ Already exists ({seed_path.stat().st_size//1024} KB)")
            elif dry_run:
                print(f"    [DRY RUN] Would generate: {seed_path}")
            else:
                variant = chr(97 + seed_idx)  # "a", "b", "c"
                prompt = LYRIA_PROMPTS[mood][tier][variant]
                print(f"    Generating 3-minute seed...")
                t0    = time.time()
                audio = generate_lyria_seed(lyria_client, prompt)
                seed_path.write_bytes(audio)
                print(f"    ✓ Saved {seed_path.stat().st_size//1024} KB in {time.time()-t0:.0f}s")
                time.sleep(15)  # Lyria rate limit — wait between seed calls

            # ── Step 2: Analyse anchor ────────────────────────
            print(f"  [2/3] Anchor analysis")
            if seed_path.exists():
                result = find_anchor(seed_path)
                # Use different top-3 windows per seed index
                candidates = result.get("top3", [])
                if seed_idx < len(candidates):
                    candidate   = candidates[seed_idx]
                    ref_start_s = candidate["start_s"]
                    ref_end_s   = candidate["end_s"]
                else:
                    ref_start_s = result["start_s"]
                    ref_end_s   = result["end_s"]
                ref_start_ms = ref_start_s * 1000
                ref_end_ms   = ref_end_s   * 1000
                print(f"    ✓ Anchor {seed_label}: {ref_start_s}s–{ref_end_s}s")
            else:
                # Dry run fallback: stagger anchors
                ref_start_ms = (30 + seed_idx * 30) * 1000
                ref_end_ms   = ref_start_ms + 30000
                print(f"    [DRY RUN] Anchor: {ref_start_ms//1000}s–{ref_end_ms//1000}s")

            # ── Step 3: Upload seed to ElevenLabs ─────────────
            print(f"  [3/3] ElevenLabs pieces from Seed {seed_label}")
            song_id = None
            if dry_run:
                song_id = f"dry_run_{seed_label}"
            elif seed_path.exists():
                print(f"    Uploading seed {seed_label} ({seed_path.stat().st_size//1024} KB)...")
                t0 = time.time()
                with open(seed_path, "rb") as f:
                    upload = el_client.music.upload(file=f)
                song_id = upload.song_id
                print(f"    ✓ song_id: {song_id} ({time.time()-t0:.0f}s)")
            else:
                print(f"    Seed not generated — skipping")
                continue

            # ── Generate pieces for this seed ─────────────────
            for phase, idx in pieces:
                out_path     = tier_dir / phase / f"{idx:02d}.mp3"
                r2_key       = f"stems/{mood}/{tier}/{phase}/{idx:02d}.mp3"
                manifest_key = f"{mood}/{tier}/{phase}/{idx:02d}"
                out_path.parent.mkdir(parents=True, exist_ok=True)

                label = f"    [{phase}/{idx:02d}.mp3]"

                if manifest_key in manifest and out_path.exists():
                    print(f"{label} ✓ Already complete")
                    continue

                if dry_run:
                    print(f"{label} [DRY RUN] Seed {seed_label}, anchor {ref_start_ms//1000}s–{ref_end_ms//1000}s")
                    continue

                if not out_path.exists():
                    print(f"{label} Generating (Seed {seed_label}, {phase})...")
                    t0 = time.time()
                    try:
                        audio = generate_el_piece(
                            el_client, song_id,
                            ref_start_ms, ref_end_ms,
                            mood, phase,
                        )
                        out_path.write_bytes(audio)
                        print(f"{label} ✓ {out_path.stat().st_size//1024} KB in {time.time()-t0:.0f}s")
                    except Exception as e:
                        print(f"{label} ✗ Failed: {e}")
                        continue
                    time.sleep(1)

                # Upload to R2
                try:
                    url = upload_r2(r2_client, out_path, r2_key)
                    manifest[manifest_key] = url
                    save_manifest(manifest)
                    print(f"{label} ✓ R2: {url}")
                except Exception as e:
                    print(f"{label} ✗ R2 failed: {e}")

    # ── Print STEM_CONFIG for this mood ───────────────────────
    print(f"\n\n{'='*60}")
    print(f"  STEM_CONFIG entry for '{mood}':")
    print(f"{'='*60}\n")
    print(f"    {mood}: {{")
    for tier in tiers:
        print(f"        {tier}: {{")
        # Gather all phases
        for phase in ["intro", "core", "outro"]:
            all_idxs = sorted(set(
                idx for _, pieces in enumerate(SEED_PLAN)
                for p, idx in pieces if p == phase
            ))
            urls = [manifest.get(f"{mood}/{tier}/{phase}/{i:02d}", "") for i in all_idxs]
            urls_str = ",\n                    ".join(f"'{u}'" for u in urls if u)
            print(f"            {phase}: [\n                    {urls_str},\n            ],")
        print(f"        }},")
    print(f"    }},\n")


# ── Entry point ───────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mood", required=True,
                        choices=list(LYRIA_PROMPTS.keys()))
    parser.add_argument("--tier", default=None, choices=TIERS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tiers = [args.tier] if args.tier else TIERS
    process_mood(args.mood, tiers, args.dry_run)


if __name__ == "__main__":
    main()
