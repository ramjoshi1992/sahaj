"""
ZenTune | elevenlabs_gen.py
============================
Generates layering-compatible stems for rhythmic moods using ElevenLabs Music API,
then uploads them to Cloudflare R2 and prints the STEM_CONFIG block for index.html.

Key design principle — LAYERING COMPATIBILITY:
  All stems for one mood are generated in the SAME musical key and BPM.
  Core stems alternate between two roles:
    'melodic'  → carries the main musical idea (goes into core-primary layer)
    'rhythmic' → provides groove and movement (goes into core-texture layer)
  When a melodic + rhythmic stem play simultaneously, they complement each other
  rather than clash, because they serve different musical functions.

Usage:
    pip install elevenlabs boto3 python-dotenv
    python elevenlabs_gen.py
    python elevenlabs_gen.py --mood happy --dry-run

Output:
    assets/stems/happy/intro/00.mp3 ... etc.
    Prints the STEM_CONFIG block to paste into index.html.

.env required:
    ELEVENLABS_API_KEY=...
    R2_ACCOUNT_ID=...
    R2_ACCESS_KEY_ID=...
    R2_SECRET_ACCESS_KEY=...
    R2_BUCKET_NAME=zentune-sessions
    R2_PUBLIC_DOMAIN=https://pub-xxx.r2.dev
"""

import os, sys, json, time, argparse, logging
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
import boto3

load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger("zentune.gen")

STEMS_DIR      = Path(__file__).parent / "assets" / "stems"
R2_PUBLIC_DOMAIN = os.getenv("R2_PUBLIC_DOMAIN", "")
R2_BUCKET_NAME   = os.getenv("R2_BUCKET_NAME", "zentune-sessions")

# ─────────────────────────────────────────────────────────────
# GENERATION CATALOGUE
# ─────────────────────────────────────────────────────────────
# Each mood defines:
#   key + bpm  — enforced in every prompt to guarantee layering compatibility
#   intro      — 2 sparse/building prompts
#   core       — 6 prompts, alternating melodic (M) and rhythmic (R) roles
#   outro      — 2 resolving/fading prompts
#
# 'melodic' stems carry the main musical idea → plays at 85% volume as primary
# 'rhythmic' stems provide groove/pulse       → plays at 35% volume as texture
# Layering melodic + rhythmic = full, varied sound with no clash
# ─────────────────────────────────────────────────────────────

CATALOGUE = {

    "happy": {
        "key": "C major", "bpm": 120,
        "intro": [
            "gentle acoustic guitar and soft piano building intro, "
            "C major, 120 BPM, upbeat feel-good, instrumental only, no lyrics, "
            "sparse beginning growing to warmth, summer morning",

            "soft ukulele strumming and light percussion intro, "
            "C major, 120 BPM, joyful and sunny, instrumental, no lyrics, "
            "simple and inviting, energy builds gently",
        ],
        "core": [
            # M: melodic — carries the musical idea
            "upbeat acoustic guitar lead melody, feel-good pop, "
            "C major, 120 BPM, summer afternoon, bright and carefree, "
            "instrumental only, no lyrics, full arrangement, catchy",

            # R: rhythmic — groove and movement
            "light drum groove and bass guitar rhythm, upbeat pop, "
            "C major, 120 BPM, positive driving energy, minimal melody, "
            "instrumental, no lyrics, rhythmic backbone, punchy",

            # M: melodic — different instrument
            "piano melody with bright chords, uplifting feel-good, "
            "C major, 120 BPM, joyful summer day, instrumental, no lyrics, "
            "warm and melodic, light orchestration",

            # R: rhythmic — different texture
            "acoustic strumming rhythm with handclaps and light shaker, "
            "C major, 120 BPM, upbeat organic groove, no lead melody, "
            "instrumental, no lyrics, rhythmic texture, folk-pop feel",

            # M: melodic — third variation
            "bright electric piano and acoustic guitar melody, pop, "
            "C major, 120 BPM, positive and uplifting, full sound, "
            "instrumental, no lyrics, melodic lead",

            # R: rhythmic — third texture
            "upbeat percussion pattern with bass and muted guitar chops, "
            "C major, 120 BPM, funk-lite groove, no featured melody, "
            "instrumental, no lyrics, rhythmic movement",
        ],
        "outro": [
            "gentle acoustic guitar wind-down, C major, 120 BPM fading, "
            "warm resolution, decreasing energy, instrumental, no lyrics, "
            "soft ending, peaceful close",

            "soft piano resolution chords, C major, gentle fade, "
            "warm and settled, 120 BPM slowing, instrumental, no lyrics, "
            "peaceful conclusion",
        ],
    },

    "kickstart": {
        "key": "G major", "bpm": 126,
        "intro": [
            "morning acoustic guitar intro with rising energy, "
            "G major, 126 BPM, bright and motivating, instrumental, no lyrics, "
            "starts simple, builds with optimism, sunrise feeling",

            "bright piano and light strings intro, "
            "G major, 126 BPM, energising morning, instrumental, no lyrics, "
            "gentle start that rises to drive",
        ],
        "core": [
            # M
            "upbeat acoustic guitar melody, driving folk-pop, "
            "G major, 126 BPM, morning motivation, forward momentum, "
            "bright and clear, instrumental, no lyrics",

            # R
            "steady kick and snare with bass guitar, morning drive, "
            "G major, 126 BPM, energetic rhythm section, no melody, "
            "instrumental, no lyrics, driving pulse",

            # M
            "bright piano lead, motivational pop, "
            "G major, 126 BPM, optimistic and energising, full arrangement, "
            "instrumental, no lyrics, upward melodic movement",

            # R
            "acoustic strumming on the beat with tambourine, "
            "G major, 126 BPM, rhythmic energy, folk-pop groove, "
            "no lead melody, instrumental, no lyrics",

            # M
            "electric piano and acoustic guitar melody, morning commute pop, "
            "G major, 126 BPM, positive and moving forward, "
            "bright instrumentation, instrumental, no lyrics",

            # R
            "punchy percussion and muted bass stabs, morning energy, "
            "G major, 126 BPM, rhythmic drive, minimal harmonic content, "
            "instrumental, no lyrics",
        ],
        "outro": [
            "gentle acoustic guitar resolution, G major, "
            "morning calm after energy, 126 BPM fading to stillness, "
            "instrumental, no lyrics, satisfying close",

            "soft piano chords resolution, G major, "
            "peaceful morning settled, gentle fade, "
            "instrumental, no lyrics, warm ending",
        ],
    },

    "unmotivated": {
        "key": "D major", "bpm": 115,
        "intro": [
            "warm acoustic guitar and piano intro, building momentum, "
            "D major, 115 BPM, motivational and encouraging, "
            "instrumental, no lyrics, starts quiet then lifts",

            "soft bass groove and warm pad intro, "
            "D major, 115 BPM, gentle energy building, "
            "instrumental, no lyrics, forward-feeling warmth",
        ],
        "core": [
            # M
            "warm acoustic guitar melody, motivational pop, "
            "D major, 115 BPM, encouraging and uplifting, "
            "full arrangement, instrumental, no lyrics, melodic drive",

            # R
            "medium-tempo drum groove and bass line, "
            "D major, 115 BPM, steady driving energy, no melody, "
            "instrumental, no lyrics, warm rhythmic backbone",

            # M
            "piano and strings melody, motivational cinematic, "
            "D major, 115 BPM, warm and forward-moving, "
            "uplifting, instrumental, no lyrics",

            # R
            "strummed acoustic chords with shaker and light kick, "
            "D major, 115 BPM, organic rhythmic movement, no lead melody, "
            "instrumental, no lyrics, warm grove",

            # M
            "electric piano melody with acoustic guitar, energy boost, "
            "D major, 115 BPM, warm positive momentum, "
            "instrumental, no lyrics, melodic encouragement",

            # R
            "funk-lite bass and percussion, steady groove, "
            "D major, 115 BPM, driving rhythm, minimal melody, "
            "instrumental, no lyrics, momentum",
        ],
        "outro": [
            "warm acoustic guitar gentle close, D major, "
            "115 BPM fading, satisfied resolution, "
            "instrumental, no lyrics, warm ending",

            "piano resolution, D major, "
            "gently fading, peaceful but still positive, "
            "instrumental, no lyrics, calm close",
        ],
    },
}


# ─────────────────────────────────────────────────────────────
# R2 CLIENT
# ─────────────────────────────────────────────────────────────

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

def upload_to_r2(local_path: Path, r2_key: str) -> str:
    get_s3().upload_file(
        Filename=str(local_path),
        Bucket=R2_BUCKET_NAME,
        Key=r2_key,
        ExtraArgs={"ContentType": "audio/mpeg"},
    )
    return f"{R2_PUBLIC_DOMAIN.rstrip('/')}/{r2_key}"


# ─────────────────────────────────────────────────────────────
# GENERATION
# ─────────────────────────────────────────────────────────────

def generate_stem(client: ElevenLabs, prompt: str, duration_ms: int = 30000) -> bytes:
    """
    Calls ElevenLabs Music API and returns raw MP3 bytes.
    Duration: 30s for core stems (they loop), 20s for intro/outro.
    """
    audio_stream = client.music.stream(
        prompt=prompt,
        output_format="mp3_44100_128",
        music_length_ms=duration_ms,   # SDK v1.50+ renamed duration_ms → music_length_ms
    )
    # Collect streaming chunks
    return b"".join(audio_stream)


def generate_mood(
    client: ElevenLabs,
    mood: str,
    config: dict,
    dry_run: bool = False,
    skip_upload: bool = False,
) -> dict:
    """
    Generates all stems for one mood, saves locally, uploads to R2.
    Returns the STEM_CONFIG entry for this mood.
    """
    log.info(f"\n{'='*52}\n  MOOD: {mood.upper()}\n{'='*52}")
    result = {"intro": [], "core": [], "outro": []}

    for phase in ["intro", "core", "outro"]:
        prompts = config[phase]
        duration_ms = 30000 if phase == "core" else 20000
        phase_dir = STEMS_DIR / mood / phase
        phase_dir.mkdir(parents=True, exist_ok=True)

        for idx, prompt in enumerate(prompts):
            out_path = phase_dir / f"{idx:02d}.mp3"
            r2_key   = f"stems/{mood}/{phase}/{idx:02d}.mp3"
            r2_url   = f"{R2_PUBLIC_DOMAIN.rstrip('/')}/{r2_key}"

            role = ""
            if phase == "core":
                role = " [melodic]" if idx % 2 == 0 else " [rhythmic]"

            log.info(f"  {mood}/{phase}/{idx:02d}.mp3{role}")

            if dry_run:
                log.info(f"    [DRY RUN] prompt: {prompt[:80]}...")
                result[phase].append(r2_url)
                continue

            if out_path.exists():
                log.info(f"    Already on disk — uploading")
                if not skip_upload:
                    r2_url = upload_to_r2(out_path, r2_key)
                result[phase].append(r2_url)
                continue

            # Generate
            log.info(f"    Generating ({duration_ms//1000}s)...")
            try:
                audio_bytes = generate_stem(client, prompt, duration_ms)
                out_path.write_bytes(audio_bytes)
                log.info(f"    ✓ {len(audio_bytes)//1024}KB saved locally")
            except Exception as e:
                log.error(f"    ✗ Generation failed: {e}")
                continue

            # Upload
            if not skip_upload:
                try:
                    r2_url = upload_to_r2(out_path, r2_key)
                    log.info(f"    ✓ Uploaded → {r2_url}")
                except Exception as e:
                    log.error(f"    ✗ Upload failed: {e}")
            else:
                log.info(f"    Skipping upload (--no-upload)")

            result[phase].append(r2_url)
            time.sleep(1)  # be polite to the API

    return result


def print_stem_config(stem_config: dict):
    """Prints the STEM_CONFIG block ready to paste into index.html."""
    print("\n" + "="*60)
    print("// Paste this into STEM_CONFIG in index.html:")
    print("="*60)
    print("const STEM_CONFIG = {")
    for mood, phases in stem_config.items():
        print(f"    {mood}: {{")
        for phase, urls in phases.items():
            if urls:
                url_list = ",\n            ".join(f"'{u}'" for u in urls)
                print(f"        {phase}: [\n            {url_list},\n        ],")
            else:
                print(f"        {phase}: [],")
        print("    },")
    print("};")
    print("="*60 + "\n")


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ZenTune ElevenLabs stem generator")
    parser.add_argument("--mood",      nargs="+", default=list(CATALOGUE.keys()),
                        help="Moods to generate (default: all)")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Plan only — no API calls, no uploads")
    parser.add_argument("--no-upload", action="store_true",
                        help="Generate locally but skip R2 upload")
    parser.add_argument("--api-key",   default=os.getenv("ELEVENLABS_API_KEY"),
                        help="ElevenLabs API key (or set ELEVENLABS_API_KEY env var)")
    args = parser.parse_args()

    if not args.dry_run and not args.api_key:
        log.error("No ElevenLabs API key. Set ELEVENLABS_API_KEY or use --api-key.")
        sys.exit(1)

    client = ElevenLabs(api_key=args.api_key or "dry-run") if not args.dry_run else None
    stem_config = {}

    moods_to_run = [m for m in args.mood if m in CATALOGUE]
    if not moods_to_run:
        log.error(f"Unknown moods. Available: {list(CATALOGUE.keys())}")
        sys.exit(1)

    for mood in moods_to_run:
        cfg = CATALOGUE[mood]
        log.info(f"Key: {cfg['key']}, BPM: {cfg['bpm']}")
        stem_config[mood] = generate_mood(
            client, mood, cfg,
            dry_run=args.dry_run,
            skip_upload=args.no_upload,
        )

    # Summary
    log.info(f"\n{'='*52}")
    log.info("  GENERATION COMPLETE")
    log.info(f"{'='*52}")
    for mood in moods_to_run:
        phases = stem_config[mood]
        counts = {p: len(u) for p, u in phases.items()}
        total  = sum(counts.values())
        log.info(f"  {mood}: {counts} = {total} tracks")

    print_stem_config(stem_config)

    # Save config to file for easy reference
    out = Path("stem_config_output.json")
    out.write_text(json.dumps(stem_config, indent=2))
    log.info(f"Config also saved to: {out}")


if __name__ == "__main__":
    main()
