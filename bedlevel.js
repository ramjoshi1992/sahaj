/*
 * ZenTune | bedlevel.js
 * =====================
 * Works out how loud the texture bed should sit, from measured properties
 * rather than a table of levels.
 *
 * The target: the texture should be perceptible but not attended to. That is
 * a masking relationship, and masking is local to frequency — so the bed is
 * placed a fixed depth below the music's energy IN THE TEXTURE'S OWN BANDS,
 * not below the music overall. A texture living where the music is quiet can
 * sit very low and still be sensed; one competing with the music has to come
 * up or it simply disappears.
 *
 *   bedDb = musicLevelInTextureBands - veil - textureLoudness
 *
 * where veil is one constant, adjusted by two things: how much presence the
 * mood wants, and how peaky the texture is. Sparse transient material pokes
 * above its own average, so it gets set lower for the same felt level.
 *
 * Adding a fifteenth texture means measuring it, not deciding a level for it.
 */

(function (global) {
  'use strict';

  const K = {
    veilDb: 19.0,       // depth below the music, in the texture's own bands
    presenceDb: 4.0,    // how far mood swings it, either side
    crestDb: 0.25,      // per dB of crest away from the library's own median
                        // (small, because a 90th-percentile loudness measure
                        //  already accounts for most of what crest describes)
    crestRef: null,     // derived from the library, not guessed at
    contextDb: 3.0,     // total swing available to time/weather/room
    minGain: 0.02,
    maxGain: 1.00,   // a limiter on the master makes this safe
  };

  // How much of the surroundings each mood wants. The only human judgement
  // in the model, and it is one number per mood rather than one level per
  // mood/texture pair.
  const PRESENCE = {
    sleepy: 0.85,
    'socially-drained': 0.70,
    anxious: 0.65,
    happy: 0.50,
    unmotivated: 0.45,
    kickstart: 0.40,
    focus: 0.25,
  };

  const dbToGain = db => Math.pow(10, db / 20);

  /* The crest reference is the median of whatever textures are actually in
   * the library, so the correction works in both directions: flat material
   * nudged up, peaky material pulled down. Measured across the current 14 the
   * range is 1.8 to 13.2 dB, so a fixed reference near the top would have
   * corrected almost nothing. */
  let _crestRef = null;
  function crestReference(library) {
    if (_crestRef != null) return _crestRef;
    const files = (library._textures && library._textures.files) || {};
    const v = Object.values(files).map(t => t.crestDb)
                    .filter(x => typeof x === 'number').sort((a, b) => a - b);
    _crestRef = v.length ? v[Math.floor(v.length / 2)] : 7.0;
    return _crestRef;
  }
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  /* Overlap of two normalised band profiles, scaled so 1.0 means the two are
   * spread independently. Above 1 they are piled into the same bands. */
  function overlapFactor(texBands, musicBands) {
    if (!texBands || !musicBands) return 1;
    const n = Math.min(texBands.length, musicBands.length);
    let s = 0;
    for (let i = 0; i < n; i++) s += texBands[i] * musicBands[i];
    return Math.max(0.05, s * n);
  }

  /* context: { hour, weather, room } — all optional.
   * room is the only one a sensor could give us and we are not asking for it;
   * it is here so the bench can audition the effect. */
  function contextOffsetDb(ctx) {
    if (!ctx) return 0;
    let d = 0;
    if (typeof ctx.hour === 'number') {
      // a room at midnight is quieter than a room at midday
      const night = (ctx.hour >= 22 || ctx.hour < 7);
      const midday = (ctx.hour >= 10 && ctx.hour < 16);
      d += night ? -1.5 : (midday ? 1.0 : 0);
    }
    if (ctx.weather === 'rain' || ctx.weather === 'storm') d += 1.0;
    if (ctx.room === 'quiet') d -= 2.0;
    if (ctx.room === 'noisy') d += 2.0;
    return clamp(d, -K.contextDb, K.contextDb);
  }

  /* Returns the linear gain for the texture bus, plus the workings, so the
   * bench can show why it landed where it did. */
  function bedLevel(library, opts) {
    const k = Object.assign({}, K, opts.constants || {});
    const group = library[opts.mood + '/' + opts.tier];
    const tex = library._textures && library._textures.files &&
                library._textures.files[opts.texture];

    if (!group || !tex || tex.loudnessDb == null || !group.music) {
      return { gain: 0.15, gainDb: null, reason: 'not calibrated — 15% fallback' };
    }

    const music = group.music;
    const ov = overlapFactor(tex.bands, music.bands);
    const localMusicDb = music.musicLoudnessDb + 10 * Math.log10(ov);

    const presence = (PRESENCE[opts.mood] != null) ? PRESENCE[opts.mood] : 0.5;
    const presenceAdj = -k.presenceDb * (presence - 0.5) * 2;   // more presence = shallower veil
    const ref = (k.crestRef != null) ? k.crestRef : crestReference(library);
    const crestAdj = k.crestDb * (tex.crestDb - ref);   // symmetric
    const ctxAdj = -contextOffsetDb(opts.context);              // noisier room = shallower veil

    const veil = k.veilDb + presenceAdj + crestAdj + ctxAdj;
    const targetDb = localMusicDb - veil;
    const gainDb = targetDb - tex.loudnessDb;
    const gain = clamp(dbToGain(gainDb), k.minGain, k.maxGain);

    return {
      gain: Math.round(gain * 1000) / 1000,
      gainDb: Math.round(gainDb * 10) / 10,
      overlap: Math.round(ov * 100) / 100,
      localMusicDb: Math.round(localMusicDb * 10) / 10,
      textureDb: tex.loudnessDb,
      crestDb: tex.crestDb,
      veil: Math.round(veil * 10) / 10,
      presence,
      crestRef: Math.round(ref * 10) / 10,
      parts: {
        base: k.veilDb,
        presence: Math.round(presenceAdj * 10) / 10,
        crest: Math.round(crestAdj * 10) / 10,
        context: Math.round(ctxAdj * 10) / 10,
      },
      clamped: gain !== dbToGain(gainDb),
    };
  }

  global.ZenBedLevel = {
    bedLevel, PRESENCE, K, overlapFactor,
    resetReference: () => { _crestRef = null; }
  };
})(typeof window !== 'undefined' ? window : globalThis);
