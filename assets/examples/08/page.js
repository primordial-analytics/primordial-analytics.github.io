/* Example 08: open enrollment site planner. Plain ES2019, no build step.
   Reads data.json (national numbers, the sites comparison) and one state-<FIPS>.json per state (tracts, counties, venues as
   parallel arrays), both written by analysis/08-open-enrollment-site-planner/web_data.py. The planner runs the same reach rule
   as sites.py: a site reaches a tract with weight exp(-2 (d / R)^2) up to R miles, d = straight-line miles x 1.3; a tract's share
   is the sum over sites capped at 1; sites are added one at a time, each the one that adds the most reach. */
Ex.ready(function () {
  "use strict";
  var F = Ex.fmt;
  var $ = function (id) {
    return document.getElementById(id);
  };
  var BASE = (($("main") || document.body).getAttribute("data-ex-data") || "").replace(/data\.json$/, "");
  var TIERS = ["kids", "medicaid", "subsidy", "gap", "d400", "noncit"];
  var NAME = { kids: "Children", medicaid: "Medicaid range", subsidy: "Subsidy range", gap: "Coverage gap", d400: "400% and over", noncit: "Noncitizen adults" };
  var DEFAULT_ON = { kids: 1, medicaid: 1, subsidy: 1, gap: 0, d400: 0 };
  var CIRC = 1.3, Z90 = 1.645, EARTH = 3958.8, POPUP = 150, MIN_DEN = 100;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var XLSX_SRC = "https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.mini.min.js";
  var XLSX_SRI = "sha512-NDQhXrK2pOCL18FV5/Nc+ya9Vz+7o8dJV1IGRwuuYuRMFhAR0allmjWdZCSHFLDYgMvXKyN2jXlSy2JJEmq+ZA==";
  var DERIVED = { limit_weight_pct: 100 * Math.exp(-2) };

  Ex.loadData().then(init, function () {
    ["chart-map", "chart-tracts", "chart-sites"].forEach(function (id) {
      if ($(id)) Ex.showError($(id), "The data did not load. The downloads below have the same numbers.");
    });
  });

  /* ---------- small helpers ---------- */
  function get(D, path) {
    if (path.indexOf("derived.") === 0) return DERIVED[path.slice(8)];
    return path.split(".").reduce(function (o, p) {
      return o == null ? o : o[p];
    }, D);
  }
  function fmtBy(code, v) {
    switch (code) {
      case "int": return F.int(v);
      case "pct0": return F.pctValue(v, 0);
      case "pct1": return F.pctValue(v, 1);
      case "pct0n": return F.num(v, 0);
      case "fpct0": return F.pct(v, 0);
      case "mil": return F.approx(v, 3);
      case "signed0": return F.signed(v, 0);
      default: return String(v);
    }
  }
  function a3(v) {
    return F.approx(v, 3);
  }
  function tractName(code) {
    return String(parseInt(code.slice(0, 4), 10)) + "." + code.slice(4);
  }
  function safeUrl(u) {
    return /^https:\/\//.test(u) ? u : "#";
  }
  function link(href, text) {
    return Ex.el("a", { href: safeUrl(href), text: text || href });
  }
  function dateText(iso) {
    var p = iso.split("-");
    return MONTHS[+p[1] - 1] + " " + +p[2];
  }
  function csvCell(v) {
    if (v == null) return "";
    var s = String(v);
    if (/^[=+\-@\t\r]/.test(s) && isNaN(+s)) s = "'" + s; // a name cannot run as a formula in a spreadsheet
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }
  function download(name, type, parts) {
    var url = URL.createObjectURL(new Blob(parts, { type: type }));
    var a = Ex.el("a", { href: url, download: name });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 4000);
  }
  function median(a) {
    var s = a.slice().sort(function (x, y) { return x - y; });
    return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : 0;
  }
  function quant(sorted, q) {
    var p = (sorted.length - 1) * q, lo = Math.floor(p), hi = Math.ceil(p);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (p - lo);
  }

  function init(D) {
    var N = D.numbers, FA = D.facts, SCALE = N.validation.D_simulation.tract_interval_scale;
    var STATES = D.states, byAbbr = {};
    STATES.forEach(function (s) { byAbbr[s.abbr] = s; });
    var oe = FA.open_enrollment;

    /* ---------- numbers written into the text from data.json ---------- */
    [].forEach.call(document.querySelectorAll("[data-n]"), function (el) {
      var v = get(D, el.getAttribute("data-n"));
      if (v != null && !isNaN(v)) el.textContent = fmtBy(el.getAttribute("data-f"), v);
    });
    fillMethodLists();

    /* ---------- state of the tool ---------- */
    var staff0 = N.example_county.staff;
    function ownMarket() {
      return cur.st && cur.st.own_marketplace;
    }
    function datesText() {
      return ownMarket() ? cur.st.name + " " + oe.state_text : oe.text;
    }
    function renderDates() {
      var el = $("cal-line");
      var t = datesText(), i = ownMarket() ? t.indexOf("its own dates") : -1;
      el.textContent = i < 0 ? t : t.slice(0, i);
      if (i >= 0) {
        el.appendChild(link(FA.state_marketplaces.find, "its own dates"));
        el.appendChild(document.createTextNode(t.slice(i + 13)));
      }
    }
    function area(zip) {
      if (!zip) return "";
      var c = cur.st && cur.st.zip_city && cur.st.zip_city[zip];
      return c ? c + " (" + zip + ")" : "ZIP " + zip;
    }
    var S = fresh();
    var cur = { st: null, abbr: null, V: null, token: 0, plan: null };
    function fresh() {
      return { k: 5, on: { kids: 1, medicaid: 1, subsidy: 1, gap: 0, d400: 0 }, nc: 0, scen: 0, mode: "venue", miles: null, fixed: [],
               staff: { p: staff0.people, apd: staff0.appointments_per_day, dpw: staff0.days_per_week }, weeks: weeksLeft().weeks };
    }
    function weeksLeft() {
      var now = new Date(), start = new Date(oe.start + "T00:00:00"), d1 = new Date(oe.deadline_jan1_coverage + "T00:00:00"), end = new Date(oe.end + "T00:00:00");
      var from = now > start ? now : start;
      var to = from <= d1 ? d1 : end;
      var iso = from <= d1 ? oe.deadline_jan1_coverage : oe.end;
      return { weeks: now > end ? 0 : Math.max(1, Math.round((to - from) / 6048e5)), date: now > end ? "" : dateText(iso) };
    }

    /* ---------- county outlines (shared us-atlas file, already projected in Albers) ---------- */
    var OUT = { county: {} };
    var proj = Ex.merc; // Web Mercator, to sit on the street tiles
    var albers = d3.geoAlbersUsa().scale(1300).translate([487.5, 305]);
    function toMerc(k, tx, ty) {
      return d3.geoTransform({ point: function (x, y) { var q = proj(albers.invert([x, y])); this.stream.point(q[0] * k + tx, q[1] * k + ty); } });
    }
    Ex.loadData(Ex.assetUrl("us-counties-albers-10m.json")).then(function (topo) {
      topojson.feature(topo, topo.objects.counties).features.forEach(function (f) { OUT.county[f.id] = f; });
      if (mapChart) mapChart.redraw();
    }, function () {});

    /* ---------- pickers ---------- */
    var stateCombo = Ex.combobox($("pick-state"), {
      id: "state", label: "State", placeholder: "Search states", noun: "states", noun_one: "state",
      items: STATES.map(function (s) { return { value: s.abbr, label: s.name, hint: s.abbr }; }),
      onSelect: function (it) { if (it) show(it.value, null); },
    });
    var countyCombo = Ex.combobox($("pick-county"), {
      id: "county", label: "County", placeholder: "Search counties", noun: "counties", noun_one: "county", items: [],
      onSelect: function (it) { if (it) show(cur.abbr, it.value); },
    });
    var existingCombo = Ex.combobox($("pick-existing"), {
      id: "existing", label: "Sites you already use", placeholder: "Search this county's venues", noun: "venues", noun_one: "venue", items: [],
      onSelect: function (it) {
        if (!it) return;
        var j = +it.value;
        if (S.fixed.indexOf(j) < 0 && S.fixed.length < 8) S.fixed.push(j);
        existingCombo.setValue("none", { silent: true });
        update();
      },
    });

    function show(abbr, fips) {
      var s = byAbbr[abbr], token = ++cur.token;
      $("results").setAttribute("aria-busy", "true");
      Ex.loadData(BASE + s.file).then(function (st) {
        if (token !== cur.token) return;
        var ci = -1;
        if (fips) st.counties.forEach(function (c, i) { if (c.f === fips) ci = i; });
        if (ci < 0) {
          var cnt = st.counties.map(function () { return 0; });
          st.tracts.c.forEach(function (c) { cnt[c]++; });
          ci = cnt.indexOf(Math.max.apply(null, cnt));
        }
        cur.st = st; cur.abbr = abbr;
        cur.V = prep(st, ci);
        S.fixed = []; S.miles = null;
        S.weeks = weeksLeft().weeks;
        renderDates();
        stateCombo.setValue(abbr, { silent: true });
        countyCombo.setItems(st.counties.map(function (c) { return { value: c.f, label: c.n }; }));
        countyCombo.setValue(st.counties[ci].f, { silent: true });
        existingCombo.setItems(cur.V.ven.map(function (v, j) { return { value: String(j), label: v.name, hint: v.city }; }));
        $("results").removeAttribute("aria-busy");
        syncControls();
        update();
      }, function () {
        $("results").removeAttribute("aria-busy");
        Ex.showError($("chart-map"), "This state's data did not load. The tract table in the downloads has the same numbers.");
      });
    }

    /* ---------- one county's tracts and venues ---------- */
    function prep(st, ci) {
      var T = st.tracts, idx = [], i;
      for (i = 0; i < T.c.length; i++) if (T.c[i] === ci) idx.push(i);
      var n = idx.length;
      var V = { st: st, ci: ci, co: st.counties[ci], n: n, idx: idx, t: {}, lo: {}, hi: {}, g: [], zip: [], rk: [], pop: new Float64Array(n), den: new Float64Array(n), direct: new Float64Array(n),
                lat: new Float64Array(n), lon: new Float64Array(n), rlat: new Float64Array(n), rlon: new Float64Array(n), esd: new Float64Array(n), elig: new Float64Array(n),
                elo: new Float64Array(n), ehi: new Float64Array(n), L: new Float64Array(n), Llo: new Float64Array(n), Lhi: new Float64Array(n), Lu: new Float64Array(n), Lse: new Float64Array(n), vset: null, pset: null };
      TIERS.forEach(function (k) { V.t[k] = new Float64Array(n); V.lo[k] = new Float64Array(n); V.hi[k] = new Float64Array(n); });
      idx.forEach(function (j, r) {
        V.g.push(T.g[j]); V.zip.push(T.zip[j]); V.rk.push(T.rk[j]);
        V.pop[r] = T.pop[j] || 0; V.den[r] = T.den[j] || 0; V.direct[r] = T.direct[j] || 0;
        V.lat[r] = T.lat[j]; V.lon[r] = T.lon[j]; V.rlat[r] = T.lat[j] * Math.PI / 180; V.rlon[r] = T.lon[j] * Math.PI / 180;
        V.esd[r] = T.esd[j] || 0; V.elig[r] = T.elig[j] || 0; V.elo[r] = T.elig_lo[j] || 0; V.ehi[r] = T.elig_hi[j] || 0;
        V.L[r] = T.L[j] || 0; V.Llo[r] = Math.max(0, T.L_lo[j] || 0); V.Lhi[r] = T.L_hi[j] || 0; V.Lu[r] = T.Lu[j] || 0; V.Lse[r] = T.Lse[j] || 0;
        TIERS.forEach(function (k) { V.t[k][r] = T[k][j] || 0; V.lo[k][r] = Math.max(0, T[k + "_lo"][j] || 0); V.hi[k][r] = T[k + "_hi"][j] || 0; });
      });
      var ven = st.venues;
      V.ven = [];
      for (i = 0; i < ven.c.length; i++) {
        if (ven.c[i] === ci) V.ven.push({ name: ven.n[i], lib: ven.k[i], addr: ven.a[i], city: ven.city[i], zip: ven.zip[i], lat: ven.lat[i], lon: ven.lon[i] });
      }
      V.r0 = V.co.r;
      V.tot = {};
      TIERS.forEach(function (k) { var s = 0; for (var q = 0; q < n; q++) s += V.t[k][q]; V.tot[k] = s; });
      var rows = [];
      for (i = 0; i < n; i++) rows.push(i);
      rows.sort(function (a, b) { return V.L[b] - V.L[a]; });
      V.topL = rows.slice(0, 12);
      return V;
    }

    /* ---------- the reach rule ---------- */
    function milesMatrix(V, slat, slon) {
      var m = slat.length, n = V.n, d = new Float32Array(m * n), j, i, sl, cs;
      for (j = 0; j < m; j++) {
        sl = slat[j] * Math.PI / 180; cs = Math.cos(sl);
        var lo = slon[j] * Math.PI / 180;
        for (i = 0; i < n; i++) {
          var a = Math.sin((sl - V.rlat[i]) / 2), b = Math.sin((lo - V.rlon[i]) / 2);
          var h = a * a + Math.cos(V.rlat[i]) * cs * b * b;
          d[j * n + i] = 2 * EARTH * Math.asin(Math.sqrt(Math.min(1, h))) * CIRC;
        }
      }
      return d;
    }
    function venueSet(V) {
      if (!V.vset) {
        var lat = V.ven.map(function (v) { return v.lat; }), lon = V.ven.map(function (v) { return v.lon; });
        V.vset = { m: lat.length, lat: lat, lon: lon, dist: milesMatrix(V, lat, lon), sp: null };
      }
      return V.vset;
    }
    function popupSet(V, w) {
      var ord = [], i;
      for (i = 0; i < V.n; i++) ord.push(i);
      ord.sort(function (a, b) { return w[b] - w[a]; });
      ord = ord.slice(0, POPUP);
      var key = ord.join(",");
      if (!V.pset || V.pset.key !== key) {
        var lat = ord.map(function (q) { return V.lat[q]; }), lon = ord.map(function (q) { return V.lon[q]; });
        V.pset = { key: key, ids: ord, m: ord.length, lat: lat, lon: lon, dist: milesMatrix(V, lat, lon), sp: null };
      }
      return V.pset;
    }
    function sparse(set, R, n) {
      if (set.sp && set.sp.R === R) return set.sp;
      var idx = [], val = [];
      for (var j = 0; j < set.m; j++) {
        var ii = [], vv = [], off = j * n;
        for (var i = 0; i < n; i++) {
          var d = set.dist[off + i];
          if (d <= R) { ii.push(i); vv.push(Math.exp(-2 * (d / R) * (d / R))); }
        }
        idx.push(ii); val.push(vv);
      }
      set.sp = { R: R, idx: idx, val: val };
      return set.sp;
    }
    function coverage(sp, sel, n) {
      var cov = new Float64Array(n);
      sel.forEach(function (j) {
        var ii = sp.idx[j], vv = sp.val[j];
        for (var q = 0; q < ii.length; q++) cov[ii[q]] += vv[q];
      });
      for (var i = 0; i < n; i++) if (cov[i] > 1) cov[i] = 1;
      return cov;
    }
    function reachOf(w, cov) {
      var s = 0;
      for (var i = 0; i < cov.length; i++) s += w[i] * cov[i];
      return s;
    }
    function greedy(sp, w, n, k, fixed, m) {
      var cov = coverage(sp, fixed, n), used = {}, chosen = [];
      fixed.forEach(function (j) { used[j] = 1; });
      for (var step = 0; step < k; step++) {
        var best = -1, bg = 0;
        for (var j = 0; j < m; j++) {
          if (used[j]) continue;
          var ii = sp.idx[j], vv = sp.val[j], g = 0;
          for (var q = 0; q < ii.length; q++) {
            var c = cov[ii[q]], c2 = c + vv[q];
            g += w[ii[q]] * ((c2 > 1 ? 1 : c2) - c);
          }
          if (g > bg) { bg = g; best = j; }
        }
        if (best < 0) break;
        chosen.push(best); used[best] = 1;
        var ib = sp.idx[best], vb = sp.val[best];
        for (var r = 0; r < ib.length; r++) cov[ib[r]] = Math.min(1, cov[ib[r]] + vb[r]);
      }
      return chosen;
    }
    function order(V, key) {
      var o = [];
      for (var i = 0; i < V.n; i++) o.push(i);
      o.sort(function (a, b) { return key[b] - key[a]; });
      return o;
    }
    function nearestUnused(set, n, ord, k, fixed) {
      var used = {}, sel = [];
      fixed.forEach(function (j) { used[j] = 1; });
      for (var q = 0; q < ord.length && sel.length < k; q++) {
        var i = ord[q], best = -1, bd = Infinity;
        for (var j = 0; j < set.m; j++) {
          if (used[j]) continue;
          var d = set.dist[j * n + i];
          if (d < bd) { bd = d; best = j; }
        }
        if (best >= 0) { used[best] = 1; sel.push(best); }
      }
      return sel;
    }

    /* ---------- one calculation: weights, plan, comparisons ---------- */
    function compute() {
      var V = cur.V, n = V.n, i;
      var w = new Float64Array(n), sd = new Float64Array(n), scale = 1 + S.scen / 100;
      var isDefault = S.nc === 0 && S.on.kids && S.on.medicaid && S.on.subsidy && !S.on.gap && !S.on.d400;
      for (i = 0; i < n; i++) {
        var mu = 0, s = 0;
        TIERS.forEach(function (k) {
          var share = k === "noncit" ? S.nc / 100 : S.on[k] ? 1 : 0;
          if (!share) return;
          mu += share * V.t[k][i];
          s += share * (V.hi[k][i] - V.lo[k][i]) / (2 * Z90) / (SCALE[k] || 1);
        });
        w[i] = mu * scale;
        sd[i] = (isDefault ? V.esd[i] : s) * scale;
      }
      var total = 0;
      for (i = 0; i < n; i++) total += w[i];
      var mode = S.mode === "venue" && !V.ven.length ? "popup" : S.mode;
      var R = S.miles || V.r0;
      var set = mode === "venue" ? venueSet(V) : popupSet(V, w);
      var fixed = mode === "venue" ? S.fixed.filter(function (j) { return j < set.m; }) : [];
      var sp = sparse(set, R, n);
      var chosen = total > 0 ? greedy(sp, w, n, S.k, fixed, set.m) : [];
      var sel = fixed.concat(chosen);
      var cov = coverage(sp, sel, n);
      var reach = reachOf(w, cov), v2 = 0;
      for (i = 0; i < n; i++) v2 += cov[i] * cov[i] * sd[i] * sd[i];
      var half = Z90 * V.co.infl * Math.sqrt(v2);
      // the same number of sites chosen the way a person would without the tool
      var wd = V.direct, rate = new Float64Array(n);
      for (i = 0; i < n; i++) rate[i] = V.den[i] >= MIN_DEN ? V.direct[i] / V.den[i] : -1;
      var pick = function (key) {
        if (!set.m) return [];
        if (mode === "venue") return nearestUnused(set, n, order(V, key), S.k, fixed);
        var pos = {};
        set.ids.forEach(function (q, p) { pos[q] = p; });
        return order(V, key).filter(function (q) { return pos[q] != null; }).slice(0, S.k).map(function (q) { return pos[q]; });
      };
      var keyCount = new Float64Array(n), keyRate = new Float64Array(n), inSet = {};
      if (mode === "popup") set.ids.forEach(function (q) { inSet[q] = 1; });
      for (i = 0; i < n; i++) {
        keyCount[i] = mode === "popup" && !inSet[i] ? -1 : wd[i];
        keyRate[i] = mode === "popup" && !inSet[i] ? -1 : rate[i];
      }
      var byCount = fixed.concat(pick(keyCount)), byRate = fixed.concat(pick(keyRate));
      var plan = { V: V, w: w, sd: sd, total: total, mode: mode, R: R, set: set, sp: sp, fixed: fixed, chosen: chosen, sel: sel, cov: cov, reach: reach, lo: Math.max(0, reach - half), hi: Math.min(total, reach + half),
                   half: half, isDefault: isDefault, byCount: reachOf(w, coverage(sp, byCount, n)), byRate: reachOf(w, coverage(sp, byRate, n)), siteReach: [] };
      plan.siteReach = sel.map(function (j) {
        var ii = sp.idx[j], vv = sp.val[j], s = 0, t = 0;
        for (var q = 0; q < ii.length; q++) { s += w[ii[q]] * vv[q]; t++; }
        return { people: s, tracts: t };
      });
      return plan;
    }

    /* ---------- rendering the answer ---------- */
    function siteLabel(p, q) {
      var j = p.sel[q];
      if (p.mode === "venue") return p.V.ven[j].name;
      var i = p.set.ids[j];
      return "Pop-up in " + (area(p.V.zip[i]) ? area(p.V.zip[i]) + ", " : "") + "tract " + tractName(p.V.g[i]);
    }
    var PHRASE = { kids: "children", medicaid: "adults in the Medicaid range", subsidy: "adults in the subsidy range", gap: "adults in the coverage gap", d400: "people at 400% of poverty and over", noncit: "noncitizen adults" };
    function whoText() {
      var on = TIERS.filter(function (k) { return k !== "noncit" && S.on[k]; }).map(function (k) { return PHRASE[k]; });
      if (S.nc) on.push(PHRASE.noncit + " (" + S.nc + "% of them)");
      return on.length ? on.join(", ") : "no one";
    }
    function update() {
      var V = cur.V;
      if (!V) return;
      var p = cur.plan = compute();
      var k = p.sel.length, kk = S.k;
      var msg = [], gone = p.V.co.elig <= 0 && p.total <= 0;
      if (p.total <= 0) msg.push(gone ? "The model counts no eligible people in this county." : "No one is counted with these choices.");
      if (S.mode === "venue" && !V.ven.length && p.total > 0) msg.push("No library or health center is in the files for this county, so sites go at tract centers.");
      else if (p.mode === "venue" && V.ven.length && p.chosen.length < kk && p.total > 0) {
        msg.push(k >= p.set.m ? "Only " + F.plural(p.set.m, "venue") + " here; the plan uses " + (p.set.m === 1 ? "it" : "all of them") + "." : "The other venues add no one within reach, so the plan uses " + F.plural(k, "site") + ".");
      }
      var empty = p.total <= 0;
      p.rough = !(p.isDefault && !S.miles && !S.scen && p.mode === "venue" && !p.fixed.length && [3, 5, 8].indexOf(S.k) >= 0);
      $("msg").hidden = !msg.length;
      $("msg").textContent = msg.join(" ");
      $("r1-label").textContent = empty ? "People reached, weighted by distance" : "People reached by " + F.plural(k, "site") + ", weighted by distance" + (p.fixed.length ? " (" + p.fixed.length + " you use)" : "");
      $("r1").textContent = empty ? "0" : a3(p.reach);
      $("r1-range").textContent = empty ? "" : (p.rough ? "Rough 90% range " : "90% range ") + a3(p.lo) + " to " + a3(p.hi) + ". That is " + F.pct(p.reach / p.total, 0) + " of the county's " + a3(p.total) + ".";
      $("r-hint").textContent = (p.isDefault && !S.scen ? "" : "Counting " + whoText() + ". ") + "People near a site count in full, at its edge " + F.pct(DERIVED.limit_weight_pct / 100, 0) + "." + (p.rough && !empty ? " The range was checked only for the default groups, distance and sites." : "");
      renderSiteList(p);
      [["r2", "count", p.byCount, "top survey-count"], ["r3", "rate", p.byRate, "top-rate"]].forEach(function (r) {
        $(r[0] + "-label").textContent = "Reached by the " + (k > 1 ? k + " " : "") + r[3] + " tract" + (k > 1 ? "s" : "");
        $(r[0]).textContent = empty ? "0" : a3(r[2]);
        var d = p.reach > 0 ? r[2] / p.reach - 1 : 0;
        $(r[0] + "-range").textContent = empty ? "" : Math.abs(d) < 0.005 ? "About the same as your plan." : F.pct(Math.abs(d), 0) + (d < 0 ? " fewer" : " more") + " people than your plan.";
      });
      // counts by group next to the checkboxes
      TIERS.forEach(function (t) { if ($("n-" + t)) $("n-" + t).textContent = F.int(V.tot[t] * (1 + S.scen / 100)); });
      $("h-miles").textContent = "Default " + F.num(V.r0, 0) + " miles for this county (" + F.num(N.validation.F_scenarios.travel_defaults_miles["2"], 0) + " urban, " + F.num(N.validation.F_scenarios.travel_defaults_miles["1"], 0) + " suburban, " +
        F.num(N.validation.F_scenarios.travel_defaults_miles["0"], 0) + " rural). Straight line times " + N.validation.F_scenarios.circuity_factor + ". The plan range is for the default.";
      $("h-mode").textContent = p.mode === "popup" ? "Sites go at the " + POPUP + " tracts with the most people counted." : "Sites are libraries (IMLS FY2023) and health center sites (HRSA).";
      $("h-nc").textContent = "Eligibility varies and the survey cannot tell. 0 leaves them out. Counted: " + F.int(V.tot.noncit * S.nc / 100) + " people.";
      $("h-scen").textContent = "A scenario for the 2026 drop in enrollment, not a forecast. Counts people in the survey years, so it scales every tract.";
      renderExisting(p);
      stateHint();
      mapLabelAndDefs(p);
      if (mapChart) mapChart.redraw();
      renderTractsSection();
      renderFullPlan(p);
      renderTractsTable(p);
      renderNeed(p);
    }

    function renderSiteList(p) {
      var ol = $("site-list");
      ol.textContent = "";
      p.sel.forEach(function (j, q) {
        var v = p.mode === "venue" ? p.V.ven[j] : null, where = v ? v.city : "";
        ol.appendChild(Ex.el("li", {}, [Ex.el("span", { class: "p8-sites__t" }, [Ex.el("strong", { text: siteLabel(p, q) }),
          Ex.el("span", { text: (where ? where + ", " : "") + a3(p.siteReach[q].people) + " people" })])]));
      });
    }
    function renderExisting(p) {
      var ul = $("used-list");
      ul.textContent = "";
      var off = p.mode !== "venue";
      S.fixed.forEach(function (j, q) {
        var v = p.V.ven[j];
        if (!v) return;
        var b = Ex.el("button", { class: "ex-link", type: "button", "aria-label": "Remove " + v.name }, ["Remove"]);
        b.addEventListener("click", function () { S.fixed.splice(q, 1); update(); });
        ul.appendChild(Ex.el("li", {}, [Ex.el("span", { text: v.name + (v.city ? ", " + v.city : "") }), " ", b]));
      });
      var inp = $("pick-existing").querySelector("input");
      if (inp) inp.disabled = off;
    }
    function stateHint() {
      var st = cur.st, parts = [];
      if (st.waiver) parts.push(st.waiver + ".");
      else if (!st.expansion) parts.push(st.name + " has not expanded Medicaid, so the Medicaid range is empty and adults under 100% of poverty are in the coverage gap.");
      if (cur.abbr === "CT") parts.push("Connecticut tracts are grouped by the Census Bureau's planning regions, which replaced counties in the 2022 data.");
      if (N.data_checks.places_missing_states.indexOf(cur.abbr) >= 0) parts.push("The CDC PLACES file has no values for " + st.name + ", so the model ran without it here.");
      $("state-hint").hidden = !parts.length;
      $("state-hint").textContent = parts.join(" ");
    }
    function syncControls() {
      var V = cur.V;
      $("f-sites").value = S.k; refreshSites();
      [].forEach.call(document.querySelectorAll('input[name="who"]'), function (c) { c.checked = !!S.on[c.value]; });
      $("f-miles").value = S.miles || V.r0;
      $("f-nc").value = S.nc; refreshNc();
      $("f-scen").value = S.scen; refreshScen();
      [].forEach.call(document.querySelectorAll('input[name="mode"]'), function (r) { r.checked = r.value === S.mode; });
      $("f-staff").value = S.staff.p; $("f-apd").value = S.staff.apd; $("f-dpw").value = S.staff.dpw; $("f-weeks").value = S.weeks;
    }
    var refreshSites = Ex.range($("f-sites"), { format: function (v) { return v + (v === 1 ? " site" : " sites"); }, onInput: function (v) { S.k = v; update(); } });
    var refreshNc = Ex.range($("f-nc"), { format: function (v) { return v + "%"; }, onInput: function (v) { S.nc = v; update(); } });
    var refreshScen = Ex.range($("f-scen"), { format: function (v) { return "+" + v + "%"; }, onInput: function (v) { S.scen = v; update(); } });
    [].forEach.call(document.querySelectorAll('input[name="who"]'), function (c) {
      c.addEventListener("change", function () { S.on[c.value] = c.checked ? 1 : 0; update(); });
    });
    [].forEach.call(document.querySelectorAll('input[name="mode"]'), function (r) {
      r.addEventListener("change", function () { if (r.checked) { S.mode = r.value; update(); } });
    });
    $("f-miles").addEventListener("change", function () {
      var v = parseFloat(this.value);
      if (!(v >= 1)) v = cur.V.r0;
      v = Math.min(v, N.validation.F_scenarios.travel_max_miles);
      S.miles = v === cur.V.r0 ? null : v;
      this.value = v;
      update();
    });
    [["f-staff", "p"], ["f-apd", "apd"], ["f-dpw", "dpw"]].forEach(function (f) {
      $(f[0]).addEventListener("change", function () {
        var v = parseInt(this.value, 10);
        S.staff[f[1]] = v >= 1 ? v : S.staff[f[1]];
        this.value = S.staff[f[1]];
        renderFullPlan(cur.plan);
      });
    });
    $("f-weeks").addEventListener("change", function () {
      var v = parseFloat(this.value);
      S.weeks = v >= 0 ? v : S.weeks;
      this.value = S.weeks;
      renderFullPlan(cur.plan);
    });
    $("reset").addEventListener("click", function () {
      S = fresh();
      show(defaultAbbr(), D.default_county);
    });
    function defaultAbbr() {
      var f = D.default_county.slice(0, 2), a = null;
      STATES.forEach(function (s) { if (s.fips === f) a = s.abbr; });
      return a;
    }

    /* on a phone, Who counts and the dates move into the inputs disclosure so the first answer sits near the State and County pickers */
    var mq = window.matchMedia("(max-width: 640px)"), moves = $("p8-moves"), mark = document.createComment("p8-moves"), more = document.querySelector(".p8-more"), moreSum = more.querySelector("summary");
    moves.parentNode.insertBefore(mark, moves);
    function placeMoves() {
      var body = more.querySelector(".p8-more__body");
      if (mq.matches) body.insertBefore(moves, body.firstChild);
      else mark.parentNode.insertBefore(moves, mark.nextSibling);
      moreSum.textContent = mq.matches ? "Who counts, dates and other inputs" : "About these inputs";
    }
    placeMoves();
    if (mq.addEventListener) mq.addEventListener("change", placeMoves);

    /* ---------- the map ---------- */
    var mapChart = null, mapLayout = null;
    function mapLabelAndDefs(p) {
      var V = p.V;
      $("t-map").textContent = "Uninsured people who could enroll, by tract, " + V.co.n + ", " + cur.abbr;
      $("map-def").textContent = "Each bubble is a census tract at its internal point; its area is the expected number of people counted under Who counts (" + whoText() + "). Darker bubbles are within reach of a site. The dashed ring is the reach limit: " +
        F.num(p.R, 1).replace(/\.0$/, "") + " miles of travel, which is " + F.num(p.R / CIRC, 1) + " miles in a straight line. A site reaches a tract at full weight when it is next door and at " + F.pct(Math.exp(-2), 0) + " at the limit.";
    }
    function fit(p, W, H) {
      var V = p.V, pts = [], xs = [], ys = [], i;
      for (i = 0; i < V.n; i++) {
        var q = proj([V.lon[i], V.lat[i]]);
        pts.push(q);
        if (q) { xs.push(q[0]); ys.push(q[1]); }
      }
      if (!xs.length) return null;
      var f = OUT.county[V.co.f];
      if (f) {
        var bb = d3.geoPath(toMerc(1, 0, 0)).bounds(f);
        xs.push(bb[0][0], bb[1][0]);
        ys.push(bb[0][1], bb[1][1]);
      }
      var x0 = d3.min(xs), x1 = d3.max(xs), y0 = d3.min(ys), y1 = d3.max(ys);
      var bw = Math.max(x1 - x0, 1e-4), bh = Math.max(y1 - y0, 1e-4); // 1e-4 of the world is about 2.5 miles
      var pad = 0.05, k = Math.min(W / (bw * (1 + 2 * pad)), H / (bh * (1 + 2 * pad)));
      var tx = (W - bw * k) / 2 - x0 * k, ty = (H - bh * k) / 2 - y0 * k;
      var j = pts.findIndex(Boolean), a = pts[j], b2 = proj([V.lon[j], V.lat[j] + 0.05]);
      var pxMile = a && b2 ? Math.hypot(b2[0] - a[0], b2[1] - a[1]) / (0.05 * 69.047) : 1;
      return { k: k, tx: tx, ty: ty, pts: pts, pxMile: pxMile * k, feat: f };
    }
    function tractTip(p, i) {
      var V = p.V, rows = [{ name: "Counted", value: F.int(p.w[i]) + " (" + F.int(Math.max(0, p.w[i] - Z90 * p.sd[i])) + " to " + F.int(p.w[i] + Z90 * p.sd[i]) + ")", color: "est" }];
      TIERS.forEach(function (t) { if (V.t[t][i] >= 0.5) rows.push({ name: NAME[t], value: F.int(V.t[t][i]) }); });
      rows.push({ name: "Within reach", value: F.pct(p.cov[i], 0) });
      return { title: "Tract " + tractName(V.g[i]) + (V.zip[i] ? ", " + area(V.zip[i]) : ""), rows: rows, note: V.rk[i] ? "Can be ranked against the county." : "Cannot be told apart from the county median." };
    }
    function drawMap(c) {
      var p = cur.plan;
      if (!p) return;
      var V = p.V, W = c.width, H = c.height, svg = c.svg, g = c.g;
      var L = mapLayout = fit(p, W, H);
      svg.attr("aria-label", "Map of " + V.co.n + ", " + cur.abbr + ". " + F.plural(p.sel.length, "site") + " reach about " + a3(p.reach) + " of " + a3(p.total) + " people counted.");
      if (!L) return;
      var X = function (q) { return q[0] * L.k + L.tx; }, Y = function (q) { return q[1] * L.k + L.ty; };
      Ex.tiles(g, { k: L.k, tx: L.tx, ty: L.ty, width: W, height: H });
      if (L.feat) {
        g.append("path").attr("class", "p8-county").attr("d", d3.geoPath(toMerc(L.k, L.tx, L.ty))(L.feat));
      }
      // candidate venues as quiet ticks
      if (p.mode === "venue") {
        g.append("g").selectAll("circle").data(V.ven).enter().append("circle").attr("class", "p8-cand").attr("r", 2)
          .each(function (v) { var q = proj([v.lon, v.lat]); if (q) { this.setAttribute("cx", X(q)); this.setAttribute("cy", Y(q)); } else this.remove(); });
      }
      // tract bubbles, big first so small ones stay hoverable
      var wmax = d3.max(Array.prototype.slice.call(p.w)) || 1;
      var rows = [];
      for (var i = 0; i < V.n; i++) if (L.pts[i] && p.w[i] > 0) rows.push(i);
      var rmax = Math.max(5, Math.min(26, 0.55 * Math.sqrt(W * H / Math.max(rows.length, 1))));
      rows.sort(function (a, b) { return p.w[b] - p.w[a]; });
      var bubbles = g.append("g").attr("class", "p8-bubbles");
      bubbles.selectAll("circle").data(rows).enter().append("circle").attr("class", "p8-tract")
        .attr("cx", function (i) { return X(L.pts[i]); }).attr("cy", function (i) { return Y(L.pts[i]); })
        .attr("r", function (i) { return Math.max(1.4, rmax * Math.sqrt(p.w[i] / wmax)); })
        .attr("fill-opacity", function (i) { return (0.14 + 0.78 * p.cov[i]).toFixed(3); });
      // rings and sites
      var sitePts = p.sel.map(function (j) { return p.mode === "venue" ? proj([p.V.ven[j].lon, p.V.ven[j].lat]) : L.pts[p.set.ids[j]]; });
      // place names: the ZIP areas of the largest tracts, where the label fits beside a bubble and clear of other labels and sites
      var taken = sitePts.filter(Boolean).map(function (q) { return [X(q) - 14, Y(q) - 14, X(q) + 14, Y(q) + 14]; }), seen = {}, named = 0;
      var places = g.append("g").attr("class", "p8-places").attr("aria-hidden", "true");
      function free(b) {
        if (b[0] < 2 || b[2] > W - 2 || b[1] < 2 || b[3] > H - 22) return false;
        return !taken.some(function (t) { return b[0] < t[2] && b[2] > t[0] && b[1] < t[3] && b[3] > t[1]; });
      }
      rows.some(function (i) {
        var z = V.zip[i], nm = z && ((cur.st.zip_city || {})[z] || "ZIP " + z);
        if (!nm || seen[nm] || !L.pts[i]) return false;
        var cx = X(L.pts[i]), cy = Y(L.pts[i]), r = Math.max(1.4, rmax * Math.sqrt(p.w[i] / wmax)), w = nm.length * 6 + 4;
        var opts = [[cx + r + 3, "start", cx + r + 3, cx + r + 3 + w], [cx - r - 3, "end", cx - r - 3 - w, cx - r - 3]];
        for (var o = 0; o < opts.length; o++) {
          var b = [Math.min(opts[o][2], opts[o][3]), cy - 8, Math.max(opts[o][2], opts[o][3]), cy + 8];
          if (free(b)) {
            places.append("text").attr("class", "p8-place").attr("x", opts[o][0]).attr("y", cy).attr("dy", "0.32em").attr("text-anchor", opts[o][1]).text(nm);
            taken.push(b); seen[nm] = 1; named++;
            break;
          }
        }
        return named >= 4;
      });
      // scale bar
      var miles = [0.5, 1, 2, 5, 10, 20, 50].filter(function (m) { return m * L.pxMile <= W * 0.3; }).pop();
      if (miles) {
        var bw = miles * L.pxMile, sb = g.append("g").attr("class", "p8-scale").attr("transform", "translate(8," + (H - 12) + ")").attr("aria-hidden", "true");
        sb.append("path").attr("d", "M0,-4V0H" + bw + "V-4");
        sb.append("text").attr("x", bw + 6).attr("dy", "0.32em").text(miles + (miles === 1 ? " mile" : " miles"));
      }
      var siteG = g.append("g");
      p.sel.forEach(function (j, q) {
        var pt = sitePts[q];
        if (!pt) return;
        siteG.append("circle").attr("class", "p8-ring").attr("cx", X(pt)).attr("cy", Y(pt)).attr("r", p.R / CIRC * L.pxMile);
      });
      var marks = siteG.selectAll("g.p8-site").data(p.sel.map(function (j, q) { return { j: j, q: q }; })).enter().append("g").attr("class", "p8-site ex-mark")
        .each(function (d) {
          var pt = sitePts[d.q];
          if (!pt) { this.remove(); return; }
          var existing = p.fixed.indexOf(d.j) >= 0;
          var s = d3.select(this).attr("transform", "translate(" + X(pt) + "," + Y(pt) + ")");
          s.append("rect").attr("class", "p8-site__box" + (existing ? " is-existing" : "")).attr("x", -9).attr("y", -9).attr("width", 18).attr("height", 18);
          s.append("rect").attr("class", "ex-focus-ring").attr("x", -13).attr("y", -13).attr("width", 26).attr("height", 26).attr("rx", 3);
          s.append("text").attr("class", "p8-site__n" + (existing ? " is-existing" : "")).attr("text-anchor", "middle").attr("dy", "0.35em").text(d.q + 1);
        });
      c.cleanup(Ex.tooltip.attach(marks, function (el) {
        var d = el.__data__, sr = p.siteReach[d.q], v = p.mode === "venue" ? p.V.ven[d.j] : null;
        return { title: "Site " + (d.q + 1) + ": " + siteLabel(p, d.q), rows: [{ name: "Expected reach", value: F.int(sr.people) + " people" }, { name: "Tracts within reach", value: F.int(sr.tracts) }],
                 note: v ? [v.addr, v.city, v.zip].filter(Boolean).join(", ") + (p.fixed.indexOf(d.j) >= 0 ? ". You use it." : "") : "A pop-up at the tract's center." };
      }));
      Ex.roving(g.node(), ".p8-site");
      // hover on bubbles
      var node = svg.node();
      function over(e) {
        var t = e.target;
        if (t.classList && t.classList.contains("p8-tract")) Ex.tooltip.show(tractTip(p, t.__data__), { x: e.clientX, y: e.clientY }, node);
        else if (!(t.closest && t.closest(".p8-site"))) Ex.tooltip.hide();
      }
      function out() { Ex.tooltip.hide(); }
      node.addEventListener("pointermove", over);
      node.addEventListener("pointerdown", over);
      node.addEventListener("pointerleave", out);
      c.cleanup(function () {
        node.removeEventListener("pointermove", over);
        node.removeEventListener("pointerdown", over);
        node.removeEventListener("pointerleave", out);
      });
    }
    mapChart = Ex.chart($("chart-map"), {
      label: "Map of the selected county", margin: { top: 4, right: 4, bottom: 4, left: 4 },
      height: function (w) { return Math.max(300, Math.min(560, w * 0.72)); }, render: drawMap,
    });

    /* ---------- tables: tracts, full plan, call sheet ---------- */
    function makeTable(slot, host, spec) {
      if (!slot.t) { slot.spec = spec; slot.t = Ex.dataTable(host, spec); }
      else slot.t.update(spec.rows, spec);
    }
    var trTable = {}, siteTable = {}, trAllTable = {};
    function topTractRows(p) {
      var V = p.V, o = order(V, p.w).slice(0, 25);
      return o.map(function (i) {
        return { tract: tractName(V.g[i]), zip: V.zip[i] || "", est: p.w[i], lo: Math.max(0, p.w[i] - Z90 * p.sd[i]), hi: p.w[i] + Z90 * p.sd[i], reach: p.cov[i],
                 kids: V.t.kids[i], medicaid: V.t.medicaid[i], subsidy: V.t.subsidy[i], gap: V.t.gap[i], d400: V.t.d400[i], noncit: V.t.noncit[i], rk: V.rk[i] ? "Yes" : "No" };
      });
    }
    function renderTractsTable(p) {
      var rows = topTractRows(p);
      var spec = {
        caption: "The 25 tracts in " + p.V.co.n + " with the most people counted. Estimate and range are for the groups under Who counts; the group columns are each group's expected people.",
        label: "Scrollable table of the top tracts",
        columns: [{ key: "tract", label: "Tract" }, { key: "zip", label: "Nearest ZIP area", text: true }, { key: "est", label: "Counted", format: F.int }, { key: "lo", label: "5th percentile", format: F.int }, { key: "hi", label: "95th percentile", format: F.int },
                  { key: "reach", label: "Within reach", format: function (v) { return F.pct(v, 0); } }, { key: "kids", label: "Children", format: F.int }, { key: "medicaid", label: "Medicaid range", format: F.int },
                  { key: "subsidy", label: "Subsidy range", format: F.int }, { key: "gap", label: "Coverage gap", format: F.int }, { key: "d400", label: "400% and over", format: F.int }, { key: "noncit", label: "Noncitizen adults", format: F.int },
                  { key: "rk", label: "Can be ranked", text: true }],
        rows: rows,
      };
      makeTable(trTable, $("table-tracts"), spec);
    }
    function weeksFor(people) {
      var cap = S.staff.p * S.staff.apd * S.staff.dpw;
      return cap > 0 ? people / cap : NaN;
    }
    function renderFullPlan(p) {
      if (!p) return;
      var rows = p.sel.map(function (j, q) {
        var v = p.mode === "venue" ? p.V.ven[j] : null, sr = p.siteReach[q];
        return { n: q + 1, site: siteLabel(p, q), kind: v ? (v.lib ? "Library" : "Health center") : "Pop-up", addr: v ? [v.addr, v.city, v.zip].filter(Boolean).join(", ") : "", people: sr.people, tracts: sr.tracts, weeks: weeksFor(sr.people) };
      });
      var cols = [{ key: "n", label: "Site" }, { key: "site", label: "Name", text: true }, { key: "kind", label: "Kind", text: true }, { key: "addr", label: "Address", text: true }, { key: "people", label: "Expected reach (people)", format: F.int },
                  { key: "tracts", label: "Tracts within reach", format: F.int }, { key: "weeks", label: "Weeks to see them all", format: function (v) { return isNaN(v) ? "n/a" : F.num(v, 1); } }];
      var spec = { caption: "The sites in your plan. Sites overlap, so their reach adds to more than the plan's.", label: "Scrollable table of the sites in the plan", columns: cols, rows: rows };
      makeTable(siteTable, $("table-sites"), spec);
      var cap = S.staff.p * S.staff.apd * S.staff.dpw * S.weeks * Math.max(1, p.sel.length);
      $("staff-line").textContent = p.total > 0 ? "With " + F.plural(S.staff.p, "person", "people") + " at each event doing " + S.staff.apd + " appointments a day, " + S.staff.dpw + " days a week, " + F.plural(p.sel.length, "site") + " can see about " + F.int(cap) + " people in " +
        F.plural(S.weeks, "week") + ". That is " + F.pct(Math.min(1, cap / Math.max(p.reach, 1)), 0) + " of the plan's expected reach." + (S.weeks === weeksLeft().weeks && weeksLeft().date ? (ownMarket() ? " The weeks run to HealthCare.gov's " + weeksLeft().date + "; set them to your state's." : " Weeks are counted to " + weeksLeft().date + ".") : "") : "";
      var co = p.V.co;
      $("selections-line").textContent = co.sel ? "In 2026, " + F.int(co.sel) + " people in " + co.n + " picked a plan on HealthCare.gov. There are " + F.num(co.sub / co.sel, 2) + " people in the subsidy range for each pick" + (co.sub_vs_state != null ? ", " + F.num(co.sub_vs_state, 2) + " times the state's ratio" : "") + ". Plan selections are not paid enrollment." : "";
    }
    function callSheet(p) {
      var V = p.V, head = ["Tract", "Tract ID (11 digits)", "Nearest ZIP area", "Population"];
      TIERS.forEach(function (t) { head.push(NAME[t] + " (expected)", NAME[t] + " 5th percentile", NAME[t] + " 95th percentile"); });
      head.push("Counted under Who counts", "Counted 5th percentile", "Counted 95th percentile", "Share within reach of the plan", "Survey's own count (default groups)", "Can be ranked");
      var lines = [head.map(csvCell).join(",")];
      order(V, p.w).forEach(function (i) {
        var r = [tractName(V.g[i]), V.co.f + V.g[i], V.zip[i] || "", Math.round(V.pop[i])];
        TIERS.forEach(function (t) { r.push(+V.t[t][i].toFixed(1), Math.round(V.lo[t][i]), Math.round(V.hi[t][i])); });
        r.push(+p.w[i].toFixed(1), Math.round(Math.max(0, p.w[i] - Z90 * p.sd[i])), Math.round(p.w[i] + Z90 * p.sd[i]), +p.cov[i].toFixed(3), +V.direct[i].toFixed(1), V.rk[i]);
        lines.push(r.map(csvCell).join(","));
      });
      return lines.join("\n") + "\n";
    }
    $("dl-call").addEventListener("click", function () {
      var p = cur.plan;
      if (!p) return;
      download("call-sheet-" + p.V.co.f + ".csv", "text/csv;charset=utf-8", ["﻿", callSheet(p)]);
    });

    /* ---------- need statement ---------- */
    function renderNeed(p) {
      var V = p.V, co = V.co, st = cur.st, def = p.isDefault && !S.scen, txt = [];
      txt.push(co.n + ", " + st.name + ": about " + a3(p.total) + " uninsured people counted (" + whoText() + ")" + (def ? ", 90% range " + a3(co.elig_lo) + " to " + a3(co.elig_hi) : "") + ". These are estimates for census tracts from the American Community Survey 2020-2024 and a small-area model, not counts of individuals.");
      var parts = TIERS.filter(function (t) { return V.tot[t] >= 0.5; }).map(function (t) { return F.int(V.tot[t]) + " " + PHRASE[t]; });
      txt.push("Across all groups the county has " + parts.join(", ") + ".");
      if (p.sel.length) {
        txt.push("A plan with " + F.plural(p.sel.length, "site") + " (" + p.sel.map(function (j, q) { return siteLabel(p, q); }).join("; ") + ") has a distance-weighted reach of about " + a3(p.reach) + ", " + (p.rough ? "rough " : "") + "90% range " + a3(p.lo) + " to " + a3(p.hi) + ", or " + F.pct(p.reach / Math.max(p.total, 1), 0) + " of the people counted. " +
          "People within " + F.num(p.R, 1).replace(/\.0$/, "") + " miles of travel of a site count in part, by distance: close to a site in full, at the edge " + F.pct(DERIVED.limit_weight_pct / 100, 0) + ". It is not a headcount of who will come.");
      }
      txt.push("The survey years predate the 2026 drop in marketplace enrollment. Noncitizen adults are " + (S.nc ? "counted at " + S.nc + "%" : "left out") + " because the survey cannot tell who is eligible. " + datesText() + " Sources: ACS 2020-2024 5-year tables C27016 and B27020, CDC PLACES 2025, Census SAHIE 2024, ACS 2024 PUMS, IMLS and HRSA site files. An example built on public data by Primordial Analytics.");
      $("need-text").textContent = txt.join("\n\n");
    }

    /* ---------- workbook, built in the browser and loaded only on click ---------- */
    function loadSheetJS() {
      return new Promise(function (resolve, reject) {
        if (window.XLSX) return resolve(window.XLSX);
        var s = document.createElement("script");
        s.src = XLSX_SRC; s.integrity = XLSX_SRI; s.crossOrigin = "anonymous"; s.referrerPolicy = "no-referrer";
        s.onload = function () { window.XLSX ? resolve(window.XLSX) : reject(new Error("no XLSX")); };
        s.onerror = reject;
        document.head.appendChild(s);
      });
    }
    function workbook(X, p) {
      var V = p.V, wb = X.utils.book_new(), co = V.co, i;
      var plan = [["Open enrollment site plan: " + co.n + ", " + cur.abbr], ["An example on public data, not client work. Yellow cells in the original are yours to change; here the staff rows recalculate."], [],
                  ["Who counts", whoText()], ["Sites", p.sel.length], ["Travel distance (miles)", p.R], ["People counted in the county", Math.round(p.total)],
                  ["Expected reach (people, distance-weighted)", Math.round(p.reach)], ["90% range low", Math.round(p.lo)], ["90% range high", Math.round(p.hi)],
                  ["Share of the county reached", +(p.reach / Math.max(p.total, 1)).toFixed(3)], [], ["Staff"],
                  ["People at each event", S.staff.p], ["Appointments a person does in a day", S.staff.apd], ["Days a week each site is open", S.staff.dpw], ["Weeks to plan for", S.weeks],
                  ["Appointments the staff hours provide, all sites", null], ["Share of the expected reach they can see", null]];
      var ws = X.utils.aoa_to_sheet(plan);
      var cap = S.staff.p * S.staff.apd * S.staff.dpw * S.weeks * p.sel.length;
      ws["B18"] = { t: "n", f: "B14*B15*B16*B17*B5", v: cap };
      ws["B19"] = { t: "n", f: "MIN(1,B18/B8)", v: Math.min(1, cap / Math.max(p.reach, 1)) };
      ws["!cols"] = [{ wch: 52 }, { wch: 22 }];
      X.utils.book_append_sheet(wb, ws, "Plan");
      var call = X.utils.aoa_to_sheet(callSheet(p).trim().split("\n").map(function (l) { return parseCsv(l).map(function (v, i) { return i < 3 ? String(v) : v; }); }));
      X.utils.book_append_sheet(wb, call, "Call sheet");
      var zips = {};
      for (i = 0; i < V.n; i++) {
        var z = V.zip[i] || "none", o = zips[z] || (zips[z] = { counted: 0, reached: 0 });
        o.counted += p.w[i]; o.reached += p.w[i] * p.cov[i];
      }
      var zrows = [["Nearest ZIP area (ZCTA, not always the mailing ZIP)", "People counted", "Of them, within reach of the plan"]];
      Object.keys(zips).sort(function (a, b) { return zips[b].counted - zips[a].counted; }).forEach(function (z) { zrows.push([z, Math.round(zips[z].counted), Math.round(zips[z].reached)]); });
      X.utils.book_append_sheet(wb, X.utils.aoa_to_sheet(zrows), "ZIP roll-up");
      var chosen = {};
      if (p.mode === "venue") p.sel.forEach(function (j) { chosen[j] = 1; });
      var vrows = [["Site", "Kind", "Address", "City", "ZIP", "Latitude", "Longitude", "In the plan"]];
      V.ven.forEach(function (v, j) { vrows.push([v.name, v.lib ? "Library" : "Health center", v.addr, v.city, v.zip, v.lat, v.lon, chosen[j] ? "Yes" : ""]); });
      X.utils.book_append_sheet(wb, X.utils.aoa_to_sheet(vrows), "Venues");
      var ass = [["Estimates: ACS 2020-2024 5-year tables C27016 and B27020, a small-area model with CDC PLACES 2025, Census SAHIE 2024 and ACS 2024 PUMS. Ranges are 5th to 95th percentiles of " + N.run.draws + " draws."],
                 ["Reach rule: a site reaches a tract with weight exp(-2 (d / R)^2) up to R = " + p.R + " miles; d is straight-line miles x " + CIRC + ". A tract's share is the sum over sites, capped at 1."],
                 ["Sites: libraries (IMLS FY2023; some will have closed) and health center sites (HRSA). They stand in for places an assister can meet people."],
                 ["The range combines tract ranges as if tracts were independent, times a county factor. It is for the default groups and distance."],
                 [datesText() + " (checked " + oe.checked + "; " + (ownMarket() ? FA.state_marketplaces.source : oe.source) + ")"],
                 ["Survey years are 2020-2024 and predate the 2026 drop in enrollment. Distance is straight-line, with no transit, hours or language."], ["An example on public data, not client work."]];
      X.utils.book_append_sheet(wb, X.utils.aoa_to_sheet(ass), "Assumptions and sources");
      return wb;
    }
    function parseCsv(line) {
      var out = [], cur2 = "", q = false;
      for (var i = 0; i < line.length; i++) {
        var ch = line[i];
        if (q) { if (ch === '"' && line[i + 1] === '"') { cur2 += '"'; i++; } else if (ch === '"') q = false; else cur2 += ch; }
        else if (ch === '"') q = true; else if (ch === ",") { out.push(cur2); cur2 = ""; } else cur2 += ch;
      }
      out.push(cur2);
      return out.map(function (s) { return s !== "" && !isNaN(+s) && !/^0\d/.test(s) ? +s : s; });
    }
    $("dl-book").addEventListener("click", function () {
      var btn = this, p = cur.plan;
      if (!p) return;
      var idle = btn.textContent;
      btn.textContent = "Preparing";
      loadSheetJS().then(function (X) {
        var out = X.write(workbook(X, p), { bookType: "xlsx", type: "array" });
        download("enrollment-plan-" + p.V.co.f + ".xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", [out]);
        btn.textContent = idle;
      }, function () {
        btn.hidden = true;
        Ex.live("The workbook could not be built. The call sheet and the example plan in the downloads have the same numbers.");
      });
    });

    /* ---------- section 2: one county's tracts, survey count against model ---------- */
    var tractsChart = null;
    function renderTractsSection() {
      var V = cur.V;
      $("t-tracts").textContent = "Uninsured adults at or below 138% of poverty, " + V.co.n + ", " + cur.abbr;
      $("tracts-def").textContent = "Each row is a tract in " + V.co.n + ", named by its nearest ZIP area and that ZIP's city where a library or health center gives one, ranked by the model's expected count (top " + V.topL.length + " of " + V.n + "; the table has all). Indigo is the survey's own count with its 90% margin of error (1.645 standard errors). Gold is the model's expected count with its 5th to 95th percentile range.";
      var fw = D.fig_width, last = fw.model_width_pp.length - 1;
      $("width-note").textContent = "Across the country, the survey's 90% range for this group is " + F.num(fw.direct_width_pp[0], 0) + " points of the cell's population wide in the smallest fifth of cells and " + F.num(fw.direct_width_pp[last], 0) + " in the largest. The model's is " +
        F.num(fw.model_width_pp[0], 0) + " and " + F.num(fw.model_width_pp[last], 0) + ".";
      var all = order(V, V.L).map(function (i) {
        return { tract: tractName(V.g[i]), zip: V.zip[i] || "", du: V.Lu[i], dlo: Math.max(0, V.Lu[i] - Z90 * V.Lse[i]), dhi: V.Lu[i] + Z90 * V.Lse[i], mu: V.L[i], lo: V.Llo[i], hi: V.Lhi[i] };
      });
      var spec = { caption: "Uninsured adults at or below 138% of poverty, every tract in " + V.co.n + ": the survey's count and the model's.", label: "Scrollable table of every tract in the county",
                   columns: [{ key: "tract", label: "Tract" }, { key: "zip", label: "Nearest ZIP area", text: true }, { key: "du", label: "Survey count", format: F.int }, { key: "dlo", label: "Survey low", format: F.int }, { key: "dhi", label: "Survey high", format: F.int },
                             { key: "mu", label: "Model estimate", format: F.int }, { key: "lo", label: "Model 5th percentile", format: F.int }, { key: "hi", label: "Model 95th percentile", format: F.int }], rows: all };
      makeTable(trAllTable, $("table-tr"), spec);
      if (!tractsChart) {
        tractsChart = Ex.chart($("chart-tracts"), {
          label: "Survey count and model estimate for the tracts with the most low-income uninsured adults",
          margin: function (w) { return { top: w < 520 ? 52 : 34, right: 14, bottom: 30, left: w < 520 ? 76 : 150 }; },
          height: function (w) { return (cur.V ? cur.V.topL.length : 6) * 36 + (w < 520 ? 86 : 68); },
          render: drawTracts,
        });
      } else tractsChart.redraw();
    }
    function drawTracts(c) {
      var V = cur.V, g = c.g, rows = V.topL.map(function (i) {
        return { i: i, tract: tractName(V.g[i]), zip: V.zip[i], du: V.Lu[i], dlo: Math.max(0, V.Lu[i] - Z90 * V.Lse[i]), dhi: V.Lu[i] + Z90 * V.Lse[i], mu: V.L[i], lo: V.Llo[i], hi: V.Lhi[i] };
      });
      var xmax = d3.max(rows, function (r) { return Math.max(r.dhi, r.hi); }) || 1;
      var x = d3.scaleLinear().domain([0, xmax]).nice().range([0, c.width]);
      var rh = 36, y = function (k) { return k * rh + rh / 2; };
      c.svg.attr("aria-label", "Survey count and model estimate of uninsured adults at or below 138% of poverty for the " + rows.length + " tracts with the most of them in " + V.co.n + ". The survey's own ranges are wide and often include zero; the model's are narrower.");
      // key, drawn on the chart in place of a legend
      var key = g.append("g").attr("transform", "translate(0," + (-c.margin.top + 12) + ")");
      key.append("circle").attr("class", "ex-dot ex-dot--obs").attr("r", 4.5).attr("cx", 5).attr("cy", 0);
      key.append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", 15).attr("y", 0).attr("dy", "0.32em").text("Survey count, 90% margin of error");
      var ky = c.narrow ? 18 : 0, kx = c.narrow ? 0 : Math.min(c.width / 2, 250);
      key.append("circle").attr("class", "ex-dot ex-dot--est").attr("r", 4.5).attr("cx", kx + 5).attr("cy", ky);
      key.append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", kx + 15).attr("y", ky).attr("dy", "0.32em").text("Model, 5th to 95th percentile");
      g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + (rows.length * rh + 4) + ")").call(d3.axisBottom(x).ticks(c.narrow ? 3 : 5).tickSize(0).tickFormat(F.int)).call(function (a) { a.select(".domain").remove(); });
      var rowsG = g.append("g").selectAll("g").data(rows).enter().append("g").attr("class", "ex-mark");
      rowsG.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", function (d, k) { return k * rh; }).attr("width", c.w).attr("height", rh).attr("fill", "transparent");
      rowsG.append("text").attr("class", "ex-svg-label").attr("x", -8).attr("y", function (d, k) { return y(k) - 5; }).attr("dy", "0.32em").attr("text-anchor", "end")
        .text(function (d) { return d.zip ? (c.narrow ? "ZIP " + d.zip : area(d.zip)) : "Tract " + d.tract; });
      rowsG.append("text").attr("class", "p8-zip").attr("x", -8).attr("y", function (d, k) { return y(k) + 9; }).attr("dy", "0.32em").attr("text-anchor", "end").text(function (d) { return d.zip ? "Tract " + d.tract : ""; });
      function whisk(sel, lo, hi, dy, cls) {
        sel.append("path").attr("class", "p8-whisk " + cls).attr("d", function (d, k) {
          var yy = y(k) + dy, a = x(d[lo]), b = x(d[hi]);
          return "M" + a + "," + (yy - 4) + "V" + (yy + 4) + "M" + a + "," + yy + "H" + b + "M" + b + "," + (yy - 4) + "V" + (yy + 4);
        });
      }
      whisk(rowsG, "dlo", "dhi", -6, "p8-whisk--obs");
      whisk(rowsG, "lo", "hi", 7, "p8-whisk--est");
      rowsG.append("circle").attr("class", "ex-dot ex-dot--obs").attr("r", 4.5).attr("cx", function (d) { return x(d.du); }).attr("cy", function (d, k) { return y(k) - 6; });
      rowsG.append("circle").attr("class", "ex-dot ex-dot--est").attr("r", 4.5).attr("cx", function (d) { return x(d.mu); }).attr("cy", function (d, k) { return y(k) + 7; });
      c.cleanup(Ex.tooltip.attach(rowsG, function (el) {
        var d = el.__data__;
        return { title: "Tract " + d.tract + (d.zip ? ", " + area(d.zip) : ""), rows: [{ name: "Survey count", value: F.int(d.du) + " (" + F.int(d.dlo) + " to " + F.int(d.dhi) + ")", color: "obs" }, { name: "Model estimate", value: F.int(d.mu) + " (" + F.int(d.lo) + " to " + F.int(d.hi) + ")", color: "est" }] };
      }));
      Ex.roving(g.node(), ".ex-mark");
    }

    /* ---------- section 3: ways to choose sites, 300 counties ---------- */
    var sitesChart = null, sitesMode = "venue", sitesTable = {};
    var ROWS = [{ key: "rate", label: "Highest rate", short: "By rate" }, { key: "direct", label: "Highest survey count", short: "By survey count" }, { key: "model", label: "Highest model count", short: "By model count" }, { key: "greedy", label: "Best reach", short: "By reach", best: true }];
    function sitesData() {
      var fs = D.fig_sites, rows = ROWS.map(function (r) {
        var sh = fs.county.map(function (c, i) { return fs[sitesMode === "venue" ? "venue_" + r.key : "popup_" + r.key][i] / fs.eligible[i]; });
        var s = sh.slice().sort(function (a, b) { return a - b; });
        return { r: r, sh: sh, med: quant(s, 0.5), q1: quant(s, 0.25), q3: quant(s, 0.75) };
      });
      return rows;
    }
    function drawSites(c) {
      var rows = sitesData(), g = c.g, fs = D.fig_sites, rh = 52;
      var x = d3.scaleLinear().domain([0, 1]).range([0, c.width]);
      c.svg.attr("aria-label", "Share of each county's eligible people reached by 5 sites, weighted by distance, by how the sites are chosen, across 300 counties. Median " + rows.map(function (r) { return r.r.label.toLowerCase() + " " + F.pct(r.med, 0); }).join(", ") + ".");
      g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + rows.length * rh + ")").call(d3.axisBottom(x).ticks(c.narrow ? 3 : 5).tickSize(0).tickFormat(function (v) { return F.pct(v, 0); })).call(function (a) { a.select(".domain").remove(); });
      var rg = g.append("g").selectAll("g").data(rows).enter().append("g").attr("class", "ex-mark").attr("transform", function (d, k) { return "translate(0," + (k * rh + rh / 2) + ")"; });
      rg.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", -rh / 2).attr("width", c.w).attr("height", rh).attr("fill", "transparent");
      rg.append("text").attr("class", function (d) { return "ex-svg-label" + (d.r.best ? " ex-sel" : ""); }).attr("x", -10).attr("dy", "0.32em").attr("text-anchor", "end").text(function (d) { return c.narrow ? d.r.short : d.r.label; });
      rg.each(function (d) {
        var s = d3.select(this);
        d.sh.forEach(function (v, i) {
          var jit = (((i * 2654435761) >>> 0) % 1000) / 1000 - 0.5;
          s.append("circle").attr("class", "p8-dot").attr("r", 2).attr("cx", x(v)).attr("cy", jit * 24);
        });
      });
      rg.append("path").attr("class", function (d) { return "p8-whisk p8-whisk--iqr" + (d.r.best ? " ex-sel" : ""); }).attr("d", function (d) { return "M" + x(d.q1) + ",-6V6M" + x(d.q1) + ",0H" + x(d.q3) + "M" + x(d.q3) + ",-6V6"; });
      rg.append("circle").attr("class", function (d) { return "ex-dot ex-dot--est" + (d.r.best ? " ex-sel" : ""); }).attr("r", 5.5).attr("cx", function (d) { return x(d.med); }).attr("cy", 0);
      rg.append("text").attr("class", function (d) { return "ex-svg-value" + (d.r.best ? " ex-sel" : ""); }).attr("x", function (d) { return x(d.q3) + 10; }).attr("y", -10).attr("dy", "0.32em").text(function (d) { return F.pct(d.med, 0); });
      var first = rows[0];
      g.append("text").attr("class", "ex-svg-label p8-anno").attr("x", 0).attr("y", -10).text(c.narrow ? "Each dot is a county" : "Each dot is a county. The ring is the median, the line the middle half.");
      c.cleanup(Ex.tooltip.attach(rg, function (el) {
        var d = el.__data__;
        return { title: d.r.label, rows: [{ name: "Median county", value: F.pct(d.med, 0), color: "est" }, { name: "Middle half", value: F.pct(d.q1, 0) + " to " + F.pct(d.q3, 0) }], note: "Share of the county's eligible people reached by 5 sites, weighted by distance." };
      }));
      Ex.roving(g.node(), ".ex-mark");
    }
    function renderSitesSection() {
      var sm = D.sites_summary, nv = N.sites[sitesMode === "venue" ? "venues" : "popup"];
      $("n-mod-med").textContent = F.signed(nv.model_over_direct.median_pct, 0);
      $("n-mod-q1").textContent = F.signed(nv.model_over_direct.q25_pct, 0);
      $("n-mod-q3").textContent = F.signed(nv.model_over_direct.q75_pct, 0);
      $("nodisc-s").hidden = sitesMode !== "venue";
      if (sitesMode === "venue") $("n-nodisc").textContent = F.num(N.sites.venues.greedy_over_direct_no_overlap_discount.median_pct, 0);
      $("sites-def").textContent = "Share = people within reach of the sites under the planner's reach rule, divided by the county's eligible people (children and adults in the Medicaid and subsidy ranges), in " + F.int(N.sites.counties) + " counties: the ones with the most tracts among those with " + 8 + " or more venues. Five sites. " +
        (sitesMode === "venue" ? "Sites are libraries and health center sites; a rule picks the nearest unused venue to each chosen tract." : "Sites are the 150 tracts with the most eligible people; a tract's own center is the site.");
      $("sites-extra").textContent = "In " + F.num(sm.top_rate_tract_not_in_top3_by_count_pct, 0) + "% of these counties the tract with the highest rate is not among the top three by the model's count. Median gain of best reach over highest survey count: " + F.num(N.sites[sitesMode === "venue" ? "venues" : "popup"].greedy_over_direct.median_pct, 0) + "%, middle half " +
        F.num(N.sites[sitesMode === "venue" ? "venues" : "popup"].greedy_over_direct.q25_pct, 0) + "% to " + F.num(N.sites[sitesMode === "venue" ? "venues" : "popup"].greedy_over_direct.q75_pct, 0) + "%.";
      var fs = D.fig_sites, pre = sitesMode === "venue" ? "venue_" : "popup_";
      var rows = fs.county.map(function (c, i) {
        return { county: fs.name[i], state: fs.state[i], tracts: fs.tracts[i], elig: fs.eligible[i], rate: fs[pre + "rate"][i] / fs.eligible[i], direct: fs[pre + "direct"][i] / fs.eligible[i], model: fs[pre + "model"][i] / fs.eligible[i], greedy: fs[pre + "greedy"][i] / fs.eligible[i] };
      });
      var pc = function (v) { return F.pct(v, 0); };
      var spec = { caption: "Share of each county's eligible people reached by 5 sites, weighted by distance, by how the sites are chosen.", label: "Scrollable table of 300 counties", columns: [{ key: "county", label: "County", text: true }, { key: "state", label: "State", text: true }, { key: "tracts", label: "Tracts", format: F.int },
                   { key: "elig", label: "Eligible people", format: F.int }, { key: "rate", label: "Highest rate", format: pc }, { key: "direct", label: "Highest survey count", format: pc }, { key: "model", label: "Highest model count", format: pc }, { key: "greedy", label: "Best reach", format: pc }], rows: rows };
      makeTable(sitesTable, $("table-sites-all"), spec);
    }
    [].forEach.call(document.querySelectorAll('input[name="sitesmode"]'), function (r) {
      r.addEventListener("change", function () { if (r.checked) { sitesMode = r.value; renderSitesSection(); if (sitesChart) sitesChart.redraw(); } });
    });
    renderSitesSection();
    sitesChart = Ex.chart($("chart-sites"), {
      label: "Share of eligible people reached by 5 sites, weighted by distance, by how the sites are chosen", margin: function (w) { return { top: 30, right: 44, bottom: 30, left: w < 520 ? 100 : 150 }; },
      height: function () { return ROWS.length * 52 + 70; }, render: drawSites,
    });

    /* ---------- method lists filled from the numbers ---------- */
    function fillMethodLists() {
      var rules = $("rules-list");
      [["medicaid_range", "Medicaid range"], ["subsidy_range", "Subsidy range"], ["coverage_gap", "Coverage gap"], ["d400", "400% and over"], ["children", "Children"], ["noncitizen", "Noncitizen adults"]].forEach(function (r) {
        rules.appendChild(Ex.el("dt", { text: r[1] }));
        rules.appendChild(Ex.el("dd", { text: FA.tier_rules[r[0]] }));
      });
      var defs = $("tier-defs");
      [["kids", "children"], ["medicaid", "medicaid_range"], ["subsidy", "subsidy_range"], ["gap", "coverage_gap"], ["d400", "d400"], ["noncit", "noncitizen"]].forEach(function (r) {
        defs.appendChild(Ex.el("dt", { text: NAME[r[0]] }));
        defs.appendChild(Ex.el("dd", { text: FA.tier_rules[r[1]] }));
      });
      var fl = $("facts-list");
      function fact(term, text, url, label) {
        fl.appendChild(Ex.el("dt", { text: term }));
        fl.appendChild(Ex.el("dd", {}, [text + " ", url ? link(url, label || "Source") : "", " Checked " + FA.checked + "."]));
      }
      fact("Open enrollment dates", oe.text.replace(/\.$/, "") + ". Starts " + dateText(oe.start) + ".", oe.source, "NAIC");
      fact("States with their own marketplace", FA.state_marketplaces.states.join(", ") + ". " + FA.state_marketplaces.note + " CMS list updated " + FA.state_marketplaces.list_updated + ".", FA.state_marketplaces.source, "CMS");
      fact("Navigator funding", "Federal navigator funding fell from $" + FA.navigator_funding.plan_year_2024_million_usd + " million for plan year 2024 to $" + FA.navigator_funding.per_year_now_million_usd + " million a year (CMS release of " + FA.navigator_funding.release_date + ").", FA.navigator_funding.source, "CMS");
      fact("Marketplace enrollment", "Effectuated enrollment was about " + FA.effectuated_enrollment.feb_2025_million + " million in February 2025 (" + FA.effectuated_enrollment.feb_2025_million_aspe + " million in the ASPE report) and " + FA.effectuated_enrollment.feb_2026_million + " million in February 2026. Cited, not recomputed.", FA.effectuated_enrollment.source, "KFF");
      fact("Medicaid expansion", "Not adopted in " + FA.medicaid_expansion.not_adopted.join(", ") + "; " + FA.medicaid_expansion.adopted_count_with_dc + " states and DC have. " + Object.keys(FA.medicaid_expansion.waiver_flags).map(function (k) { return k + ": " + FA.medicaid_expansion.waiver_flags[k] + "."; }).join(" "), FA.medicaid_expansion.source, "KFF");
      fact("2027 federal rules", FA.federal_law_2027.work_requirements + " " + FA.federal_law_2027.immigrants, FA.federal_law_2027.source, "KFF");
      fact("Immigrant eligibility", FA.immigrant_eligibility.note, FA.immigrant_eligibility.source, "KFF FAQ");
      fact("Not modeled", FA.not_modelled.join("; ") + ".");
      var V = N.validation, ck = $("checks-list"), pc = function (v) { return F.pct(v, 0); };
      function li(head, text) { ck.appendChild(Ex.el("li", {}, [Ex.el("strong", { text: head + " " }), text])); }
      li("Held-out tracts.", "We withheld 20% of tracts with 3,000 or more people at random, refit, and checked the 90% range against the survey's own count (plus simulated survey noise). It held " + pc(V.A_holdout.L.coverage90) + " of the time for adults at or below 138%, " + pc(V.A_holdout.C.coverage90) + " for adults 138 to 399%, " + pc(V.A_holdout.kids.coverage90) + " for children and " + pc(V.A_holdout.D.coverage90) + " for adults at 400% and over. The model's error was " + F.num(V.A_holdout.L.rmse_model, 0) + " people a tract for adults at or below 138%, against " + F.num(V.A_holdout.L.rmse_places_only, 0) + " for PLACES alone and " + F.num(V.A_holdout.L.rmse_county_rate, 0) + " for the county rate.");
      li("Independent county check.", "Refit without SAHIE and summed to counties, the model's 90% interval overlaps SAHIE's in " + pc(V.B_sahie_independent_refit.L.interval_overlap_share) + " of counties for adults at or below 138%, " + pc(V.B_sahie_independent_refit.C.interval_overlap_share) + " for adults 138 to 399% and " + pc(V.B_sahie_independent_refit.kids.interval_overlap_share) + " for children. The median gap in the rate is " + F.num(V.B_sahie_independent_refit.L.median_abs_rate_gap_points, 1) + " points for the lowest-income adults. The production model's agreement is higher by design, so it proves little.");
      li("Replication.", "A fit on the 2015-2019 survey was not run, and neither was a binomial-logit check of interval width.");
      li("Simulation inside the model.", "We drew a true world from the fitted model, simulated the survey's report for every tract, including zero cells, and reran everything. Before widening, the 90% tract ranges covered " + pc(V.D_simulation.tiers.kids.coverage90) + " to " + pc(V.D_simulation.tiers.medicaid.coverage90) + " of true values by group; a group below 88% was widened, and the default group now covers " + pc(V.D_simulation.elig.coverage90_published) + ". The survey's own 90% intervals covered " + pc(V.D_simulation.L.direct_coverage90) + ". This is a world the model describes, not the real one.");
      li("Site plans.", "In 20 counties, plans chosen from the model's estimates lost " + F.num(V.E1_regret.median_regret_model_pct, 1) + "% of reach on simulated truth at the median and plans chosen from the survey's own counts lost " + F.num(V.E1_regret.median_regret_direct_pct, 1) + "%. The planner's range held " + F.num(V.E2_browser_interval.greedy_5.mean_share_of_draws_inside_interval_pct, 0) + "% of simulated outcomes for 5-site plans and " + F.num(V.E2_browser_interval.greedy_8.mean_share_of_draws_inside_interval_pct, 0) + "% for 8-site plans. Against the exact best plan in " + V.E3_greedy_vs_exact.counties + " counties, the greedy rule was " + F.num(V.E3_greedy_vs_exact.median_gap_pct, 1) + "% short at the median and " + F.num(V.E3_greedy_vs_exact.max_gap_pct, 1) + "% at worst.");
      li("Scenarios.", "The noncitizen share counted, the more-uninsured slider and the 1.3 circuity factor are scenarios and are not validated. The person-file check on the noncitizen share is a consistency check: " + F.num(V.F_noncitizen_consistency_check.person_file_noncitizen_share_of_uninsured_adults_pct, 1) + "% in the file, " + F.num(V.F_noncitizen_consistency_check.modelled_pct, 1) + "% modeled.");
    }

    /* ---------- go ---------- */
    var d0 = D.default_county;
    show(defaultAbbr(), d0);
  }
});
