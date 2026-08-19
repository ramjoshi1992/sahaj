"""
ZenTune | prompt_library.py  v2
=================================
Single source of truth for all generation prompts.

Changes from v1:
  - Each mood/tier now has 3 DISTINCT seed variants (a, b, c)
  - Each variant has different lead instrument, energy arc, and structural shape:
      Variant A: standard arc, peaks at ~1:30
      Variant B: double peak (peaks at ~1:00, dips, peaks again at ~2:00)
      Variant C: early peak, sustained high energy from ~0:45 onward
  - More granular timestamp sections force genuine dynamic variation
  - ElevenLabs configs kept per mood (unchanged from v1)

Structure:
    LYRIA_PROMPTS[mood][tier]["a"|"b"|"c"]  → Lyria prompt string
    ELEVENLABS_CONFIG[mood]                  → { style_text, style_tags, negative_styles }
"""

LYRIA_PROMPTS = {

    # ═══════════════════════════════════════════════════════════
    # HAPPY — C major
    # ═══════════════════════════════════════════════════════════
    "happy": {
        "energetic": {
            "a": """Style: Upbeat Acoustic Pop, Summer Feel-good
Mood: Radiantly joyful, carefree, bright morning energy
Instrumentation: Fingerpicked acoustic guitar lead, bright upright piano supporting
Tempo & Key: 126 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Solo guitar, clean bright tone, single melodic phrase
[0:15-0:35] [Build] Piano enters with staccato chords, energy rising steadily
[0:35-1:00] [Rise] Guitar melody becomes more active, piano fills expand
[1:00-1:30] [Pre-peak] Full arrangement, rhythmic momentum building to apex
[1:30-2:00] [Peak] Maximum energy, guitar and piano in full interplay, soaring
[2:00-2:30] [Sustain] Energy holds, melodic variation, joyful and confident
[2:30-2:50] [Wind down] Gradual softening, guitar fingerpicking returns
[2:50-3:00] [Outro] Single guitar phrase, warm resolution""",

            "b": """Style: Upbeat Pop, Bright Summer Piano
Mood: Joyful, ebullient, celebrating the day
Instrumentation: Bright piano lead, acoustic guitar rhythmic support, light percussion
Tempo & Key: 126 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Solo piano, bright single-note melody, inviting
[0:15-0:40] [Build] Guitar strumming joins, energy lifts quickly
[0:40-1:00] [First peak] Both instruments full, first energy apex, joyful burst
[1:00-1:20] [Dip] Texture briefly thins, piano alone with softer voicing
[1:20-1:45] [Return] Guitar re-enters with fresh energy, building again
[1:45-2:20] [Second peak] Bigger than first, full arrangement, maximum joy
[2:20-2:45] [Resolution] Gradual easing, piano melody continues softly
[2:45-3:00] [Outro] Piano and guitar quiet close, warm and satisfied""",

            "c": """Style: Upbeat Folk-Pop, Rhythmic Summer Energy
Mood: Energetic joy, dancing, irresistible forward motion
Instrumentation: Acoustic guitar with strong rhythmic attack, piano chord stabs, hand percussion
Tempo & Key: 126 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar rhythmic pattern immediately, driving from bar one
[0:15-0:40] [Rise] Piano chord stabs join, percussion enters, energy spikes fast
[0:40-1:45] [Peak sustained] Full arrangement at maximum energy, holds long
[1:45-2:00] [Shift] Brief melodic change, new rhythmic idea introduced
[2:00-2:30] [Drive] Back to full energy with variation, rhythmic and bright
[2:30-2:50] [Ease] Percussion drops, guitar and piano soften gradually
[2:50-3:00] [Outro] Rhythmic guitar alone, final strum fades""",
        },

        "balanced": {
            "a": """Style: Warm Acoustic Pop, Afternoon Sunshine
Mood: Comfortable joy, warm happiness, steady positivity
Instrumentation: Acoustic guitar lead melody, piano harmony, subtle warmth
Tempo & Key: 120 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Warm guitar strumming, settled and inviting
[0:15-0:40] [Build] Piano adds harmonic warmth, natural energy rise
[0:40-1:00] [Expansion] Full texture, unhurried but joyful
[1:00-1:30] [Development] Guitar melody leads, piano supports, melodic peak
[1:30-2:00] [Peak] Both instruments full, warm and bright, comfortable apex
[2:00-2:30] [Continuation] Energy stays present, melodic variation continues
[2:30-2:50] [Easing] Gradual warm soften, guitar fingerpicking
[2:50-3:00] [Outro] Single warm guitar phrase, natural close""",

            "b": """Style: Acoustic Pop, Piano-led Warm Joy
Mood: Flowing happiness, natural and organic, effortlessly positive
Instrumentation: Piano lead with flowing melodic lines, guitar chord support
Tempo & Key: 120 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Piano alone, flowing melodic idea, warm tone
[0:15-0:40] [Build] Guitar strumming joins naturally
[0:40-1:05] [First bloom] Both instruments in harmony, first energy peak
[1:05-1:25] [Breath] Piano continues solo, guitar rests briefly
[1:25-1:55] [Full return] Guitar back with fresh energy, piano more expressive
[1:55-2:30] [Second bloom] Richer than first, piano melody soars, full warmth
[2:30-2:50] [Settling] Natural deceleration, piano simplifies
[2:50-3:00] [Outro] Final piano phrase, gentle and complete""",

            "c": """Style: Feel-good Acoustic, Rhythmic Warmth
Mood: Grounded joy, steady warmth, easy contentment
Instrumentation: Guitar and piano equal partners, rhythmic interplay throughout
Tempo & Key: 120 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar sets rhythm, piano immediately responds
[0:15-0:35] [Quick rise] Rhythmic energy builds fast, both instruments active
[0:35-1:50] [Core] Sustained warm energy, guitar and piano trading melodic ideas
[1:50-2:05] [Variation] New melodic idea shared between instruments
[2:05-2:30] [Drive] Return to main theme with fuller arrangement
[2:30-2:50] [Wind down] Rhythmic elements soften, warmth remains
[2:50-3:00] [Outro] Quiet guitar and piano together, warm close""",
        },

        "mellow": {
            "a": """Style: Cozy Acoustic, Intimate Evening Joy
Mood: Soft happiness, tender warmth, quiet contentment
Instrumentation: Solo fingerpicked acoustic guitar, very soft piano enters late
Tempo & Key: 108 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Solo guitar fingerpicking, intimate and close-mic'd
[0:20-0:50] [Solo development] Guitar melody unfolds, unhurried and warm
[0:50-1:20] [Piano joins] Piano enters very softly underneath guitar
[1:20-1:50] [Gentle peak] Both instruments at their softest fullness, warm
[1:50-2:20] [Continuation] Quiet melodic conversation, tender
[2:20-2:45] [Return to solo] Piano fades, guitar alone again
[2:45-3:00] [Outro] Single guitar phrase, fades to warmth""",

            "b": """Style: Nocturne Acoustic, Soft Evening Piano
Mood: Quiet joy, evening peace, gentle happiness
Instrumentation: Piano nocturne-style lead, acoustic guitar very soft support
Tempo & Key: 108 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Piano alone, gentle flowing melody, soft pedal
[0:20-0:50] [Development] Piano explores melodic idea, spacious
[0:50-1:15] [Guitar enters] Soft guitar adds warmth underneath
[1:15-1:45] [First gentle peak] Both soft and warm, intimate fullness
[1:45-2:00] [Quiet dip] Piano simplifies, guitar barely there
[2:00-2:30] [Return] Piano melody returns, slightly more expressive
[2:30-2:50] [Fading] Piano melody slows and softens
[2:50-3:00] [Outro] Final piano notes, sparse and warm""",

            "c": """Style: Intimate Duo, Late Evening Warmth
Mood: Sleepy happiness, cozy and close, the day winding down joyfully
Instrumentation: Guitar and piano close and equal, minimal and warm
Tempo & Key: 108 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Guitar and piano together from the start, quiet
[0:20-0:55] [Interplay] Instruments respond to each other softly
[0:55-1:30] [Warmth] Slightly fuller, both playing melodic ideas
[1:30-1:55] [Peak] Softest possible fullness, warm and close
[1:55-2:20] [Simplify] Texture thins, one instrument at a time
[2:20-2:45] [Quieter] Both very soft, fading warmth
[2:45-3:00] [Outro] Single instrument fades to silence""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # KICKSTART — G major
    # ═══════════════════════════════════════════════════════════
    "kickstart": {
        "energetic": {
            "a": """Style: Morning Drive Pop, Guitar-led Energy
Mood: High-energy optimism, sunrise confidence, strong momentum
Instrumentation: Driving acoustic guitar with strong pick attack, piano supporting
Tempo & Key: 128 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar with immediate rhythmic attack, strong from bar one
[0:15-0:35] [Build] Piano chord fills enter, momentum intensifying
[0:35-1:00] [Rise] Both instruments pushing, clear forward drive
[1:00-1:30] [Pre-peak] Maximum rhythmic density, energy building to apex
[1:30-2:00] [Peak] Guitar and piano at full drive, triumphant morning energy
[2:00-2:30] [Sustain] Energy holds high, melodic variation over driving rhythm
[2:30-2:50] [Ease] Gradual softening of rhythm, guitar continues melody
[2:50-3:00] [Outro] Guitar resolves, strong and confident close""",

            "b": """Style: Motivational Pop, Piano-driven Morning
Mood: Optimistic clarity, purposeful, bright mental energy
Instrumentation: Bright piano lead, acoustic guitar rhythmic support, light percussion
Tempo & Key: 128 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Piano bright melody alone, clear and purposeful
[0:15-0:35] [Build] Guitar rhythm joins, energy climbs quickly
[0:35-1:05] [First peak] Full arrangement, first energy apex, bright and driven
[1:05-1:25] [Momentary dip] Piano continues solo, guitar briefly drops
[1:25-1:50] [Rebuild] Guitar returns with greater force, energy rises again
[1:50-2:20] [Second peak] Bigger and more triumphant, full arrangement soaring
[2:20-2:45] [Wind down] Gradual decrease, piano melody continues
[2:45-3:00] [Outro] Piano resolves, ready for the day""",

            "c": """Style: Energetic Folk-Pop, Percussion-forward Drive
Mood: Unstoppable momentum, physical energy, action-ready
Instrumentation: Acoustic percussion prominent, guitar rhythm, piano accents
Tempo & Key: 128 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:10] [Intro] Percussion pattern starts immediately, driving
[0:10-0:35] [Guitar joins] Guitar rhythm locks with percussion, urgent
[0:35-0:55] [Piano] Piano accents add brightness, energy spikes
[0:55-2:00] [Peak sustained] Full driving energy held for extended period
[2:00-2:20] [Variation] Percussion pattern shifts, new rhythmic idea
[2:20-2:40] [Drive] Full return with combined energy
[2:40-3:00] [Resolution] Percussion fades last, strong rhythmic close""",
        },

        "balanced": {
            "a": """Style: Morning Acoustic Pop, Guitar-melody Drive
Mood: Clear purposeful optimism, grounded forward motion
Instrumentation: Acoustic guitar melody lead, piano chord support, steady rhythm
Tempo & Key: 122 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar melody, purposeful and clear
[0:15-0:40] [Build] Piano joins with steady chords, momentum grows
[0:40-1:10] [Development] Guitar melody develops, piano more active
[1:10-1:45] [Peak] Full balanced arrangement, confident and forward
[1:45-2:10] [Continuation] Energy sustained, melodic variation
[2:10-2:35] [Softening] Gradual reduction, guitar melody continues
[2:35-3:00] [Outro] Guitar resolves naturally, ready feeling""",

            "b": """Style: Piano-momentum Morning, Motivational Flow
Mood: Flowing motivation, progressive energy, building confidence
Instrumentation: Piano melodic lead with flowing lines, guitar rhythmic support
Tempo & Key: 122 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Piano flowing melody, immediate but unhurried
[0:15-0:40] [Build] Guitar rhythm joins, steady momentum
[0:40-1:05] [First bloom] Both instruments full, first energy bloom
[1:05-1:25] [Breath] Piano simplifies, guitar holds rhythm
[1:25-1:55] [Return] Piano more expressive, guitar energises
[1:55-2:25] [Full bloom] Greatest energy, piano soaring over guitar
[2:25-2:45] [Ease] Natural deceleration, piano simplifies again
[2:45-3:00] [Outro] Piano resolves, confident and complete""",

            "c": """Style: Rhythmic Morning Folk, Duo Drive
Mood: Steady energetic purpose, equally balanced drive
Instrumentation: Guitar and piano equal partners, rhythmic interplay, light bass
Tempo & Key: 122 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar rhythm and piano chords simultaneously
[0:15-0:35] [Immediate energy] Both instruments in rhythmic drive from early
[0:35-1:50] [Core] Sustained balanced energy, trading melodic ideas
[1:50-2:05] [Variation] New complementary melodic idea between instruments
[2:05-2:30] [Full return] Main theme returns with added confidence
[2:30-2:50] [Wind down] Rhythmic elements ease, warmth remains
[2:50-3:00] [Outro] Final phrase together, purposeful close""",
        },

        "mellow": {
            "a": """Style: Gentle Morning Folk, Soft Awakening Guitar
Mood: Hopeful ease, gentle morning optimism, soft awakening
Instrumentation: Fingerpicked acoustic guitar lead, piano enters softly mid-way
Tempo & Key: 114 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Solo guitar, gentle fingerpicking, morning light quality
[0:20-0:50] [Solo development] Guitar melody unfolds, quiet forward pull
[0:50-1:20] [Piano joins] Piano enters very gently underneath
[1:20-1:50] [Together] Soft fullness, both instruments quiet but present
[1:50-2:20] [Continuation] Gentle melodic interplay, hopeful and easy
[2:20-2:45] [Return to solo] Piano fades, guitar fingerpicking alone
[2:45-3:00] [Outro] Simple guitar phrase, ready for the day""",

            "b": """Style: Soft Piano Morning, Warm Motivation
Mood: Warm gentle motivation, soft purposefulness, easy confidence
Instrumentation: Piano warm lead, guitar soft support
Tempo & Key: 114 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Piano soft warm melody, unhurried
[0:20-0:50] [Develop] Piano explores melody with gentle warmth
[0:50-1:15] [Guitar] Guitar enters softly, adds texture
[1:15-1:45] [Together] Both instruments in soft harmony
[1:45-2:00] [Quiet moment] Piano simplifies, introspective
[2:00-2:30] [Warm return] Both instruments soft and warm together
[2:30-2:50] [Fading] Instruments soften and slow
[2:50-3:00] [Outro] Final warm piano notes fade""",

            "c": """Style: Acoustic Duo Morning, Warm Ease
Mood: Quiet readiness, gentle warmth, soft forward energy
Instrumentation: Guitar and piano together from start, both gentle and equal
Tempo & Key: 114 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Guitar and piano together, quiet and warm
[0:20-0:55] [Interplay] Instruments respond to each other gently
[0:55-1:30] [Soft bloom] Slightly fuller, warmest point
[1:30-2:00] [Sustained] Warmth holds, easy and confident
[2:00-2:30] [Simplify] Texture reduces, more space between notes
[2:30-2:50] [Quieter] Both very soft
[2:50-3:00] [Outro] Single instrument carries to close""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # UNMOTIVATED — D major
    # ═══════════════════════════════════════════════════════════
    "unmotivated": {
        "energetic": {
            "a": """Style: Motivational Pop, Guitar-driven Encouragement
Mood: Warm urgency, encouraging push, getting-things-done
Instrumentation: Strummed acoustic guitar with forward drive, piano supporting
Tempo & Key: 118 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar with immediate momentum, warm and driving
[0:15-0:40] [Build] Piano enters with encouragement, energy lifts
[0:40-1:05] [Rise] Both instruments pushing warmly forward
[1:05-1:35] [Peak] Full warm arrangement, maximum motivational energy
[1:35-2:05] [Sustain] Energy holds, melodic variation over warm rhythm
[2:05-2:30] [Ease] Gradual soften, guitar melody continues warm
[2:30-2:50] [Wind down] Rhythm reduces, warmth remains
[2:50-3:00] [Outro] Guitar warmly resolves, energy carried forward""",

            "b": """Style: Warm Piano Motivation, Encouraging Flow
Mood: Flowing encouragement, steady warm confidence, forward pull
Instrumentation: Piano warm lead with flowing phrases, guitar rhythm support
Tempo & Key: 118 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Piano warm flowing melody, immediately encouraging
[0:15-0:40] [Build] Guitar strumming joins warmly
[0:40-1:05] [First lift] Both instruments full, warm first energy lift
[1:05-1:25] [Breath] Piano continues softer, guitar holds gentle rhythm
[1:25-1:55] [Return] Guitar re-energises, piano more expressive
[1:55-2:20] [Full lift] Greatest warmth and energy, piano melody soars
[2:20-2:45] [Ease] Natural warm deceleration
[2:45-3:00] [Outro] Piano warm close, motivation preserved""",

            "c": """Style: Rhythmic Encouragement, Driven Warmth
Mood: Driving warm energy, rhythm-led motivation, unstoppable warmth
Instrumentation: Acoustic guitar strong rhythm, piano accents, subtle percussion
Tempo & Key: 118 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar rhythm warm and immediate
[0:15-0:35] [Percussion] Light percussion joins, warm drive builds fast
[0:35-0:55] [Piano] Piano accents add brightness and warmth
[0:55-2:00] [Peak sustained] Full warm driving energy held, motivating
[2:00-2:20] [Variation] Rhythmic shift, new warm pattern
[2:20-2:40] [Drive] Full warm return
[2:40-3:00] [Close] Rhythm fades warm, guitar alone closes""",
        },

        "balanced": {
            "a": """Style: Motivational Acoustic, Guitar Momentum
Mood: Steady encouraging energy, sustainable warm drive
Instrumentation: Acoustic guitar rhythm and melody, warm piano support
Tempo & Key: 112 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Warm guitar, immediate but unhurried
[0:15-0:40] [Build] Piano joins with warm chords, steady build
[0:40-1:10] [Development] Guitar melody develops, piano more active
[1:10-1:40] [Peak] Full warm arrangement, balanced drive
[1:40-2:10] [Continuation] Energy sustained, warm melodic variation
[2:10-2:35] [Soften] Gradual reduction, guitar warmth remains
[2:35-3:00] [Outro] Guitar warm close, momentum preserved""",

            "b": """Style: Piano Warmth, Flowing Motivation
Mood: Organic warm encouragement, natural forward motion
Instrumentation: Piano flowing warm lead, guitar gentle rhythm
Tempo & Key: 112 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Piano warm flowing, encouraging from first note
[0:15-0:40] [Build] Guitar joins gently, warmth expands
[0:40-1:05] [First warmth] Both full, first warm peak
[1:05-1:25] [Breath] Piano simplifies, quiet moment
[1:25-1:55] [Return] Guitar re-energises, piano opens up
[1:55-2:25] [Full warmth] Greatest expressive warmth, piano leads
[2:25-2:45] [Easing] Natural warm deceleration
[2:45-3:00] [Outro] Piano warm resolution""",

            "c": """Style: Balanced Duo, Warm Rhythmic Drive
Mood: Equal warm partnership, rhythmic encouragement
Instrumentation: Guitar and piano equal, warm rhythmic interplay
Tempo & Key: 112 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:15] [Intro] Guitar and piano together warmly
[0:15-0:35] [Early energy] Both in warm rhythmic drive quickly
[0:35-1:50] [Core] Sustained warm balanced energy, melodic trading
[1:50-2:05] [New idea] Fresh melodic phrase shared warmly
[2:05-2:30] [Return] Main theme with added warm confidence
[2:30-2:50] [Wind down] Rhythm eases, warmth persists
[2:50-3:00] [Outro] Together warmly to close""",
        },

        "mellow": {
            "a": """Style: Gentle Acoustic Motivation, Soft Guitar Encouragement
Mood: Quiet determination, soft warm push, gentle forward pull
Instrumentation: Fingerpicked acoustic guitar, very soft piano
Tempo & Key: 104 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Solo guitar gentle fingerpicking, quiet but purposeful
[0:20-0:50] [Develop] Guitar melody, soft forward pull
[0:50-1:20] [Piano] Piano enters very softly, warm encouragement
[1:20-1:50] [Together] Soft fullness, gentle motivating warmth
[1:50-2:20] [Continue] Quiet interplay, tender encouragement
[2:20-2:45] [Return] Guitar fingerpicking alone again
[2:45-3:00] [Outro] Simple guitar, gentle close""",

            "b": """Style: Soft Piano Encouragement, Warm Quiet Push
Mood: Tender motivation, soft warmth, quiet confidence
Instrumentation: Piano soft warm lead, guitar barely there
Tempo & Key: 104 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Piano soft warm, encouraging
[0:20-0:50] [Develop] Piano explores warmly
[0:50-1:15] [Guitar] Guitar very soft underneath
[1:15-1:45] [Together] Both quiet and warm
[1:45-2:00] [Simplify] Piano alone, introspective warmth
[2:00-2:30] [Return] Both soft and encouraging
[2:30-2:50] [Fade] Instruments soften further
[2:50-3:00] [Outro] Final warm piano notes""",

            "c": """Style: Quiet Duo Warmth, Gentle Joint Momentum
Mood: Soft shared warmth, easy gentle drive
Instrumentation: Guitar and piano together, both very gentle
Tempo & Key: 104 BPM, D major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Both together quietly from start
[0:20-0:55] [Interplay] Gentle responses between instruments
[0:55-1:30] [Warmth] Softest fullness, encouraging warmth
[1:30-2:00] [Sustained] Warm quiet energy holds
[2:00-2:30] [Simplify] Texture reduces gradually
[2:30-2:50] [Quieter] Both very gentle
[2:50-3:00] [Outro] One instrument to close softly""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # FOCUS — A minor
    # ═══════════════════════════════════════════════════════════
    "focus": {
        "energetic": {
            "a": """Style: Alert Ambient, Clean Piano Focus
Mood: Sharp concentration, active mental clarity, bright alertness
Instrumentation: Clean electric piano, sparse high notes, subtle bass pulse
Tempo & Key: 84 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Single piano note, crisp and clear, long decay
[0:20-0:50] [Build] Bass pulse enters subtly, piano notes more frequent
[0:50-1:30] [Alert state] Piano active, bass present, alert minimal texture
[1:30-1:50] [Variation] Harmonic shift, new piano pattern, maintains clarity
[1:50-2:20] [Continuation] Alert state resumes, slightly fuller
[2:20-2:45] [Ease] Piano spacing increases, fewer notes
[2:45-3:00] [Outro] Single piano line, clear fade""",

            "b": """Style: Bright Focus Ambient, Guitar Harmonics
Mood: Alert focus, harmonically rich clarity, awake concentration
Instrumentation: Guitar harmonics and overtones, minimal piano accents
Tempo & Key: 84 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Guitar harmonic tone, shimmering and clear
[0:20-0:45] [Develop] Guitar harmonics expand, bright and present
[0:45-1:15] [First texture] Piano accent notes join sparingly
[1:15-1:40] [Dip] Guitar harmonics thin, wide spacing
[1:40-2:10] [Return] Harmonics fuller again, clearer than before
[2:10-2:40] [Bright] Brightest point, harmonics and piano together
[2:40-3:00] [Fade] Guitar harmonics alone, gradually sparse""",

            "c": """Style: Minimal Electronic-adjacent Focus, Bass-led
Mood: Deep alert focus, low distraction, present and locked in
Instrumentation: Subtle bass pulse, piano sparse single notes, near-silence
Tempo & Key: 84 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Bass pulse alone, very subtle, grounding
[0:20-0:50] [Piano enters] Single piano notes, widely spaced
[0:50-1:30] [Minimal texture] Bass and piano in sparse dialogue
[1:30-1:50] [Silence moment] Only bass pulse, maximum space
[1:50-2:20] [Return] Piano re-enters, slightly more active
[2:20-2:45] [Simplify] Piano spaces out again
[2:45-3:00] [Outro] Bass pulse alone fades""",
        },

        "balanced": {
            "a": """Style: Neutral Focus Ambient, Piano-centred
Mood: Deep steady concentration, neutral mental state, clear mind
Instrumentation: Soft piano, subtle warm pad underneath
Tempo & Key: 78 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Piano soft and grounding, neutral tone
[0:20-0:50] [Pad enters] Warm pad underneath, depth added
[0:50-1:30] [Main state] Balanced minimal arrangement, pure concentration
[1:30-1:50] [Harmonic shift] Subtle chord change, maintains focus
[1:50-2:20] [Continue] Focus state maintained, slight variation
[2:20-2:45] [Thin] Pad fades, piano alone
[2:45-3:00] [Outro] Piano sparse notes fade""",

            "b": """Style: Flowing Focus, Guitar Harmonic Texture
Mood: Sustained concentration flow, organic focus
Instrumentation: Guitar harmonics layered, piano occasional notes
Tempo & Key: 78 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Guitar harmonics, flowing and non-intrusive
[0:20-0:50] [Layer] Second guitar harmonic layer, depth
[0:50-1:20] [Piano] Piano notes sparsely placed, organic
[1:20-1:50] [Quiet moment] Guitar harmonics thin, wide space
[1:50-2:20] [Return] Both elements return more fully
[2:20-2:45] [Fade] Harmonics thin gradually
[2:45-3:00] [Outro] Single harmonic tone fades""",

            "c": """Style: Dark Neutral Ambient, Pad-led Focus
Mood: Absorbed concentration, low stimulation, quiet immersion
Instrumentation: Warm neutral pad, piano single notes widely spaced
Tempo & Key: 78 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Pad alone, neutral and enveloping
[0:20-0:50] [Deepen] Pad thickens subtly, immersive
[0:50-1:30] [Piano] Single piano notes, very sparse
[1:30-1:50] [Pad alone] Piano stops, just pad
[1:50-2:20] [Return] Piano notes re-enter sparingly
[2:20-2:45] [Thin] Pad reduces, space expands
[2:45-3:00] [Outro] Pad alone fades to silence""",
        },

        "mellow": {
            "a": """Style: Dark Ambient Focus, Evening Concentration
Mood: Deep inward focus, low stimulation, quiet concentration
Instrumentation: Dark piano, long reverb, maximum space between notes
Tempo & Key: 70 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Single dark piano note, vast reverb tail
[0:25-0:55] [Second note] Another note, very different pitch, long decay
[0:55-1:30] [Sparse melody] 3-4 notes forming a minimal phrase
[1:30-1:55] [Silence] Long pause, reverb only
[1:55-2:20] [Return] Sparse notes again, slightly different
[2:20-2:45] [Fewer] Even more space, one note every 15s
[2:45-3:00] [Final note] Single note fades to complete silence""",

            "b": """Style: Guitar Drone Focus, Meditative
Mood: Absorbed stillness, drone-led deep focus
Instrumentation: Low guitar drone, guitar harmonics, no percussion
Tempo & Key: 70 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Low guitar drone establishes
[0:25-0:55] [Harmonics] Guitar harmonics float above drone
[0:55-1:30] [Deepen] Drone and harmonics in dialogue, deep
[1:30-1:55] [Sparse] Harmonics stop, drone alone
[1:55-2:20] [Return] Harmonics re-enter very slowly
[2:20-2:45] [Fade] Harmonics drop off, drone alone
[2:45-3:00] [Outro] Drone fades slowly to silence""",

            "c": """Style: Near-Silence Ambient, Maximum Space
Mood: Absolute stillness, deepest focus, barely-there music
Instrumentation: Piano and pad together but extremely sparse
Tempo & Key: 70 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Pad barely audible, enters from silence
[0:30-1:00] [Piano] Single piano note, very soft, long decay
[1:00-1:30] [Dialogue] Pad shifts slightly, piano responds
[1:30-2:00] [Maximum space] Near silence, only faint pad
[2:00-2:30] [One phrase] 2-3 piano notes, final melodic gesture
[2:30-3:00] [Dissolve] Pad fades completely to silence""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # DEEPWORK — D minor
    # ═══════════════════════════════════════════════════════════
    "deepwork": {
        "energetic": {
            "a": """Style: Deep Focus Ambient, Piano-led Flow
Mood: Total absorption, active flow state, present immersion
Instrumentation: Piano warm flowing phrases, deep bass drone underneath
Tempo & Key: 68 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Piano single notes, establishing deep space
[0:25-0:55] [Drone enters] Bass drone, piano becomes more active
[0:55-1:35] [Flow] Piano and drone in immersive dialogue
[1:35-1:55] [Deepening] Piano slows, drone more prominent
[1:55-2:20] [Return] Piano re-engages, richer harmonic movement
[2:20-2:45] [Thin] Piano phrases space out
[2:45-3:00] [Outro] Drone alone fades""",

            "b": """Style: Drone-led Deep Work, Evolving Texture
Mood: Hypnotic immersion, time-dissolving focus
Instrumentation: Evolving drone layers, piano occasional accent
Tempo & Key: 68 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Single drone tone, simple and immersive
[0:25-1:00] [Layer] Second drone pitch adds, harmonic richness
[1:00-1:30] [Piano] Piano single notes over drone
[1:30-1:55] [Drop] Piano stops, drone layers alone
[1:55-2:20] [Evolve] Drone shifts harmonically, piano returns
[2:20-2:45] [Simplify] Drone reduces to single pitch
[2:45-3:00] [Fade] Single drone tone fades to silence""",

            "c": """Style: Bass Pulse Deepwork, Rhythmic Flow
Mood: Rhythmically anchored deep focus, locked-in state
Instrumentation: Subtle bass pulse rhythm, dark piano, warm pad
Tempo & Key: 68 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Bass pulse alone, regular and grounding
[0:25-0:55] [Pad] Warm pad enters, depth expands
[0:55-1:30] [Piano] Dark piano notes join sparsely
[1:30-1:55] [Pulse alone] Piano and pad drop, bass pulse only
[1:55-2:20] [Return] All elements re-enter gradually
[2:20-2:45] [Reduce] Elements drop off one by one
[2:45-3:00] [Outro] Bass pulse alone fades""",
        },

        "balanced": {
            "a": """Style: Warm Immersive Ambient, Piano-drone Blend
Mood: Complete immersion, zero distraction, timeless quality
Instrumentation: Piano and warm drone blended equally
Tempo & Key: 62 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Warm pad, slow and enveloping
[0:25-0:55] [Piano] Piano notes blend into pad texture
[0:55-1:35] [Merged] Piano and drone indistinguishable, deeply immersive
[1:35-1:55] [Shift] Harmonic movement, new tonal centre briefly
[1:55-2:20] [Return] Original harmony, deepened immersion
[2:20-2:45] [Thin] Texture reduces slowly
[2:45-3:00] [Outro] Drone alone, fades""",

            "b": """Style: Evolving Pad Deep Work, Harmonic Drift
Mood: Drifting deep concentration, harmonic evolution
Instrumentation: Evolving warm pad with slow harmonic movement
Tempo & Key: 62 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Pad from silence, very slow
[0:30-1:00] [Warm] Pad reaches warmth, enveloping
[1:00-1:30] [Drift] Harmonic drift begins, subtle movement
[1:30-2:00] [Deep] Darkest and most immersive
[2:00-2:30] [Return drift] Slowly returns to opening harmony
[2:30-3:00] [Fade] Pad fades very slowly""",

            "c": """Style: Bass-grounded Deep Work, Low and Immersive
Mood: Gravity-like immersion, deeply grounded focus
Instrumentation: Deep bass drone, dark piano, very warm pad
Tempo & Key: 62 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Deep bass drone, immediately grounding
[0:30-1:00] [Pad] Warm pad adds above drone
[1:00-1:30] [Piano] Dark piano very sparse
[1:30-2:00] [Maximum depth] All elements, darkest and deepest
[2:00-2:30] [Reduce] Piano stops, pad and drone remain
[2:30-3:00] [Fade] Pad fades, drone last to go""",
        },

        "mellow": {
            "a": """Style: Near-hypnotic Ambient, Night Deepwork
Mood: Near-hypnotic absorption, minimum stimulation, profound depth
Instrumentation: Dark piano, barely audible, deep bass barely there
Tempo & Key: 55 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Bass drone barely perceptible, from silence
[0:30-1:00] [Piano] Single dark piano note, 30 second gap
[1:00-1:30] [Second note] Another piano note, different pitch
[1:30-2:00] [Silence] Drone only, vast space
[2:00-2:30] [Final phrase] 2 piano notes, last musical gesture
[2:30-3:00] [Dissolve] Everything fades to complete silence""",

            "b": """Style: Drone Only Deep Work, Maximum Stillness
Mood: Absolute stillness, drone-consciousness, dissolved into sound
Instrumentation: Two drone pitches only, slowly evolving
Tempo & Key: 55 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:40] [Drone one] Single drone pitch from silence
[0:40-1:20] [Second drone] Second pitch very slowly fades in
[1:20-1:50] [Both] Both drones together, harmonic resonance
[1:50-2:20] [One fades] First drone fades, second remains
[2:20-3:00] [Singular] Single drone pitch fades to silence""",

            "c": """Style: Sub-bass Night Ambient, Deepest Immersion
Mood: Physical immersion, felt rather than heard, deepest state
Instrumentation: Sub-bass drone, piano one note every 20 seconds
Tempo & Key: 55 BPM, D minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:40] [Intro] Sub-bass drone, felt as much as heard
[0:40-1:10] [Piano note] Single very soft piano note
[1:10-1:50] [Sub-bass alone] Piano stops, only sub-bass
[1:50-2:20] [Second note] Another piano note, very distant
[2:20-3:00] [Dissolve] Sub-bass fades over 40 seconds to silence""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # ANXIOUS — F major
    # ═══════════════════════════════════════════════════════════
    "anxious": {
        "energetic": {
            "a": """Style: Grounding Acoustic, Guitar-led Calm
Mood: Gentle grounding, nervous system regulation, soft reassurance
Instrumentation: Nylon guitar soft fingerpicking, piano very warm underneath
Tempo & Key: 74 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Solo nylon guitar, grounding immediately
[0:20-0:50] [Piano] Piano enters very warmly underneath
[0:50-1:25] [Gentle fullness] Both soft and warm, holding space
[1:25-1:45] [Variation] Melodic shift, gentle resolution movement
[1:45-2:10] [Continue] Warmth and groundedness maintained
[2:10-2:40] [Thin] Piano fades, guitar continues softly
[2:40-3:00] [Outro] Guitar alone, final gentle phrase""",

            "b": """Style: Piano Reassurance, Calming Flow
Mood: Warm reassurance, piano-led calm, nervous system settling
Instrumentation: Piano warm gentle melody, guitar harmonic support
Tempo & Key: 74 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Piano warm and gentle, immediately reassuring
[0:20-0:50] [Guitar] Guitar harmonic warmth underneath
[0:50-1:20] [Together] Both soft, first gentle peak of warmth
[1:20-1:40] [Quiet] Piano simplifies, very gentle
[1:40-2:10] [Warm return] Both elements return, warmer
[2:10-2:40] [Fade] Piano slows and softens
[2:40-3:00] [Outro] Final warm piano resolution""",

            "c": """Style: Pad-guitar Grounding, Enveloping Calm
Mood: Enveloping warmth, total softness, safe and held
Instrumentation: Warm pad enveloping, guitar very soft above it
Tempo & Key: 74 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Pad arrives from silence, warm and safe
[0:25-0:55] [Guitar] Nylon guitar very softly above pad
[0:55-1:30] [Enveloped] Pad and guitar together, held feeling
[1:30-1:55] [Pad alone] Guitar stops, pad alone, pure warmth
[1:55-2:20] [Guitar returns] Guitar re-enters very gently
[2:20-2:45] [Thin] Guitar fades, pad alone
[2:45-3:00] [Outro] Pad fades slowly to warmth""",
        },

        "balanced": {
            "a": """Style: Therapeutic Acoustic, Guitar Ground
Mood: Deep calm, slow breathing, steady grounding, no tension
Instrumentation: Nylon guitar slow, piano warm long notes
Tempo & Key: 68 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Guitar slow and grounding, maximum space
[0:25-1:00] [Piano] Piano warm long notes, no hurry
[1:00-1:35] [Together] Both soft and very grounded
[1:35-2:00] [Guitar alone] Piano fades, guitar continues slowly
[2:00-2:30] [Piano returns] Both together, final warmth
[2:30-3:00] [Fade] Both slow to near-silence""",

            "b": """Style: Piano Calm, Long Resonance
Mood: Piano-led deep calm, resonance as medicine
Instrumentation: Piano with long sustain pedal, wide chord voicings
Tempo & Key: 68 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Piano wide chord, long resonance, space
[0:25-0:55] [Second chord] Different chord, long decay
[0:55-1:30] [Slow phrases] 3-4 note phrases, maximum resonance
[1:30-2:00] [Very sparse] One chord every 20 seconds
[2:00-2:30] [Return] Short melodic gesture, warm
[2:30-3:00] [Final chord] One final chord, long fade""",

            "c": """Style: String Pad Calm, Enveloping Safety
Mood: Completely held, string warmth, no sharp edges
Instrumentation: Warm string pad, guitar very soft, no piano
Tempo & Key: 68 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] String pad from silence, enveloping
[0:30-1:00] [Deepen] Strings fuller, warm and safe
[1:00-1:30] [Guitar] Guitar harmonic barely above strings
[1:30-2:00] [Strings alone] Guitar fades, pure strings
[2:00-2:30] [Thin] Strings reduce, fewer voices
[2:30-3:00] [Fade] Strings fade to warmth""",
        },

        "mellow": {
            "a": """Style: Near-silence Calming, Vast Space
Mood: Profound calm, maximum space, breath-like rhythm
Instrumentation: Very soft piano, near-silence, vast reverb
Tempo & Key: 60 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Barely-there piano, enters from silence
[0:30-1:00] [Two notes] Two piano notes, vast space between
[1:00-1:30] [Phrase] Short 3-note phrase, long reverb
[1:30-2:00] [Silence] Pure silence, reverb tail only
[2:00-2:30] [Return] Two piano notes, slightly warmer
[2:30-3:00] [Dissolve] Piano fades to silence""",

            "b": """Style: Soft Pad Safety, Maximum Warmth
Mood: Completely held in warmth, nothing to fear, total safety
Instrumentation: Warm pad extremely soft, no other instrument
Tempo & Key: 60 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:40] [Intro] Pad from complete silence, barely perceptible
[0:40-1:20] [Warm] Pad reaches warmth, fully enveloping
[1:20-1:50] [Held] Warmth sustained, deepest safety
[1:50-2:20] [Shift] Pad moves to different harmonic centre
[2:20-3:00] [Fade] Pad very slowly returns to silence""",

            "c": """Style: Guitar Whisper, Intimate Ground
Mood: Whisper-quiet intimacy, guitar barely there, held
Instrumentation: Single nylon guitar, whisper-quiet, vast space
Tempo & Key: 60 BPM, F major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Single guitar note, barely audible
[0:30-1:00] [Phrase] 3-note phrase, very slow
[1:00-1:30] [Space] Long silence, reverb only
[1:30-2:00] [Return] Another phrase, slightly warmer
[2:00-2:30] [Simpler] Single notes only
[2:30-3:00] [Fade] Guitar fades to complete silence""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # STRESSED — E major
    # ═══════════════════════════════════════════════════════════
    "stressed": {
        "energetic": {
            "a": """Style: Singing Bowl Meditation, Bowl-led Release
Mood: Immediate release, tension dissolving, bowl resonance
Instrumentation: Singing bowl primary, piano very soft underneath
Tempo & Key: 62 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Singing bowl struck, long resonance, immediate release
[0:25-0:55] [Piano] Piano warmth underneath bowl resonance
[0:55-1:30] [Together] Bowl and piano in peaceful dialogue
[1:30-1:55] [Bowl alone] Piano stops, bowl resonance only
[1:55-2:20] [Return] Piano warmly returns, tension further dissolved
[2:20-2:45] [Thin] Piano fades, bowl alone
[2:45-3:00] [Final strike] Last bowl strike, long fade""",

            "b": """Style: Piano Meditation, Slow Chord Release
Mood: Piano-led decompression, chord resonance releasing stress
Instrumentation: Piano slow and spacious, long chord sustains
Tempo & Key: 62 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Piano single note, very long sustain
[0:25-0:55] [Second] Different note, resonant and peaceful
[0:55-1:30] [Chord] Full warm chord, tension releasing
[1:30-1:55] [Space] Silence, chord reverb only
[1:55-2:20] [Phrase] Short melodic phrase, peaceful resolution
[2:20-2:45] [Single notes] Return to sparse single notes
[2:45-3:00] [Final chord] Last chord, long fade to peace""",

            "c": """Style: Strings and Bowl, Enveloping Peace
Mood: Completely enveloped in peace, no resistance
Instrumentation: Warm strings, singing bowl, no piano
Tempo & Key: 62 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Strings arrive very slowly from silence
[0:30-1:00] [Bowl] Singing bowl joins, resonance over strings
[1:00-1:35] [Together] Strings and bowl in peaceful harmony
[1:35-2:00] [Strings alone] Bowl stops, strings continue warmly
[2:00-2:30] [Bowl returns] Final bowl strike over strings
[2:30-3:00] [Fade] Strings fade slowly to peace""",
        },

        "balanced": {
            "a": """Style: Deep Meditation, Bowl and Piano Peace
Mood: Complete decompression, mind emptying, profound peace
Instrumentation: Singing bowl, piano soft, deep pad
Tempo & Key: 56 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Bowl struck softly, long resonance
[0:30-1:00] [Piano] Piano single notes between bowl strikes
[1:00-1:30] [Pad] Deep warm pad enters underneath
[1:30-2:00] [All three] Bowl, piano, pad in meditative harmony
[2:00-2:30] [Simplify] Pad and bowl only, piano stops
[2:30-3:00] [Fade] All fade slowly to stillness""",

            "b": """Style: Slow Piano Meditation, Harmonic Resolution
Mood: Harmonic resolution of stress, piano as therapy
Instrumentation: Piano very slow with harmonic resolution focus
Tempo & Key: 56 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Tension chord, very soft, held
[0:30-1:00] [Movement] Slow harmonic movement toward resolution
[1:00-1:30] [Near resolution] Almost resolved, beautiful tension
[1:30-2:00] [Resolution] Final resolution chord, peace achieved
[2:00-2:30] [Aftermath] Resonance of resolved chord
[2:30-3:00] [Fade] Harmony fades slowly""",

            "c": """Style: Deep Pad Meditation, Immersive Peace
Mood: Dissolved into peace, no thoughts, pure rest
Instrumentation: Deep warm pad primary, piano only occasionally
Tempo & Key: 56 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:35] [Intro] Deep pad from silence, very slow
[0:35-1:05] [Warmth] Pad reaches fullness, enveloping
[1:05-1:35] [Piano] Piano one note, long decay, peaceful
[1:35-2:05] [Pad alone] Piano stops, pure pad warmth
[2:05-2:35] [Return] Piano one final phrase
[2:35-3:00] [Dissolve] Pad fades to complete stillness""",
        },

        "mellow": {
            "a": """Style: Profound Stillness, Bowl Alone
Mood: Nothing but peace, stillness as medicine
Instrumentation: Single singing bowl, vast silence around it
Tempo & Key: 50 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:40] [First strike] Bowl struck, listen to full decay (30+ seconds)
[0:40-1:20] [Second strike] Different bowl, different pitch, full decay
[1:20-1:50] [Silence] Pure silence between strikes
[1:50-2:20] [Third strike] Softer, even longer decay
[2:20-3:00] [Final resonance] Last strike, fade completely to silence""",

            "b": """Style: Near-silence Piano, One Note Medicine
Mood: Each note a breath, space as healing
Instrumentation: Piano single notes, one every 15-20 seconds
Tempo & Key: 50 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:35] [First note] Single piano note, very soft, vast reverb
[0:35-1:05] [Space] Pure silence
[1:05-1:35] [Second note] Different pitch, equally soft
[1:35-2:05] [Space] Pure silence again
[2:05-2:35] [Third note] Softest of all
[2:35-3:00] [Fade] Reverb tail only, to silence""",

            "c": """Style: Sub-frequency Peace, Felt Not Heard
Mood: Peace felt in body, sub-bass as medicine
Instrumentation: Sub-bass drone alone, barely perceptible
Tempo & Key: 50 BPM, E major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:60] [Emerge] Sub-bass drone rises from complete silence (one minute)
[1:00-1:45] [Present] Drone at its most present, felt physically
[1:45-2:20] [Shift] Subtle harmonic shift in drone
[2:20-3:00] [Return to silence] Very slow fade back to complete silence""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # SOCIALLY DRAINED — G major
    # ═══════════════════════════════════════════════════════════
    "socially-drained": {
        "energetic": {
            "a": """Style: Gentle Restorative, Piano Solitude
Mood: Welcomed solitude, quiet recharging, just for yourself
Instrumentation: Piano gentle solo, pad very underneath
Tempo & Key: 70 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Piano alone, solitude settling
[0:25-0:55] [Pad] Pad enters very softly underneath
[0:55-1:30] [Together] Quiet restoration, gentle fullness
[1:30-1:55] [Variation] Piano melodic shift, still inward
[1:55-2:20] [Continue] Quiet warmth sustained
[2:20-2:45] [Thin] Pad fades, piano alone
[2:45-3:00] [Outro] Piano alone, solitude complete""",

            "b": """Style: Guitar Harmonic Restoration, Introspective
Mood: Inward rest, guitar harmonics as companion, quiet
Instrumentation: Guitar harmonics layered, pad underneath
Tempo & Key: 70 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Guitar harmonic layer one, shimmering quietly
[0:25-0:55] [Second layer] Second harmonic, depth added
[0:55-1:30] [Pad] Pad enters gently underneath harmonics
[1:30-1:55] [Quiet peak] All elements at their softest fullness
[1:55-2:20] [Reduce] Pad fades, harmonics alone
[2:20-2:45] [Thin] One harmonic layer remains
[2:45-3:00] [Fade] Final harmonic fades""",

            "c": """Style: Minimal Piano, Maximum Quiet
Mood: Minimum input needed, maximum quiet, just resting
Instrumentation: Piano very minimal, single notes only, pad
Tempo & Key: 70 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Pad from silence, very gentle
[0:30-1:00] [Piano] Single piano notes, widely spaced
[1:00-1:30] [Quieter] Even more space, fewer notes
[1:30-2:00] [Pad alone] Piano stops, pad alone
[2:00-2:30] [Return] Piano one phrase, very soft
[2:30-3:00] [Dissolve] Both fade to rest""",
        },

        "balanced": {
            "a": """Style: Quiet Comfort Piano, Healing Solitude
Mood: Comfortable alone, quietly healing, soft and private
Instrumentation: Piano gentle warmth, guitar harmonics optional
Tempo & Key: 64 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Piano gentle and warm, exhale feeling
[0:25-0:55] [Develop] Piano explores quietly
[0:55-1:30] [Guitar] Guitar harmonics barely present
[1:30-1:55] [Piano alone] Guitar fades, piano solitude
[1:55-2:20] [Return] Both very softly together
[2:20-2:50] [Thin] Back to piano alone
[2:50-3:00] [Outro] Final soft piano""",

            "b": """Style: Harmonic Quiet, Guitar and Pad Restoration
Mood: Deep quiet, harmonics as comfort, non-demanding
Instrumentation: Guitar harmonics primary, warm pad, no piano
Tempo & Key: 64 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Guitar harmonics, very soft and non-intrusive
[0:30-1:00] [Pad] Warm pad underneath, comfort
[1:00-1:30] [Together] Harmonics and pad, still and quiet
[1:30-2:00] [Harmonics alone] Pad fades, harmonics alone shimmer
[2:00-2:30] [Pad returns] Brief return of pad warmth
[2:30-3:00] [Fade] All fades gently""",

            "c": """Style: Near-silence Restoration, Space as Healing
Mood: Space itself is healing, minimum stimulation
Instrumentation: Piano single notes, pad barely audible
Tempo & Key: 64 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:35] [Intro] Pad barely audible, from silence
[0:35-1:05] [Piano] One piano note, long decay
[1:05-1:35] [Space] Silence with pad only
[1:35-2:05] [Second note] Another piano note
[2:05-2:35] [Final phrase] 2-3 notes, resolving
[2:35-3:00] [Dissolve] Pad fades slowly to silence""",
        },

        "mellow": {
            "a": """Style: Deep Rest Ambient, Total Quiet
Mood: Complete withdrawal, deep solitude, profound restoration
Instrumentation: Very soft piano, dark warm pad, near-silence
Tempo & Key: 57 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:35] [Intro] Dark pad from silence
[0:35-1:05] [Piano] Single piano note, barely audible
[1:05-1:40] [Pad alone] Piano stops, pad alone
[1:40-2:10] [Second note] One more piano note
[2:10-3:00] [Dissolve] Everything fades slowly""",

            "b": """Style: Drone Rest, Enveloping Dark
Mood: Enveloped in darkness, safe and deeply resting
Instrumentation: Dark warm drone, no other instrument
Tempo & Key: 57 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:45] [Emerge] Drone from silence, very slowly
[0:45-1:30] [Present] Drone at its warmest and most present
[1:30-2:00] [Shift] Subtle harmonic movement
[2:00-3:00] [Return and fade] Returns to opening pitch, fades over a minute""",

            "c": """Style: Guitar Whisper, Introvert Rest
Mood: Quietest possible music, just presence, deeply private
Instrumentation: Single nylon guitar, whisper-quiet
Tempo & Key: 57 BPM, G major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:35] [Intro] Guitar barely audible, one note
[0:35-1:10] [Phrase] 3-note phrase, whisper-quiet
[1:10-1:45] [Space] Long silence
[1:45-2:20] [Return] One more quiet phrase
[2:20-3:00] [Fade] Guitar fades to complete silence""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # HEARTBROKEN — A minor
    # ═══════════════════════════════════════════════════════════
    "heartbroken": {
        "energetic": {
            "a": """Style: Emotional Healing Acoustic, Guitar-led
Mood: Honest grief, gentle catharsis, beginning of healing
Instrumentation: Fingerpicked guitar emotional lead, piano warm underneath
Tempo & Key: 66 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Solo guitar, honest and tender, feeling every note
[0:20-0:50] [Piano] Piano enters with warmth, emotional support
[0:50-1:25] [Together] Both instruments, emotion fully expressed
[1:25-1:50] [Swell] Strings or piano swell, cathartic moment
[1:50-2:15] [Ease] Energy reduces, after the release
[2:15-2:45] [Tender] Quieter, warmer, something released
[2:45-3:00] [Outro] Guitar alone, lighter than at start""",

            "b": """Style: Piano Emotion, Cathartic Release
Mood: Piano as emotional expression, honest sadness, warmth in pain
Instrumentation: Piano emotional lead, strings or pad warm support
Tempo & Key: 66 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Piano alone, honest and unhurried
[0:20-0:50] [Support] Warm strings enter gently
[0:50-1:20] [Build] Both toward emotional peak
[1:20-1:50] [Peak] Emotional catharsis, piano expressing fully
[1:50-2:15] [Release] Post-catharsis, warmth and relief
[2:15-2:45] [Settle] Piano simplifies, strings thin
[2:45-3:00] [Outro] Final piano phrase, healing""",

            "c": """Style: Guitar-strings Healing, Cathartic Arc
Mood: Cathartic journey, string warmth supporting guitar grief
Instrumentation: Guitar and strings (no piano), equal emotional partners
Tempo & Key: 66 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:20] [Intro] Guitar tender and honest
[0:20-0:55] [Strings] Strings enter warmly underneath
[0:55-1:30] [Together] Guitar melody over warm strings
[1:30-1:55] [Catharsis] Strings swell, guitar emotional peak
[1:55-2:20] [After] Post-catharsis quiet, both soft
[2:20-2:45] [Guitar alone] Strings fade, guitar continues tender
[2:45-3:00] [Outro] Guitar resolves, something healed""",
        },

        "balanced": {
            "a": """Style: Emotional Acoustic, Warm Honest Grief
Mood: Deep feeling without drama, warmth inside sadness
Instrumentation: Guitar emotional, piano warm long notes
Tempo & Key: 60 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Guitar honest and tender
[0:25-0:55] [Piano] Piano warm long chords underneath
[0:55-1:30] [Full] Both expressing together
[1:30-1:55] [Quieter] Reduction, more intimate
[1:55-2:20] [Return] Both again, warmer
[2:20-2:45] [Thin] Piano alone briefly
[2:45-3:00] [Outro] Guitar closes gently""",

            "b": """Style: Piano-strings Healing, Warm Sadness
Mood: Sadness held in warmth, strings as comfort
Instrumentation: Piano lead, warm strings pad underneath
Tempo & Key: 60 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Piano alone, slow and honest
[0:25-0:55] [Strings] Strings enter warmly
[0:55-1:30] [Together] Piano melody over warm strings
[1:30-2:00] [Deep] Deepest emotional moment
[2:00-2:30] [Ease] Post-peak warmth, softer
[2:30-3:00] [Fade] Both fade slowly""",

            "c": """Style: Intimate Duo, Close Emotional Honesty
Mood: Two instruments as emotional companions, close and honest
Instrumentation: Guitar and piano equal, close and intimate
Tempo & Key: 60 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Both together, honest from start
[0:25-0:55] [Dialogue] Instruments respond to each other emotionally
[0:55-1:30] [Shared] Sharing the feeling, fuller together
[1:30-2:00] [Peak] Emotional peak shared between instruments
[2:00-2:30] [After] Post-peak warmth, quieter
[2:30-3:00] [Fade] Together fade, something shared""",
        },

        "mellow": {
            "a": """Style: Dark Tender, Guitar Night Grief
Mood: Night grief, tender and dark, held in darkness
Instrumentation: Solo guitar barely audible, dark and tender
Tempo & Key: 53 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Guitar barely there, tender
[0:25-0:55] [Phrase] Short tender melody, slowly
[0:55-1:25] [Space] Long space after phrase
[1:25-1:55] [Return] New tender phrase
[1:55-2:25] [Quieter] Even softer, more space
[2:25-3:00] [Fade] Guitar fades to silence""",

            "b": """Style: Dark Piano, Grief Held Gently
Mood: Piano as the only companion in the dark
Instrumentation: Dark piano, very slow, warm reverb
Tempo & Key: 53 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Piano dark note, long reverb
[0:30-1:00] [Second] Different note, holds in darkness
[1:00-1:30] [Phrase] 3-note phrase, tender and slow
[1:30-2:00] [Space] Long silence after phrase
[2:00-2:30] [Return] One more tender phrase
[2:30-3:00] [Final note] Single note fades to warmth""",

            "c": """Style: Strings Night, Dark Warmth
Mood: Dark strings as warmth in grief, completely held
Instrumentation: Low strings very soft, barely audible
Tempo & Key: 53 BPM, A minor
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:40] [Emerge] Strings from silence, very slowly
[0:40-1:20] [Present] Strings at their warmest, holding grief
[1:20-1:50] [Movement] Slow harmonic shift in strings
[1:50-2:20] [Held] Returns, still warm and dark
[2:20-3:00] [Fade] Strings fade very slowly to silence""",
        },
    },

    # ═══════════════════════════════════════════════════════════
    # SLEEPY — C major
    # ═══════════════════════════════════════════════════════════
    "sleepy": {
        "energetic": {
            "a": """Style: Sleep Preparation Piano, Drowsy Arc
Mood: Body growing heavy, sleep approaching, mind releasing
Instrumentation: Very soft piano, warm pad underneath
Tempo & Key: 58 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:25] [Intro] Piano very soft, sleep beginning
[0:25-0:55] [Pad] Warm pad enters, heaviness spreading
[0:55-1:30] [Heaviest] Both at their softest fullness, very heavy
[1:30-1:55] [Lighter] Piano less frequent, drowsy
[1:55-2:20] [Drifting] Piano barely there, pad sustains
[2:20-2:45] [Threshold] Sleep threshold, barely conscious
[2:45-3:00] [Gone] Fades to sleep""",

            "b": """Style: Sleep Pad, Warmth Descending
Mood: Warmth like a blanket, consciousness gently leaving
Instrumentation: Warm pad descending harmonically, piano one note
Tempo & Key: 58 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Pad from silence, warm
[0:30-1:00] [Deepen] Pad descends harmonically, heavier
[1:00-1:30] [Piano] One piano note, almost inaudible
[1:30-2:00] [Deepest] Pad at heaviest, piano gone
[2:00-2:30] [Fade begins] Pad starts very slow fade
[2:30-3:00] [Asleep] Complete fade to silence""",

            "c": """Style: Delta-adjacent, Harmonic Sleep
Mood: Delta wave territory, body completely still
Instrumentation: Low drone harmonics, near-silence
Tempo & Key: 58 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:40] [Emerge] Low harmonic from silence
[0:40-1:20] [Present] Low harmonic at its most present
[1:20-1:50] [Shift] Very subtle harmonic shift
[1:50-2:30] [Thin] Harmonic reduces
[2:30-3:00] [Silence] Fades completely""",
        },

        "balanced": {
            "a": """Style: Near-silence Sleep, Piano One Note
Mood: Deep drowsiness, one note every 20 seconds
Instrumentation: Piano single notes, very widely spaced, warm pad
Tempo & Key: 52 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:30] [Intro] Pad barely audible from silence
[0:30-0:55] [First note] Piano note, very soft
[0:55-1:25] [Space] Long silence with pad
[1:25-1:50] [Second note] Another piano note
[1:50-2:20] [Long space] Maximum silence
[2:20-2:45] [Final note] Last piano note
[2:45-3:00] [Asleep] Pad fades to silence""",

            "b": """Style: Sleep Drone, Low Constant
Mood: Drone as sleep medicine, constant low warmth
Instrumentation: Low drone only, no other instrument
Tempo & Key: 52 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:45] [Emerge] Drone from complete silence over 45 seconds
[0:45-1:30] [Present] Drone at its most present, constant
[1:30-2:00] [Shift] Microscopic harmonic shift
[2:00-3:00] [Fade] Very long slow fade back to silence""",

            "c": """Style: Sub-bass Sleep, Felt in Body
Mood: Sleep felt physically, sub-frequency as cradle
Instrumentation: Sub-bass only, barely audible
Tempo & Key: 52 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-1:00] [Emerge] Sub-bass rises from nothing over one minute
[1:00-1:45] [Cradle] Sub-bass constant, sleep fully invited
[1:45-3:00] [Return] Very slow fade back to nothing over 75 seconds""",
        },

        "mellow": {
            "a": """Style: Deepest Sleep, Piano Fading Out
Mood: Already asleep, music barely reaching consciousness
Instrumentation: Piano almost inaudible, one note every 30 seconds
Tempo & Key: 46 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-0:45] [First note] Piano note barely audible from silence
[0:45-1:30] [Space] Pure silence
[1:30-2:00] [Second note] Second piano note, even softer
[2:00-3:00] [Silence] Pure silence, sleep complete""",

            "b": """Style: Pure Warmth Sleep, Pad Alone
Mood: Pure warmth, sleep as homecoming
Instrumentation: Warm pad only, no other element
Tempo & Key: 46 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-1:00] [Emerge] Pad rises from silence over one minute
[1:00-1:30] [Peak] Warmest point, barely audible
[1:30-3:00] [Return] Slow fade back to complete silence""",

            "c": """Style: Silence Music, Consciousness Threshold
Mood: Music at the threshold of silence, almost nothing
Instrumentation: The space between notes, reverb tails only
Tempo & Key: 46 BPM, C major
Vocal Style: Instrumental only, no vocals, no vocalizing, no humming
Structure:
[0:00-1:00] [Emergence] Single drone tone rises from silence, almost imperceptible
[1:00-2:00] [Presence] At its most present, still barely there
[2:00-3:00] [Return to silence] Fades completely over one minute""",
        },
    },
}


# ─────────────────────────────────────────────────────────────
# ELEVENLABS CONFIG PER MOOD
# ─────────────────────────────────────────────────────────────

ELEVENLABS_CONFIG = {
    "happy": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Pure music.",
        "style_tags": ["upbeat","feel-good","acoustic guitar","piano","C major","summer","joyful","positive","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","spoken word","dark","sad","minor key"],
    },
    "kickstart": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Pure music.",
        "style_tags": ["energetic","morning","driving","acoustic guitar","piano","G major","motivating","bright","forward momentum","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","spoken word","dark","sleepy","slow"],
    },
    "unmotivated": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Pure music.",
        "style_tags": ["warm","motivational","encouraging","acoustic guitar","piano","D major","gentle drive","positive momentum","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","spoken word","aggressive","dark","melancholic"],
    },
    "focus": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Pure ambient music.",
        "style_tags": ["focus","concentration","minimal","piano","ambient","A minor","clean","neutral","non-distracting","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","percussion","drums","upbeat","busy","distracting"],
    },
    "deepwork": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Deep ambient music.",
        "style_tags": ["deep","immersive","drone","piano","ambient","D minor","flow state","hypnotic","timeless","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","percussion","drums","upbeat","melodic hooks","bright"],
    },
    "anxious": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Calming ambient music.",
        "style_tags": ["calming","grounding","gentle","soft piano","warm pad","F major","432Hz","nervous system","reassuring","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","tense","dissonant","fast","energetic","busy","percussion"],
    },
    "stressed": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Meditative ambient music.",
        "style_tags": ["meditative","stress relief","singing bowl","piano","E major","peaceful","releasing","stillness","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","tense","busy","fast","percussion","energetic","dissonant"],
    },
    "socially-drained": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Quiet restorative ambient music.",
        "style_tags": ["quiet","restorative","minimal","piano","warm pad","G major","solitude","recharging","gentle","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","social","busy","energetic","percussion","bright"],
    },
    "heartbroken": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Emotional healing music.",
        "style_tags": ["healing","emotional","tender","acoustic guitar","piano","A minor","cathartic","warm","honest","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","happy","upbeat","bright","energetic","major key"],
    },
    "sleepy": {
        "style_text": "Instrumental only. No vocals. No singing. No humming. Deep sleep music.",
        "style_tags": ["sleep","drowsy","very slow","soft piano","drone","C major","delta waves","heavy","warm","instrumental"],
        "negative_styles": ["vocals","singing","voice","lyrics","humming","energetic","bright","upbeat","percussion","rhythm"],
    },
}


# ─────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tiers    = ["energetic","balanced","mellow"]
    variants = ["a","b","c"]
    moods    = list(LYRIA_PROMPTS.keys())

    total = len(moods) * len(tiers) * len(variants)
    print(f"Lyria prompts : {len(moods)} moods x {len(tiers)} tiers x {len(variants)} variants = {total}")
    print(f"EL configs    : {len(ELEVENLABS_CONFIG)} moods\n")

    errors = []
    for mood in moods:
        for tier in tiers:
            for v in variants:
                if v not in LYRIA_PROMPTS[mood][tier]:
                    errors.append(f"Missing: {mood}/{tier}/{v}")
        if mood not in ELEVENLABS_CONFIG:
            errors.append(f"Missing EL config: {mood}")

    if errors:
        for e in errors: print(f"  x {e}")
    else:
        print("  All 90 Lyria prompts present")
        print("  All 10 ElevenLabs configs present")
        print("  All 3 variants (a/b/c) per tier confirmed")
