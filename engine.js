/*
 * ZenTune | engine.js
 * ===================
 * Plays a plan from sequencer.js. Knows nothing about moods, tiers or the
 * library — a plan is self-contained, carrying its own URLs, gains, entry
 * offsets and join timings.
 *
 * Scheduling is done in AudioContext time, not with a timer per segment.
 * Each segment is created a couple of seconds before it is due and started
 * at an exact context time, so joins land where the plan says rather than
 * wherever the event loop happened to be. setTimeout only decides *when to
 * schedule*, never when a sound begins.
 *
 * Two join shapes, as settled by ear:
 *   crossfade   same family; equal-power sine/cosine over the plan's
 *               crossfade length, which is a whole metrical unit of that
 *               group and never longer than 3.5s.
 *   sequential  different families; fade out, a breath of near silence,
 *               fade in. Nothing overlaps.
 *
 * The texture bed runs underneath the whole session on its own gain, loops
 * continuously, and is the only thing that never stops between movements.
 */

(function (global) {
  'use strict';

  const LOOKAHEAD_S   = 6.0;   // create a segment this far before it is due
  const PREFETCH      = 3;     // decode this many segments ahead
  const TEX_GAIN      = 0.15;
  const TEX_FADE_IN   = 10.0;
  const TEX_FADE_OUT  = 18.0;
  const CURVE_STEPS   = 96;

  function curve(rise, peak) {
    const a = new Float32Array(CURVE_STEPS);
    for (let i = 0; i < CURVE_STEPS; i++) {
      const x = (i / (CURVE_STEPS - 1)) * Math.PI / 2;
      a[i] = (rise ? Math.sin(x) : Math.cos(x)) * peak;
    }
    return a;
  }

  class ZenEngine {
    constructor(opts) {
      opts = opts || {};
      this.onSegment  = opts.onSegment  || function () {};
      this.onBoundary = opts.onBoundary || function () {};
      this.onProgress = opts.onProgress || function () {};
      this.onState    = opts.onState    || function () {};
      this.onLog      = opts.onLog      || function () {};
      this.buffers = new Map();
      this.ctx = null;
      this.speed = 1;
      this.playing = false;
      this._timers = [];
      this._voices = [];
      this._texture = null;
      this._index = -1;
      this.texTarget = TEX_GAIN;
    }

    // Must be called from inside a user gesture, or the context stays
    // suspended and nothing will sound.
    async open() {
      if (!this.ctx) {
        const AC = global.AudioContext || global.webkitAudioContext;
        this.ctx = new AC();
        this.master = this.ctx.createGain();
        this.master.gain.value = 0.8;

        /* A safety limiter, not an effect. The texture bed is level-matched
         * to the music at runtime, and the quietest source recordings need
         * close to unity gain to get there — their peaks are already near
         * full scale even though their average level is 24dB down. Summed
         * with the music that can pass 0dBFS on transients. Threshold is set
         * high enough that nothing touches it in normal playing. */
        this.limiter = this.ctx.createDynamicsCompressor();
        this.limiter.threshold.value = -1.5;
        this.limiter.knee.value = 0;
        this.limiter.ratio.value = 20;
        this.limiter.attack.value = 0.003;
        this.limiter.release.value = 0.25;

        this.master.connect(this.limiter).connect(this.ctx.destination);
        this.musicBus = this.ctx.createGain();
        this.musicBus.connect(this.master);
        this.textureBus = this.ctx.createGain();
        this.textureBus.gain.value = 0;
        this.textureBus.connect(this.master);
      }
      if (this.ctx.state === 'suspended') await this.ctx.resume();
      return this.ctx;
    }

    async fetchBuffer(url) {
      if (this.buffers.has(url)) return this.buffers.get(url);
      const pending = (async () => {
        const t0 = performance.now();
        const res = await fetch(url);
        if (!res.ok) throw new Error(res.status + ' fetching ' + url);
        const arr = await res.arrayBuffer();
        const buf = await this.ctx.decodeAudioData(arr);
        this.onLog('loaded ' + url.split('/').slice(-2).join('/') +
                   '  ' + (arr.byteLength / 1048576).toFixed(1) + 'MB  ' +
                   Math.round(performance.now() - t0) + 'ms');
        return buf;
      })();
      this.buffers.set(url, pending);
      const buf = await pending;
      this.buffers.set(url, buf);
      return buf;
    }

    /* Only the first segment and the texture are awaited. Everything else is
     * fetched during playback — a 45-minute plan references about a dozen
     * files and there is no reason to hold the session open for all of them. */
    async load(plan, opts) {
      opts = opts || {};
      await this.open();
      this.plan = plan;
      this.textureUrl = opts.texture || null;
      this.onState({ phase: 'loading' });

      const first = this.fetchBuffer(plan.items[0].url);
      const tex = this.textureUrl ? this.fetchBuffer(this.textureUrl) : null;
      await Promise.all([first, tex].filter(Boolean));

      this._prefetchFrom(1);
      this.onState({ phase: 'ready' });
      return this;
    }

    _prefetchFrom(i) {
      if (!this.plan) return;
      const seen = new Set();
      for (let k = i; k < Math.min(i + PREFETCH, this.plan.items.length); k++) {
        const u = this.plan.items[k].url;
        if (seen.has(u)) continue;
        seen.add(u);
        this.fetchBuffer(u).catch(e => this.onLog(e.message, 'err'));
      }
    }

    async start(fromIndex) {
      await this.open();
      this.stopVoices();
      const p = this.plan;
      const i0 = fromIndex || 0;
      const now = this.ctx.currentTime + 0.15;

      this._baseAt = p.items[i0].at;
      this._baseCtx = now;
      this.playing = true;
      this._index = -1;

      if (this.textureUrl) this._startTexture(now);
      this._scheduleFrom(i0, now);
      this._tick();
      this.onState({ phase: 'playing' });
    }

    _startTexture(when) {
      const buf = this.buffers.get(this.textureUrl);
      if (!buf || buf instanceof Promise) return;
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      src.loop = true;
      src.connect(this.textureBus);
      src.start(when);
      const peak = this.texTarget;
      const g = this.textureBus.gain;
      g.cancelScheduledValues(when);
      g.setValueAtTime(0.0001, when);
      g.setValueCurveAtTime(curve(true, peak), when, TEX_FADE_IN);
      this._texture = src;

      // fade the bed out over the tail of the session, after the music has gone
      const total = (this.planDuration() - this._baseAt) / this.speed;
      const at = when + Math.max(1, total - TEX_FADE_OUT * 0.6);
      g.setValueCurveAtTime(curve(false, peak), at, TEX_FADE_OUT);
      try { src.stop(at + TEX_FADE_OUT + 1); } catch (e) {}
    }

    planDuration() { return this.plan ? this.plan.duration : 0; }

    /* Schedule one segment at an exact context time, then set a timer to
     * schedule the next one shortly before it is due. */
    _scheduleFrom(i, when) {
      const p = this.plan;
      if (!p || i >= p.items.length || !this.playing) return;
      const it = p.items[i];
      const prev = p.items[i - 1];

      const play = () => {
        const buf = this.buffers.get(it.url);
        if (!buf || buf instanceof Promise) {
          // not decoded yet — wait a beat and try again rather than dropping it
          this._timers.push(setTimeout(() => this._scheduleFrom(i, this.ctx.currentTime + 0.1), 250));
          return;
        }
        const src = this.ctx.createBufferSource();
        src.buffer = buf;
        const g = this.ctx.createGain();
        const fin = prev ? (prev.join === 'crossfade' ? p.crossfade : p.fadeIn)
                         : p.fadeIn;
        g.gain.setValueAtTime(0.0001, when);
        g.gain.setValueCurveAtTime(curve(true, it.gain), when, fin);
        src.connect(g).connect(this.musicBus);
        src.start(when, it.entry);

        if (it.join) {
          const fout = it.join === 'crossfade' ? p.crossfade : p.fadeOut;
          const outAt = when + (it.len - fout) / this.speed;
          g.gain.setValueCurveAtTime(curve(false, it.gain), outAt, fout);
          try { src.stop(outAt + fout + 0.3); } catch (e) {}
        } else {
          try { src.stop(when + it.len / this.speed + 0.3); } catch (e) {}
        }

        this._voices.push({ src, gain: g, i });
        this._index = i;
        this.onSegment(it, i);
        if (prev && prev.family !== it.family) this.onBoundary(it, i);
        this._prefetchFrom(i + 1);

        const nx = p.items[i + 1];
        if (nx) {
          const gap = (nx.at - it.at) / this.speed;
          const nextWhen = when + gap;
          const lead = Math.max(0.05, (nextWhen - this.ctx.currentTime - LOOKAHEAD_S));
          this._timers.push(setTimeout(
            () => this._scheduleFrom(i + 1, nextWhen), lead * 1000));
        } else {
          const endIn = (it.len / this.speed + 1) * 1000;
          this._timers.push(setTimeout(() => {
            this.onState({ phase: 'complete' });
            this.playing = false;
          }, endIn));
        }
      };

      const lead = (when - this.ctx.currentTime - LOOKAHEAD_S) * 1000;
      if (lead > 20) this._timers.push(setTimeout(play, lead));
      else play();
    }

    _tick() {
      if (!this.playing) return;
      const el = (this.ctx.currentTime - this._baseCtx) * this.speed + this._baseAt;
      this.onProgress(Math.max(0, el), this.planDuration());
      this._raf = global.requestAnimationFrame
        ? global.requestAnimationFrame(() => this._tick())
        : setTimeout(() => this._tick(), 200);
    }

    async pause() {
      if (!this.ctx || this.ctx.state !== 'running') return;
      await this.ctx.suspend();     // context time stops, so schedules hold
      this.onState({ phase: 'paused' });
    }

    async resume() {
      if (!this.ctx || this.ctx.state !== 'suspended') return;
      await this.ctx.resume();
      this.onState({ phase: 'playing' });
    }

    stopVoices() {
      this._timers.forEach(clearTimeout);
      this._timers = [];
      if (!this.ctx) return;
      const t = this.ctx.currentTime;
      this._voices.forEach(v => {
        try {
          v.gain.gain.cancelScheduledValues(t);
          v.gain.gain.setValueAtTime(Math.max(v.gain.gain.value, 0.0001), t);
          v.gain.gain.linearRampToValueAtTime(0.0001, t + 0.35);
          v.src.stop(t + 0.45);
        } catch (e) {}
      });
      this._voices = [];
    }

    stop() {
      this.playing = false;
      if (this._raf && global.cancelAnimationFrame) global.cancelAnimationFrame(this._raf);
      this.stopVoices();
      if (this._texture) {
        try {
          const t = this.ctx.currentTime;
          this.textureBus.gain.cancelScheduledValues(t);
          this.textureBus.gain.setValueAtTime(this.textureBus.gain.value, t);
          this.textureBus.gain.linearRampToValueAtTime(0.0001, t + 1.2);
          this._texture.stop(t + 1.4);
        } catch (e) {}
        this._texture = null;
      }
      this.onState({ phase: 'idle' });
    }

    setVolume(v) { if (this.master) this.master.gain.value = v; }
    // how hard the safety limiter is working, in dB. Should sit at 0 almost
    // always; anything sustained means a level is wrong upstream.
    get limiterReduction() {
      return this.limiter ? Math.round(this.limiter.reduction * 10) / 10 : 0;
    }
    setTextureGain(v) {
      if (!this.textureBus) return;
      const t = this.ctx.currentTime;
      this.textureBus.gain.cancelScheduledValues(t);
      this.textureBus.gain.setValueAtTime(this.textureBus.gain.value, t);
      this.textureBus.gain.linearRampToValueAtTime(Math.max(0.0001, v), t + 0.4);
    }
    setTextureTarget(v) { this.texTarget = Math.max(0.0001, v); }
    setSpeed(s) { this.speed = s; }
    get currentIndex() { return this._index; }
  }

  global.ZenEngine = ZenEngine;
})(typeof window !== 'undefined' ? window : globalThis);
