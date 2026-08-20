/*
 * ZenTune | sequencer.js
 * ======================
 * library.json + mood/tier/duration  ->  a session plan.
 *
 * A session is three movements, one per seed family. Each movement opens
 * with its seed, cycles that family's three middle pieces, and closes with
 * the same seed. A family's material never appears outside its own movement,
 * so the only cross-family joins are the two movement boundaries.
 *
 * Joins follow the rule settled by ear:
 *   same family  -> crossfade, at the group's own metrical length (<=3.5s).
 *                   These pieces are ~0.99 similar; a long crossfade combs
 *                   rather than smooths.
 *   different    -> sequential. Fade out, a breath of near silence, fade in.
 *                   Nothing overlaps. The breath is what makes the boundary
 *                   register at all in groups where the families sound alike.
 *
 * Randomness lives in three places: which family opens and closes, the order
 * of middles within each cycle, and which window of a piece each visit uses.
 * Everything else is fixed.
 */

(function (global) {
  'use strict';

  const FADE_OUT = 4.8;      // cross-family
  const BREATH   = 1.2;
  const FADE_IN  = 6.0;
  const END_GAP  = 3.0;      // stop a mid-session seed ending short of silence
  const SEG_MIN  = 35;
  const SEG_MAX  = 100;
  const SEG_WANT = 75;       // target middle-segment length
  const MIN_MOVEMENT = 240;  // below this a movement has no room to breathe

  // deterministic RNG so a plan can be reproduced from its seed number
  function rng(seed) {
    let a = seed >>> 0;
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function shuffled(arr, rand) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  // n start points spread across the usable part of a piece
  function windows(usable, n, segLen) {
    const span = Math.max(0, usable - segLen - 1);
    if (n <= 1) return [round1(span / 2)];
    const out = [];
    for (let i = 0; i < n; i++) out.push(round1((span * i) / (n - 1)));
    return out;
  }

  const round1 = v => Math.round(v * 10) / 10;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  /* Short sessions use two movements rather than three. Three would leave
   * each one barely longer than its own seed opening and ending, and a
   * 10-minute session wants fewer boundaries, not more. Two of three also
   * means six ordered pairs, so the variety goes up rather than down. */
  function familyOrder(g, rand, targetS, avoid) {
    const fams = ['A', 'B', 'C'].filter(f => g.families[f] && g.families[f].seed);
    const room = Math.floor(targetS / MIN_MOVEMENT);
    const n = Math.max(1, Math.min(fams.length, room));
    let order = shuffled(fams, rand);

    /* A reroll has to be audibly different, and every plan opens with a seed
     * track from its beginning — so with three families, one reroll in three
     * would start with byte-identical audio to the one just rejected. Moving
     * that family out of first place is what makes the button mean anything. */
    if (avoid && order[0] === avoid && order.length > 1) {
      const j = 1 + Math.floor(rand() * (order.length - 1));
      [order[0], order[j]] = [order[j], order[0]];
    }
    return order.slice(0, n);
  }

  /* Build the item list for one pass at a given target length. Crossfades
   * eat wall-clock time, so the caller runs this twice and rescales. */
  function pass(g, order, targetS, rand, warmStart) {
    const pools = {};
    let poolTotal = 0;
    order.forEach(f => { pools[f] = g.families[f].pool; poolTotal += pools[f]; });

    const items = [];
    order.forEach((fam, fi) => {
      const spec = g.families[fam];
      const seedName = spec.seed;
      const sd = g.pieces[seedName];
      const mids = spec.mids.slice();
      const alloc = targetS * (pools[fam] / poolTotal);
      const isLast = fi === order.length - 1;

      // the seed frame scales with the movement, so a short session does not
      // spend most of itself opening and closing
      const openLen = clamp(alloc * 0.18, 30, Math.min(75, sd.usableEnd * 0.42));
      const endLen  = clamp(alloc * 0.20, 35, Math.min(85, sd.usableEnd * 0.48));
      const body    = Math.max(SEG_MIN * mids.length, alloc - openLen - endLen);

      const cycles = Math.max(1, Math.round(body / (mids.length * SEG_WANT)));
      const segLen = clamp(body / (mids.length * cycles), SEG_MIN, SEG_MAX);

      const win = {}, used = {};
      mids.forEach(m => {
        win[m] = windows(g.pieces[m].usableEnd, cycles, segLen);
        used[m] = 0;
      });

      /* A fresh session opens at bar one, because that is the seed's composed
       * opening. A reroll starts partway in instead: sleep seeds in particular
       * are quiet and sparse for their first fifteen seconds, so beginning at
       * zero means the change you asked for is inaudible until it is too late
       * to feel like a change. */
      const warm = warmStart && fi === 0;
      const openEntry = warm
        ? round1(Math.min(Math.max(0, sd.usableEnd - openLen - 4), 32))
        : 0;
      items.push({ family: fam, stem: seedName, role: 'opening',
                   entry: openEntry, len: openLen });

      let lastOfCycle = null;
      for (let c = 0; c < cycles; c++) {
        let ord = shuffled(mids, rand);
        // a cycle must not open on the piece the previous one closed with,
        // or the same stem plays twice running across the boundary
        if (mids.length > 1 && ord[0] === lastOfCycle) {
          const j = 1 + Math.floor(rand() * (ord.length - 1));
          [ord[0], ord[j]] = [ord[j], ord[0]];
        }
        ord.forEach(m => {
          items.push({ family: fam, stem: m, role: 'middle',
                       entry: win[m][used[m]++], len: segLen });
        });
        lastOfCycle = ord[ord.length - 1];
      }

      // the seed's own ending; only the final movement runs into its silence
      const from = Math.max(0, sd.duration - endLen - (isLast ? 0 : END_GAP));
      items.push({ family: fam, stem: seedName, role: 'ending',
                   entry: round1(from), len: endLen });
    });
    return items;
  }

  function layout(items, crossfade) {
    let t = 0;
    items.forEach((it, i) => {
      it.at = round1(t);
      const nx = items[i + 1];
      if (!nx) { it.join = null; return; }
      const same = nx.family === it.family;
      it.join = same ? 'crossfade' : 'sequential';
      t += same ? it.len - crossfade : it.len - FADE_OUT + BREATH;
    });
    const last = items[items.length - 1];
    return round1(last.at + last.len);
  }

  function buildPlan(library, opts) {
    const mood = opts.mood, tier = opts.tier;
    const key = mood + '/' + tier;
    const g = library[key];
    if (!g) throw new Error('no library entry for ' + key);

    const minutes = opts.minutes || 20;
    const seedNum = (opts.seed == null) ? (Math.random() * 1e9) | 0 : opts.seed | 0;
    const rand = rng(seedNum);
    const target = minutes * 60;
    const xf = g.crossfade || 2.5;

    const order = familyOrder(g, rand, target, opts.avoid);

    // two passes: build, measure the shortfall the joins cost, rebuild
    let items = pass(g, order, target, rng(seedNum), opts.warmStart);
    let dur = layout(items, xf);
    if (dur > 0) {
      items = pass(g, order, target * (target / dur), rng(seedNum), opts.warmStart);
      dur = layout(items, xf);
    }

    items.forEach(it => {
      const p = g.pieces[it.stem];
      it.url = p.url;
      it.gain = p.gain;
      it.bpm = p.bpm;
      it.pulsed = p.pulsed;
      it.len = round1(it.len);
      it.entry = round1(it.entry);
    });

    const boundaries = items
      .map((it, i) => (i > 0 && it.family !== items[i - 1].family)
        ? { at: it.at, from: items[i - 1].family, to: it.family } : null)
      .filter(Boolean);

    const reuse = {};
    order.forEach(f => {
      const spent = items.filter(i => i.family === f)
                         .reduce((s, i) => s + i.len, 0);
      reuse[f] = Math.round((spent / g.families[f].pool) * 100) / 100;
    });

    return {
      key, mood, tier, minutes, seed: seedNum,
      order, duration: dur, items, boundaries, reuse,
      crossfade: xf, fadeOut: FADE_OUT, breath: BREATH, fadeIn: FADE_IN,
      bar: g.bar, pulsedCount: g.pulsedCount,
      betweenFamily: g.betweenFamily
    };
  }

  global.SAHAJ_SEQ_BUILD = '2026-08-20a';
  global.ZenSequencer = { buildPlan, rng, FADE_OUT, BREATH, FADE_IN };
})(typeof window !== 'undefined' ? window : globalThis);
