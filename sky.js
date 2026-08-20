/*
 * sahaj | sky.js
 * =============
 * The background is the real sky where you are, computed rather than fetched.
 *
 * Sun position comes from the NOAA solar algorithm — latitude, longitude and
 * the clock give solar altitude to a fraction of a degree, no network needed.
 * Sky colour follows from that altitude, because that is what actually sets it:
 * light from a low sun travels far further through the atmosphere, Rayleigh
 * scattering strips the short wavelengths, and what reaches you is red.
 *
 * Cloud cover and precipitation come from the weather call the app already
 * makes. Cloud pulls the gradient toward grey and flattens it, because an
 * overcast sky is a diffuser — the sun stops being a direction and becomes
 * an even glow.
 *
 * This is more accurate than a photograph would be: it is this person's sky at
 * this minute, not a stock image of dusk. It also costs no bandwidth, works
 * with no connection, and keeps moving during a session — start at sunset and
 * the screen really does darken, because the sun really is going down.
 */

(function (global) {
  'use strict';

  const rad = Math.PI / 180, deg = 180 / Math.PI;

  /* NOAA solar position. Returns altitude in degrees above the horizon
   * (negative below), plus the fraction of the day elapsed. */
  function solarAltitude(lat, lon, date) {
    const d = date || new Date();
    const jd = d.getTime() / 86400000 + 2440587.5;
    const n = jd - 2451545.0;

    const L = (280.460 + 0.9856474 * n) % 360;                 // mean longitude
    const g = ((357.528 + 0.9856003 * n) % 360) * rad;         // mean anomaly
    const lambda = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * rad;
    const eps = (23.439 - 0.0000004 * n) * rad;                // obliquity

    const decl = Math.asin(Math.sin(eps) * Math.sin(lambda));
    let ra = Math.atan2(Math.cos(eps) * Math.sin(lambda), Math.cos(lambda)) * deg;
    if (ra < 0) ra += 360;

    const gmst = (18.697374558 + 24.06570982441908 * n) % 24;
    const lst = (gmst * 15 + lon + 360) % 360;
    let ha = (lst - ra + 540) % 360 - 180;

    const alt = Math.asin(
      Math.sin(lat * rad) * Math.sin(decl) +
      Math.cos(lat * rad) * Math.cos(decl) * Math.cos(ha * rad)
    ) * deg;

    return { altitude: alt, hourAngle: ha, declination: decl * deg };
  }

  const lerp = (a, b, t) => a + (b - a) * t;
  const mix = (c1, c2, t) => [
    Math.round(lerp(c1[0], c2[0], t)),
    Math.round(lerp(c1[1], c2[1], t)),
    Math.round(lerp(c1[2], c2[2], t)),
  ];
  const hex = c => '#' + c.map(v =>
    Math.max(0, Math.min(255, v)).toString(16).padStart(2, '0')).join('');

  /* Anchor skies at known solar altitudes. Each is [zenith, middle, horizon];
   * the horizon warms and the zenith darkens as the sun drops, which is the
   * visible consequence of a longer path through the atmosphere. */
  const ANCHORS = [
    { alt:  60, sky: [[ 22, 63,110], [ 55,116,159], [147,186,213]] }, // high sun
    { alt:  20, sky: [[ 25, 68,113], [ 62,124,163], [174,201,214]] },
    { alt:   6, sky: [[ 34, 60,105], [117,110,140], [226,168,124]] }, // golden
    { alt:   0, sky: [[ 29, 41, 84], [104, 74,110], [216,124, 92]] }, // sunset
    { alt:  -4, sky: [[ 23, 27, 62], [ 74, 52, 90], [184, 96, 84]] }, // civil
    { alt:  -8, sky: [[ 14, 18, 44], [ 44, 38, 74], [110, 66, 82]] }, // nautical
    { alt: -14, sky: [[  8, 11, 27], [ 18, 22, 46], [ 44, 40, 68]] },
    { alt: -20, sky: [[  5,  7, 13], [ 10, 15, 28], [ 22, 29, 48]] }, // night
  ];

  function anchorFor(alt) {
    if (alt >= ANCHORS[0].alt) return ANCHORS[0].sky;
    const last = ANCHORS[ANCHORS.length - 1];
    if (alt <= last.alt) return last.sky;
    for (let i = 0; i < ANCHORS.length - 1; i++) {
      const a = ANCHORS[i], b = ANCHORS[i + 1];
      if (alt <= a.alt && alt > b.alt) {
        const t = (a.alt - alt) / (a.alt - b.alt);
        return [mix(a.sky[0], b.sky[0], t),
                mix(a.sky[1], b.sky[1], t),
                mix(a.sky[2], b.sky[2], t)];
      }
    }
    return last.sky;
  }


  /* ── stars ─────────────────────────────────────────────────
   * The 56 brightest, by right ascension, declination and visual magnitude.
   * Real positions, so the pattern above Coventry in August really is the
   * Summer Triangle, and it really does rotate through a long session.
   * About 2KB — cheaper than any image of a night sky.  [RA°, Dec°, mag] */
  const STARS = [
    [101.29,-16.72,-1.46,'Sirius'],   [95.99,-52.70,-0.74,'Canopus'],
    [219.90,-60.83,-0.27,'Rigil Kent'],[213.92,19.18,-0.05,'Arcturus'],
    [279.23,38.78,0.03,'Vega'],       [79.17,45.99,0.08,'Capella'],
    [78.63,-8.20,0.13,'Rigel'],       [114.83,5.22,0.34,'Procyon'],
    [24.43,-57.24,0.46,'Achernar'],   [88.79,7.41,0.50,'Betelgeuse'],
    [210.96,-60.37,0.61,'Hadar'],     [297.70,8.87,0.77,'Altair'],
    [186.65,-63.10,0.77,'Acrux'],     [68.98,16.51,0.85,'Aldebaran'],
    [201.30,-11.16,1.04,'Spica'],     [247.35,-26.43,1.09,'Antares'],
    [116.33,28.03,1.14,'Pollux'],     [344.41,-29.62,1.16,'Fomalhaut'],
    [310.36,45.28,1.25,'Deneb'],      [191.93,-59.69,1.25,'Mimosa'],
    [152.09,11.97,1.35,'Regulus'],    [104.66,-28.97,1.50,'Adhara'],
    [113.65,31.89,1.58,'Castor'],     [187.79,-57.11,1.59,'Gacrux'],
    [263.40,-37.10,1.62,'Shaula'],    [81.28,6.35,1.64,'Bellatrix'],
    [81.57,28.61,1.65,'Elnath'],      [84.05,-1.20,1.69,'Alnilam'],
    [85.19,-1.94,1.74,'Alnitak'],     [332.06,-46.96,1.74,'Alnair'],
    [193.51,55.96,1.76,'Alioth'],     [165.93,61.75,1.79,'Dubhe'],
    [51.08,49.86,1.79,'Mirfak'],      [107.10,-26.39,1.83,'Wezen'],
    [276.04,-34.38,1.85,'Kaus Aust'], [206.89,49.31,1.86,'Alkaid'],
    [89.88,44.95,1.90,'Menkalinan'],  [99.43,16.40,1.93,'Alhena'],
    [95.67,-17.96,1.98,'Mirzam'],     [37.95,89.26,1.98,'Polaris'],
    [141.90,-8.66,1.98,'Alphard'],    [31.79,23.46,2.00,'Hamal'],
    [283.82,-26.30,2.05,'Nunki'],     [2.10,29.09,2.06,'Alpheratz'],
    [17.43,35.62,2.06,'Mirach'],      [86.94,-9.67,2.09,'Saiph'],
    [263.73,12.56,2.08,'Rasalhague'], [30.97,42.33,2.10,'Almach'],
    [177.26,14.57,2.14,'Denebola'],   [305.56,40.26,2.23,'Sadr'],
    [200.98,54.93,2.23,'Mizar'],      [10.13,56.54,2.24,'Schedar'],
    [269.15,51.49,2.24,'Eltanin'],    [2.29,59.15,2.28,'Caph'],
    [165.46,56.38,2.34,'Merak'],      [326.05,9.88,2.38,'Enif'],
  ];

  // how much sky a place actually has. The Nominatim call already tells us this.
  const DARKNESS = { urban: 0.28, suburban: 0.55, rural: 1.0, coastal: 0.9 };

  function localSiderealDeg(lon, date) {
    const jd = date.getTime() / 86400000 + 2440587.5;
    const n = jd - 2451545.0;
    const gmst = (18.697374558 + 24.06570982441908 * n) % 24;
    return (gmst * 15 + lon + 360) % 360;
  }

  /* Stars placed for a south-facing view: azimuth 120-240° across the width,
   * horizon to 85° up the height. opts as for sky(), plus place. */
  function stars(opts) {
    const o = opts || {};
    const lat = o.lat != null ? o.lat : 52.41;
    const lon = o.lon != null ? o.lon : -1.51;
    const date = o.date || new Date();
    const cloud = Math.max(0, Math.min(1, o.cloud || 0));
    const sun = solarAltitude(lat, lon, date).altitude;

    // nothing until civil twilight, full dark by -18°
    const night = Math.max(0, Math.min(1, (-sun - 6) / 12));
    if (night <= 0 || cloud > 0.95) return [];

    /* Attenuation, not a switch. The old exponent took half cloud down to 30%
     * — but broken cloud is exactly when you do see the bright ones, and in
     * England it is most nights. Overcast still means none. */
    const clear = Math.pow(1 - cloud, 1.15);
    const place = DARKNESS[o.place] != null ? DARKNESS[o.place] : 0.55;
    const limit = 1.9 + place * 3.2;         // faintest magnitude visible here
    const lst = localSiderealDeg(lon, date);
    const latR = lat * rad;

    const out = [];
    for (const [ra, dec, mag, name] of STARS) {
      if (mag > limit) continue;
      const decR = dec * rad;
      const ha = ((lst - ra + 540) % 360 - 180) * rad;
      const alt = Math.asin(Math.sin(decR) * Math.sin(latR) +
                            Math.cos(decR) * Math.cos(latR) * Math.cos(ha)) * deg;
      if (alt < 2) continue;                  // below or in the murk at the horizon
      let az = Math.atan2(-Math.sin(ha) * Math.cos(decR),
                          Math.cos(latR) * Math.sin(decR) -
                          Math.sin(latR) * Math.cos(decR) * Math.cos(ha)) * deg;
      az = (az + 360) % 360;
      if (az < 120 || az > 240) continue;     // outside a south-facing window

      // fainter stars fade first, and everything dims near the horizon
      const bright = Math.max(0, Math.min(1, (limit - mag) / 2.2));
      const horizon = Math.min(1, alt / 22);

      /* Scintillation: light from a low star crosses far more turbulent air,
       * which is why Sirius near the horizon flickers while Vega overhead sits
       * still. Airmass goes as 1/sin(altitude), so twinkle follows it — this is
       * the reason for the motion rather than an excuse for it. */
      const airmass = 1 / Math.max(0.09, Math.sin(alt * rad));
      const twinkle = Math.round(Math.min(0.42, (airmass - 1) * 0.085) * 100) / 100;

      out.push({
        name, mag, alt: Math.round(alt * 10) / 10, az: Math.round(az * 10) / 10,
        x: (az - 120) / 120,
        y: 1 - Math.min(1, alt / 85),
        // diameter in px — these are points of light, not discs
        size: Math.round((1.4 + (2.6 - Math.min(mag, 2.6)) * 1.15) * 10) / 10,
        opacity: Math.round(bright * night * clear * horizon * 0.9 * 100) / 100,
        twinkle,
        period: Math.round((2.6 + (mag + 1.5) * 0.9) * 10) / 10,   // seconds
        phase: Math.round(((ra * 7 + dec * 13) % 100) / 100 * 100) / 100,
      });
    }
    return out;
  }

  /* opts: { lat, lon, date, cloud (0-1), precip (0-1) } */
  function sky(opts) {
    const o = opts || {};
    const lat = o.lat != null ? o.lat : 52.41;    // Coventry, if we know nothing
    const lon = o.lon != null ? o.lon : -1.51;
    const { altitude } = solarAltitude(lat, lon, o.date);
    const cloud = Math.max(0, Math.min(1, o.cloud || 0));
    const precip = Math.max(0, Math.min(1, o.precip || 0));

    let stops = anchorFor(altitude).map(c => c.slice());

    /* Overcast is a diffuser: the sun stops being a direction. Pull every stop
     * toward a neutral grey of matching brightness, and flatten the spread
     * between them, which is what removes the sense of where the sun is. */
    if (cloud > 0) {
      const k = cloud * 0.78;
      stops = stops.map(c => {
        const lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
        const grey = [lum * 0.94, lum * 0.97, lum * 1.06];
        return mix(c, grey, k);
      });
      const mid = stops[1];
      stops = stops.map(c => mix(c, mid, cloud * 0.34));
    }
    if (precip > 0) stops = stops.map(c => mix(c, [26, 30, 36], precip * 0.42));

    // ink has to stay legible on whatever that produced
    const midLum = 0.2126 * stops[1][0] + 0.7152 * stops[1][1] + 0.0722 * stops[1][2];
    const light = midLum > 118;

    return {
      altitude: Math.round(altitude * 10) / 10,
      stops: stops.map(hex),
      css: `linear-gradient(178deg, ${hex(stops[0])} 0%, ${hex(stops[1])} 52%, ${hex(stops[2])} 100%)`,
      ink: light ? '#14161C' : '#F4F1E9',
      dim: light ? 'rgba(20,22,28,.62)' : 'rgba(244,241,233,.56)',
      faint: light ? 'rgba(20,22,28,.38)' : 'rgba(244,241,233,.30)',
      rule: light ? 'rgba(20,22,28,.16)' : 'rgba(244,241,233,.14)',
      isLight: light,
      phase: altitude > 12 ? 'day' : altitude > 0 ? 'golden'
           : altitude > -6 ? 'civil' : altitude > -12 ? 'nautical'
           : altitude > -18 ? 'astronomical' : 'night',
    };
  }

  /* Repaint slowly. The sky moves on the scale of minutes, so anything faster
   * is animation for its own sake — and during a session the change should be
   * something you notice afterwards, not while it happens. */
  function bind(el, opts, everyMs) {
    const paint = () => {
      const s = sky(Object.assign({}, opts, { date: new Date() }));
      el.style.background = s.css;
      el.style.setProperty('--ink', s.ink);
      el.style.setProperty('--dim', s.dim);
      el.style.setProperty('--faint', s.faint);
      el.style.setProperty('--rule', s.rule);
      return s;
    };
    const first = paint();
    const id = setInterval(paint, everyMs || 60000);
    return { stop: () => clearInterval(id), current: first };
  }

  /* Open-Meteo: free, no key, and it carries cloud cover, precipitation and
   * the sunrise/sunset times the tier boundaries want anyway. */
  async function weather(lat, lon) {
    const url = 'https://api.open-meteo.com/v1/forecast'
      + `?latitude=${lat.toFixed(3)}&longitude=${lon.toFixed(3)}`
      + '&current=cloud_cover,precipitation,weather_code'
      + '&daily=sunrise,sunset&timezone=auto&forecast_days=1';
    const r = await fetch(url);
    if (!r.ok) throw new Error('weather ' + r.status);
    const j = await r.json();
    return {
      cloud: (j.current.cloud_cover || 0) / 100,
      precip: Math.min(1, (j.current.precipitation || 0) / 2.5),
      code: j.current.weather_code,
      sunrise: j.daily.sunrise[0],
      sunset: j.daily.sunset[0],
    };
  }

  global.SAHAJ_SKY_BUILD = '2026-08-20a';
  global.SahajSky = { sky, stars, solarAltitude, localSiderealDeg, bind, weather, STARS };
})(typeof window !== 'undefined' ? window : globalThis);
