// Low-poly people, vehicles, kit and ships for the Ten Days map, built from boxes in code (no model
// files). Each model is one geometry with vertex colours and a per-vertex part id, so the page can
// draw a whole crowd of one kind with a single instanced mesh and swing legs, arms and flags in the
// vertex shader. Units: metres, y up, the model faces +z.
//
// Shapes follow photographs of Petrograd in 1917, and colours Reed's words or the few colour sources
// there are; docs/uniforms.md has the file behind each and says which colours are assumed. The
// soldier's long belted greatcoat, the rolled coat worn as a bandolier, a papakha light or dark or a
// peaked cap; the yunkers' "red shoulder-straps of the yunker-schools" (Reed); the Women's Battalion
// in light lambswool hats; Baltic sailors in black pea coats and peakless caps, some with machine-gun
// belts crossed on the chest (a period image, not one the photographs checked show on a sailor); Red
// Guards in workmen's clothes, with a red arm band that is the map's marker, not a documented one;
// the Don Cossack's red stripe on dark-blue trousers; peasants' foot-cloths and bast shoes; Reed's
// "elephant-coloured" armoured cars.
// Bundled into the page by tools/bundle.py, which inlines this file where app.html says so.
var PEOPLE = (function (THREE) {
  'use strict';
  var V3 = THREE.Vector3;
  var BOX = new THREE.BoxGeometry(1, 1, 1).toNonIndexed();
  var ICO = new THREE.IcosahedronGeometry(0.5, 1);   // already non-indexed
  var CYL = {}, TAPER = {};
  function cylGeo(seg) { return CYL[seg] || (CYL[seg] = new THREE.CylinderGeometry(0.5, 0.5, 1, seg, 1).toNonIndexed()); }
  // a box whose top and bottom differ: coat skirts, skirts, hulls
  function taperGeo(tx, tz, bx, bz) {
    var k = [tx, tz, bx, bz].join(',');
    if (TAPER[k]) return TAPER[k];
    var v = [[-bx, -0.5, -bz], [bx, -0.5, -bz], [bx, -0.5, bz], [-bx, -0.5, bz], [-tx, 0.5, -tz], [tx, 0.5, -tz], [tx, 0.5, tz], [-tx, 0.5, tz]];
    var f = [[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6], [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2], [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]];
    var P = [], N = [], a = new V3(), b = new V3(), c = new V3(), n = new V3(), m = new V3();
    f.forEach(function (t) {
      a.fromArray(v[t[0]]); b.fromArray(v[t[1]]); c.fromArray(v[t[2]]);
      n.subVectors(b, a).cross(m.subVectors(c, a)).normalize();
      if (n.dot(m.copy(a).add(b).add(c)) < 0) { var s = b.clone(); b.copy(c); c.copy(s); n.negate(); }
      P.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z); N.push(n.x, n.y, n.z, n.x, n.y, n.z, n.x, n.y, n.z);
    });
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3)); g.setAttribute('normal', new THREE.Float32BufferAttribute(N, 3));
    return (TAPER[k] = g);
  }

  var tm = new THREE.Matrix4(), tq = new THREE.Quaternion(), te = new THREE.Euler(), ts = new V3(), tp = new V3(), nm = new THREE.Matrix3();
  var cv = new V3(), cn = new V3();
  function Model() { this.p = []; this.n = []; this.c = []; this.a = []; }
  Model.prototype.put = function (geo, col, x, y, z, sx, sy, sz, rx, ry, rz, part) {
    tm.compose(tp.set(x, y, z), tq.setFromEuler(te.set(rx || 0, ry || 0, rz || 0, 'YXZ')), ts.set(sx, sy, sz));
    nm.getNormalMatrix(tm);
    // colours are written as seen (sRGB) and stored linear, so a navy coat renders navy, not slate
    var P = geo.attributes.position.array, N = geo.attributes.normal.array, c = (col instanceof THREE.Color ? col.clone() : new THREE.Color(col)).convertSRGBToLinear();
    for (var i = 0; i < P.length; i += 3) {
      cv.set(P[i], P[i + 1], P[i + 2]).applyMatrix4(tm); cn.set(N[i], N[i + 1], N[i + 2]).applyMatrix3(nm).normalize();
      this.p.push(cv.x, cv.y, cv.z); this.n.push(cn.x, cn.y, cn.z); this.c.push(c.r, c.g, c.b); this.a.push(part || 0);
    }
    return this;
  };
  // box: centre and size; cyl: centre, diameter, height (along y before rotation)
  Model.prototype.box = function (col, x, y, z, sx, sy, sz, rx, ry, rz, part) { return this.put(BOX, col, x, y, z, sx, sy, sz, rx, ry, rz, part); };
  Model.prototype.cyl = function (col, x, y, z, d, h, seg, rx, ry, rz, part, d2) { return this.put(cylGeo(seg || 8), col, x, y, z, d, h, d2 || d, rx, ry, rz, part); };
  Model.prototype.taper = function (col, x, y, z, tw, td, bw, bd, h, rx, ry, rz, part) { return this.put(taperGeo(tw / 2, td / 2, bw / 2, bd / 2), col, x, y, z, 1, h, 1, rx, ry, rz, part); };
  Model.prototype.ball = function (col, x, y, z, d, part, sy, sz) { return this.put(ICO, col, x, y, z, d, d * (sy || 1), d * (sz || 1), 0, 0, 0, part); };
  Model.prototype.geometry = function (scale) {
    var s = scale || 1, P = s === 1 ? this.p : this.p.map(function (v) { return v * s; });
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3));
    g.setAttribute('aPart', new THREE.Float32BufferAttribute(this.a, 1));
    g.computeBoundingSphere();
    return g;
  };

  // ---------- palette ----------
  var C = {
    skin: '#d8ae88', skin2: '#c99b74', boots: '#1d1a17', leather: '#4a3424', wood: '#4b3526', steel: '#9da3a8', brass: '#b08c3c',
    shinel: '#6f6a58', khaki: '#6b6848', yunker: '#66655f', officer: '#7a776d', navy: '#1b1f2b', red: '#a8261f', gold: '#c4a24a',
    black: '#161514', fur: '#2a2522', furGrey: '#5d5852', white: '#e6e1d4'
  };

  // ---------- people ----------
  // o: coat, len ('long' | 'mid' | 'short'), legs, hat, hatCol, band, rifle, skatka, belts, armband, boards,
  //    lampas, skirt, scarf, beard, notebook, sabre; pose: 'stand' (the default), and for a fight 'aim'
  //    (standing, the rifle at the shoulder), 'kneel' (kneeling to fire), 'charge' (running, bayonet
  //    first), 'prone' (flat on the face) or 'fallen' (on the back, the rifle dropped beside)
  function person(o) {
    var pose = o.pose || 'stand';
    if (pose === 'fallen' || pose === 'prone') return lieDown(person(Object.assign({}, o, { pose: 'stand', rifle: false, cane: false })), pose === 'fallen', o.rifle);
    var m = new Model(), coat = o.coat, legs = o.legs || coat, boots = o.boots || C.boots, skin = o.skin || C.skin;
    var kneel = pose === 'kneel' && !o.skirt && o.rifle, aim = (pose === 'aim' || pose === 'kneel') && o.rifle, charge = pose === 'charge' && o.rifle;
    var dy = kneel ? -0.38 : 0;   // kneeling, everything above the hips comes down
    // legs swing about the hip at y = 0.86 (parts 1, 2)
    if (kneel) {   // the left knee up, the right knee on the ground
      m.box(legs, -0.1, 0.49, 0.21, 0.15, 0.16, 0.46, 0, 0, 0, 1); m.box(legs, -0.1, 0.27, 0.44, 0.15, 0.44, 0.16, 0, 0, 0, 1);
      m.box(boots, -0.1, 0.07, 0.5, 0.165, 0.14, 0.26, 0, 0, 0, 1);
      m.box(legs, 0.1, 0.275, -0.02, 0.15, 0.44, 0.16, 0, 0, 0, 2); m.box(legs, 0.1, 0.09, -0.26, 0.15, 0.15, 0.42, 0, 0, 0, 2);
      m.box(boots, 0.1, 0.1, -0.52, 0.165, 0.2, 0.12, 0, 0, 0, 2);
    } else if (o.skirt) {
      m.taper(o.skirt, 0, 0.47, 0, 0.42, 0.3, 0.58, 0.46, 0.86, 0, 0, 0, 0);
      m.box(boots, -0.08, 0.04, 0.08, 0.12, 0.08, 0.2, 0, 0, 0, 1); m.box(boots, 0.08, 0.04, 0.08, 0.12, 0.08, 0.2, 0, 0, 0, 2);
    } else {
      var st = aim ? 0.09 : 0;   // firing, the left foot forward
      [-1, 1].forEach(function (sx, i) {
        m.box(legs, 0.1 * sx, 0.56, -st * sx, 0.15, 0.62, 0.17, 0, 0, 0, i + 1);
        m.box(boots, 0.1 * sx, 0.15, 0.025 - st * sx, 0.165, 0.3, 0.24, 0, 0, 0, i + 1);
        if (o.lampas) m.box(o.lampas, 0.178 * sx, 0.6, -st * sx, 0.012, 0.52, 0.05, 0, 0, 0, i + 1);
      });
    }
    // body
    m.box(coat, 0, 1.13 + dy, 0, 0.44, 0.56, 0.26);
    if (o.len === 'long') m.taper(coat, 0, 0.66 + dy, 0, 0.44, 0.27, 0.56, 0.36, 0.5);
    else if (o.len === 'mid') m.taper(coat, 0, 0.78 + dy, 0, 0.44, 0.27, 0.5, 0.32, 0.26);
    if (o.belt !== false) m.box(o.beltCol || C.leather, 0, 0.88 + dy, 0, 0.455, 0.055, 0.28);
    if (o.skatka) { m.box(o.skatka, 0.02, 1.13 + dy, 0.14, 0.11, 0.74, 0.09, 0, 0, 0.78); m.box(o.skatka, 0.02, 1.13 + dy, -0.14, 0.11, 0.74, 0.09, 0, 0, -0.78); }
    if (o.belts) { m.box(o.belts, 0, 1.13 + dy, 0.138, 0.05, 0.66, 0.02, 0, 0, 0.62); m.box(o.belts, 0, 1.13 + dy, 0.138, 0.05, 0.66, 0.02, 0, 0, -0.62); }
    if (o.sash) m.box(o.sash, 0, 0.9 + dy, 0, 0.47, 0.08, 0.29);
    if (o.collar) m.box(o.collar, 0, 1.41 + dy, -0.01, 0.4, 0.07, 0.27);
    if (o.boards) { m.box(o.boards, -0.17, 1.42 + dy, 0, 0.1, 0.025, 0.13); m.box(o.boards, 0.17, 1.42 + dy, 0, 0.1, 0.025, 0.13); }
    // arms swing about the shoulder at y = 1.38 (parts 3, 4); a rifle arm holds still
    var armR = o.rifle || o.notebook ? 0 : 4;
    if (aim) {   // the rifle at the right shoulder, the left hand under the fore-end, aiming along +z
      m.box(coat, 0.205, 1.37 + dy, 0.18, 0.12, 0.13, 0.4, 0, -0.35, 0); m.box(skin, 0.14, 1.37 + dy, 0.37, 0.09, 0.1, 0.1);
      m.box(coat, -0.105, 1.37 + dy, 0.275, 0.12, 0.13, 0.64, 0, 0.54, 0); m.box(skin, 0.06, 1.36 + dy, 0.56, 0.09, 0.1, 0.1);
      if (o.armband) m.box(o.armband, -0.21, 1.37 + dy, 0.1, 0.155, 0.155, 0.08, 0, 0.54, 0);
      m.box(C.wood, 0.12, 1.42 + dy, 0.55, 0.045, 0.07, 1.2); m.box(C.steel, 0.12, 1.43 + dy, 1.36, 0.012, 0.012, 0.42);
    } else if (charge) {   // running, the rifle slanted forward and up, bayonet first
      m.box(coat, 0.24, 1.19, -0.02, 0.12, 0.42, 0.14, 0.1, 0, 0.12); m.box(skin, 0.2, 0.98, -0.06, 0.09, 0.1, 0.1);
      m.box(coat, -0.085, 1.34, 0.275, 0.12, 0.13, 0.66, 0, 0.59, 0); m.box(skin, 0.1, 1.3, 0.55, 0.09, 0.1, 0.1);
      if (o.armband) m.box(o.armband, -0.2, 1.36, 0.1, 0.155, 0.155, 0.08, 0, 0.59, 0);
      m.box(C.wood, 0.15, 1.2, 0.4, 0.045, 0.07, 1.22, -0.43, 0, 0); m.box(C.steel, 0.085, 1.54, 1.14, 0.012, 0.012, 0.42, -0.43, 0, 0);
    } else {
      m.box(coat, -0.285, 1.1 + dy, 0, 0.12, 0.58, 0.14, 0, 0, -0.07, 3);
      m.box(skin, -0.31, 0.78 + dy, 0, 0.09, 0.1, 0.1, 0, 0, 0, 3);
      if (o.armband) m.box(o.armband, -0.29, 1.25 + dy, 0, 0.135, 0.08, 0.155, 0, 0, -0.07, 3);
    }
    if (aim || charge) { /* the arms are drawn above */ } else if (o.rifle) {
      m.box(coat, 0.27, 1.13, 0.07, 0.12, 0.5, 0.14, -0.35, 0, 0.05, 0);
      m.box(skin, 0.3, 0.92, 0.17, 0.09, 0.1, 0.1);
      m.box(C.wood, 0.31, 1.2, 0.18, 0.04, 1.28, 0.06); m.box(C.steel, 0.31, 2.02, 0.18, 0.012, 0.42, 0.012);
    } else {
      m.box(coat, 0.285, 1.1, 0, 0.12, 0.58, 0.14, 0, 0, 0.07, armR);
      m.box(skin, 0.31, 0.78, 0, 0.09, 0.1, 0.1, 0, 0, 0, armR);
      if (o.notebook) m.box(C.white, 0.33, 0.86, 0.09, 0.1, 0.14, 0.03, -0.3);
      if (o.cane) m.box(C.black, 0.33, 0.45, 0.04, 0.03, 0.8, 0.03, 0, 0, 0, armR);
    }
    if (o.sabre) m.box(C.steel, -0.25, 0.62 + dy, -0.06, 0.03, 0.8, 0.05, 0.25);
    // head
    var head = new Model();
    head.box(skin, 0, 1.45, 0, 0.12, 0.08, 0.12);
    head.ball(skin, 0, 1.6, 0.01, 0.26);
    if (o.beard) head.box(o.beard, 0, 1.52, 0.08, 0.2, 0.14, 0.1);
    hat(head, o, coat);
    if (o.scarfNeck) head.box(o.scarfNeck, 0, 1.4, 0.02, 0.3, 0.07, 0.3);
    for (var hi = 0; hi < head.p.length; hi += 3) { m.p.push(head.p[hi], head.p[hi + 1] + dy, head.p[hi + 2] + (aim ? 0.04 : 0)); m.n.push(head.n[hi], head.n[hi + 1], head.n[hi + 2]); }
    m.c.push.apply(m.c, head.c); m.a.push.apply(m.a, head.a);
    return m;
  }
  function hat(m, o, coat) {
    var hc = o.hatCol || coat;
    switch (o.hat) {
      case 'furazhka':   // peaked cap
        m.cyl(o.band || hc, 0, 1.685, 0, 0.255, 0.05, 12); m.cyl(hc, 0, 1.73, 0, 0.29, 0.05, 12);
        m.box(C.black, 0, 1.675, 0.12, 0.16, 0.02, 0.09, 0.25); break;
      case 'papakha':    // tall fur hat
        m.cyl(hc, 0, 1.75, 0, 0.27, 0.19, 10); break;
      case 'sailor':     // peakless cap with ribbons
        m.cyl(C.black, 0, 1.685, 0, 0.25, 0.05, 12); m.cyl(hc, 0, 1.725, 0, 0.31, 0.04, 12);
        m.box(C.black, -0.04, 1.57, -0.15, 0.03, 0.2, 0.01, 0.15); m.box(C.black, 0.04, 1.57, -0.15, 0.03, 0.2, 0.01, 0.15); break;
      case 'cap':        // workman's cap
        m.cyl(hc, 0, 1.7, -0.01, 0.28, 0.06, 10); m.box(hc, 0, 1.68, 0.12, 0.2, 0.025, 0.1, 0.2); break;
      case 'bowler':
        m.cyl(hc, 0, 1.68, 0, 0.36, 0.02, 14); m.cyl(hc, 0, 1.75, 0, 0.23, 0.12, 12); m.ball(hc, 0, 1.81, 0, 0.23, 0, 0.4); break;
      case 'fedora':
        m.cyl(hc, 0, 1.68, 0, 0.4, 0.02, 14); m.cyl(hc, 0, 1.75, 0, 0.23, 0.13, 10); m.cyl(o.band || C.black, 0, 1.71, 0, 0.235, 0.03, 10); break;
      case 'scarf':      // headscarf
        m.ball(hc, 0, 1.62, -0.015, 0.3, 0, 1, 1.05); m.box(hc, 0, 1.47, -0.1, 0.16, 0.12, 0.05, -0.3); break;
      case 'ladyhat':
        m.cyl(hc, 0, 1.69, 0, 0.5, 0.025, 16); m.cyl(hc, 0, 1.75, 0, 0.24, 0.1, 12); m.box(o.band || C.white, 0.08, 1.82, -0.04, 0.03, 0.16, 0.12, 0, 0, -0.4); break;
      case 'fur':        // peasant's fur hat
        m.cyl(hc, 0, 1.73, 0, 0.3, 0.14, 10); break;
    }
  }
  // a standing figure laid on the ground: on its back (up) or on its face, feet at the origin, and
  // a rifle, if it had one, dropped beside it. Nothing of it swings.
  function lieDown(m, up, rifle) {
    for (var i = 0; i < m.p.length; i += 3) {
      var y = m.p[i + 1], z = m.p[i + 2], ny = m.n[i + 1], nz = m.n[i + 2];
      if (up) { m.p[i + 1] = z + 0.15; m.p[i + 2] = -y; m.n[i + 1] = nz; m.n[i + 2] = -ny; }
      else { m.p[i + 1] = -z + 0.15; m.p[i + 2] = y; m.n[i + 1] = -nz; m.n[i + 2] = ny; }
    }
    for (var k = 0; k < m.a.length; k++) m.a[k] = 0;
    if (rifle) { m.box(C.wood, 0.5, 0.035, up ? -0.75 : 0.75, 0.045, 0.06, 1.28, 0, 0.12, 0); m.box(C.steel, 0.53, 0.035, up ? -1.55 : 1.55, 0.012, 0.012, 0.42, 0, 0.12, 0); }
    return m;
  }

  var FIG_OPTS = {
    soldier: ({ coat: C.shinel, len: 'long', hat: 'papakha', hatCol: C.furGrey, rifle: true, skatka: '#5c5747' }),
    soldier2: ({ coat: C.shinel, len: 'long', hat: 'furazhka', hatCol: C.khaki, rifle: true, skatka: '#5c5747' }),
    soldier3: ({ coat: C.shinel, len: 'long', hat: 'papakha', hatCol: '#8a8580', rifle: true }),
    yunker: ({ coat: C.yunker, len: 'long', hat: 'furazhka', hatCol: '#5a5a55', band: C.red, rifle: true, boards: C.red }),
    officer: ({ coat: C.officer, len: 'long', hat: 'furazhka', hatCol: '#62604f', band: C.red, boards: C.gold, sabre: true, beltCol: '#5a3d26' }),
    sailor: ({ coat: C.navy, len: 'short', hat: 'sailor', hatCol: '#141518', rifle: true, beltCol: C.black, collar: '#dcdde2' }),   // the striped vest at the neck
    sailor2: ({ coat: C.navy, len: 'mid', hat: 'sailor', hatCol: C.navy, rifle: true, belts: C.brass, beltCol: C.black }),
    redguard: ({ coat: '#2e2b27', len: 'mid', legs: '#24221f', hat: 'cap', hatCol: '#3b3732', rifle: true, armband: C.red, beltCol: C.leather }),
    redguard2: ({ coat: '#3a3833', len: 'short', legs: '#2a2825', hat: 'cap', hatCol: '#2d2b28', rifle: true, armband: C.red, skatka: '#4a4339' }),
    cossack: ({ coat: '#5f5b49', len: 'long', legs: '#252c42', hat: 'papakha', hatCol: C.fur, rifle: true, lampas: C.red, sabre: true }),
    womansoldier: ({ coat: C.shinel, len: 'long', hat: 'papakha', hatCol: '#cfcac0', rifle: true, skatka: '#5c5747' }),
    worker: ({ coat: '#4a443b', len: 'short', legs: '#2c2a27', hat: 'cap', hatCol: '#37332e' }),
    worker2: ({ coat: '#353531', len: 'mid', legs: '#272522', hat: 'cap', hatCol: '#454038', beard: '#4e3f30' }),
    workerwoman: ({ coat: '#5a4a40', len: 'short', skirt: '#35302d', hat: 'scarf', hatCol: '#a03a2c', belt: false }),
    workerwoman2: ({ coat: '#3f3f45', len: 'short', skirt: '#2c2a2a', hat: 'scarf', hatCol: '#d2cbbb', belt: false }),
    bourgeois: ({ coat: '#1e1d1c', len: 'long', legs: '#2f2f31', hat: 'bowler', hatCol: '#141414', collar: '#4e3b2d', belt: false, cane: true }),
    bourgeois2: ({ coat: '#2b2a2f', len: 'long', legs: '#25252a', hat: 'fedora', hatCol: '#3a3632', collar: '#5c4838', belt: false }),
    bourgeoiswoman: ({ coat: '#3b2b38', len: 'long', skirt: '#2d2530', hat: 'ladyhat', hatCol: '#1d1b1f', band: '#d6cdb9', collar: '#5a4636', belt: false }),
    intelligent: ({ coat: '#2d3340', len: 'long', legs: '#262a33', hat: 'furazhka', hatCol: '#22293b', band: '#6f8fb8', belt: false }),
    peasant: ({ coat: '#7b6d5a', len: 'long', legs: '#c2b79c', boots: '#a88e5c', hat: 'fur', hatCol: '#56473a', beard: '#6b5944', sash: '#9b2a20', belt: false }),   // foot-cloths, bast shoes
    child: ({ coat: '#4a443b', len: 'short', legs: '#2c2a27', hat: 'cap', hatCol: '#37332e', belt: false }),
    reed: ({ coat: '#25221f', len: 'long', legs: '#1f1d1b', hat: 'fedora', hatCol: '#2a2724', band: '#111', belt: false, notebook: true, scarfNeck: '#cfc7b4' })
  };
  var FIG = {};
  Object.keys(FIG_OPTS).forEach(function (k) { FIG[k] = person(FIG_OPTS[k]); });
  // where a rifle's muzzle is, in each firing pose (model metres, facing +z)
  var MUZZLE = { aim: [0.12, 1.42, 1.15], kneel: [0.12, 1.04, 1.15], charge: [0.09, 1.5, 1.02] };
  var POSED = {};
  // a figure type in a pose, built the first time it is asked for: 'soldier.aim', 'redguard.fallen'
  function posed(key) {
    if (POSED[key]) return POSED[key];
    var p = key.split('.'), o = FIG_OPTS[p[0]];
    if (!o) return null;
    return (POSED[key] = person(Object.assign({}, o, { pose: p[1] })).geometry(FIG_SCALE[p[0]] || 1));
  }
  var FIG_SCALE = { womansoldier: 0.94, workerwoman: 0.94, workerwoman2: 0.94, bourgeoiswoman: 0.95, child: 0.62 };
  // a type's variants, so a body of men is not a row of clones
  var VARIANTS = { soldier: ['soldier', 'soldier2', 'soldier3'], sailor: ['sailor', 'sailor2'], redguard: ['redguard', 'redguard2'], worker: ['worker', 'worker2'],
    workerwoman: ['workerwoman', 'workerwoman2'], bourgeois: ['bourgeois', 'bourgeois2'] };

  // ---------- animals and vehicles ----------
  function horse(col, rider) {
    var m = new Model(), dark = new THREE.Color(col).multiplyScalar(0.55);
    m.box(col, 0, 1.25, 0, 0.52, 0.55, 1.45);
    m.box(col, 0, 1.62, 0.78, 0.3, 0.6, 0.34, -0.55); m.box(col, 0, 1.86, 1.02, 0.24, 0.24, 0.5, 0.35);
    m.box(dark, 0, 1.65, 0.68, 0.06, 0.5, 0.3, -0.55);
    m.box(dark, 0, 1.15, -0.8, 0.08, 0.55, 0.08, 0.35);
    [[-0.17, 0.55, 1], [0.17, 0.55, 2], [-0.17, -0.55, 2], [0.17, -0.55, 1]].forEach(function (l) {
      m.box(col, l[0], 0.5, l[1], 0.12, 1.0, 0.14, 0, 0, 0, l[2]); m.box(C.black, l[0], 0.04, l[1], 0.13, 0.08, 0.15, 0, 0, 0, l[2]);
    });
    if (rider) {
      var r = rider;
      m.box(r.coat, 0, 1.88, -0.05, 0.42, 0.56, 0.26); m.box(r.legs || r.coat, -0.25, 1.45, 0.05, 0.13, 0.5, 0.2, 0.2); m.box(r.legs || r.coat, 0.25, 1.45, 0.05, 0.13, 0.5, 0.2, 0.2);
      if (r.lampas) { m.box(r.lampas, -0.32, 1.45, 0.05, 0.01, 0.45, 0.05, 0.2); m.box(r.lampas, 0.32, 1.45, 0.05, 0.01, 0.45, 0.05, 0.2); }
      m.box(r.coat, -0.28, 1.86, 0.08, 0.11, 0.5, 0.13, -0.5); m.box(r.coat, 0.28, 1.86, 0.08, 0.11, 0.5, 0.13, -0.5);
      m.ball(C.skin, 0, 2.33, -0.04, 0.26); m.cyl(r.hat, 0, 2.48, -0.04, 0.27, 0.18, 10);
      if (r.lance) m.box(C.wood, 0.34, 2.3, 0.1, 0.035, 3.2, 0.035, 0.12);
      else m.box(C.wood, 0.3, 2.05, -0.2, 0.04, 1.1, 0.06, 0.5);
    }
    return m;
  }
  function wheel(m, col, x, y, z, d, w) { m.cyl(col, x, y, z, d, w, 14, 0, 0, Math.PI / 2); m.cyl('#3a3530', x, y, z, d * 0.35, w * 1.3, 8, 0, 0, Math.PI / 2); }
  function armoured(col) {   // an Austin, the commonest in Petrograd: two turrets side by side
    var m = new Model(), dk = new THREE.Color(col).multiplyScalar(0.7);
    m.box(col, 0, 1.3, -0.55, 1.95, 1.55, 3.1);
    m.taper(col, 0, 1.1, 1.45, 1.5, 0.9, 1.75, 1.05, 1.0, Math.PI / 2, 0, 0);
    m.box(dk, 0, 1.55, 0.95, 1.7, 0.08, 0.5, -0.5);
    [-0.52, 0.52].forEach(function (x) { m.cyl(col, x, 2.36, -1.05, 0.95, 0.6, 12); m.cyl('#26241f', x, 2.38, -0.4, 0.09, 0.8, 6, Math.PI / 2, 0, 0); });
    [[-1.02, 1.35], [1.02, 1.35], [-1.02, -1.45], [1.02, -1.45]].forEach(function (w) { wheel(m, '#1f1e1c', w[0], 0.47, w[1], 0.94, 0.24); });
    m.box(dk, 0, 0.62, -0.1, 2.2, 0.08, 4.4);
    return m;
  }
  function truck(col) {
    var m = new Model(), dk = new THREE.Color(col).multiplyScalar(0.75);
    m.box(col, 0, 1.05, 1.75, 1.3, 0.75, 1.1); m.box(dk, 0, 1.75, 0.95, 1.6, 1.25, 0.9); m.box('#1a1a1a', 0, 2.15, 1.42, 1.4, 0.35, 0.04);
    m.box(col, 0, 0.95, -1.05, 2.0, 0.12, 3.3);
    [-1, 1].forEach(function (s) { m.box(dk, 0.99 * s, 1.2, -1.05, 0.06, 0.45, 3.3); });
    m.box(dk, 0, 1.2, -2.68, 2.0, 0.45, 0.06);
    [[-0.85, 1.75], [0.85, 1.75], [-0.85, -1.6], [0.85, -1.6]].forEach(function (w) { wheel(m, '#1c1b1a', w[0], 0.48, w[1], 0.95, 0.22); });
    return m;
  }
  function car(col) {
    var m = new Model(), dk = new THREE.Color(col).multiplyScalar(0.6);
    m.box(col, 0, 0.95, -0.3, 1.5, 0.55, 2.6); m.box(col, 0, 0.95, 1.45, 1.1, 0.5, 1.0);
    m.box('#3b2c20', 0, 1.3, -0.65, 1.3, 0.4, 0.5); m.box('#3b2c20', 0, 1.25, 0.25, 1.3, 0.3, 0.45);
    m.box('#9fb0b8', 0, 1.45, 0.75, 1.3, 0.45, 0.03, -0.15);
    [-1, 1].forEach(function (s) { m.box(dk, 0.8 * s, 0.7, 0.3, 0.25, 0.06, 3.8); });
    m.box('#d8c98a', -0.42, 1.05, 2.0, 0.18, 0.18, 0.06); m.box('#d8c98a', 0.42, 1.05, 2.0, 0.18, 0.18, 0.06);
    [[-0.78, 1.3], [0.78, 1.3], [-0.78, -1.2], [0.78, -1.2]].forEach(function (w) { wheel(m, '#1c1b1a', w[0], 0.42, w[1], 0.84, 0.14); });
    return m;
  }
  function fieldGun(col) {   // the 3-inch, Reed's "three-inch field-gun"
    var m = new Model();
    wheel(m, '#3d3226', -0.72, 0.68, 0, 1.36, 0.1); wheel(m, '#3d3226', 0.72, 0.68, 0, 1.36, 0.1);
    m.cyl(col, 0, 0.68, 0, 0.12, 1.5, 6, 0, 0, Math.PI / 2);
    m.box(col, 0, 1.05, 0.25, 1.35, 1.0, 0.05, -0.12);
    m.cyl(col, 0, 1.0, 0.75, 0.14, 2.3, 8, Math.PI / 2 - 0.08, 0, 0);
    m.box(col, 0, 0.42, -1.25, 0.2, 0.16, 2.5, -0.27);
    return m;
  }
  function maxim(col) {      // a Maxim on its Sokolov carriage
    var m = new Model();
    wheel(m, '#2c2925', -0.3, 0.24, -0.15, 0.48, 0.06); wheel(m, '#2c2925', 0.3, 0.24, -0.15, 0.48, 0.06);
    m.box(col, 0, 0.5, -0.1, 0.5, 0.08, 0.7); m.box(col, 0, 0.62, 0.05, 0.16, 0.18, 0.62);
    m.cyl(col, 0, 0.64, 0.55, 0.11, 0.55, 8, Math.PI / 2, 0, 0); m.box(col, 0, 0.72, 0.3, 0.55, 0.5, 0.03, -0.1);
    m.box(C.brass, 0.14, 0.55, 0.05, 0.05, 0.25, 0.4, 0, 0, 0.6);
    return m;
  }
  function cab() {           // an izvozchik: droshky, horse and driver
    var m = horse('#4a3424');
    var d = new Model();
    d.p = m.p.slice(); d.n = m.n.slice(); d.c = m.c.slice(); d.a = m.a.slice();
    d.box('#1e1c1b', 0, 0.85, -1.9, 1.1, 0.35, 1.6); d.box('#2b2622', 0, 1.15, -2.3, 1.0, 0.45, 0.5);
    wheel(d, '#2a221b', -0.62, 0.42, -1.4, 0.84, 0.06); wheel(d, '#2a221b', 0.62, 0.42, -1.4, 0.84, 0.06);
    wheel(d, '#2a221b', -0.62, 0.48, -2.45, 0.96, 0.06); wheel(d, '#2a221b', 0.62, 0.48, -2.45, 0.96, 0.06);
    d.box('#26314a', 0, 1.45, -1.45, 0.62, 0.7, 0.55); d.ball(C.skin, 0, 1.98, -1.45, 0.26); d.cyl('#1e1c1b', 0, 2.13, -1.45, 0.3, 0.12, 10);
    return d;
  }
  function tram() {
    var m = new Model();
    m.box('#8a2f27', 0, 1.25, 0, 2.3, 1.2, 9.0); m.box('#d8cfae', 0, 2.25, 0, 2.3, 0.8, 9.0);
    for (var z = -3.6; z <= 3.6; z += 1.2) { m.box('#3a4450', 1.16, 2.25, z, 0.02, 0.6, 0.85); m.box('#3a4450', -1.16, 2.25, z, 0.02, 0.6, 0.85); }
    m.box('#3b3a38', 0, 2.75, 0, 2.2, 0.2, 9.2); m.box('#2c2b29', 0, 3.6, 1.5, 0.05, 0.05, 3.4, 0.45);
    wheel(m, '#1c1b1a', -0.8, 0.35, 2.2, 0.7, 0.12); wheel(m, '#1c1b1a', 0.8, 0.35, 2.2, 0.7, 0.12);
    wheel(m, '#1c1b1a', -0.8, 0.35, -2.2, 0.7, 0.12); wheel(m, '#1c1b1a', 0.8, 0.35, -2.2, 0.7, 0.12);
    return m;
  }
  function bicycle() {
    var m = new Model();
    wheel(m, '#1c1b1a', 0, 0.34, 0.55, 0.68, 0.04); wheel(m, '#1c1b1a', 0, 0.34, -0.55, 0.68, 0.04);
    m.box('#2d3a2e', 0, 0.62, 0, 0.04, 0.05, 1.0, 0.25); m.box('#2d3a2e', 0, 0.55, 0.4, 0.04, 0.5, 0.04, 0.4); m.box('#1a1a1a', 0, 0.9, -0.25, 0.1, 0.04, 0.22);
    m.box('#2d3a2e', 0, 0.95, 0.5, 0.5, 0.03, 0.03);
    return m;
  }
  function barricade(seed) {
    var m = new Model(), r = function (i) { var x = Math.sin(seed * 91.7 + i * 12.9) * 43758.5; return x - Math.floor(x); };
    for (var i = 0; i < 9; i++) {
      var x = (r(i) - 0.5) * 5.6, z = (r(i + 20) - 0.5) * 0.9, t = r(i + 40);
      if (t < 0.4) m.box(t < 0.2 ? '#6b5236' : '#7a6a52', x, 0.35 + r(i + 60) * 0.5, z, 0.7 + r(i + 7) * 0.4, 0.6, 0.6, 0, r(i + 3) * 0.6, 0);
      else if (t < 0.7) m.cyl('#5b4632', x, 0.45, z, 0.6, 0.85, 10);
      else m.cyl('#7d6243', x, 0.25 + r(i + 5) * 0.7, z, 0.26, 2.4, 6, 0, r(i + 9) * 1.2, Math.PI / 2);
    }
    m.box('#5a4a38', 0, 0.2, 0, 5.8, 0.4, 1.3);
    return m;
  }
  function rifleHeap() {     // rifles thrown down in a heap ("a heap of rifles thrown down by the yunkers")
    var m = new Model(), r = function (i) { var x = Math.sin(i * 78.233 + 12.9) * 43758.5; return x - Math.floor(x); };
    for (var i = 0; i < 16; i++) {
      var a = r(i) * Math.PI * 2, x = (r(i + 20) - 0.5) * 1.3, z = (r(i + 40) - 0.5) * 1.3, y = 0.04 + (i % 5) * 0.055, tilt = (r(i + 60) - 0.5) * 0.3;
      m.box(C.wood, x, y, z, 0.07, 0.06, 1.25, tilt, a, 0);
      m.box('#2a2b2c', x + Math.sin(a) * 0.58, y + 0.012, z + Math.cos(a) * 0.58, 0.028, 0.028, 0.45, tilt, a, 0);
    }
    return m;
  }
  function fireLogs() {
    var m = new Model();
    for (var i = 0; i < 5; i++) m.cyl('#3a2a1c', 0, 0.12, 0, 0.12, 1.1, 6, Math.PI / 2, i * 1.26, 0.18);
    m.cyl('#2a2523', 0, 0.03, 0, 1.3, 0.06, 12);
    return m;
  }
  function flag(col, w, h, pole) {   // cloth is part 5, so it waves
    var m = new Model();
    m.box(C.wood, 0, pole / 2, 0, 0.04, pole, 0.04);
    var nx = 6, ny = 3;
    for (var i = 0; i < nx; i++) for (var j = 0; j < ny; j++)
      m.box(col, 0.02 + (i + 0.5) * w / nx, pole - 0.06 - (j + 0.5) * h / ny, 0, w / nx * 1.02, h / ny * 1.02, 0.015, 0, 0, 0, 5);
    return m;
  }
  function banner(col) {             // a banner on two poles, carried
    var m = new Model();
    m.box(C.wood, -1.0, 1.4, 0, 0.04, 2.8, 0.04); m.box(C.wood, 1.0, 1.4, 0, 0.04, 2.8, 0.04);
    for (var i = 0; i < 8; i++) m.box(col, -0.95 + (i + 0.5) * 1.9 / 8, 2.35, 0, 1.9 / 8 * 1.02, 0.7, 0.015, 0, 0, 0, 5);
    return m;
  }
  function torch() { var m = new Model(); m.box(C.wood, 0, 1.25, 0, 0.04, 1.0, 0.04); m.cyl('#3a2a1c', 0, 1.78, 0, 0.09, 0.12, 6); return m; }

  // the cruiser Aurora, at her real size (126.8 m by 16.8 m): three funnels, two masts
  function avrora() {
    var m = new Model(), hull = '#7b8084', hull2 = '#6c7175', deck = '#8f8068', fun = '#80858a';   // grey overall, as in the photographs of 1909-14
    var L = 126.8, B = 16.8, segs = 16;
    for (var i = 0; i < segs; i++) {
      var z0 = -L / 2 + i * L / segs, z1 = z0 + L / segs, zm = (z0 + z1) / 2, u = (zm + L / 2) / L;
      var w = B * (u > 0.78 ? Math.max(0.12, (1 - u) / 0.22) : u < 0.1 ? 0.72 + u * 2.8 : 1);
      m.taper(hull, 0, 3.0, zm, w, L / segs * 1.02, w * 0.86, L / segs * 1.02, 6.0);
      m.box('#5a2620', 0, 0.2, zm, w * 0.86, 0.6, L / segs * 1.02);
      m.box(deck, 0, 6.05, zm, w * 0.96, 0.12, L / segs * 1.02);
    }
    m.box(hull2, 0, 8.0, 34, 9, 4, 12); m.box(hull2, 0, 10.5, 36, 6, 2, 6); m.box('#3f4447', 0, 12.0, 36, 4, 1, 4);
    m.box(hull2, 0, 7.5, -36, 7, 3, 10);
    [14, 0, -14].forEach(function (z) { m.cyl(fun, 0, 15, z, 3.4, 18, 14, 0, 0, 0, 0, 2.6); m.cyl('#1e1f20', 0, 24.2, z, 3.5, 1.2, 14, 0, 0, 0, 0, 2.7); });
    m.cyl('#3a3a38', 0, 22, 44, 0.7, 34, 6); m.box('#3a3a38', 0, 30, 44, 10, 0.3, 0.3);
    m.cyl('#3a3a38', 0, 20, -44, 0.6, 30, 6); m.box('#3a3a38', 0, 27, -44, 8, 0.3, 0.3);
    for (var g = -3; g <= 3; g++) { [-1, 1].forEach(function (s) { m.box('#3a3d40', s * 7.6, 7.0, g * 12, 1.4, 1.4, 1.8); m.cyl('#2e3133', s * 9.0, 7.0, g * 12, 0.3, 3.5, 6, 0, 0, Math.PI / 2); }); }
    m.box('#3a3d40', 0, 7.2, 50, 2.4, 1.6, 3); m.cyl('#2e3133', 0, 7.3, 54, 0.35, 4.5, 6, Math.PI / 2, 0, 0);
    m.box('#3a3d40', 0, 7.2, -54, 2.4, 1.6, 3); m.cyl('#2e3133', 0, 7.3, -58, 0.35, 4.5, 6, Math.PI / 2, 0, 0);
    [-22, -8, 8, 22].forEach(function (z) { m.box('#d9d4c6', 6.2, 8.6, z, 1.6, 1.0, 6); m.box('#d9d4c6', -6.2, 8.6, z, 1.6, 1.0, 6); });
    return m;
  }

  function build() {
    var out = { fig: {}, kit: {}, figScale: FIG_SCALE, variants: VARIANTS, muzzle: MUZZLE, armed: {} };
    Object.keys(FIG_OPTS).forEach(function (k) { if (FIG_OPTS[k].rifle) out.armed[k] = true; });
    Object.keys(FIG).forEach(function (k) { out.fig[k] = FIG[k].geometry(FIG_SCALE[k] || 1); });
    out.kit = {
      armoured: armoured('#77746a').geometry(), truck: truck('#5d5b47').geometry(), car: car('#1d1d1f').geometry(),
      gun: fieldGun('#4d5242').geometry(), mg: maxim('#3c3f36').geometry(), cab: cab().geometry(), tram: tram().geometry(),
      bicycle: bicycle().geometry(), barricade: barricade(1).geometry(), barricade2: barricade(2).geometry(),
      logs: fireLogs().geometry(), rifles: rifleHeap().geometry(), whiteflag: flag('#efece3', 1.0, 0.65, 2.6).geometry(), flag: flag('#b3261e', 1.0, 0.65, 2.6).geometry(), banner: banner('#a8241c').geometry(),
      torch: torch().geometry(), horse: horse('#5a3f2a').geometry(), horse2: horse('#3a2c22').geometry(),
      cavalry: horse('#4e3826', { coat: '#5f5b49', legs: '#252c42', lampas: C.red, hat: C.fur }).geometry(),
      avrora: avrora().geometry()
    };
    return out;
  }

  // The shared material: Lambert with vertex colours, plus a vertex hook. Per instance, aAnim is
  // (phase, walk amount, idle amount): legs and arms swing when walking, a crowd turns its heads a
  // little, flags wave whatever happens.
  function material(uniforms) {
    var mat = new THREE.MeshLambertMaterial({ vertexColors: true });
    mat.onBeforeCompile = function (sh) {
      sh.uniforms.uTime = uniforms.uTime;
      sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float aPart;\nattribute vec3 aAnim;\nuniform float uTime;')
        .replace('#include <begin_vertex>', [
          '#include <begin_vertex>',
          'float sw = sin(uTime * 6.5 + aAnim.x) * aAnim.y;',
          'if (aPart > 0.5 && aPart < 2.5) { float a = (aPart < 1.5 ? sw : -sw) * 0.55; float yy = transformed.y - 0.86;',
          '  transformed.y = 0.86 + yy * cos(a) - transformed.z * sin(a); transformed.z = yy * sin(a) + transformed.z * cos(a); }',
          'else if (aPart > 2.5 && aPart < 4.5) { float a = (aPart < 3.5 ? -sw : sw) * 0.5; float yy = transformed.y - 1.38;',
          '  transformed.y = 1.38 + yy * cos(a) - transformed.z * sin(a); transformed.z = yy * sin(a) + transformed.z * cos(a); }',
          'else if (aPart > 4.5) { transformed.z += sin(uTime * 4.0 + transformed.x * 3.5 + aAnim.x) * 0.09 * (0.2 + abs(transformed.x)); }',
          'if (aPart < 4.5) { float t = sin(uTime * 0.6 + aAnim.x * 1.7) * 0.35 * aAnim.z; float cx = cos(t), sx = sin(t);',
          '  transformed.xz = vec2(transformed.x * cx + transformed.z * sx, -transformed.x * sx + transformed.z * cx); }',
          'transformed.y += abs(sw) * 0.04;'
        ].join('\n'));
    };
    return mat;
  }

  return { build: build, material: material, posed: posed };
})(THREE);
