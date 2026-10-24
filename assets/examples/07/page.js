/* Example 07: health center site planner. Plain ES2019, no build step.
   Reads data.json (fitted parameter sets, centers, numbers.json as `numbers`) and zcta.bin.gz (one column per quantity, one value per ZIP
   area), both written by analysis/07-health-center-site-planner/web_data.py. The browser fits nothing. For a site at a point it applies
   the formula in analysis/.../project.py to the 24 shipped parameter sets:
     w(z) = theta * f(d),  f(d) = exp(-(max(d, 0.1) / rho_k)^gamma_k),  k = density class of ZIP z
     draw(z) = L(z) w / (1 + S + w),  new(z) = draw / (1 + S),  neighbor c loses lam_cz w / (1 + S + w)
   and scales every flow by K / D when the total draw D is above the capacity K. Intervals are the 10th to 90th percentile over the sets. */
Ex.ready(function () {
  "use strict";
  var F = Ex.fmt;
  var $ = function (id) {
    return document.getElementById(id);
  };
  var BASE = (($("main") || document.body).getAttribute("data-ex-data") || "").replace(/data\.json$/, "");
  var EARTH = 3958.8, DFLOOR = 0.1, RADIUS = 60, NEAR = 15, AREA_R = 40, NBR = 6;
  var NA16 = 65535, S_SCALE = 5500, SB_SCALE = 400, L_SCALE = 24, S_FLOOR = 0.01, L_FLOOR = 10, LAM_SCALE = 200;
  var PAYERS = ["uninsured", "medicaid", "medicare", "private"];
  var PAYER_NAME = { uninsured: "Uninsured", medicaid: "Medicaid", medicare: "Medicare", private: "Private" };
  var CLASSES = ["rural", "suburban", "urban"];
  var CLASS_WORD = { rural: "rural areas", suburban: "the suburbs", urban: "cities" };
  var CLASS_ADJ = { rural: "rural", suburban: "suburban", urban: "urban" };
  var DEFAULT_CENTER = "rural_median";
  var CAP_MIN = 100, CAP_MAX = 15000;
  var MI_DEG = (Math.PI / 180) * EARTH;
  var TYPES = [{ key: "chc" }, { key: "special" }];

  var TYPED = { "<i4": Int32Array, "<u4": Uint32Array, "|u1": Uint8Array, "<u2": Uint16Array, "<i2": Int16Array, "|i1": Int8Array };

  Ex.loadData().then(
    function (D) {
      setMsg("Loading the ZIP area data (" + (D.bin_gz_bytes / 1048576).toFixed(1) + " MB, once).");
      return loadColumns(D).then(
        function (ab) {
          init(D, ab);
        },
        function (e) {
          setMsg(e && e.message ? e.message : "The ZIP area data did not load.", true);
          showFailure(D);
        }
      );
    },
    function () {
      setMsg("The data did not load. The downloads below have the same numbers.", true);
      showFailure(null);
    }
  );

  /* ---------- small helpers ---------- */
  function setMsg(t, bad) {
    var el = $("msg");
    el.textContent = t || "";
    el.hidden = !t;
    el.classList.toggle("p7-bad", !!bad);
  }
  function showFailure() {
    ["chart-map", "chart-src"].forEach(function (id) {
      if ($(id)) Ex.showError($(id), "The ZIP data did not load. The ZIP table in the downloads has the same numbers.");
    });
  }
  function loadColumns() {
    return fetch(BASE + "zcta.bin.gz", { credentials: "same-origin" }).then(function (r) {
      if (!r.ok) throw new Error("The ZIP area data did not load (" + r.status + ").");
      return r.arrayBuffer().then(function (ab) {
        var b = new Uint8Array(ab, 0, 2);
        if (!(b[0] === 0x1f && b[1] === 0x8b)) return ab; // a server that already unpacked it
        if (typeof DecompressionStream === "undefined") throw new Error("This browser cannot unpack the ZIP data. The ZIP table in the downloads has the same numbers.");
        return new Response(new Blob([ab]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
      });
    });
  }
  function quant(a, q) {
    var s = Array.prototype.slice.call(a).sort(function (x, y) {
      return x - y;
    });
    var p = (s.length - 1) * q, lo = Math.floor(p), hi = Math.ceil(p);
    return s[lo] + (s[hi] - s[lo]) * (p - lo);
  }
  function q3(a) {
    var s = Array.prototype.slice.call(a).sort(function (x, y) {
      return x - y;
    });
    var f = function (q) {
      var p = (s.length - 1) * q, lo = Math.floor(p), hi = Math.ceil(p);
      return s[lo] + (s[hi] - s[lo]) * (p - lo);
    };
    return [f(0.1), f(0.5), f(0.9)];
  }
  function a3(v) {
    return F.approx(v, 3);
  }
  function r10(v) {
    return F.int(Math.round(v / 10) * 10);
  }
  function pc(v) {
    return F.pct(v, 0);
  }
  function titleCase(s) {
    if (s !== s.toUpperCase()) return s;
    return s
      .toLowerCase()
      .replace(/(^|[\s(\-/])([a-z])/g, function (m, p, c) {
        return p + c.toUpperCase();
      })
      .replace(/\b(Of|The|And|For|At|In)\b(?!\))/g, function (m, w, i) {
        return i ? w.toLowerCase() : w;
      })
      .replace(/\b([bcdfghjklmnpqrstvwxz]{2,3})\b/gi, function (m) {
        return m.toUpperCase();
      });
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
  function safeUrl(u) {
    return /^https:\/\//.test(u) ? u : "#";
  }
  function get(D, path) {
    return path.split(".").reduce(function (o, p) {
      return o == null ? o : o[p];
    }, D);
  }
  function fmtBy(code, v) {
    switch (code) {
      case "int": return F.int(v);
      case "pct0n": return F.num(v, 0);
      case "pct0": return F.pctValue(v, 0);
      case "pct1": return F.pctValue(v, 1);
      case "f0": return F.pct(v, 0);
      case "f1": return F.pct(v, 1);
      case "num1": return F.num(v, 1);
      case "num2": return F.num(v, 2);
      case "mil1": return (v / 1e6).toFixed(1) + " million";
      case "k": return F.approx(v, 3);
      default: return String(v);
    }
  }

  /* ---------- everything else runs once the columns are in ---------- */
  function init(D, ab) {
    var N = D.numbers;
    setMsg("");

    /* the numbers in the text come from data.json */
    [].forEach.call(document.querySelectorAll("[data-n]"), function (el) {
      var v = get(D, el.getAttribute("data-n"));
      if (v != null && (el.getAttribute("data-f") === "str" || !isNaN(v))) el.textContent = fmtBy(el.getAttribute("data-f"), v);
    });

    /* ---------- columns ---------- */
    var C = {};
    D.columns.forEach(function (c) {
      var T = TYPED[c.dtype], size = T.BYTES_PER_ELEMENT;
      C[c.name] = c.offset % size === 0 ? new T(ab, c.offset, c.length) : new T(ab.slice(c.offset, c.offset + c.length * size));
    });
    var n = C.lat.length, B = D.sets.length;
    var lat = new Float64Array(n), lon = new Float64Array(n), ux = new Float64Array(n), uy = new Float64Array(n), uz = new Float64Array(n);
    var S0 = new Float64Array(n);
    var i, b, j;
    for (i = 0; i < n; i++) {
      lat[i] = C.lat[i] / 1e4;
      lon[i] = C.lon[i] / 1e4;
      var la = (lat[i] * Math.PI) / 180, lo = (lon[i] * Math.PI) / 180;
      ux[i] = Math.cos(la) * Math.cos(lo);
      uy[i] = Math.cos(la) * Math.sin(lo);
      uz[i] = Math.sin(la);
      S0[i] = Math.expm1(C.S0[i] / S_SCALE);
    }
    var SS = [], LL = [];
    for (b = 0; b < B; b++) {
      var sb = new Float32Array(n), lb = new Float32Array(n), cs = C["S_" + b], cl = C["L_" + b];
      for (i = 0; i < n; i++) {
        sb[i] = (S0[i] + S_FLOOR) * Math.exp(cs[i] / SB_SCALE) - S_FLOOR;
        lb[i] = Math.max((C.low[i] + L_FLOOR) * Math.exp(cl[i] / L_SCALE) - L_FLOOR, 0);
      }
      SS.push(sb);
      LL.push(lb);
    }
    var OBS = PAYERS.map(function (p) {
      return C["obs_" + p];
    });
    var NEWP = PAYERS.map(function (p) {
      return C["new_" + p];
    });
    var NBRC = [], NBRL = [];
    for (j = 0; j < NBR; j++) {
      NBRC.push(C["nbr_c" + j]);
      NBRL.push(C["nbr_lam" + j]);
    }
    var zipStr = function (z) {
      return ("0000" + C.zip[z]).slice(-5);
    };
    var zipIndex = {};
    for (i = 0; i < n; i++) zipIndex[C.zip[i]] = i;
    var countyOf = function (z) {
      var p = D.counties[C.county[z]].split("|");
      return p[0];
    };
    var stateOf = function (z) {
      return D.states[C.state[z]];
    };
    var placeOf = function (z) {
      return countyOf(z) + ", " + stateOf(z);
    };
    var isSmall = function (z) {
      return C.small[z] === 1;
    };
    // small ZIPs and campus ZIPs (students inflate the low-income count) stay in totals but out of ranks
    var unranked = function (z) {
      return C.small[z] === 1 || C.campus[z] === 1;
    };
    var nCenters = D.centers.length;
    var nameOf = function (c) {
      return titleCase(c < nCenters ? D.centers[c].name : D.lookalikes[c - nCenters].name);
    };
    var ownSites = {};
    for (i = 0; i < C.site_lat.length; i++) (ownSites[C.site_center[i]] = ownSites[C.site_center[i]] || []).push(i);
    var slat = function (s) {
      return C.site_lat[s] / 1e4;
    };
    var slon = function (s) {
      return C.site_lon[s] / 1e4;
    };

    /* ZIP areas sorted by latitude, so a circle search scans a band */
    var order = Array.prototype.slice.call(new Int32Array(n).map(function (_, k) { return k; })).sort(function (x, y) {
      return lat[x] - lat[y];
    });
    var latSorted = Float64Array.from(order, function (z) {
      return lat[z];
    });
    function lowerBound(v) {
      var lo = 0, hi = n;
      while (lo < hi) {
        var mid = (lo + hi) >> 1;
        if (latSorted[mid] < v) lo = mid + 1;
        else hi = mid;
      }
      return lo;
    }
    function unit(la, lo) {
      var a = (la * Math.PI) / 180, o = (lo * Math.PI) / 180;
      return [Math.cos(a) * Math.cos(o), Math.cos(a) * Math.sin(o), Math.sin(a)];
    }
    function chord2(r) {
      var c = 2 * Math.sin(r / EARTH / 2);
      return c * c;
    }
    /** ZIP areas within r miles of a point: indices and straight-line miles */
    function within(la, lo, r) {
      var dl = r / 69.0 + 0.01;
      var from = lowerBound(la - dl), to = lowerBound(la + dl + 1e-9);
      var a = unit(la, lo), lim = chord2(r), zs = [], ds = [];
      for (var k = from; k < to; k++) {
        var z = order[k];
        var dx = ux[z] - a[0], dy = uy[z] - a[1], dz = uz[z] - a[2];
        var c2 = dx * dx + dy * dy + dz * dz;
        if (c2 <= lim) {
          zs.push(z);
          ds.push(2 * EARTH * Math.asin(Math.min(1, Math.sqrt(c2) / 2)));
        }
      }
      return { z: zs, d: ds };
    }
    function milesBetween(la1, lo1, la2, lo2) {
      var a = unit(la1, lo1), c = unit(la2, lo2);
      var dx = a[0] - c[0], dy = a[1] - c[1], dz = a[2] - c[2];
      return 2 * EARTH * Math.asin(Math.min(1, Math.sqrt(dx * dx + dy * dy + dz * dz) / 2));
    }

    /* ---------- the projection of a new site (project.py, steps 5 and 6) ---------- */
    function evalDN(la, lo, type, outD, outN) {
      var w0 = within(la, lo, RADIUS), zs = w0.z, ds = w0.d, m = zs.length;
      for (var s = 0; s < B; s++) {
        var st = D.sets[s], th = st.theta[type], Sb = SS[s], Lb = LL[s], Dt = 0, Nt = 0;
        for (var k = 0; k < m; k++) {
          var z = zs[k], c = C.dclass[z];
          var f = Math.exp(-Math.pow(Math.max(ds[k], DFLOOR) / st.rho[c], st.gamma[c]));
          var w = th * f, S = Sb[z], den = 1 + S + w, dr = (Lb[z] * w) / den;
          Dt += dr;
          Nt += dr / (1 + S);
        }
        outD[s] = Dt;
        outN[s] = Nt;
      }
    }
    function projectSite(la, lo, K, type) {
      var w0 = within(la, lo, RADIUS), zs = w0.z, ds = w0.d, m = zs.length;
      if (!m) return null;
      var P = { z: zs, d: ds, pat: new Float64Array(B), neu: new Float64Array(B), nb: new Float64Array(B), share: new Float64Array(B), unscaledD: new Float64Array(B), nUnscaled: new Float64Array(B),
                pay: [], payShare: [], draw: [], loss: {} };
      for (var s = 0; s < B; s++) {
        var st = D.sets[s], th = st.theta[type], Sb = SS[s], Lb = LL[s];
        var dr = new Float64Array(m), nw = new Float64Array(m), fr = new Float64Array(m), Dt = 0, Nt = 0;
        for (var k = 0; k < m; k++) {
          var z = zs[k], c = C.dclass[z];
          var f = Math.exp(-Math.pow(Math.max(ds[k], DFLOOR) / st.rho[c], st.gamma[c]));
          var w = th * f, S = Sb[z], den = 1 + S + w, d1 = (Lb[z] * w) / den;
          dr[k] = d1;
          nw[k] = d1 / (1 + S);
          fr[k] = w / den;
          Dt += d1;
          Nt += nw[k];
        }
        var scale = Dt > K ? K / Dt : 1;
        P.unscaledD[s] = Dt;
        P.nUnscaled[s] = Nt;
        P.pat[s] = Dt * scale;
        P.neu[s] = Nt * scale;
        P.nb[s] = (Dt - Nt) * scale;
        P.share[s] = Dt > 0 ? Nt / Dt : NaN;
        var pay = [0, 0, 0, 0];
        for (var k2 = 0; k2 < m; k2++) {
          var z2 = zs[k2], nbf = dr[k2] - nw[k2];
          for (j = 0; j < 4; j++) pay[j] += scale * (nw[k2] * (NEWP[j][z2] / 1e4) + nbf * (OBS[j][z2] / 1e4));
          dr[k2] *= scale;
          fr[k2] *= scale;
          for (j = 0; j < NBR; j++) {
            var cc = NBRC[j][z2];
            if (cc === NA16) continue;
            var lam = NBRL[j][z2] / LAM_SCALE;
            (P.loss[cc] = P.loss[cc] || new Float64Array(B))[s] += fr[k2] * lam * lam;
          }
        }
        var tot = pay[0] + pay[1] + pay[2] + pay[3];
        P.pay.push(pay);
        P.payShare.push(
          pay.map(function (v) {
            return tot > 0 ? v / tot : NaN;
          })
        );
        P.draw.push(dr);
      }
      P.q = { pat: q3(P.pat), neu: q3(P.neu), nb: q3(P.nb), share: q3(P.share) };
      P.payQ = PAYERS.map(function (p, jj) {
        return q3(
          P.payShare.map(function (v) {
            return v[jj];
          })
        );
      });
      // top neighbors by median loss, then top source ZIPs by median patients
      P.neighbors = Object.keys(P.loss)
        .map(function (c) {
          return { c: +c, med: quant(P.loss[c], 0.5), q: q3(P.loss[c]) };
        })
        .sort(function (a, b2) {
          return b2.med - a.med || b2.c - a.c;
        });
      var src = [];
      for (var k3 = 0; k3 < m; k3++) {
        var vals = P.draw.map(function (dr2) {
          return dr2[k3];
        });
        src.push({ z: zs[k3], q: q3(vals) });
      }
      src.sort(function (a, b2) {
        return b2.q[1] - a.q[1];
      });
      P.sources = src;
      return P;
    }

    /* the rank among ZIP areas within 15 miles, on new patients at the chosen capacity; run in slices so a dense metro does not freeze the page.
       The per-ZIP values do not depend on capacity, so they are kept and a change of capacity only re-counts. */
    var rankJob = 0, rankCache = null;
    function rankFrom(rc, P, K, cand) {
      var ranks = new Float64Array(B), self = -1, best = 0.5;
      for (var k0 = 0; k0 < rc.near.length; k0++) {
        var dd = milesBetween(cand.lat, cand.lon, lat[rc.near[k0]], lon[rc.near[k0]]);
        if (dd < best) {
          best = dd;
          self = k0;
        }
      }
      var value = function (Dv, Nv, s) {
        return Dv[s] > 0 ? Math.min(Dv[s], K) * (Nv[s] / Dv[s]) : 0;
      };
      for (var s = 0; s < B; s++) {
        var mine = value(P.unscaledD, P.nUnscaled, s), r = 1;
        for (var k = 0; k < rc.near.length; k++) {
          if (k === self) continue;
          if (value(rc.DD[k], rc.NN[k], s) > mine) r++;
        }
        ranks[s] = r;
      }
      return { q: q3(ranks), total: rc.near.length + (self >= 0 ? 0 : 1) };
    }
    function rankNearby(P, la, lo, K, type, cand, done) {
      var job = ++rankJob, key = type + "|" + la + "|" + lo;
      if (rankCache && rankCache.key === key && rankCache.ready) {
        done(rankFrom(rankCache, P, K, cand));
        return;
      }
      var rc = (rankCache = {
        key: key, ready: false, DD: [], NN: [], at: 0,
        near: within(la, lo, NEAR).z.filter(function (z) {
          return !unranked(z);
        }),
      });
      function step() {
        if (job !== rankJob) return;
        var t0 = performance.now();
        while (rc.at < rc.near.length && performance.now() - t0 < 12) {
          var d0 = new Float64Array(B), n0 = new Float64Array(B);
          evalDN(lat[rc.near[rc.at]], lon[rc.near[rc.at]], type, d0, n0);
          rc.DD.push(d0);
          rc.NN.push(n0);
          rc.at++;
        }
        if (rc.at < rc.near.length) setTimeout(step, 0);
        else {
          rc.ready = true;
          done(rankFrom(rc, P, K, cand));
        }
      }
      step();
    }

    /* ---------- state ---------- */
    var fixtureGrant = N.projection.fixtures.centers[DEFAULT_CENTER].grant;
    var defaultCi = Math.max(0, D.centers.findIndex(function (c) {
      return c.grant === fixtureGrant;
    }));
    var S = fresh();
    function fresh() {
      return { start: "center", ci: defaultCi, az: null, pt: null, cap: D.default_capacity, type: 0, rank: "people", cand: null, shown: 6, kept: null, user: false };
    }
    var A = null; // the service area: {z, d, rows (sorted), stats}
    var P = null; // the projection for the placed site
    var RK = null; // rank result
    var hits = [];
    var chartMap, chartSrc;

    /* ---------- the service area ---------- */
    function areaFromCenter(ci) {
      var seen = {}, zs = [], ds = [];
      (ownSites[ci] || []).forEach(function (s) {
        var w0 = within(slat(s), slon(s), AREA_R);
        for (var k = 0; k < w0.z.length; k++) {
          var z = w0.z[k];
          if (seen[z] == null) {
            seen[z] = zs.length;
            zs.push(z);
            ds.push(w0.d[k]);
          } else if (w0.d[k] < ds[seen[z]]) ds[seen[z]] = w0.d[k];
        }
      });
      return { z: zs, d: ds };
    }
    function metric(z) {
      // the quantity the ranking and the map color use: people (count) or share (of low-income residents who are not patients)
      return S.rank === "people" ? C.notp_p50[z] : 1 - reachOf(z)[1];
    }
    function noPatients(z) {
      return C.pat_total[z] === 0;
    }
    function reachOf(z) {
      if (isSmall(z)) return null;
      if (noPatients(z)) return [0, 0, 0];
      return [C.pen_p10[z] / 1e4, C.pen_p50[z] / 1e4, C.pen_p90[z] / 1e4];
    }
    function sortArea() {
      var key = {};
      A.z.forEach(function (z) {
        key[z] = S.rank === "people" ? C.notp_p50[z] : isSmall(z) ? -1 : 1 - reachOf(z)[1];
      });
      A.rows = A.z.slice().sort(function (x, y) {
        return unranked(x) - unranked(y) || key[y] - key[x] || x - y;
      });
    }
    function areaStats() {
      var low = 0, pat = 0, moe = 0;
      A.z.forEach(function (z) {
        low += C.low[z];
        pat += C.pat_total[z];
        moe += C.low_moe90[z] * C.low_moe90[z];
      });
      A.low = low;
      A.pat = pat;
      A.moe = Math.sqrt(moe);
      if (S.start === "center") {
        var c = D.centers[S.ci];
        A.notp = [c.area_not_p10, c.area_not_p50, c.area_not_p90];
        A.cLow = c.area_low_income;
        A.cPat = c.area_patients_all_centers;
      } else {
        var sums = [];
        for (var s = 0; s < B; s++) {
          var t = 0;
          for (var k = 0; k < A.z.length; k++) t += Math.max(0, LL[s][A.z[k]] - C.pat_low[A.z[k]]);
          sums.push(t);
        }
        A.notp = q3(sums);
        A.cLow = low;
        A.cPat = pat;
      }
    }

    /* ---------- rendering: the area ---------- */
    function areaName() {
      if (S.start === "center") return titleCase(D.centers[S.ci].name);
      if (S.start === "zip") return "ZIP " + zipStr(S.az);
      return S.pt.lat.toFixed(2) + ", " + S.pt.lon.toFixed(2);
    }
    function renderArea() {
      var p = $("area-line");
      p.textContent = "";
      p.appendChild(Ex.el("strong", { text: "About " + a3(A.notp[1]) }));
      p.appendChild(document.createTextNode(
        " low-income residents within " + AREA_R + " miles of " + (S.start === "center" ? "the sites of " : "") + areaName() + " are not patients (80% range " + a3(A.notp[0]) + " to " + a3(A.notp[2]) +
        ") of " + a3(A.cLow) + " (90% margin plus or minus " + a3(A.moe) + "). Patients of all centers: " + a3(A.cPat) + "."
      ));
      $("map-hint").textContent =
        F.int(A.z.length) + " ZIP areas within " + AREA_R + " miles. Gray squares are sites. The gold diamond is your site; rings mark where it draws most. Select a ZIP to move it.";
      $("t-zips").textContent = "ZIP areas, " + (S.rank === "people" ? "most residents who are not patients first" : "largest share who are not patients first");
    }
    function rowText(z) {
      var r = reachOf(z);
      return {
        zip: zipStr(z) + (C.campus[z] === 1 ? " (campus)" : ""), place: placeOf(z), low: C.low[z], pat: C.pat_total[z],
        reach: r ? (noPatients(z) ? "none reported" : pc(r[1]) + " (" + F.num(r[0] * 100, 0) + " to " + F.num(r[2] * 100, 0) + ")") : "small ZIP",
        notp: F.int(C.notp_p50[z]) + " (" + F.int(C.notp_p10[z]) + " to " + F.int(C.notp_p90[z]) + ")",
        unins: C.unins[z], hrsa: C.hrsa_pen[z] === NA16 ? "n/a" : pc(C.hrsa_pen[z] / 1e4),
      };
    }
    function renderTable() {
      var host = $("table-zips");
      var rows = A.rows.slice(0, S.shown);
      var selZ = S.cand && S.cand.z != null ? S.cand.z : null;
      if (selZ != null && A.z.indexOf(selZ) >= 0 && rows.indexOf(selZ) < 0) rows.push(selZ);
      var cols = [["ZIP", false], ["Not patients (80% range)", false], ["Share reached (80% range)", false], ["County", true], ["Uninsured adults", false]];
      var thead = Ex.el("tr", {}, cols.map(function (c, k) {
        return Ex.el("th", { scope: "col", class: c[1] && k ? "is-text" : false, text: c[0] });
      }));
      var tbody = Ex.el("tbody");
      rows.forEach(function (z) {
        var t = rowText(z), sel = z === selZ;
        var btn = Ex.el("button", { class: "ex-link p7-zipbtn", type: "button", "aria-label": "Place a site at ZIP " + t.zip + ", " + t.place, "data-z": String(z), text: t.zip });
        if (sel) btn.setAttribute("aria-current", "true");
        btn.addEventListener("click", function () {
          place({ z: z, lat: lat[z], lon: lon[z] }, "table");
        });
        var tr = Ex.el("tr", { class: sel ? "is-sel" : false }, [
          Ex.el("th", { scope: "row" }, [btn]),
          Ex.el("td", { text: t.notp }),
          Ex.el("td", { text: t.reach }),
          Ex.el("td", { class: "is-text", text: t.place }),
          Ex.el("td", { text: F.int(t.unins) }),
        ]);
        tbody.appendChild(tr);
      });
      var table = Ex.el("table", { class: "ex-table p7-zips" }, [
        Ex.el("caption", { text: "ZIP areas within " + AREA_R + " miles, " + (S.rank === "people" ? "by low-income residents who are not patients" : "by share of low-income residents who are not patients") + ". Small ZIPs (under 1,000 low-income residents) and campus ZIPs come last." }),
        Ex.el("thead", {}, [thead]),
        tbody,
      ]);
      host.textContent = "";
      host.appendChild(Ex.el("div", { class: "ex-table-wrap p7-scroll", role: "region", tabindex: "0", "aria-label": "Scrollable table of ZIP areas in the service area" }, [table]));
      var more = $("more-zips");
      var left = A.rows.length - S.shown;
      more.hidden = left <= 0;
      if (left > 0) more.textContent = "Show " + Math.min(left, 20) + " more of " + F.int(left) + " ZIPs";
      $("ziplist").hidden = false;
    }

    /* ---------- the map ---------- */
    function mapGeom(w) {
      // equirectangular miles around the area's middle
      var xs = A.z.map(function (z) { return z; });
      var la0 = d3.mean(xs, function (z) { return lat[z]; }), lo0 = d3.mean(xs, function (z) { return lon[z]; });
      var cs = Math.cos((la0 * Math.PI) / 180);
      var px = function (z) { return (lon[z] - lo0) * cs * MI_DEG; };
      var py = function (z) { return -(lat[z] - la0) * MI_DEG; };
      var ex = d3.extent(xs, px), ey = d3.extent(xs, py);
      var spanX = Math.max(ex[1] - ex[0], 8), spanY = Math.max(ey[1] - ey[0], 8);
      return { la0: la0, lo0: lo0, cs: cs, ex: ex, ey: ey, spanX: spanX, spanY: spanY };
    }
    var geom = null;
    function mapHeight(w) {
      if (!A) return 300;
      geom = mapGeom(w);
      var aspect = geom.spanY / geom.spanX;
      return Math.max(240, Math.min(w < 520 ? 360 : 440, w * aspect + 60));
    }
    function drawMap(c) {
      if (!A) return;
      var g = c.g, G = geom || mapGeom(c.w);
      var PAD = 12, W = c.width, H = c.height - 22;
      // Web Mercator, to sit on the street tiles; s is pixels per mile at the area's middle
      var m = A.z.map(function (z) { return Ex.merc([lon[z], lat[z]]); });
      var mx = d3.extent(m, function (q) { return q[0]; }), my = d3.extent(m, function (q) { return q[1]; });
      var SX = Math.max(mx[1] - mx[0], 1e-4), SY = Math.max(my[1] - my[0], 1e-4);
      var k = Math.min((W - 2 * PAD) / SX, (H - 2 * PAD) / SY);
      var ox = (W - SX * k) / 2 - mx[0] * k, oy = (H - SY * k) / 2 - my[0] * k;
      var s = k / (2 * Math.PI * EARTH * G.cs);
      var sx = function (la, lo) { return Ex.merc([lo, la])[0] * k + ox; };
      var sy = function (la, lo) { return Ex.merc([lo, la])[1] * k + oy; };
      var X = function (z) { return sx(lat[z], lon[z]); };
      var Y = function (z) { return sy(lat[z], lon[z]); };
      var vals = A.z.filter(function (z) { return !isSmall(z); }).map(metric).sort(d3.ascending);
      var hi = vals.length ? d3.quantile(vals, 0.95) : 1;
      if (!(hi > 0)) hi = 1;
      var color = Ex.scaleSeq([0, hi]);
      var maxLow = d3.max(A.z, function (z) { return C.low[z]; }) || 1;
      var rad = function (z) { return (c.narrow ? 1.6 : 2) + (c.narrow ? 3.4 : 4.6) * Math.sqrt(C.low[z] / maxLow); };
      renderRamp(hi);
      // everything on the map is clipped to the plot, so nothing lands on the scale bar, the caption or the next heading
      g.append("clipPath").attr("id", "p7-clip").append("rect").attr("width", W).attr("height", H);
      var plot = g.append("g").attr("clip-path", "url(#p7-clip)");
      Ex.tiles(plot, { k: k, tx: ox, ty: oy, width: W, height: H });
      // sites in view
      var mine = {};
      if (S.start === "center") (ownSites[S.ci] || []).forEach(function (q) { mine[q] = 1; });
      var others = [], own = [];
      for (var q = 0; q < C.site_lat.length; q++) {
        var a = slat(q), o = slon(q), x0 = sx(a, o), y0 = sy(a, o);
        if (x0 < -6 || x0 > W + 6 || y0 < -6 || y0 > H + 6) continue;
        (mine[q] ? own : others).push({ x: x0, y: y0 });
      }
      plot.append("g").selectAll("rect.p7-site").data(others).join("rect").attr("class", "p7-site").attr("x", function (d) { return d.x - 2.5; }).attr("y", function (d) { return d.y - 2.5; }).attr("width", 5).attr("height", 5);
      plot.append("g").selectAll("rect.p7-site").data(own).join("rect").attr("class", "p7-site is-own").attr("x", function (d) { return d.x - 3.5; }).attr("y", function (d) { return d.y - 3.5; }).attr("width", 7).attr("height", 7);
      // dots, large first so small ones stay visible
      var zs = A.z.slice().sort(function (x, y) { return C.low[y] - C.low[x]; });
      var layer = plot.append("g");
      hits = [];
      zs.forEach(function (z) {
        var small = isSmall(z), x = X(z), y = Y(z), r = rad(z);
        layer.append("circle").attr("class", "p7-dot" + (small ? " is-small" : "")).attr("cx", x).attr("cy", y).attr("r", r)
          .attr("fill", small ? "none" : color(metric(z)));
        hits.push({ z: z, x: x, y: y, r: r });
      });
      // the top three ZIPs by the ranking, named, with their county
      var label = function (z, text, extra) {
        var x = X(z), flip = x + rad(z) + 8 + text.length * 6.6 > W;
        plot.append("text").attr("class", "p7-zip-label" + (extra || "")).attr("x", flip ? x - rad(z) - 4 : x + rad(z) + 4).attr("y", Y(z)).attr("dy", "0.32em").attr("text-anchor", flip ? "end" : "start").text(text);
      };
      A.rows.slice(0, 3).forEach(function (z) {
        label(z, c.narrow ? zipStr(z) : zipStr(z) + " " + countyOf(z).replace(/ (County|Parish|Borough|Municipality|Census Area)$/, ""));
      });
      // the placed site and the ZIPs it would draw most from
      if (S.cand && P) {
        P.sources.slice(0, 6).forEach(function (srcRow) {
          if (A.z.indexOf(srcRow.z) < 0) return;
          plot.append("circle").attr("class", "p7-src").attr("cx", X(srcRow.z)).attr("cy", Y(srcRow.z)).attr("r", rad(srcRow.z) + 3);
        });
        var cx = sx(S.cand.lat, S.cand.lon), cy = sy(S.cand.lat, S.cand.lon);
        plot.append("path").attr("class", "p7-cand").attr("d", "M" + cx + "," + (cy - 8) + "L" + (cx + 8) + "," + cy + "L" + cx + "," + (cy + 8) + "L" + (cx - 8) + "," + cy + "Z");
      }
      // scale bar
      var miles = [2, 5, 10, 20, 25, 50].filter(function (m) { return m * s < W * 0.3; }).pop() || 2;
      var bx = 4, by = c.height - 8;
      var bar = g.append("g").attr("class", "p7-scale");
      bar.append("path").attr("d", "M" + bx + "," + (by - 4) + "V" + by + "H" + (bx + miles * s) + "V" + (by - 4));
      bar.append("text").attr("x", bx + miles * s + 6).attr("y", by).text(miles + " miles");
      // hover and tap: one handler for all dots
      var svgNode = c.svg.node();
      function nearest(e) {
        var r = svgNode.getBoundingClientRect(), px = e.clientX - r.left - c.margin.left, py = e.clientY - r.top - c.margin.top, best = null, bd = 1e9;
        for (var k = 0; k < hits.length; k++) {
          var h = hits[k], dd = (h.x - px) * (h.x - px) + (h.y - py) * (h.y - py), lim = Math.max(h.r + 3, 9);
          if (dd < bd && dd <= lim * lim) {
            bd = dd;
            best = h;
          }
        }
        return best;
      }
      c.svg.on("pointermove.p7", function (e) {
        var h = nearest(e);
        svgNode.style.cursor = h ? "pointer" : "";
        if (h && e.pointerType === "mouse") Ex.tooltip.show(zipTip(h.z), { x: e.clientX, y: e.clientY }, svgNode);
        else if (!h) Ex.tooltip.hide();
      });
      c.svg.on("pointerleave.p7", function () {
        Ex.tooltip.hide();
      });
      c.svg.on("click.p7", function (e) {
        var h = nearest(e);
        if (h) place({ z: h.z, lat: lat[h.z], lon: lon[h.z] }, "map");
      });
      c.svg.attr("aria-label", "Map of " + F.int(A.z.length) + " ZIP areas within " + AREA_R + " miles. " + (S.rank === "people" ? "Darker dots have more low-income residents who are not patients." : "Darker dots have a larger share of low-income residents who are not patients.") + " The table below the map has the same numbers.");
    }
    function renderRamp(hi) {
      Ex.ramp($("ramp"), { title: S.rank === "people" ? "Low-income residents who are not patients, per ZIP" : "Share of low-income residents who are not patients", domain: [0, hi], format: S.rank === "people" ? F.int : function (v) { return F.pct(v, 0); } });
    }
    function zipTip(z) {
      var r = reachOf(z);
      return {
        title: "ZIP " + zipStr(z) + ", " + placeOf(z),
        rows: [
          { name: "Low-income residents", value: F.int(C.low[z]), color: "obs" },
          { name: "Not patients", value: F.int(C.notp_p50[z]) + " (" + F.int(C.notp_p10[z]) + " to " + F.int(C.notp_p90[z]) + ")", color: "est" },
          { name: "Share reached", value: r ? (noPatients(z) ? "none reported" : pc(r[1])) : "small ZIP", color: "est" },
          { name: "Patients, all centers", value: F.int(C.pat_total[z]), color: "obs" },
        ],
        note: "Click to place a site here.",
      };
    }

    /* ---------- placing a site ---------- */
    function place(cand, how, capOnly) {
      S.cand = cand;
      if (!capOnly) S.user = how !== "auto" && how !== "reset";
      P = projectSite(cand.lat, cand.lon, S.cap, S.type);
      if (!capOnly) RK = null;
      if (!P) {
        $("site").hidden = true;
        $("fig-src").hidden = true;
        setMsg("No ZIP area with residents lies within " + RADIUS + " miles of that point.", true);
        return;
      }
      setMsg("");
      renderSite();
      if (!capOnly) {
        renderTable();
        chartMap.redraw();
      }
      rankNearby(P, cand.lat, cand.lon, S.cap, S.type, cand, function (r) {
        RK = r;
        renderRank();
        if (S.kept) renderCompare();
      });
      if (how === "table") {
        var el = $("site-title");
        if (el && el.getBoundingClientRect().top < 0) el.scrollIntoView({ block: "start", behavior: Ex.reducedMotion() ? "auto" : "smooth" });
        else if (el && el.getBoundingClientRect().bottom > window.innerHeight) el.scrollIntoView({ block: "nearest", behavior: Ex.reducedMotion() ? "auto" : "smooth" });
      }
      if (how !== "auto") Ex.live("Site placed at " + siteName() + ". " + F.int(Math.round(P.q.neu[1])) + " new patients a year.");
    }
    function siteName() {
      return S.cand.z != null && S.cand.lat === lat[S.cand.z] ? "ZIP " + zipStr(S.cand.z) + ", " + placeOf(S.cand.z) : S.cand.lat.toFixed(4) + ", " + S.cand.lon.toFixed(4);
    }
    function range80(q, f) {
      return "80% range " + f(q[0]) + " to " + f(q[2]);
    }
    var range0 = function (q, f) {
      return f(q[0]) === f(q[2]) ? "Same across the 80% range" : range80(q, f);
    };
    function payText(k) {
      var v = P.payQ[k], lo = Math.round(v[0] * 100), hi = Math.round(v[2] * 100);
      return { mid: pc(v[1]), range: lo === hi ? "" : lo + " to " + hi + "%" };
    }
    function renderSite() {
      var q = P.q;
      $("site").hidden = false;
      $("fig-src").hidden = false;
      $("site-title").textContent = "A site at " + siteName();
      $("rs").textContent = r10(q.neu[1]);
      $("rs-range").textContent = range0(q.neu, r10);
      $("rt").textContent = r10(q.nb[1]);
      $("rt-range").textContent = range0(q.nb, r10);
      renderRank();
      var capNote = $("cap-note");
      capNote.hidden = !(q.pat[1] < S.cap * 0.99);
      capNote.textContent = capNote.hidden ? "" : "The model's draw here is below your capacity, so these figures follow the draw.";
      var top = P.neighbors.filter(function (x) { return x.med >= 5; }).slice(0, 3);
      $("nb-line").textContent = top.length
        ? "Other centers lose the most patients: " + top.map(function (x) { return nameOf(x.c) + ", " + r10(x.med) + " a year"; }).join("; ") + "."
        : "No other center reports patients near this site.";
      var pay = $("pay");
      pay.textContent = "";
      PAYERS.forEach(function (p, k) {
        var t = payText(k);
        pay.appendChild(Ex.el("div", {}, [
          Ex.el("dt", { text: PAYER_NAME[p] }),
          Ex.el("dd", { text: t.mid }),
          Ex.el("span", { class: "p7-pay__bar", "aria-hidden": "true", style: "width:" + Math.round(P.payQ[k][1] * 100) + "%" }),
        ].concat(t.range ? [Ex.el("dd", { class: "p7-pay__r", text: t.range })] : [])));
      });
      $("site-def").textContent =
        "Patients are the capacity you set, or the model's draw where that is smaller. Patients who use no center today are taken from people with no center in the model; the rest come from nearby centers. Payer mix: patients from neighbors keep their ZIP's observed mix; new patients are uninsured at the ACS share for the ZIP.";
      renderSources();
      renderCompare();
    }
    function renderRank() {
      $("rr-label").textContent = "Rank among ZIPs within " + NEAR + " miles";
      if (!RK) {
        $("rr").textContent = "...";
        $("rr-range").textContent = "ranking nearby ZIPs";
        return;
      }
      var r = RK.q, f = function (v) { return F.int(Math.round(v)); };
      $("rr").textContent = f(r[1]) + " of " + F.int(RK.total);
      $("rr-range").textContent = range0(r, f);
    }
    function renderSources() {
      var rows = P.sources.slice(0, 6).map(function (s) {
        return { z: s.z, zip: zipStr(s.z), place: placeOf(s.z), p10: s.q[0], p50: s.q[1], p90: s.q[2] };
      });
      var allRows = P.sources.slice(0, 20).map(function (s) {
        return { zip: zipStr(s.z), place: placeOf(s.z), p10: s.q[0], p50: s.q[1], p90: s.q[2] };
      });
      srcRows = rows;
      chartSrc.redraw();
      if (srcTable) srcTable.update(allRows);
      else
        srcTable = Ex.dataTable($("table-src"), {
          caption: "The 20 ZIP areas the site would draw the most patients from, median and 80% range across parameter sets.",
          label: "Scrollable table of source ZIP areas",
          columns: [
            { key: "zip", label: "ZIP" },
            { key: "place", label: "County", text: true },
            { key: "p50", label: "Patients a year, median", format: F.int },
            { key: "p10", label: "10th percentile", format: F.int },
            { key: "p90", label: "90th percentile", format: F.int },
          ],
          rows: allRows,
        });
    }
    var srcRows = [], srcTable = null;

    /* ---------- compare two sites ---------- */
    function snapshot() {
      if (!P) return null;
      var q = P.q;
      return {
        where: siteName(), cap: S.cap, type: TYPES[S.type].key,
        pat: r10(q.pat[1]), neu: r10(q.neu[1]) + " (" + r10(q.neu[0]) + " to " + r10(q.neu[2]) + ")", nb: r10(q.nb[1]) + " (" + r10(q.nb[0]) + " to " + r10(q.nb[2]) + ")",
        share: pc(q.share[1]),
        pay: PAYERS.map(function (p, k) { var t = payText(k); return t.mid + (t.range ? " (" + t.range.replace("%", "") + ")" : ""); }),
        rank: RK ? F.int(Math.round(RK.q[1])) + " of " + F.int(RK.total) : "n/a",
      };
    }
    function renderCompare() {
      var box = $("cmp-box");
      box.hidden = !S.kept;
      if (!S.kept) return;
      var now = snapshot();
      var rows = [
        ["Where", S.kept.where, now.where], ["Capacity a year", F.int(S.kept.cap), F.int(now.cap)], ["Patients a year", S.kept.pat, now.pat],
        ["Patients who use no center today", S.kept.neu, now.neu], ["Taken from other centers", S.kept.nb, now.nb], ["Share who use no center today", S.kept.share, now.share],
      ].concat(PAYERS.map(function (p, k) { return [PAYER_NAME[p] + " patients", S.kept.pay[k], now.pay[k]]; })).concat([["Rank among nearby ZIPs", S.kept.rank, now.rank]]);
      var table = Ex.el("table", { class: "ex-table" }, [
        Ex.el("caption", { text: "The site you kept and the site now on screen. Ranges are 80%." }),
        Ex.el("thead", {}, [Ex.el("tr", {}, [Ex.el("th", { scope: "col", text: "Measure" }), Ex.el("th", { scope: "col", class: "is-text", text: "Kept" }), Ex.el("th", { scope: "col", class: "is-text", text: "Now" })])]),
        Ex.el("tbody", {}, rows.map(function (r) {
          return Ex.el("tr", {}, [Ex.el("th", { scope: "row", text: r[0] }), Ex.el("td", { class: "is-text", text: r[1] }), Ex.el("td", { class: "is-text", text: r[2] })]);
        })),
      ]);
      var host = $("table-cmp");
      host.textContent = "";
      host.appendChild(Ex.el("div", { class: "ex-table-wrap is-short", role: "region", tabindex: "0", "aria-label": "Scrollable table comparing two sites" }, [table]));
    }

    /* ---------- the charts ---------- */
    function axisX(c, x, ticks, h, fmt) {
      c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + h + ")").call(d3.axisBottom(x).ticks(ticks).tickSize(0).tickPadding(8).tickFormat(fmt));
    }
    chartMap = Ex.chart($("chart-map"), {
      label: "Map of ZIP areas.",
      margin: { top: 6, right: 6, bottom: 4, left: 6 },
      height: mapHeight,
      maxHeight: 640,
      render: drawMap,
    });
    chartSrc = Ex.chart($("chart-src"), {
      label: "Dot plot of the ZIP areas a new site would draw most patients from.",
      margin: function (w) {
        return { top: 6, right: w < 520 ? 46 : 40, bottom: 28, left: w < 520 ? 64 : 150 };
      },
      height: function () {
        return srcRows.length * 26 + 40;
      },
      render: function (c) {
        if (!srcRows.length) return;
        var ROW = 26, h = srcRows.length * ROW;
        var x = d3.scaleLinear().domain([0, d3.max(srcRows, function (r) { return r.p90; }) * 1.05 || 1]).nice().range([0, c.width]);
        axisX(c, x, c.narrow ? 3 : 5, h, function (v) { return F.int(v); });
        var g = c.g.selectAll("g.ex-mark").data(srcRows).join("g").attr("class", "ex-mark").attr("transform", function (d, i) { return "translate(0," + (i * ROW + ROW / 2) + ")"; });
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", -ROW / 2).attr("width", c.w).attr("height", ROW);
        g.append("text").attr("class", function (d, i) { return "ex-svg-label" + (i === 0 ? " ex-sel" : ""); }).attr("x", -10).attr("dy", "0.35em").attr("text-anchor", "end")
          .text(function (d) { return c.narrow ? d.zip : d.zip + " " + d.place; });
        g.append("path").attr("class", "ex-ci-whisker ex-ci-whisker--est").attr("d", function (d) { return "M" + x(d.p10) + ",-4V4M" + x(d.p10) + ",0H" + x(d.p90) + "M" + x(d.p90) + ",-4V4"; });
        g.append("line").attr("class", function (d, i) { return "ex-stem ex-stem--est" + (i === 0 ? " ex-sel" : ""); }).attr("x1", 0).attr("x2", function (d) { return x(d.p50); }).attr("y1", 0).attr("y2", 0);
        g.append("circle").attr("class", function (d, i) { return "ex-dot ex-dot--est" + (i === 0 ? " ex-sel" : ""); }).attr("cx", function (d) { return x(d.p50); }).attr("cy", 0).attr("r", 4.5);
        g.append("text").attr("class", "ex-svg-value").attr("x", function (d) { return x(d.p90) + 8; }).attr("dy", "0.35em").text(function (d) { return F.int(Math.round(d.p50)); });
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return { title: "ZIP " + d.zip + ", " + d.place, rows: [{ name: "Patients a year", value: F.int(Math.round(d.p50)), color: "est" }, { name: "80% range", value: F.int(Math.round(d.p10)) + " to " + F.int(Math.round(d.p90)) }] };
        });
        Ex.roving(c.g.node(), ".ex-mark");
        var first = srcRows[0];
        c.svg.attr("aria-label", "Dot plot of the ZIP areas a new site would draw most patients from. ZIP " + first.zip + " is highest at " + F.int(Math.round(first.p50)) + " patients a year.");
      },
    });

    /* ---------- gaps: share of low-income residents in thinly reached ZIPs, by density class ---------- */
    var byClass = CLASSES.map(function (k) {
      var d = N.reach.by_density_class[k];
      return { k: k, u25: d.share_in_zctas_under_25pct_pct, u10: d.share_in_zctas_under_10pct_pct, pen: d.penetration_p10_p50_p90, low: d.low_income_residents, zctas: d.zctas, notp: d.not_patients };
    });
    byClass.sort(function (x, y) { return y.u25[1] - x.u25[1]; });
    var thin = byClass.slice().sort(function (x, y) { return x.pen[1] - y.pen[1]; })[0];
    (function () {
      var others = byClass.filter(function (r) { return r.k !== thin.k; });
      $("gap-class").textContent = CLASS_WORD[thin.k];
      var lede = document.querySelector("#gaps .ex-lede");
      lede.textContent =
        F.num(thin.u25[1], 0) + "% of low-income residents in " + CLASS_ADJ[thin.k] + " ZIPs live where centers reach under a quarter of them, against " +
        F.num(others[0].u25[1], 0) + "% in " + CLASS_ADJ[others[0].k] + " and " + F.num(others[1].u25[1], 0) + "% in " + CLASS_ADJ[others[1].k] + " ZIPs.";
      $("gaps-def").textContent =
        "Each dot is the share of a class's low-income residents who live in ZIP areas where patients of all centers are under 10% or under 25% of low-income residents. ZIP classes: rural, suburban and urban by residents per square mile.";
    })();
    Ex.chart($("chart-gaps"), {
      label: "Dot plot of the share of low-income residents who live in ZIP areas where health centers reach under 10% and under 25%, by ZIP class. " + CLASS_WORD[thin.k] + " are highest at " + F.num(thin.u25[1], 0) + "% under 25%.",
      margin: function (w) {
        return { top: 24, right: w < 520 ? 16 : 40, bottom: 28, left: w < 520 ? 74 : 110 };
      },
      height: function () {
        return byClass.length * 52 + 58;
      },
      render: function (c) {
        var ROW = 52, h = byClass.length * ROW;
        var x = d3.scaleLinear().domain([0, 70]).range([0, c.width]);
        axisX(c, x, c.narrow ? 3 : 4, h, function (v) { return v + "%"; });
        var g = c.g.selectAll("g.ex-mark").data(byClass).join("g").attr("class", "ex-mark").attr("transform", function (d, i) { return "translate(0," + (i * ROW + ROW / 2 + 8) + ")"; });
        var sel = function (d) { return d.k === thin.k ? " ex-sel" : ""; };
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", -ROW / 2).attr("width", c.w).attr("height", ROW);
        g.append("text").attr("class", function (d) { return "ex-svg-label" + sel(d); }).attr("x", -12).attr("dy", "0.35em").attr("text-anchor", "end").text(function (d) { return d.k.charAt(0).toUpperCase() + d.k.slice(1) + (c.narrow ? "" : " ZIPs"); });
        g.append("line").attr("class", function (d) { return "ex-stem ex-stem--est" + sel(d); }).attr("x1", 0).attr("x2", function (d) { return x(d.u25[1]); }).attr("y1", 0).attr("y2", 0);
        [["u10", "under 10%"], ["u25", "under 25%"]].forEach(function (m) {
          g.append("circle").attr("class", function (d) { return "ex-dot ex-dot--est" + sel(d); }).attr("cx", function (d) { return x(d[m[0]][1]); }).attr("cy", 0).attr("r", 5);
          g.append("text").attr("class", function (d) { return "ex-svg-value" + sel(d); }).attr("x", function (d) { return x(d[m[0]][1]); }).attr("y", -13).attr("text-anchor", "middle").text(function (d) { return F.num(d[m[0]][1], 0) + "%"; });
        });
        // name the two dots once, on the first row
        var first = byClass[0];
        [["u10", "under 10%"], ["u25", "under 25%"]].forEach(function (m) {
          c.g.append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", x(first[m[0]][1])).attr("y", ROW / 2 + 8 - 28).attr("text-anchor", "middle").text(m[1]);
        });
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.k.charAt(0).toUpperCase() + d.k.slice(1) + " ZIPs",
            rows: [
              { name: "Reach under 25%", value: F.num(d.u25[1], 1) + "% (" + F.num(d.u25[0], 1) + " to " + F.num(d.u25[2], 1) + ")", color: "est" },
              { name: "Reach under 10%", value: F.num(d.u10[1], 1) + "% (" + F.num(d.u10[0], 1) + " to " + F.num(d.u10[2], 1) + ")", color: "est" },
              { name: "Patients per low-income resident", value: F.pct(d.pen[1], 1) },
            ],
            note: "Share of the class's low-income residents. 80% range in brackets.",
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
      },
    });
    Ex.dataTable($("table-gaps"), {
      caption: "Share of low-income residents in ZIP areas where centers reach under 10% and under 25%, with the 80% range of 2,000 draws.",
      label: "Scrollable table of reach by ZIP class",
      columns: [
        { key: "k", label: "ZIP class", format: function (v) { return v.charAt(0).toUpperCase() + v.slice(1); } },
        { key: "zctas", label: "ZIP areas", format: F.int },
        { key: "low", label: "Low-income residents", format: F.int },
        { key: "u25", label: "Under 25% reached", format: function (v) { return F.num(v[1], 1) + "% (" + F.num(v[0], 1) + " to " + F.num(v[2], 1) + ")"; } },
        { key: "u10", label: "Under 10% reached", format: function (v) { return F.num(v[1], 1) + "% (" + F.num(v[0], 1) + " to " + F.num(v[2], 1) + ")"; } },
        { key: "pen", label: "Patients per low-income resident", format: function (v) { return F.pct(v[1], 1); } },
        { key: "notp", label: "Residents who are not patients", format: function (v) { return F.int(v[1]); } },
      ],
      rows: byClass,
    });

    /* ---------- checks: leave-one-center-out ---------- */
    var CG = D.check_c_groups;
    var checkRows = [["all", "All centers"], ["urban", "Urban"], ["rural", "Rural"], ["single_site", "Single-site"]].map(function (r) {
      var g = CG[r[0]];
      return { key: r[0], name: r[1], centers: g.centers, model: g.model_weighted, near: g.nearest_weighted, pop: g.population_weighted, mmean: g.model_mean, nmean: g.nearest_mean, pmean: g.population_mean };
    });
    $("checks-def").textContent =
      "Each dot is the share of a held-out center's patients who live in the 20 ZIP areas a rule picked, weighted by center size, with no data on that center except its site locations. Rules: the model, the 20 ZIPs nearest the center's sites, the 20 ZIPs with the most low-income residents within 60 miles.";
    Ex.chart($("chart-checks"), {
      label: "Dot plot of the share of held-out centers' patients living in the model's top 20 ZIPs, the 20 nearest ZIPs and the 20 ZIPs with most low-income residents. The model finds " + F.num(checkRows[0].model * 100, 0) + " of 100 across all centers, the nearest ZIPs " + F.num(checkRows[0].near * 100, 0) + ".",
      margin: function (w) {
        return { top: 30, right: w < 520 ? 34 : 56, bottom: 28, left: w < 520 ? 74 : 104 };
      },
      height: function () {
        return checkRows.length * 50 + 66;
      },
      render: function (c) {
        var ROW = 50, h = checkRows.length * ROW;
        var x = d3.scaleLinear().domain([0, 1]).range([0, c.width]);
        axisX(c, x, c.narrow ? 3 : 5, h, function (v) { return Math.round(v * 100); });
        var g = c.g.selectAll("g.ex-mark").data(checkRows).join("g").attr("class", "ex-mark").attr("transform", function (d, i) { return "translate(0," + (i * ROW + ROW / 2 + 6) + ")"; });
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", -ROW / 2).attr("width", c.w).attr("height", ROW);
        g.append("text").attr("class", function (d, i) { return "ex-svg-label" + (i === 0 ? " ex-sel" : ""); }).attr("x", -12).attr("dy", "0.35em").attr("text-anchor", "end").text(function (d) { return d.name; });
        g.append("line").attr("class", "ex-stem p7-stem-grey").attr("x1", function (d) { return x(d.pop); }).attr("x2", function (d) { return x(d.model); }).attr("y1", 0).attr("y2", 0);
        g.append("circle").attr("class", "ex-dot p7-dot-pop").attr("cx", function (d) { return x(d.pop); }).attr("cy", 0).attr("r", 4);
        g.append("circle").attr("class", "ex-dot p7-dot-near").attr("cx", function (d) { return x(d.near); }).attr("cy", 0).attr("r", 4.5);
        g.append("circle").attr("class", "ex-dot ex-dot--obs").attr("cx", function (d) { return x(d.model); }).attr("cy", 0).attr("r", 5);
        g.append("text").attr("class", "ex-svg-value").attr("x", function (d) { return x(d.model) + 11; }).attr("dy", "0.35em").text(function (d) { return F.num(d.model * 100, 0); });
        var f = checkRows[0], y0 = ROW / 2 + 6;
        [[f.model, "model", -15], [f.near, "20 nearest ZIPs", 19], [f.pop, "most residents", -15]].forEach(function (m) {
          c.g.append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", x(m[0])).attr("y", y0 + m[2]).attr("text-anchor", "middle").text(m[1]);
        });
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.name + ", " + d.centers + " centers",
            rows: [
              { name: "Model's top 20", value: F.num(d.model * 100, 1), color: "obs" },
              { name: "20 nearest ZIPs", value: F.num(d.near * 100, 1) },
              { name: "20 most low-income residents", value: F.num(d.pop * 100, 1) },
            ],
            note: "Patients out of 100, weighted by center size. Plain mean over centers: " + F.num(d.mmean * 100, 0) + ", " + F.num(d.nmean * 100, 0) + ", " + F.num(d.pmean * 100, 0) + ".",
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
      },
    });
    Ex.dataTable($("table-checks"), {
      caption: "Patients out of 100 living in the 20 ZIP areas each rule picked, weighted by center size, and the plain mean over centers.",
      label: "Scrollable table of the leave-one-center-out check",
      columns: [
        { key: "name", label: "Centers held out" },
        { key: "centers", label: "Centers", format: F.int },
        { key: "model", label: "Model", format: function (v) { return F.num(v * 100, 1); } },
        { key: "near", label: "20 nearest ZIPs", format: function (v) { return F.num(v * 100, 1); } },
        { key: "pop", label: "20 most low-income residents", format: function (v) { return F.num(v * 100, 1); } },
        { key: "mmean", label: "Model, mean", format: function (v) { return F.num(v * 100, 1); } },
        { key: "nmean", label: "Nearest, mean", format: function (v) { return F.num(v * 100, 1); } },
        { key: "pmean", label: "Most residents, mean", format: function (v) { return F.num(v * 100, 1); } },
      ],
      rows: checkRows,
    });

    /* ---------- limits and methods lists, filled from numbers.json ---------- */
    (function () {
      var ul = $("limits-list");
      N.limits.forEach(function (t) {
        ul.appendChild(Ex.el("li", { text: t }));
      });
      var cl = $("checks-list"), r1 = function (v) { return F.num(v, 1); };
      var Ck = N.checks, A_ = Ck.A.cells_up_to_39.by_size.all, Bk = Ck.B, Cc = Ck.C, Dd = Ck.D, Ee = Ck.E, Ff = Ck.F;
      var fx = N.projection.fixtures;
      var items = [
        ["Hidden cells.", "We hid visible cells under 40 patients at " + F.int(Ck.A.cells_up_to_39.centers) + " centers and gave the sampler only each center's exact hidden total. The fitted expectation placed small cells worse than an equal split (mean error " + r1(A_.mae_poisson) + " against " + r1(A_.mae_equal_split) + " patients), so placement uses a flat prior with the exact sums. One placed cell is nearly the whole 1 to 15 range. ZIP counts move, national totals do not."],
        ["Random holdout.", "We held out " + F.pct(Bk.share_of_pairs, 1) + " of center-by-ZIP cells (" + F.int(Bk.held_out_pairs) + " pairs). Rank correlation on cells with patients: model " + F.num(Bk.gravity.spearman_cells_with_patients, 2) + ", two-step floating catchment " + F.num(Bk.two_step_floating_catchment.spearman_cells_with_patients, 2) + ", population only " + F.num(Bk.population_only.spearman_cells_with_patients, 2) + ". The 80% intervals cover " + pc(Bk.interval_80_coverage) + " of held-out cells, so they are wider than needed."],
        ["Leave one center out.", F.int(Cc.centers) + " centers in " + Cc.folds + " folds. Patients in the model's top 20 ZIPs: " + r1(100 * Cc.top20_model_patient_weighted) + " of 100 weighted by center size, " + r1(100 * Cc.top20_model_mean) + " as a mean over centers. The 20 nearest ZIPs: " + r1(100 * Cc.top20_nearest_zips_patient_weighted) + " and " + r1(100 * Cc.top20_nearest_zips_mean) + ". The 20 ZIPs with the most low-income residents: " + r1(100 * Cc.top20_population_only_patient_weighted) + " and " + r1(100 * Cc.top20_population_only_mean) + ". The model beats the nearest-ZIPs rule for " + pc(Cc.share_centers_model_beats_nearest) + " of centers, and for " + pc(Cc.by_sites_bin["1"].share_centers_model_beats_nearest) + " of the " + Cc.by_sites_bin["1"].centers + " single-site centers, the closest to a new site. Its total patients fall within a factor of two for " + pc(Cc.total_ratio_within_factor_2) + " of centers."],
        ["Openings in 2025.", "Fit on UDS 2024, then predict the change in patients within 5 miles of the " + Dd.sites_evaluated + " sites added to scope in the first half of 2025, against matched control ZIPs. Median predicted gain " + F.int(Dd.median_predicted_change) + " patients, observed " + F.int(Dd.median_observed_excess) + ": " + r1(Dd.predicted_over_observed_median) + " times too high, " + r1(Dd.exposure_scaled.predicted_over_observed_median) + " times after scaling for the part of the year a site was open. Rank correlation " + F.num(Dd.spearman_predicted_vs_observed, 2) + ". The observed change fell inside the 80% interval for " + pc(Dd.observed_inside_80_interval_params_only) + " of sites. This test failed, so the projection is untested against openings and capacity is an input. Closed sites are not in HRSA's file."],
        ["HRSA's published reach.", "For " + F.int(Ee.zctas_compared_low_income_penetration) + " ZIP areas, small ones included, our reach correlates " + F.num(Ee.pearson_low_income_penetration, 2) + " with HRSA's published penetration (" + F.num(Ee.pearson_low_income_penetration_without_small_zips, 2) + " for the " + F.int(Ee.zctas_compared_without_small_zips) + " that are not small, the ones with reach in the downloadable table; median ratio " + F.num(Ee.median_ratio_ours_to_hrsa, 2) + ": ours is lower by about the income scaling). HRSA uses the same UDS ZIP table, so this checks our joins and denominators, not the model. Our ranking of people who are not patients correlates " + F.num(Ee.spearman_not_patients_count_vs_hrsa_uns, 2) + " with HRSA's Unmet Need Score: a different concept. The ten largest disagreements are in " + Object.keys(Ee.largest_disagreements_by_state).join(", ") + ". Read those rows with care."],
        ["Sensitivity.", "Of the top 50 ZIPs by residents who are not patients, " + Ff.top50_not_patients.without_income_scaling_of_patients + " stay if patients are not scaled to income and " + Ff.top50_not_patients.total_population_base + " stay if all residents are the base. Of the top 50 by new patients at one capacity, " + Ff.top50_new_patients_at_capacity.pairs_within_40_miles + " stay with a 40-mile cut-off, " + Ff.top50_new_patients_at_capacity.pairs_within_100_miles + " with 100 miles, " + Ff.top50_new_patients_at_capacity.total_population_base + " with all residents as the base and " + Ff.top50_new_patients_at_capacity.sites_added_in_2026_included + " with 2026 sites added, but " + Ff.top50_new_patients_at_capacity.zips_within_1pct_of_the_50th_value + " ZIPs sit within 1% of the 50th value, so that list is mostly ties. The median share of a site's patients who use no center today is " + F.num(Ff.share_new_by_zip_p10_p50_p90.main_page_sets[1], 2) + " with low-income residents as the market and " + F.num(Ff.share_new_by_zip_p10_p50_p90.total_population_base[1], 2) + " with all residents."],
        ["Two-step catchment.", "Its access score at " + N.checks.sfca_vs_gravity.radius_miles + " miles correlates " + F.num(N.checks.sfca_vs_gravity.spearman_access_vs_penetration, 2) + " with our reach and " + F.num(N.checks.sfca_vs_gravity.spearman_access_vs_not_patients_rank, 2) + " with our ranking of people who are not patients. " + F.num(N.checks.sfca_vs_gravity.lowest_tenth_by_access_also_lowest_tenth_by_penetration_pct, 0) + "% of the ZIPs in its lowest tenth are also in ours."],
        ["Refits.", N.model.bootstrap_convergence.stopped_at_cap + " of " + N.model.bootstrap_convergence.refits + " bootstrap refits stopped at the " + F.int(N.model.bootstrap_convergence.iteration_cap) + "-iteration cap. We continued " + N.model.bootstrap_convergence.continued_refits.refits + " of them for " + F.int(N.model.bootstrap_convergence.continued_refits.extra_iterations) + " more iterations: the decay parameters moved by under " + F.num(100 * Math.max(N.model.bootstrap_convergence.continued_refits.max_relative_change_rho, N.model.bootstrap_convergence.continued_refits.max_relative_change_gamma), 1) + "% and the new-site level by " + F.num(100 * N.model.bootstrap_convergence.continued_refits.max_relative_change_new_site_level_chc, 2) + "%. The level at a zero center effect is not pinned down; the projection does not use it."],
        ["Two worked cases.", "ZIP " + fx.served_by_three_centers.capacity_5000.zcta + " (" + fx.served_by_three_centers.capacity_5000.county + ", " + fx.served_by_three_centers.capacity_5000.state + "), an urban ZIP served by " + fx.served_by_three_centers.capacity_5000.centers_with_patients + " centers: " + pc(fx.served_by_three_centers.capacity_5000.share_new_p10_p50_p90[1]) + " of a site's patients use no center today. ZIP " + fx.no_site_within_20_miles.capacity_5000.zcta + " (" + fx.no_site_within_20_miles.capacity_5000.county + ", " + fx.no_site_within_20_miles.capacity_5000.state + "), rural with no site within 20 miles: " + pc(fx.no_site_within_20_miles.capacity_5000.share_new_p10_p50_p90[1]) + ". The tool reproduces both."],
      ];
      items.forEach(function (it) {
        cl.appendChild(Ex.el("li", {}, [Ex.el("strong", { text: it[0] + " " }), document.createTextNode(it[1])]));
      });
      var fl = $("facts-list"), fa = D.facts, np = fa.new_access_points_2026, mc = fa.medicaid_community_engagement;
      [
        ["New Access Points, 2026", np.new_sites + " new sites and about $" + np.millions_usd + " million announced " + np.announced + " (" + np.source + "). Checked " + np.checked + ".", np.url],
        ["Medicaid work requirements", "States start no later than " + mc.states_start_no_later_than + ", with renewals " + mc.renewals_for_expansion_adults + " for expansion adults (" + mc.source + "). Checked " + mc.checked + ".", mc.url],
        ["HRSA grant rules", fa.link_only[0].status, fa.link_only[0].url],
      ].forEach(function (r) {
        fl.appendChild(Ex.el("dt", {}, [Ex.el("a", { href: safeUrl(r[2]), text: r[0] })]));
        fl.appendChild(Ex.el("dd", { text: r[1] }));
      });
      var sl = $("sources-list");
      N.sources.forEach(function (s) {
        sl.appendChild(Ex.el("dt", {}, [Ex.el("a", { href: safeUrl(s[1]), text: s[0] })]));
        sl.appendChild(Ex.el("dd", { text: F.int(+s[2].replace("bytes=", "")) + " bytes, " + s[3] + ". Downloaded " + N.data_downloaded + "." }));
      });
      var mp = N.model.main, bs = N.model.bootstrap_spread_p10_p50_p90;
      var prow = [2, 1, 0].map(function (k) {
        var cn = CLASSES[k], sp = function (o) { return F.num(o[1], 2) + " (" + F.num(o[0], 2) + " to " + F.num(o[2], 2) + ")"; };
        return { cls: cn.charAt(0).toUpperCase() + cn.slice(1), zctas: N.reach.by_density_class[cn].zctas, rho: F.num(mp.rho[k], 2), rhoB: sp(bs.rho[cn]), gamma: F.num(mp.gamma[k], 2), gammaB: sp(bs.gamma[cn]) };
      });
      Ex.dataTable($("table-params"), {
        caption: "Distance decay f(d) = exp(-(d / rho)^gamma) by ZIP class: main fit, and the median and 10th to 90th percentile of the bootstrap refits.",
        label: "Scrollable table of model parameters",
        columns: [
          { key: "cls", label: "ZIP class" }, { key: "zctas", label: "ZIP areas", format: F.int }, { key: "rho", label: "rho, miles" }, { key: "rhoB", label: "rho, refits" }, { key: "gamma", label: "gamma" }, { key: "gammaB", label: "gamma, refits" },
        ],
        rows: prow,
      });
    })();

    /* ---------- the inputs ---------- */
    var centerItems = D.centers.map(function (c, k) {
      return { value: String(k), label: titleCase(c.name) + ", " + c.state, hint: c.state, search: c.grant + " " + c.name };
    });
    var zipItems = null;
    var combo = null;
    function buildPicker() {
      var host = $("pick-start");
      if (combo && combo.destroy) combo.destroy();
      combo = null;
      host.className = "";
      host.textContent = "";
      if (S.start === "center") {
        combo = Ex.combobox(host, {
          id: "center", label: "Health center", placeholder: "Search " + F.int(nCenters) + " centers", noun: "centers", items: centerItems, value: String(S.ci), maxResults: 50,
          onSelect: function (it) {
            if (!it) return;
            S.ci = +it.value;
            setAnchor();
          },
        });
      } else if (S.start === "point") {
        buildPoint(host);
      } else {
        if (!zipItems)
          zipItems = Array.prototype.map.call(C.zip, function (zz, z) {
            return { value: String(z), label: zipStr(z) + " " + placeOf(z), hint: stateOf(z), search: countyOf(z) };
          });
        combo = Ex.combobox(host, {
          id: "zip", label: "ZIP code", placeholder: "Search " + F.int(n) + " ZIP areas", noun: "ZIP areas", items: zipItems, value: S.az != null ? String(S.az) : undefined, maxResults: 50,
          onSelect: function (it) {
            if (!it) return;
            S.az = +it.value;
            setAnchor();
          },
        });
      }
    }
    function buildPoint(host) {
      host.className = "ex-field";
      var input = Ex.el("input", { class: "ex-input", id: "f-ll", type: "text", inputmode: "decimal", autocomplete: "off", placeholder: "40.44, -79.99", "aria-describedby": "h-ll e-ll", value: S.pt ? S.pt.lat.toFixed(4) + ", " + S.pt.lon.toFixed(4) : false });
      var btn = Ex.el("button", { class: "ex-link", type: "button", text: "Place" });
      var err = Ex.el("div", { class: "ex-error", id: "e-ll", hidden: true });
      host.appendChild(Ex.el("label", { class: "ex-label", for: "f-ll", text: "Latitude, longitude" }));
      host.appendChild(Ex.el("div", { class: "p7-ll" }, [input, btn]));
      host.appendChild(Ex.el("div", { class: "ex-hint", id: "h-ll", text: "Decimal degrees, as copied from a map. The point needs a ZIP area within " + AREA_R + " miles." }));
      host.appendChild(err);
      function go() {
        var m = input.value.trim().match(/^(-?\d+(?:\.\d+)?)\s*[,\s]\s*(-?\d+(?:\.\d+)?)$/);
        var la = m ? +m[1] : NaN, lo = m ? +m[2] : NaN;
        var msg = "";
        if (!m || la < 17 || la > 72 || lo > -60 || lo < -180) msg = "Enter latitude and longitude in decimal degrees, for example 40.44, -79.99.";
        else if (!within(la, lo, AREA_R).z.length) msg = "No ZIP area lies within " + AREA_R + " miles of that point.";
        err.textContent = msg;
        err.hidden = !msg;
        input.setAttribute("aria-invalid", msg ? "true" : "false");
        if (msg) return;
        S.pt = { lat: la, lon: lo };
        S.user = false;
        setAnchor();
      }
      btn.addEventListener("click", go);
      input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          go();
        }
      });
    }
    function setAnchor() {
      S.shown = 6;
      A = S.start === "center" ? areaFromCenter(S.ci) : (function () { var w0 = S.start === "zip" ? within(lat[S.az], lon[S.az], AREA_R) : within(S.pt.lat, S.pt.lon, AREA_R); return { z: w0.z, d: w0.d }; })();
      sortArea();
      areaStats();
      renderArea();
      // a placed site stays only if it lies in the new area; otherwise the best ZIP of the area (or the ZIP itself) is placed
      var cand;
      if (S.start === "zip") cand = { z: S.az, lat: lat[S.az], lon: lon[S.az] };
      else if (S.start === "point") cand = { z: null, lat: S.pt.lat, lon: S.pt.lon };
      else {
        var keep = S.cand && S.user && S.cand.z != null && A.z.indexOf(S.cand.z) >= 0;
        var top = A.rows[0];
        cand = keep ? S.cand : { z: top, lat: lat[top], lon: lon[top] };
      }
      place(cand, "auto");
      if (S.rank === "share") Ex.live("Ranked by share.");
    }
    function setCap(v, typed) {
      S.cap = v;
      if (!typed) $("f-cap").value = v;
      $("f-capr").value = v;
      capRefresh();
      if (S.cand) place(S.cand, "auto", true);
    }
    var capRefresh = Ex.range($("f-capr"), {
      format: function (v) { return F.int(v); },
      onInput: function (v) {
        $("e-cap").hidden = true;
        $("f-cap").removeAttribute("aria-invalid");
        setCap(v);
      },
    });
    $("f-cap").addEventListener("input", function () {
      var v = this.value.trim(), x = +v, ok = v !== "" && isFinite(x) && x >= CAP_MIN && x <= CAP_MAX;
      $("e-cap").hidden = ok;
      this.setAttribute("aria-invalid", ok ? "false" : "true");
      if (!ok) {
        $("e-cap").textContent = "Enter a whole number from 100 to 15,000.";
        return;
      }
      setCap(Math.round(x), true);
    });
    $("f-cap").addEventListener("change", function () {
      if (this.getAttribute("aria-invalid") === "true") {
        this.value = S.cap;
        this.setAttribute("aria-invalid", "false");
        $("e-cap").hidden = true;
      }
    });
    [].forEach.call(document.querySelectorAll("input[name=start]"), function (r) {
      r.addEventListener("change", function () {
        if (!r.checked) return;
        S.start = r.value;
        if (S.start === "zip" && S.az == null) S.az = S.cand && S.cand.z != null ? S.cand.z : A.rows[0];
        if (S.start === "point" && !S.pt) S.pt = S.cand ? { lat: S.cand.lat, lon: S.cand.lon } : { lat: lat[A.rows[0]], lon: lon[A.rows[0]] };
        buildPicker();
        S.user = false;
        setAnchor();
      });
    });
    [].forEach.call(document.querySelectorAll("input[name=ctype]"), function (r) {
      r.addEventListener("change", function () {
        if (!r.checked) return;
        S.type = +r.value;
        if (S.cand) place(S.cand, "auto");
      });
    });
    [].forEach.call(document.querySelectorAll("input[name=rank]"), function (r) {
      r.addEventListener("change", function () {
        if (!r.checked) return;
        S.rank = r.value;
        S.shown = 6;
        sortArea();
        renderArea();
        renderTable();
        chartMap.redraw();
        Ex.live("Ranked by " + (S.rank === "people" ? "people" : "share") + ".");
      });
    });
    $("more-zips").addEventListener("click", function () {
      S.shown += 20;
      renderTable();
    });
    $("reset").addEventListener("click", function () {
      var f = fresh();
      S = f;
      document.querySelector("input[name=start][value=center]").checked = true;
      document.querySelector("input[name=ctype][value='0']").checked = true;
      document.querySelector("input[name=rank][value=people]").checked = true;
      $("e-cap").hidden = true;
      $("f-cap").removeAttribute("aria-invalid");
      $("f-cap").value = S.cap;
      $("f-capr").value = S.cap;
      capRefresh();
      buildPicker();
      setAnchor();
      Ex.live("Reset to the example center.");
    });

    /* ---------- hints in the inputs disclosure ---------- */
    $("h-cap").textContent = "The median site sees " + F.int(D.default_capacity) + " patients a year; the middle half run " + F.int(D.capacity_p25_p75[0]) + " to " + F.int(D.capacity_p25_p75[1]) + ". Capacity is your input. The model says who the patients would be, not how many a site draws.";
    $("h-type").textContent = "Health center is a typical single site. Special population is a site funded only for migrant, homeless or public housing patients; it draws fewer.";
    $("h-rank").textContent = "People ranks ZIP areas by residents who are not patients. Share ranks them by the share of low-income residents who are not patients. Areas with no patients reported rank first by share.";
    $("h-area").textContent = "A center's area is every ZIP area within " + AREA_R + " miles of any of its permanent sites. For a ZIP it is " + AREA_R + " miles around that ZIP's center.";
    $("h-rankn").textContent = "The rank counts ZIP areas within " + NEAR + " miles (small and campus ones left out) on new patients at your capacity.";
    $("f-cap").value = S.cap;
    $("f-capr").value = S.cap;
    capRefresh();

    /* ---------- actions ---------- */
    function summaryText() {
      var t = [];
      t.push(areaName() + ": within " + AREA_R + " miles there are about " + a3(A.notp[1]) + " low-income residents who are not health center patients (80% range " + a3(A.notp[0]) + " to " + a3(A.notp[2]) + "), out of " + a3(A.cLow) + " low-income residents. Patients of all centers there: " + a3(A.cPat) + ".");
      if (P) {
        var q = P.q, top = P.neighbors.filter(function (x) { return x.med >= 5; }).slice(0, 3);
        t.push("A new site at " + siteName() + " with room for " + F.int(S.cap) + " patients a year: about " + r10(q.neu[1]) + " patients (80% range " + r10(q.neu[0]) + " to " + r10(q.neu[2]) + ") would use no health center today, and " + r10(q.nb[1]) + " would come from other centers" + (top.length ? ", most from " + top.map(function (x) { return nameOf(x.c) + " (" + r10(x.med) + ")"; }).join("; ") : "") + ".");
        t.push("Expected payer mix: " + PAYERS.map(function (p, k) { return pc(P.payQ[k][1]) + " " + PAYER_NAME[p].toLowerCase(); }).join(", ") + (RK ? ". Rank " + F.int(Math.round(RK.q[1])) + " of " + F.int(RK.total) + " ZIPs within " + NEAR + " miles on new patients at this capacity" : "") + ".");
      }
      t.push("An example on public data, not client work. A scenario, not a forecast. Sources: HRSA UDS 2025 and site list, Census ACS 2020-2024, Primordial Analytics model. " + location.href.split("#")[0]);
      return t.join("\n\n");
    }
    function flip(btn, text) {
      var idle = btn.getAttribute("data-idle") || btn.textContent;
      btn.setAttribute("data-idle", idle);
      btn.textContent = text;
      setTimeout(function () {
        btn.textContent = idle;
      }, 2200);
    }
    $("copy-sum").addEventListener("click", function () {
      var btn = this;
      Promise.resolve(Ex.copy(summaryText())).then(function (ok) {
        flip(btn, ok ? "Copied" : "Copy failed. Use Print brief.");
        Ex.live(ok ? "Summary copied" : "Copy failed");
      });
    });
    $("b-keep").addEventListener("click", function () {
      S.kept = snapshot();
      renderCompare();
      $("cmp-box").open = true;
      Ex.live("Site kept. Place another to compare.");
    });
    $("dl-table").addEventListener("click", function () {
      var head = ["zip", "county", "state", "density_class", "miles_to_area_center", "low_income_residents", "patients_all_centers", "share_reached_p10", "share_reached_p50", "share_reached_p90", "not_patients_p10", "not_patients_p50", "not_patients_p90", "uninsured_adults_below_200", "hrsa_published_penetration", "small_zip", "campus_zip", "no_patients_reported"];
      var dist = {};
      A.z.forEach(function (z, k) { dist[z] = A.d[k]; });
      var lines = [head.join(",")];
      A.rows.forEach(function (z) {
        var r = reachOf(z);
        lines.push([zipStr(z), countyOf(z), stateOf(z), CLASSES[C.dclass[z]], dist[z].toFixed(1), C.low[z], C.pat_total[z],
          r && !noPatients(z) ? r[0].toFixed(3) : "", r && !noPatients(z) ? r[1].toFixed(3) : "", r && !noPatients(z) ? r[2].toFixed(3) : "",
          C.notp_p10[z], C.notp_p50[z], C.notp_p90[z], C.unins[z], C.hrsa_pen[z] === NA16 ? "" : (C.hrsa_pen[z] / 1e4).toFixed(2), isSmall(z) ? 1 : 0, C.campus[z], noPatients(z) ? 1 : 0].map(csvCell).join(","));
      });
      download("zip-areas-" + (S.start === "center" ? D.centers[S.ci].grant : zipStr(S.az)) + ".csv", "text/csv;charset=utf-8", ["﻿", lines.join("\n"), "\n"]);
    });
    function brief() {
      var host = $("p7-brief");
      host.textContent = "";
      var kids = [
        Ex.el("h2", { text: document.querySelector(".ex-hero__title").textContent }),
        Ex.el("p", { text: document.querySelector(".ex-hero__question").textContent + " An example on public data, not client work." }),
        Ex.el("h3", { text: areaName() }),
        Ex.el("p", { text: "Within " + AREA_R + " miles: about " + a3(A.notp[1]) + " low-income residents are not health center patients (80% range " + a3(A.notp[0]) + " to " + a3(A.notp[2]) + ") of " + a3(A.cLow) + " low-income residents. Patients of all centers: " + a3(A.cPat) + "." }),
      ];
      if (P) {
        var q = P.q;
        kids.push(Ex.el("h3", { text: "A site at " + siteName() + ", " + F.int(S.cap) + " patients a year" }));
        kids.push(Ex.el("p", { text: "About " + r10(q.neu[1]) + " patients (80% range " + r10(q.neu[0]) + " to " + r10(q.neu[2]) + ") use no health center today. " + r10(q.nb[1]) + " come from other centers. Payer mix: " + PAYERS.map(function (p, k) { return pc(P.payQ[k][1]) + " " + PAYER_NAME[p].toLowerCase(); }).join(", ") + "." }));
      }
      var rows = A.rows.slice(0, 10);
      kids.push(Ex.el("h3", { text: "Top ZIP areas" }));
      kids.push(Ex.el("table", { class: "ex-table" }, [
        Ex.el("thead", {}, [Ex.el("tr", {}, ["ZIP", "County", "Low-income residents", "Share reached", "Not patients"].map(function (h, k) { return Ex.el("th", { scope: "col", text: h }); }))]),
        Ex.el("tbody", {}, rows.map(function (z) {
          var t = rowText(z);
          return Ex.el("tr", {}, [Ex.el("th", { scope: "row", text: t.zip }), Ex.el("td", { text: t.place }), Ex.el("td", { text: F.int(t.low) }), Ex.el("td", { text: t.reach }), Ex.el("td", { text: t.notp })]);
        })),
      ]));
      kids.push(Ex.el("p", { class: "p7-brief__src", text: "Sources: HRSA UDS 2025 and site list; Census ACS 2020-2024 tables C17002 and C27016; Primordial Analytics model. Data downloaded " + N.data_downloaded + ". Printed " + new Date().toISOString().slice(0, 10) + ". A scenario, not a forecast. " + location.href.split("#")[0] }));
      kids.forEach(function (k) { host.appendChild(k); });
    }
    $("print-brief").addEventListener("click", function () {
      brief();
      document.body.classList.add("p7-print");
      window.print();
    });
    window.addEventListener("afterprint", function () {
      document.body.classList.remove("p7-print");
      $("p7-brief").textContent = "";
    });

    /* ---------- start ---------- */
    buildPicker();
    setAnchor();
  }
});
