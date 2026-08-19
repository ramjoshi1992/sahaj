# Provenance

_Generated 2026-08-19 by `provenance.py`. The inventory is read from `library.json` and `credits.json`; the decisions below are maintained by hand._

## What this is

A generative music system. Every session is assembled at playback time from a measured library, following rules arrived at by listening. No two sessions are identical, and no session exists as a file.

## Human authorship

The recorded material is the raw input, not the work. The work is the sequence of judgements below — each one taken by ear, several of them reversing an earlier decision after hearing the result.

**Mood set.** Ten candidate moods reduced to seven by hand. deepwork was judged to overlap focus, stressed to overlap anxious, and heartbroken too niche for the scope.

**Prompt authorship.** Every Lyria prompt written by hand in prompt_library.py — instrumentation, energy arc and BPM range specified per mood, per tier, per seed variant.

**Seed variants.** Three seeds per group (a/b/c) deliberately given different energy arcs and lead instruments rather than being regenerated from one prompt.

**Anchor selection.** stem_analyser.py scores 30-second windows on energy, brightness and onset density; the chosen window for each seed sets what the conditioned pieces are derived from.

**Conditioning strength.** Set by hand per phase — high for intros and outros so they resolve, medium for cores so they vary.

**Layered architecture rejected.** Two core stems playing simultaneously was built, listened to, and abandoned. The material is complete arrangements, not stems, so layering two of them plays two pieces at once. Replaced by sequential playback.

**Family movement structure.** Arrived at by ear over four renders. A session is three movements, one per seed family; each opens with its seed, cycles that family's middles, and closes with the same seed. Family integrity is the rule that makes it work.

**Join rules.** Same family crossfades at a whole metrical unit under 3.5s; different families transition sequentially with a breath and no overlap. The 8.4s crossfade was reduced after hearing comb filtering on near-identical material.

**Bed level model.** Texture level derived from measured band overlap, loudness and crest rather than a fixed percentage, after finding the 14 recordings sit 24 dB apart in perceived level.

**Sky and stars.** Background computed from solar position and real star positions for the listener's location and minute, not stock imagery.

## Inventory

- 21 mood/tier groups
- 252 audio pieces (63 seed tracks, 189 conditioned)
- 14 texture beds

| group | families | pool | crossfade | pulsed |
|---|---|---|---|---|
| anxious/balanced | 3 | 24.8 min | 3.429s | 4/12 |
| anxious/energetic | 3 | 24.5 min | 3.2s | 7/12 |
| anxious/mellow | 3 | 24.7 min | 1.999s | 11/12 |
| focus/balanced | 3 | 25.3 min | 2.999s | 3/12 |
| focus/energetic | 3 | 25.1 min | 2.999s | 7/12 |
| focus/mellow | 3 | 25.0 min | 3.429s | 11/12 |
| happy/balanced | 3 | 25.1 min | 2.0s | 5/12 |
| happy/energetic | 3 | 25.4 min | 1.967s | 10/12 |
| happy/mellow | 3 | 25.3 min | 2.182s | 8/12 |
| kickstart/balanced | 3 | 25.4 min | 2.0s | 10/12 |
| kickstart/energetic | 3 | 23.9 min | 2.0s | 12/12 |
| kickstart/mellow | 3 | 25.3 min | 2.087s | 4/12 |
| sleepy/balanced | 3 | 22.6 min | 3.2s | 1/12 |
| sleepy/energetic | 3 | 24.6 min | 1.999s | 2/12 |
| sleepy/mellow | 3 | 21.2 min | 2.5s | 0/12 |
| socially-drained/balanced | 3 | 25.0 min | 1.846s | 3/12 |
| socially-drained/energetic | 3 | 24.9 min | 3.428s | 8/12 |
| socially-drained/mellow | 3 | 23.8 min | 2.0s | 1/12 |
| unmotivated/balanced | 3 | 23.6 min | 2.162s | 6/12 |
| unmotivated/energetic | 3 | 24.6 min | 2.466s | 10/12 |
| unmotivated/mellow | 3 | 25.0 min | 2.263s | 9/12 |

## Generation providers

**Lyria 3 Pro (Google, via Gemini API)** — 63 seed tracks.  
Google's generative AI terms give users rights to outputs, with indemnification. Lyria is a Generative AI Preview / Pre-GA offering.

**ElevenLabs Music (Pro plan)** — 189 conditioned pieces.  
Generated while on a paid plan, which carries a perpetual commercial licence that survives cancellation. Note: anything generated after cancellation falls under free-tier terms and is NOT cleared for commercial use.

## Third-party material

Texture beds are Creative Commons recordings from Freesound. Licences verified from the Freesound API by `check_licences.py`.

| texture | source | author | licence |
|---|---|---|---|
| beach_1 | [376795](https://freesound.org/people/amholma/sounds/376795/) | amholma | CC0 |
| beach_2 | [197714](https://freesound.org/people/tim.kahn/sounds/197714/) | tim.kahn | CC-BY |
| cafe_1 | [260062](https://freesound.org/people/mhtaylor67/sounds/260062/) | mhtaylor67 | CC0 |
| city_1 | [716384](https://freesound.org/people/lastraindrop/sounds/716384/) | lastraindrop | CC0 |
| fireplace_1 | [370938](https://freesound.org/people/jmehlferber/sounds/370938/) | jmehlferber | CC0 |
| forest_1 | [427400](https://freesound.org/people/Imjeax/sounds/427400/) | Imjeax | CC-BY |
| forest_2 | [850507](https://freesound.org/people/GammaGool/sounds/850507/) | GammaGool | CC0 |
| night_1 | [210540](https://freesound.org/people/Sclolex/sounds/210540/) | Sclolex | CC0 |
| rain | [234317](https://freesound.org/people/nick121087/sounds/234317/) | nick121087 | CC0 |
| river_1 | [469009](https://freesound.org/people/INNORECORDS/sounds/469009/) | INNORECORDS | CC0 |
| storm_1 | [704603](https://freesound.org/people/VKProduktion/sounds/704603/) | VKProduktion | CC0 |
| storm_2 | [575652](https://freesound.org/people/Garuda1982/sounds/575652/) | Garuda1982 | CC0 |
| suburb_1 | [639133](https://freesound.org/people/kevp888/sounds/639133/) | kevp888 | CC-BY |
| suburb_2 | [205183](https://freesound.org/people/justingregoire/sounds/205183/) | justingregoire | CC0 |

### Attribution

The following must be credited wherever the app is published:

- "Forest Ambient LOOP" by Imjeax (https://freesound.org/people/Imjeax/sounds/427400/) licensed under CC-BY
- "220618_1982_FR_CalmSuburbanStreet.wav" by kevp888 (https://freesound.org/people/kevp888/sounds/639133/) licensed under CC-BY
- "Atlantic Ocean Waves" by tim.kahn (https://freesound.org/people/tim.kahn/sounds/197714/) licensed under CC-BY

## Position on ownership

Rights to use are granted contractually by both providers. Copyright ownership of AI-generated output is unresolved in several jurisdictions, and the US Copyright Office holds that output without human creative input is not protectable. This document exists to record the human creative input, which is substantial and is concentrated in the system rather than in any individual file.

The defensible asset is the architecture — the family movement structure, the sequencer, the bed-level model and the measured library. The audio alone does not reproduce it.

_Not legal advice. Worth a solicitor's review before launch._