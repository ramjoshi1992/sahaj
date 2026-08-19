"""
Lull | provenance.py
====================
Generates PROVENANCE.md — the record of how this music was made and what
rights attach to it.

Two things are worth documenting, and only one can be automated.

The inventory — what exists, what it was measured at, which third-party
assets are involved and under what licence — comes straight out of
library.json and credits.json, so it can never drift from the truth.

The creative judgements cannot be extracted from anything. They are the
decisions taken by ear: rejecting one architecture after hearing it, choosing
where a movement should turn, tuning a constant until it sat right. Those are
what distinguish authored work from model output, so they are kept in a hand-
maintained block below and carried through each regeneration.

    python provenance.py
    python provenance.py --out docs\\PROVENANCE.md
"""

import argparse, json, subprocess
from datetime import date
from pathlib import Path

# ── the part no script can derive: judgements made by ear ────────────────
# Add to this as decisions are taken. Keep them dated and specific — "we
# listened and changed X because Y" is the record that matters.
DECISIONS = [
    ("Mood set", "Ten candidate moods reduced to seven by hand. deepwork was "
     "judged to overlap focus, stressed to overlap anxious, and heartbroken "
     "too niche for the scope."),
    ("Prompt authorship", "Every Lyria prompt written by hand in "
     "prompt_library.py — instrumentation, energy arc and BPM range specified "
     "per mood, per tier, per seed variant."),
    ("Seed variants", "Three seeds per group (a/b/c) deliberately given "
     "different energy arcs and lead instruments rather than being "
     "regenerated from one prompt."),
    ("Anchor selection", "stem_analyser.py scores 30-second windows on energy, "
     "brightness and onset density; the chosen window for each seed sets what "
     "the conditioned pieces are derived from."),
    ("Conditioning strength", "Set by hand per phase — high for intros and "
     "outros so they resolve, medium for cores so they vary."),
    ("Layered architecture rejected", "Two core stems playing simultaneously "
     "was built, listened to, and abandoned. The material is complete "
     "arrangements, not stems, so layering two of them plays two pieces at "
     "once. Replaced by sequential playback."),
    ("Family movement structure", "Arrived at by ear over four renders. A "
     "session is three movements, one per seed family; each opens with its "
     "seed, cycles that family's middles, and closes with the same seed. "
     "Family integrity is the rule that makes it work."),
    ("Join rules", "Same family crossfades at a whole metrical unit under "
     "3.5s; different families transition sequentially with a breath and no "
     "overlap. The 8.4s crossfade was reduced after hearing comb filtering on "
     "near-identical material."),
    ("Bed level model", "Texture level derived from measured band overlap, "
     "loudness and crest rather than a fixed percentage, after finding the 14 "
     "recordings sit 24 dB apart in perceived level."),
    ("Sky and stars", "Background computed from solar position and real star "
     "positions for the listener's location and minute, not stock imagery."),
]

PROVIDERS = [
    ("Lyria 3 Pro (Google, via Gemini API)", "63 seed tracks",
     "Google's generative AI terms give users rights to outputs, with "
     "indemnification. Lyria is a Generative AI Preview / Pre-GA offering."),
    ("ElevenLabs Music (Pro plan)", "189 conditioned pieces",
     "Generated while on a paid plan, which carries a perpetual commercial "
     "licence that survives cancellation. Note: anything generated after "
     "cancellation falls under free-tier terms and is NOT cleared for "
     "commercial use."),
]


def git_first_last(path="."):
    try:
        out = subprocess.run(["git", "log", "--reverse", "--format=%ad", "--date=short"],
                             cwd=path, capture_output=True, text=True, timeout=10)
        lines = [l for l in out.stdout.splitlines() if l.strip()]
        if lines:
            return lines[0], lines[-1]
    except Exception:
        pass
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", default="library.json")
    ap.add_argument("--credits", default="credits.json")
    ap.add_argument("--out", default="PROVENANCE.md")
    args = ap.parse_args()

    lib = json.loads(Path(args.lib).read_text(encoding="utf-8")) \
        if Path(args.lib).exists() else {}
    creds = json.loads(Path(args.credits).read_text(encoding="utf-8")) \
        if Path(args.credits).exists() else {}

    groups = {k: v for k, v in lib.items() if not k.startswith("_")}
    pieces = sum(len(g.get("pieces", {})) for g in groups.values())
    seeds = sum(1 for g in groups.values() for p in g.get("pieces", {})
                if p.startswith("seed_"))
    textures = lib.get("_textures", {}).get("files", {})
    first, last = git_first_last()

    L = []
    w = L.append
    w("# Provenance")
    w("")
    w(f"_Generated {date.today().isoformat()} by `provenance.py`. "
      "The inventory is read from `library.json` and `credits.json`; the "
      "decisions below are maintained by hand._")
    w("")
    w("## What this is")
    w("")
    w("A generative music system. Every session is assembled at playback time "
      "from a measured library, following rules arrived at by listening. No "
      "two sessions are identical, and no session exists as a file.")
    w("")

    w("## Human authorship")
    w("")
    w("The recorded material is the raw input, not the work. The work is the "
      "sequence of judgements below — each one taken by ear, several of them "
      "reversing an earlier decision after hearing the result.")
    w("")
    for title, body in DECISIONS:
        w(f"**{title}.** {body}")
        w("")

    w("## Inventory")
    w("")
    w(f"- {len(groups)} mood/tier groups")
    w(f"- {pieces} audio pieces ({seeds} seed tracks, {pieces-seeds} conditioned)")
    w(f"- {len(textures)} texture beds")
    if first:
        w(f"- development from {first} to {last}")
    w("")
    if groups:
        w("| group | families | pool | crossfade | pulsed |")
        w("|---|---|---|---|---|")
        for k in sorted(groups):
            g = groups[k]
            fams = len(g.get("families", {}))
            pool = g.get("totalPool", 0)
            w(f"| {k} | {fams} | {pool/60:.1f} min | "
              f"{g.get('crossfade','—')}s | {g.get('pulsedCount','—')}/12 |")
        w("")

    w("## Generation providers")
    w("")
    for name, what, terms in PROVIDERS:
        w(f"**{name}** — {what}.  ")
        w(f"{terms}")
        w("")

    w("## Third-party material")
    w("")
    if creds:
        w("Texture beds are Creative Commons recordings from Freesound. "
          "Licences verified from the Freesound API by `check_licences.py`.")
        w("")
        w("| texture | source | author | licence |")
        w("|---|---|---|---|")
        for t in sorted(creds):
            c = creds[t]
            lic = c.get("license", "")
            short = ("CC0" if "zero" in lic.lower() else
                     "CC-BY-NC" if "by-nc" in lic.lower() else
                     "CC-BY" if "by" in lic.lower() else lic)
            w(f"| {t} | [{c.get('id')}]({c.get('url')}) | "
              f"{c.get('username')} | {short} |")
        w("")
        need = [c for c in creds.values()
                if "zero" not in (c.get("license") or "").lower()]
        if need:
            w("### Attribution")
            w("")
            w("The following must be credited wherever the app is published:")
            w("")
            for c in sorted(need, key=lambda x: x.get("username", "")):
                w(f"- {c.get('attribution')}")
            w("")
        blocked = [t for t, c in creds.items() if not c.get("usable", True)]
        if blocked:
            w(f"**Not cleared for commercial use: {', '.join(blocked)}** — "
              "these must be replaced before the app charges for anything.")
            w("")
    else:
        w("_credits.json not found — run `check_licences.py` first._")
        w("")

    w("## Position on ownership")
    w("")
    w("Rights to use are granted contractually by both providers. Copyright "
      "ownership of AI-generated output is unresolved in several "
      "jurisdictions, and the US Copyright Office holds that output without "
      "human creative input is not protectable. This document exists to "
      "record the human creative input, which is substantial and is "
      "concentrated in the system rather than in any individual file.")
    w("")
    w("The defensible asset is the architecture — the family movement "
      "structure, the sequencer, the bed-level model and the measured "
      "library. The audio alone does not reproduce it.")
    w("")
    w("_Not legal advice. Worth a solicitor's review before launch._")

    Path(args.out).write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {args.out}  ({len('\n'.join(L))//1024 + 1} KB)")
    print(f"  {len(groups)} groups, {pieces} pieces, {len(textures)} textures, "
          f"{len(DECISIONS)} recorded decisions")
    if creds:
        need = sum(1 for c in creds.values()
                   if "zero" not in (c.get("license") or "").lower())
        print(f"  {need} texture(s) require attribution")


if __name__ == "__main__":
    main()
