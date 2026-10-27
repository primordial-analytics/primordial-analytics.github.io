/* Example 12: who funds organizations like yours. Plain ES2019, no build step.
   Reads data.json (national findings, checks, the state list) and one state-<XX>.json per state, both written by
   analysis/12-health-funder-network/web_data.py (the file format is in its docstring). Nothing is modeled here: the page ranks
   funders itself from the grant rows. A funder's score is the number of distinct peers (of the kinds ticked) in the state that it
   gave to; ties go to the funder with more peers anywhere. With an organization chosen, peers in its 3-digit ZIP area count
   first (the method that won the backtest in graph.py). Choices are kept in the URL hash. */
Ex.ready(function () {
  "use strict";
  var F = Ex.fmt;
  var $ = function (id) {
    return document.getElementById(id);
  };
  var BASE = (($("main") || document.body).getAttribute("data-ex-data") || "").replace(/data\.json$/, "");
  var PAGE = 20, FEW = 10, TOP_SUGGEST = 8, TOP_PEERS = 12, MAX_FUNDERS = 16, TOP_STATE = 12, MAX_STATE_PEERS = 60, TOP_US = 20, MAX_US_PEERS = 150;

  /* columns of the state files (see web_data.py) */
  var P_EIN = 0, P_NAME = 1, P_CITY = 2, P_KIND = 3, P_TOP = 6, P_ZIP3 = 7, P_ST = 8;
  var F_EIN = 0, F_NAME = 1, F_CITY = 2, F_ST = 3, F_TYPE = 4, F_CHAN = 5, F_PRE = 6, F_WEB = 7, F_ALL = 8, F_MED = 10, F_LAST = 11, F_GEN = 12, F_NEW = 13;
  var G_F = 0, G_P = 1, G_YEAR = 2, G_AMT = 3, G_PURPOSE = 5;

  var KINDS = [
    { k: "free_clinic", code: "fc", label: "free clinics" },
    { k: "health_center", code: "hc", label: "health centers" },
    { k: "care_provider", code: "cp", label: "other care nonprofits" },
  ];
  var TYPE_LABEL = { private: "Private foundation", charity: "Community foundation or charity", hospital: "Hospital or health system" };
  var NAMES = {
    AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California", CO: "Colorado", CT: "Connecticut", DE: "Delaware", DC: "District of Columbia", FL: "Florida", GA: "Georgia", GU: "Guam", US: "all states",
    HI: "Hawaii", ID: "Idaho", IL: "Illinois", IN: "Indiana", IA: "Iowa", KS: "Kansas", KY: "Kentucky", LA: "Louisiana", ME: "Maine", MD: "Maryland", MA: "Massachusetts", MI: "Michigan",
    MN: "Minnesota", MS: "Mississippi", MO: "Missouri", MT: "Montana", NE: "Nebraska", NV: "Nevada", NH: "New Hampshire", NJ: "New Jersey", NM: "New Mexico", NY: "New York",
    NC: "North Carolina", ND: "North Dakota", OH: "Ohio", OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania", PR: "Puerto Rico", RI: "Rhode Island", SC: "South Carolina", SD: "South Dakota",
    TN: "Tennessee", TX: "Texas", UT: "Utah", VT: "Vermont", VA: "Virginia", VI: "U.S. Virgin Islands", WA: "Washington", WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming",
  };

  Ex.loadData().then(init, function (err) {
    console.error(err);
    ["rank-list", "chart-degree", "chart-type", "chart-pre", "chart-kinds"].forEach(function (id) {
      Ex.showError($(id), "The data did not load. The downloads below have the same numbers.");
    });
  });

  /* ---------- small helpers ---------- */
  function get(D, path) {
    return path.split(".").reduce(function (o, p) {
      return o == null ? o : o[p];
    }, D);
  }
  function fmtBy(code, v) {
    var ci = function (a) {
      return F.pct(a[0], 0) + " (" + F.pct(a[1], 0) + " to " + F.pct(a[2], 0) + ")";
    };
    switch (code) {
      case "int": return F.int(v);
      case "pct0n": return F.num(v, 0);
      case "pct0frac": return F.pct(v, 0);
      case "acc": return ci([v.accuracy].concat(v.accuracy_ci));
      case "prec": return ci([v.precision].concat(v.precision_ci));
      case "rec": return ci([v.recall].concat(v.recall_ci));
      case "share": return ci([v[0], Math.max(0, v[1][0]), v[1][1]]);
      case "hit": return ci([v.hit_rate, v.hit_lo, v.hit_hi]);
      default: return String(v);
    }
  }
  /* The filings are in capitals. Title-case them; text that already has lower case is left alone. */
  var SMALL = { a: 1, an: 1, and: 1, at: 1, by: 1, de: 1, for: 1, in: 1, of: 1, on: 1, or: 1, the: 1, to: 1 };
  var KEEP = { llc: 1, llp: 1, lp: 1, usa: 1, ii: 1, iii: 1, iv: 1, hiv: 1, aids: 1, ymca: 1, ywca: 1, fqhc: 1, dba: 1, pc: 1, nyc: 1 };
  function nice(s) {
    if (!s || s !== s.toUpperCase()) return s || "";
    return s.toLowerCase().split(" ").map(function (w, i) {
      var core = w.replace(/[^a-z]/g, "");
      if (KEEP[core] || (core.length && core.length <= 3 && !/[aeiouy]/.test(core))) return w.toUpperCase();
      if (i && SMALL[core]) return w;
      return w.replace(/^mc([a-z])/, function (m, c) { return "mc" + c.toUpperCase(); }).replace(/(^|[-/(])([a-z])/g, function (m, a, b) { return a + b.toUpperCase(); });
    }).join(" ");
  }
  function purposeText(s) {
    if (!s) return "";
    s = s.trim();
    return s === s.toUpperCase() ? s.charAt(0) + s.slice(1).toLowerCase() : s;
  }
  function siteUrl(w) {
    var s = String(w || "").trim().toLowerCase().replace(/^https?:\/\//, "").replace(/\/+$/, "");
    return /^[a-z0-9-]+(\.[a-z0-9-]+)+(\/[^\s"'<>]*)?$/.test(s) ? { href: "https://" + s, text: s.replace(/^www\./, "") } : null;
  }
  function usd(v) {
    return v == null ? "—" : F.usd(v);
  }
  function pctOrDash(v) {
    return v == null ? "—" : F.pct(v, 0);
  }
  function median(a) {
    var s = a.slice().sort(function (x, y) { return x - y; });
    return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : 0;
  }
  function typeLabel(f) {
    if (f[F_CHAN] === "matching") return "Matching program";
    // a return that reports donor-advised funds is typed "daf", which includes most community foundations; only the national sponsors are listed as funds
    if (f[F_TYPE] === "daf") return f[F_CHAN] === "national_daf" ? "Donor-advised fund" : TYPE_LABEL.charity;
    return TYPE_LABEL[f[F_TYPE]] || TYPE_LABEL.charity;
  }

  function init(D) {
    var N = D.numbers || {};
    var STATES = D.states, byAbbr = {};
    STATES.forEach(function (s) { byAbbr[s.st] = s; });
    byAbbr.US = { st: "US" }; // all states: state-US.json holds the leading funders and every organization they fund
    var DEFAULT = STATES.slice().sort(function (a, b) { return b.peers - a.peers; })[0].st;

    /* ---------- numbers written into the text from data.json ---------- */
    [].forEach.call(document.querySelectorAll("[data-n]"), function (el) {
      var v = get(D, el.getAttribute("data-n"));
      if (v != null && !(typeof v === "number" && isNaN(v))) el.textContent = fmtBy(el.getAttribute("data-f"), v);
    });

    /* ---------- state of the tool ---------- */
    function fresh() {
      return { st: DEFAULT, org: null, kinds: { free_clinic: 1, health_center: 1, care_provider: 1 }, daf: 0, pre: 0 };
    }
    var S = fresh();
    var cur = { abbr: null, d: null, token: 0, p: null, net: null };
    var shown = PAGE, expanded = {}, touched = false;

    /* ---------- the URL hash: #st=OR&org=<EIN>&k=fc.hc&daf=1&pre=1 ---------- */
    function readHash() {
      var h = location.hash.replace(/^#/, "");
      if (h.indexOf("=") < 0) return null;
      var q = {};
      h.split("&").forEach(function (kv) {
        var i = kv.indexOf("=");
        if (i > 0) {
          try { q[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1)); } catch (e) { /* a bad escape is ignored */ }
        }
      });
      return q;
    }
    function fromHash(q) {
      var s = fresh();
      if (q.st && byAbbr[q.st.toUpperCase()]) s.st = q.st.toUpperCase();
      if (/^\d{9}$/.test(q.org || "")) s.org = q.org;
      if (q.k != null) {
        var on = q.k.split(".");
        KINDS.forEach(function (K) { s.kinds[K.k] = on.indexOf(K.code) >= 0 ? 1 : 0; });
      }
      s.daf = q.daf === "1" ? 1 : 0;
      s.pre = q.pre === "1" ? 1 : 0;
      s.f = /^\d{9}$/.test(q.f || "") ? q.f : null;
      return s;
    }
    function writeHash() {
      if (!touched) return;
      var on = KINDS.filter(function (K) { return S.kinds[K.k]; }).map(function (K) { return K.code; });
      var p = ["st=" + S.st];
      if (S.org) p.push("org=" + S.org);
      if (on.length !== KINDS.length) p.push("k=" + on.join("."));
      if (S.daf) p.push("daf=1");
      if (S.pre) p.push("pre=1");
      if (flow) p.push("f=" + flow.ein);
      try { history.replaceState(null, "", location.pathname + location.search + "#" + p.join("&")); } catch (e) { /* no history API: the choices still work */ }
    }

    /* ---------- pickers ---------- */
    var stateCombo = Ex.combobox($("pick-state"), {
      id: "state", label: "State", hint: "Clear it to see all states.", placeholder: "Search states", noun: "states", noun_one: "state",
      items: [{ value: "US", label: "All states", hint: "US", search: "united states national" }].concat(STATES.map(function (s) { return { value: s.st, label: NAMES[s.st] || s.st, hint: s.st }; }).sort(function (a, b) { return a.label < b.label ? -1 : 1; })),
      onSelect: function (it) {
        // clearing the state shows all states
        touched = true;
        show(it ? it.value : "US", null);
      },
    });
    var orgCombo = Ex.combobox($("pick-org"), {
      id: "org", label: "Your organization", hint: "Optional. Leave it empty to see every funder in the state.", placeholder: "Search by name", noun: "organizations", noun_one: "organization", items: [],
      emptyText: "Not in the list. Leave this empty to see every funder.",
      onSelect: function (it) {
        touched = true;
        dropFlow();
        S.org = it ? it.value : null;
        shown = PAGE;
        update();
      },
    });

    /* ---------- one state's rows ---------- */
    function prep(d) {
      d.pIdx = {};
      d.peers.forEach(function (p, i) { d.pIdx[p[P_EIN]] = i; });
      d.byF = d.funders.map(function () { return []; });
      d.byP = d.peers.map(function () { return []; });
      d.fp = {};
      d.grants.forEach(function (g, i) {
        d.byF[g[G_F]].push(i);
        d.byP[g[G_P]].push(i);
        d.fp[g[G_F] + "|" + g[G_P]] = 1;
      });
      if (d.counts) {
        // all states: the file holds only the leading funders, so the totals come with it
        d.nDaf = d.counts["fc.hc.cp|1|0"] - d.counts["fc.hc.cp|0|0"];
        d.nPre = d.counts["fc.hc.cp|1|0"] - d.counts["fc.hc.cp|1|1"];
        return d;
      }
      d.nDaf = d.funders.filter(function (f) { return f[F_CHAN] !== "direct"; }).length;
      d.nPre = d.funders.filter(function (f) { return f[F_PRE]; }).length;
      d.kindN = {};
      d.peers.forEach(function (p) { d.kindN[p[P_KIND]] = (d.kindN[p[P_KIND]] || 0) + 1; });
      return d;
    }
    function show(abbr, org, then) {
      var token = ++cur.token;
      $("results").setAttribute("aria-busy", "true");
      Ex.loadData(BASE + "state-" + abbr + ".json").then(function (raw) {
        if (token !== cur.token) return;
        var d = raw.pIdx ? raw : prep(raw);
        cur.abbr = abbr;
        cur.d = d;
        S.st = abbr;
        S.org = org && d.pIdx[org] != null ? org : null;
        shown = PAGE;
        expanded = {};
        // all states has no organization picker: an organization's funders are in its state's file
        if (d.counts) S.org = null;
        $("pick-org").hidden = !!d.counts;
        orgCombo.setItems(d.counts ? [] : d.peers.map(function (p) { return { value: p[P_EIN], label: nice(p[P_NAME]), hint: nice(p[P_CITY]), search: p[P_EIN] }; }));
        orgCombo.setValue(S.org, { silent: true });
        stateCombo.setValue(abbr, { silent: true });
        $("results").removeAttribute("aria-busy");
        syncControls();
        update();
        if (then) then();
      }, function () {
        $("results").removeAttribute("aria-busy");
        Ex.showError($("rank-list"), "This state's data did not load. The downloads below have the same numbers.");
      });
    }

    /* ---------- the ranking ---------- */
    function peerFilter(d) {
      var ok = [], n = 0;
      d.peers.forEach(function (p, i) {
        ok[i] = !!S.kinds[p[P_KIND]];
        if (ok[i]) n++;
      });
      if (d.counts) n = d3.sum(KINDS, function (K) { return S.kinds[K.k] ? d.kindN[K.k] || 0 : 0; });
      return { ok: ok, n: n };
    }
    function countKey() {
      return KINDS.filter(function (K) { return S.kinds[K.k]; }).map(function (K) { return K.code; }).join(".") + "|" + S.daf + "|" + S.pre;
    }
    function currentFunders(d, oi) {
      var by = {};
      d.byP[oi].forEach(function (gi) {
        var g = d.grants[gi], o = by[g[G_F]] || (by[g[G_F]] = { fi: g[G_F], total: 0, years: {} });
        o.total += g[G_AMT] || 0;
        o.years[g[G_YEAR]] = 1;
      });
      return Object.keys(by).map(function (k) { return by[k]; }).sort(function (a, b) {
        return b.total - a.total || (d.funders[a.fi][F_NAME] < d.funders[b.fi][F_NAME] ? -1 : 1);
      });
    }
    function compute() {
      var d = cur.d, pf = peerFilter(d), oi = S.org != null ? d.pIdx[S.org] : -1;
      var mine = {}, cf = oi >= 0 ? currentFunders(d, oi) : [];
      cf.forEach(function (c) { mine[c.fi] = 1; });
      var rows = [], zip3 = oi >= 0 ? d.peers[oi][P_ZIP3] : null;
      d.funders.forEach(function (f, fi) {
        if (mine[fi] || (!S.daf && f[F_CHAN] !== "direct") || (S.pre && f[F_PRE])) return;
        var seen = {}, n = 0, near = 0, gl = [];
        d.byF[fi].forEach(function (gi) {
          var pi = d.grants[gi][G_P];
          if (!pf.ok[pi] || pi === oi) return;
          gl.push(gi);
          if (!seen[pi]) {
            seen[pi] = 1;
            n++;
            if (d.peers[pi][P_ZIP3] === zip3) near++;
          }
        });
        if (n) rows.push({ fi: fi, n: n, near: near, grants: gl });
      });
      rows.sort(function (a, b) {
        var fa = d.funders[a.fi], fb = d.funders[b.fi];
        return b.near - a.near || b.n - a.n || fb[F_ALL] - fa[F_ALL] || (fa[F_NAME] < fb[F_NAME] ? -1 : 1);
      });
      // all states: the file holds every funder down to the d.top-th for each choice, ties included, and no further
      if (d.counts && rows.length > d.top) {
        var cut = rows[d.top - 1].n;
        rows = rows.filter(function (r) { return r.n >= cut; });
      }
      return { ok: pf.ok, nPeers: pf.n, oi: oi, cf: cf, rows: rows };
    }

    /* ---------- controls ---------- */
    function syncControls() {
      var d = cur.d;
      [].forEach.call(document.querySelectorAll('input[name="kind"]'), function (c) {
        c.checked = !!S.kinds[c.value];
        $("n-" + c.value).textContent = F.int(d.kindN[c.value] || 0);
      });
      $("f-daf").checked = !!S.daf;
      $("f-pre").checked = !!S.pre;
      $("n-daf").textContent = F.int(d.nDaf);
      $("n-pre").textContent = F.int(d.nPre);
    }
    [].forEach.call(document.querySelectorAll('input[name="kind"]'), function (c) {
      c.addEventListener("change", function () {
        touched = true;
        S.kinds[c.value] = c.checked ? 1 : 0;
        shown = PAGE;
        update();
      });
    });
    $("f-daf").addEventListener("change", function () {
      touched = true;
      S.daf = this.checked ? 1 : 0;
      shown = PAGE;
      update();
    });
    $("f-pre").addEventListener("change", function () {
      touched = true;
      S.pre = this.checked ? 1 : 0;
      shown = PAGE;
      update();
    });
    $("reset").addEventListener("click", function () {
      S = fresh();
      touched = false;
      dropFlow();
      try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* see writeHash */ }
      show(DEFAULT, null);
    });
    $("more").addEventListener("click", function () {
      shown += PAGE;
      renderList(cur.p);
      var items = $("rank-list").querySelectorAll(".p12-row");
      var first = items[shown - PAGE];
      if (first) first.querySelector("button").focus();
    });
    // on a phone the two lists of checkboxes start closed, so the answer sits near the pickers
    if (window.matchMedia("(max-width: 959px)").matches) $("p12-more").open = false;
    window.addEventListener("hashchange", function () {
      var q = readHash();
      if (!q) return;
      var s = fromHash(q);
      S = s;
      var keep = flow && s.f === flow.ein;
      if (!keep) dropFlow();
      show(s.st, s.org, !keep && s.f && function () { openFlow(s.f); });
    });

    /* ---------- the answer ---------- */
    function orgName() {
      var p = cur.p;
      return p.oi >= 0 ? nice(cur.d.peers[p.oi][P_NAME]) : "";
    }
    function kindsText(d, ok) {
      var parts = [];
      KINDS.forEach(function (K) {
        var n = 0;
        d.peers.forEach(function (p, i) { if (ok[i] && p[P_KIND] === K.k) n++; });
        if (n) parts.push(F.int(n) + " " + K.label);
      });
      return parts.join(", ");
    }
    function update() {
      var d = cur.d;
      if (!d) return;
      var p = (cur.p = compute()), name = NAMES[cur.abbr] || cur.abbr, rows = p.rows, msg = [];
      writeHash();
      if (!KINDS.some(function (K) { return S.kinds[K.k]; })) msg.push("Tick at least one kind of organization.");
      else if (!p.nPeers) msg.push("No organization of these kinds in " + name + " is in the data.");
      else if (p.nPeers < FEW) msg.push("Only " + F.plural(p.nPeers, "organization") + " like yours in " + name + " " + (p.nPeers === 1 ? "is" : "are") + " in the data, so each funder's count rests on few organizations.");
      if (p.oi >= 0 && !p.cf.length) msg.push("We found no grants to " + orgName() + " in 2022 to 2025. It may file under another name, or its funders may give less than the forms list. The list shows funders of organizations like it.");
      else if (p.nPeers && !rows.length) msg.push("No funders match these choices.");
      else if (rows.length > 1 && rows[0].n === 1) msg.push("Every funder here gave to one organization like yours, so the order follows their giving in other states.");
      $("msg").hidden = !msg.length;
      $("msg").textContent = msg.join(" ");

      $("r1-label").textContent = "Funders of organizations like yours in " + name;
      var total = d.counts ? d.counts[countKey()] || 0 : rows.length;
      $("r1").textContent = F.int(total);
      $("r1-range").textContent = rows.length ? "The top funder gave to " + F.int(rows[0].n) + " of the " + F.int(p.nPeers) + "." + (rows.length < total ? " The " + F.int(rows.length) + " that gave to the most are listed." : "") : "";
      $("r2-label").textContent = "Organizations like yours counted in " + name;
      $("r2").textContent = F.int(p.nPeers);
      $("r2-range").textContent = kindsText(d, p.ok);
      $("r3-box").hidden = p.oi < 0;
      if (p.oi >= 0) {
        $("r3-label").textContent = "Current funders of " + orgName();
        $("r3").textContent = F.int(p.cf.length);
        $("r3-range").textContent = p.cf.length ? "Left out of the list below." : "";
      }

      $("t-rank").textContent = "Funders of organizations like yours in " + name;
      $("rank-hint").textContent = rows.length
        ? (p.oi >= 0
          ? "Ranked by how many organizations like yours in " + orgName() + "'s 3-digit ZIP area each funder gave to, 2022 to 2025, then by how many of the " + F.int(p.nPeers) + " in the state."
          : "Ranked by how many of the " + F.int(p.nPeers) + " organizations like yours each funder gave to, 2022 to 2025.") +
          " Ties go to the funder with more peers anywhere." + (p.cf.length ? " Funders of " + orgName() + " are left out." : "")
        : "";
      renderList(p);
      renderCurrent(p);
      renderNet(p);
      if (flow) renderFlow();
    }

    /* ---------- the ranked list ---------- */
    function stat(label, value) {
      return Ex.el("div", { class: "p12-stat" }, [Ex.el("dt", { text: label }), Ex.el("dd", { text: value })]);
    }
    function link(href, text, hidden) {
      return Ex.el("a", { href: href, target: "_blank", rel: "noopener" }, [text, Ex.el("span", { class: "ex-vh", text: " (" + hidden + ", opens in a new tab)" })]);
    }
    function peersTable(host, r, f) {
      var d = cur.d;
      var rows = r.grants.map(function (gi) {
        var g = d.grants[gi], pe = d.peers[g[G_P]];
        return { peer: nice(pe[P_NAME]) + (pe[P_CITY] ? ", " + nice(pe[P_CITY]) : "") + (d.counts ? ", " + pe[P_ST] : ""), year: g[G_YEAR], amount: g[G_AMT], purpose: purposeText(d.purposes[g[G_PURPOSE]]) };
      }).sort(function (a, b) { return a.peer < b.peer ? -1 : a.peer > b.peer ? 1 : b.year - a.year; });
      Ex.dataTable(host, {
        caption: "Grants from " + nice(f[F_NAME]) + " to organizations like yours in " + (NAMES[cur.abbr] || cur.abbr) + ", 2022 to 2025",
        label: "Scrollable table of the peers " + nice(f[F_NAME]) + " funded",
        columns: [{ key: "peer", label: "Organization" }, { key: "year", label: "Year", format: String }, { key: "amount", label: "Amount", format: usd }, { key: "purpose", label: "Purpose on the form", text: true }],
        rows: rows,
      });
    }
    function rowEl(r, rank) {
      var d = cur.d, f = d.funders[r.fi], id = "peers-" + f[F_EIN];
      var li = Ex.el("li", { class: "p12-row" });
      var ein = String(f[F_EIN]).replace(/\D/g, "");
      var site = siteUrl(f[F_WEB]);
      var btn = Ex.el("button", { class: "ex-link", type: "button", "aria-expanded": "false", "aria-controls": id }, ["Show the " + F.plural(r.n, "organization")]);
      var panel = Ex.el("div", { class: "p12-peers", id: id, hidden: true });
      var follow = Ex.el("button", { class: "ex-link", type: "button" }, ["Follow the money"]);
      follow.addEventListener("click", function () { openFlow(f[F_EIN]); });
      var acts = Ex.el("div", { class: "p12-acts" }, [follow, btn]);
      if (/^\d{9}$/.test(ein)) acts.appendChild(link("https://projects.propublica.org/nonprofits/organizations/" + ein, "Form 990s", "ProPublica Nonprofit Explorer"));
      if (site) acts.appendChild(link(site.href, "Website: " + site.text, "website"));
      var main = Ex.el("div", { class: "p12-main" }, [
        Ex.el("strong", { class: "p12-name", text: nice(f[F_NAME]) }),
        Ex.el("span", { class: "p12-meta", text: [nice(f[F_CITY]), f[F_ST]].filter(Boolean).join(", ") + " · " + typeLabel(f) }),
      ]);
      if (f[F_PRE]) main.appendChild(Ex.el("span", { class: "p12-badge", text: "Funds only preselected organizations" }));
      var stats = Ex.el("dl", { class: "p12-stats" }, [
        cur.p.oi >= 0 ? stat("Funded nearby", F.int(r.near)) : null,
        stat(d.counts ? "Organizations funded" : "Organizations funded here", F.int(r.n)),
        stat("Median grant", usd(f[F_MED])),
        stat("Latest year", String(f[F_LAST])),
        stat("For general support", pctOrDash(f[F_GEN])),
        stat("Grantees new to it", pctOrDash(f[F_NEW])),
      ].filter(Boolean));
      li.appendChild(Ex.el("span", { class: "p12-rank", text: String(rank) }));
      li.appendChild(main);
      li.appendChild(stats);
      li.appendChild(acts);
      li.appendChild(panel);
      function open(on) {
        btn.setAttribute("aria-expanded", on ? "true" : "false");
        btn.textContent = (on ? "Hide the " : "Show the ") + F.plural(r.n, "organization");
        panel.hidden = !on;
        if (on) {
          if (!panel.firstChild) peersTable(panel, r, f);
          expanded[f[F_EIN]] = 1;
        } else delete expanded[f[F_EIN]];
      }
      btn.addEventListener("click", function () { open(panel.hidden); });
      if (expanded[f[F_EIN]]) open(true);
      return li;
    }
    function renderList(p) {
      var host = $("rank-list"), rows = p.rows;
      host.textContent = "";
      if (!rows.length) {
        $("more").hidden = true;
        return;
      }
      host.classList.toggle("p12-list--near", p.oi >= 0);
      host.appendChild(Ex.el("div", { class: "p12-head", "aria-hidden": "true" }, [
        Ex.el("span", { text: "Funder" }), p.oi >= 0 ? Ex.el("span", { text: "Funded nearby" }) : null, Ex.el("span", { text: cur.d.counts ? "Organizations like yours funded" : "Organizations like yours funded here" }), Ex.el("span", { text: "Median grant" }), Ex.el("span", { text: "Latest year" }),
        Ex.el("span", { text: "For general support" }), Ex.el("span", { text: "Grantees new to it" }),
      ].filter(Boolean)));
      var ol = Ex.el("ol", { class: "p12-rows", "aria-label": "Funders, most organizations like yours first" });
      rows.slice(0, shown).forEach(function (r, i) { ol.appendChild(rowEl(r, i + 1)); });
      host.appendChild(ol);
      var left = rows.length - shown;
      $("more").hidden = left <= 0;
      if (left > 0) $("more").textContent = "Show " + Math.min(PAGE, left) + " more (" + F.int(left) + " left)";
    }

    /* ---------- your current funders ---------- */
    var curTable = null;
    function renderCurrent(p) {
      $("current").hidden = p.oi < 0 || !p.cf.length;
      if (p.oi < 0 || !p.cf.length) return;
      var d = cur.d, pe = d.peers[p.oi], total = 0;
      var rows = p.cf.map(function (c) {
        total += c.total;
        return { funder: nice(d.funders[c.fi][F_NAME]), years: Object.keys(c.years).sort().join(", "), total: c.total };
      });
      $("t-current").textContent = "Current funders of " + orgName();
      var top = pe[P_TOP];
      $("conc-line").textContent = F.plural(p.cf.length, "funder") + " gave " + orgName() + " " + usd(total) + " in 2022 to 2025." + (top != null ? " Your largest funder gave " + F.pct(top, 0) + " of the grant dollars we can see." : "");
      var spec = {
        caption: "Funders that gave to " + orgName() + ", 2022 to 2025",
        label: "Scrollable table of the current funders",
        columns: [{ key: "funder", label: "Funder" }, { key: "years", label: "Years", text: true }, { key: "total", label: "Total", format: usd }],
        rows: rows,
      };
      if (!curTable) curTable = Ex.dataTable($("table-current"), spec);
      else curTable.update(rows, spec);
    }

    /* ---------- the network figure: computed once per choice, no animation ----------
       With an organization that has funders: it, its funders, the peers they share and the suggested funders.
       Otherwise: the state's top funders in the list and the organizations like yours they fund. */
    var netChart = null;
    function buildNet(p) {
      return p.oi >= 0 && p.cf.length ? buildEgo(p) : buildState(p);
    }
    function buildState(p) {
      var d = cur.d, top = p.rows.slice(0, d.counts ? TOP_US : TOP_STATE), cnt = {};
      if (!top.length) return null;
      top.forEach(function (r) {
        var seen = {};
        r.grants.forEach(function (gi) {
          var pi = d.grants[gi][G_P];
          if (!seen[pi]) { seen[pi] = 1; cnt[pi] = (cnt[pi] || 0) + 1; }
        });
      });
      var peers = Object.keys(cnt).map(function (k) { return { pi: +k, n: cnt[k] }; }).sort(function (a, b) {
        return b.n - a.n || (d.peers[a.pi][P_NAME] < d.peers[b.pi][P_NAME] ? -1 : 1);
      });
      var all = peers.length, size = d3.scaleSqrt().domain([1, d3.max(top, function (r) { return r.n; })]).range([8, 17]);
      peers = peers.slice(0, d.counts ? MAX_US_PEERS : MAX_STATE_PEERS);
      var nodes = top.map(function (s, i) { return { id: "s" + s.fi, t: "s", fi: s.fi, r: size(s.n), rank: i + 1, s: s }; }), links = [];
      peers.forEach(function (q) {
        nodes.push({ id: "p" + q.pi, t: "p", pi: q.pi, r: 3.5 + Math.min(q.n, 6) * 0.6, n: q.n });
        top.forEach(function (s) {
          if (d.fp[s.fi + "|" + q.pi]) links.push({ source: "s" + s.fi, target: "p" + q.pi, type: "s" });
        });
      });
      return { mode: "state", nodes: nodes, links: links, sugg: top, peers: peers, allPeers: all };
    }
    function buildEgo(p) {
      var d = cur.d, oi = p.oi;
      var cf = p.cf.slice(0, MAX_FUNDERS);
      var shared = {};
      p.cf.forEach(function (c) {
        d.byF[c.fi].forEach(function (gi) {
          var pi = d.grants[gi][G_P];
          if (pi === oi || !p.ok[pi]) return;
          (shared[pi] || (shared[pi] = {})) [c.fi] = 1;
        });
      });
      var peers = Object.keys(shared).map(function (k) { return { pi: +k, n: Object.keys(shared[k]).length }; }).sort(function (a, b) {
        return b.n - a.n || (d.peers[a.pi][P_NAME] < d.peers[b.pi][P_NAME] ? -1 : 1);
      }).slice(0, TOP_PEERS);
      var sugg = p.rows.slice(0, TOP_SUGGEST);
      var nodes = [{ id: "o", t: "o", r: 11 }], links = [];
      cf.forEach(function (c) {
        nodes.push({ id: "f" + c.fi, t: "f", fi: c.fi, r: 5.5, c: c });
        links.push({ source: "f" + c.fi, target: "o", type: "f" });
      });
      peers.forEach(function (q) { nodes.push({ id: "p" + q.pi, t: "p", pi: q.pi, r: 4, n: q.n }); });
      sugg.forEach(function (s, i) {
        nodes.push({ id: "s" + s.fi, t: "s", fi: s.fi, r: 10, rank: i + 1, s: s });
        links.push({ source: "s" + s.fi, target: "o", type: "weak" });
      });
      nodes.forEach(function (a) {
        if (a.t !== "f" && a.t !== "s") return;
        peers.forEach(function (q) {
          if (d.fp[a.fi + "|" + q.pi]) links.push({ source: a.id, target: "p" + q.pi, type: a.t });
        });
      });
      return { mode: "ego", nodes: nodes, links: links, cf: cf, moreCf: p.cf.length - cf.length, peers: peers, shared: shared, sugg: sugg };
    }
    function renderNet(p) {
      var net = (cur.net = buildNet(p));
      $("fig-net").hidden = !net;
      if (!net) return;
      var ego = net.mode === "ego", name = NAMES[cur.abbr] || cur.abbr, n = net.sugg.length;
      $("t-net").textContent = ego ? "Who funds " + orgName() + ", and who funds its peers" : (n === 1 ? "The one funder" : (n < TOP_STATE ? "The " : "The top ") + F.int(n) + " funders") + " in " + name + " and the organizations like yours " + (n === 1 ? "it funds" : "they fund");
      $("key-ego").hidden = !ego;
      $("key-state").hidden = ego;
      $("net-all").hidden = !ego;
      $("net-hint").textContent = "Point at or tab to a circle to see its connections. Select a funder to follow its money, or an organization to see its own funders" + (cur.d.counts ? ", in its state." : ".") +
        (!ego && net.allPeers > net.peers.length ? " Shown: the " + F.int(net.peers.length) + " of " + F.int(net.allPeers) + " organizations funded by the most of these funders." : "");
      renderNetText(net);
      if (!netChart) {
        netChart = Ex.chart($("chart-net"), {
          label: "Network of funders and organizations like yours",
          margin: function (w) { return { top: 14, right: w < 520 ? 14 : 130, bottom: 14, left: w < 520 ? 14 : 130 }; },
          // a ring of more funders (all states) needs more room
          height: function (w) { var big = cur.net && cur.net.sugg.length > TOP_STATE; return Math.round(Math.min(big ? 720 : 580, Math.max(w < 520 ? 420 : big ? 520 : 400, w * (w < 520 ? (big ? 1.3 : 1.05) : big ? 0.75 : 0.62)))); },
          render: drawNet,
        });
      }
      netChart.redraw();
    }
    function layout(net, w, h) {
      var cx = w / 2, cy = h / 2, R = Math.min(cx, cy) - 14;
      if (net.mode === "state") return layoutState(net, w, h, cx, cy, R);
      var ring = { o: 0, f: 0.3, p: 0.64, s: 0.98 };
      var count = { f: 0, p: 0, s: 0 }, idx = { f: 0, p: 0, s: 0 };
      var nodes = net.nodes.map(function (n) {
        var m = Object.assign({}, n);
        if (m.t !== "o") count[m.t]++;
        return m;
      });
      nodes.forEach(function (n) {
        if (n.t === "o") { n.x = cx; n.y = cy; n.fx = cx; n.fy = cy; return; }
        var a = (2 * Math.PI * idx[n.t]++) / count[n.t] + (n.t === "p" ? 0.4 : n.t === "s" ? 0.2 : 0);
        n.x = cx + Math.cos(a) * ring[n.t] * R;
        n.y = cy + Math.sin(a) * ring[n.t] * R;
      });
      var links = net.links.map(function (l) { return { source: l.source, target: l.target, type: l.type }; });
      var sim = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(function (n) { return n.id; }).distance(function (l) { return l.type === "weak" ? R : R * 0.34; }).strength(function (l) { return l.type === "weak" ? 0.01 : l.type === "f" ? 0.2 : 0.03; }))
        .force("charge", d3.forceManyBody().strength(-90))
        .force("collide", d3.forceCollide(function (n) { return n.r + (n.t === "s" ? 12 : 5); }))
        .force("radial", d3.forceRadial(function (n) { return ring[n.t] * R; }, cx, cy).strength(1))
        .stop();
      for (var i = 0; i < 300; i++) sim.tick();
      nodes.forEach(function (n) {
        n.x = Math.max(n.r + 2, Math.min(w - n.r - 2, n.x));
        n.y = Math.max(n.r + 2, Math.min(h - n.r - 2, n.y));
      });
      return { nodes: nodes, links: links.filter(function (l) { return l.type !== "weak"; }), cx: cx };
    }
    function layoutState(net, w, h, cx, cy, R) {
      // funders evenly on an outer ellipse; each organization pulled toward the funders that gave to it, so the ones
      // several funders share sit in the middle and the ones a single funder holds sit next to it
      // names sit beside the ring on a wide screen only, so a phone's ring fills the figure
      var rx = Math.min(w / 2 - (w < 500 ? 16 : 60), R * 1.4), ry = Math.min(cy - 20, R * 1.4), nf = net.sugg.length, at = {}, j = 0;
      var nodes = net.nodes.map(function (n, i) {
        var m = Object.assign({}, n);
        if (m.t === "s") {
          // half a step off the top, so no name sits straight above or below the middle
          var a = -Math.PI / 2 + (Math.PI * (2 * i + 1)) / nf;
          m.fx = m.x = cx + Math.cos(a) * rx;
          m.fy = m.y = cy + Math.sin(a) * ry;
          at[m.id] = m;
        }
        return m;
      });
      var links = net.links.map(function (l) { return { source: l.source, target: l.target, type: l.type }; });
      nodes.forEach(function (m) {
        if (m.t !== "p") return;
        var mine = links.filter(function (l) { return l.target === m.id; }).map(function (l) { return at[l.source]; });
        var a = (2 * Math.PI * j++) / net.peers.length;
        m.x = cx + 0.55 * (d3.mean(mine, function (f) { return f.x; }) - cx) + Math.cos(a) * 4;
        m.y = cy + 0.55 * (d3.mean(mine, function (f) { return f.y; }) - cy) + Math.sin(a) * 4;
      });
      var sim = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(function (n) { return n.id; }).distance(R * 0.3).strength(0.12))
        .force("charge", d3.forceManyBody().strength(-14))
        .force("collide", d3.forceCollide(function (n) { return n.r + (n.t === "s" ? 8 : 1.5); }))
        .stop();
      for (var k = 0; k < 300; k++) {
        sim.tick();
        nodes.forEach(function (n) {
          if (n.t !== "p") return;
          // keep organizations inside the ring of funders
          var dx = (n.x - cx) / (rx * 0.8), dy = (n.y - cy) / (ry * 0.8), q = Math.sqrt(dx * dx + dy * dy);
          if (q > 1) { n.x = cx + (n.x - cx) / q; n.y = cy + (n.y - cy) / q; }
        });
      }
      return { nodes: nodes, links: links, cx: cx };
    }
    function nodeTip(n) {
      var d = cur.d, p = cur.p, net = cur.net;
      if (n.t === "o") return { title: orgName(), rows: [{ name: "Current funders", value: F.int(p.cf.length), color: "obs" }, { name: "Peers sharing a funder", value: F.int(Object.keys(net.shared).length), color: "ref" }], note: F.int(net.peers.length) + " with the most shared funders are shown." };
      if (n.t === "f") {
        var f = d.funders[n.fi], shared = net.peers.filter(function (q) { return d.fp[n.fi + "|" + q.pi]; }).length;
        return { title: nice(f[F_NAME]), rows: [{ name: "Gave to you", value: usd(n.c.total), color: "obs" }, { name: "Years", value: Object.keys(n.c.years).sort().join(", ") }, { name: "Also gave to peers shown", value: F.int(shared) }], note: typeLabel(f) + ". Select it to follow its money." };
      }
      var ego = net.mode === "ego";
      if (n.t === "p") {
        var pe = d.peers[n.pi];
        return { title: nice(pe[P_NAME]), rows: [{ name: ego ? "Funders it shares with you" : "Funders shown that gave to it", value: F.int(n.n), color: "obs" }], note: nice(pe[P_CITY]) + (d.counts ? ", " + pe[P_ST] : "") + ". Select it to see its own funders." };
      }
      var sf = d.funders[n.fi];
      return { title: n.rank + ". " + nice(sf[F_NAME]), rows: [{ name: "Organizations like yours funded here", value: F.int(n.s.n), color: "est" }], note: typeLabel(sf) + (ego ? ". Suggested; it does not fund you now." : ". Number " + n.rank + " in the list.") + " Select it to follow its money." };
    }
    function short(s, n) {
      return s.length > n ? s.slice(0, n - 1).trimEnd() + "…" : s;
    }
    function drawNet(c) {
      var net = cur.net, d = cur.d;
      if (!net) return;
      var L = layout(net, c.width, c.height), g = c.g, ego = net.mode === "ego";
      c.svg.attr("aria-label", (ego
        ? "Network of " + orgName() + ": " + F.plural(net.cf.length, "current funder") + ", " + F.plural(net.peers.length, "peer") + " that share a funder with it and " + F.plural(net.sugg.length, "suggested funder")
        : "Network of the top " + F.plural(net.sugg.length, "funder") + " in " + (NAMES[cur.abbr] || cur.abbr) + " and " + F.plural(net.peers.length, "organization") + " like yours they fund") + ". The text version below lists the same connections.");
      g.classed("p12-net--state", !ego);
      var edges = g.append("g").selectAll("line").data(L.links).enter().append("line")
        .attr("class", function (l) { return "p12-edge p12-edge--" + (l.type === "s" ? "sugg" : "obs"); })
        .attr("x1", function (l) { return l.source.x; }).attr("y1", function (l) { return l.source.y; })
        .attr("x2", function (l) { return l.target.x; }).attr("y2", function (l) { return l.target.y; });
      var order = { p: 0, f: 1, s: 2, o: 3 };
      var ng = g.append("g").selectAll("g").data(L.nodes.slice().sort(function (a, b) { return order[a.t] - order[b.t]; })).enter().append("g")
        .attr("class", function (n) { return "ex-mark p12-node p12-node--" + n.t; }).attr("transform", function (n) { return "translate(" + n.x + "," + n.y + ")"; });
      ng.append("circle").attr("class", "ex-hit").attr("r", function (n) { return n.r + 5; }).attr("fill", "transparent");
      ng.append("circle").attr("class", "p12-dot").attr("r", function (n) { return n.r; });
      ng.filter(function (n) { return n.t === "s"; }).append("text").attr("class", "p12-num").attr("dy", "0.34em").attr("text-anchor", "middle").text(function (n) { return n.rank; });
      // names on the nodes that matter, on a wide screen; the tooltip and the text version carry the rest
      var label = function (sel, text, dy) {
        sel.append("text").attr("class", "ex-svg-label ex-svg-label--direct p12-lab").attr("dy", dy || "0.32em")
          .attr("x", function (n) { return n.x < L.cx ? -(n.r + 6) : n.r + 6; }).attr("text-anchor", function (n) { return n.x < L.cx ? "end" : "start"; }).text(text)
          .each(function (n) {
            // trim a name that would run past the edge of the figure
            var room = (n.x < L.cx ? n.x + c.margin.left : c.width + c.margin.right - n.x) - n.r - 8, t = this.textContent;
            while (t.length > 4 && this.getComputedTextLength() > room) this.textContent = (t = t.slice(0, -2).trimEnd()) + "…";
          });
      };
      if (!c.narrow) label(ng.filter(function (n) { return n.t === "s"; }), function (n) { return short(nice(d.funders[n.fi][F_NAME]), 26); });
      ng.filter(function (n) { return n.t === "o"; }).append("text").attr("class", "ex-svg-label ex-svg-label--direct p12-lab").attr("y", 26).attr("text-anchor", "middle").text(short(orgName(), c.narrow ? 24 : 34));
      // pointing at or focusing a circle lights its links and neighbours
      var adj = {};
      L.links.forEach(function (l) {
        (adj[l.source.id] = adj[l.source.id] || {})[l.target.id] = 1;
        (adj[l.target.id] = adj[l.target.id] || {})[l.source.id] = 1;
      });
      function hl(n) {
        g.classed("p12-hl", !!n);
        ng.classed("is-on", function (m) { return !!n && (m.id === n.id || !!(adj[n.id] || {})[m.id]); });
        edges.classed("is-on", function (l) { return !!n && (l.source.id === n.id || l.target.id === n.id); });
      }
      ng.on("pointerenter.hl focus.hl", function (e, n) { hl(n); }).on("pointerleave.hl blur.hl", function () { hl(null); });
      // a funder opens its money trace
      ng.filter(function (n) { return n.t === "s" || n.t === "f"; }).attr("role", "button").classed("p12-pick", true)
        .on("click.pick", function (e, n) { openFlow(d.funders[n.fi][F_EIN]); })
        .on("keydown.pick", function (e, n) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openFlow(d.funders[n.fi][F_EIN], { keyboard: true }); }
        });
      // an organization opens its own network
      ng.filter(function (n) { return n.t === "p"; }).attr("role", "button").classed("p12-pick", true)
        .on("click.pick", function (e, n) { pickOrg(n.pi, false); })
        .on("keydown.pick", function (e, n) {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pickOrg(n.pi, true); }
        });
      c.cleanup(Ex.tooltip.attach(ng, function (el) { return nodeTip(el.__data__); }));
      Ex.roving(g.node(), ".ex-mark");
    }
    function pickOrg(pi, keyboard) {
      var pe = cur.d.peers[pi];
      function after() {
        $("fig-net").scrollIntoView({ block: "nearest" });
        // the figure was redrawn; keep keyboard focus in it, on the organization just chosen
        var mark = keyboard && ($("chart-net").querySelector(".p12-node--o") || $("chart-net").querySelector(".p12-node--s"));
        if (mark) mark.focus();
      }
      touched = true;
      // from all states, open the organization's own state
      if (cur.d.counts) return show(pe[P_ST], pe[P_EIN], after);
      S.org = pe[P_EIN];
      orgCombo.setValue(S.org, { silent: true });
      shown = PAGE;
      update();
      after();
    }
    $("net-all").addEventListener("click", function () {
      touched = true;
      S.org = null;
      orgCombo.setValue(null, { silent: true });
      shown = PAGE;
      update();
    });
    function renderNetText(net) {
      var d = cur.d, host = $("net-text");
      host.textContent = "";
      function list(title, items, ordered) {
        host.appendChild(Ex.el("p", { class: "p12-nettext__h", text: title }));
        var ul = Ex.el(ordered ? "ol" : "ul");
        items.forEach(function (t) { ul.appendChild(Ex.el("li", { text: t })); });
        host.appendChild(ul);
      }
      if (net.mode === "state") {
        list("Top funders, as numbered in the list", net.sugg.map(function (s) {
          return nice(d.funders[s.fi][F_NAME]) + ", funded " + F.plural(s.n, "organization") + " like yours here";
        }), true);
        list("Organizations like yours they fund" + (net.allPeers > net.peers.length ? " (the " + F.int(net.peers.length) + " of " + F.int(net.allPeers) + " funded by the most of them)" : ""), net.peers.map(function (q) {
          var by = [];
          net.sugg.forEach(function (s, i) { if (d.fp[s.fi + "|" + q.pi]) by.push(i + 1); });
          return nice(d.peers[q.pi][P_NAME]) + ", funded by " + (by.length === 1 ? "number " : "numbers ") + by.join(", ");
        }));
        return;
      }
      list("Your current funders" + (net.moreCf > 0 ? " (largest " + net.cf.length + " of " + (net.cf.length + net.moreCf) + ")" : ""), net.cf.map(function (n) {
        var f = d.funders[n.fi];
        return nice(f[F_NAME]) + ", " + usd(n.total) + " in " + Object.keys(n.years).sort().join(", ");
      }));
      if (net.peers.length) {
        list("Organizations like yours that share a funder with you", net.peers.map(function (q) {
          var names = net.cf.filter(function (c) { return net.shared[q.pi][c.fi]; }).map(function (c) { return nice(d.funders[c.fi][F_NAME]); });
          return nice(d.peers[q.pi][P_NAME]) + ", " + F.plural(q.n, "shared funder") + (names.length ? ": " + names.slice(0, 3).join("; ") + (names.length > 3 ? " and others" : "") : "");
        }));
      }
      if (net.sugg.length) {
        list("Suggested funders, as numbered in the list", net.sugg.map(function (s) {
          var to = net.peers.filter(function (q) { return d.fp[s.fi + "|" + q.pi]; }).map(function (q) { return nice(d.peers[q.pi][P_NAME]); });
          return nice(d.funders[s.fi][F_NAME]) + ", funded " + F.plural(s.n, "organization") + " like yours here" + (to.length ? ", including " + to.slice(0, 3).join("; ") : "");
        }), true);
      }
    }


    /* ---------- follow the money: one funder's trace (flow-NN.json, written by web_data.py) ----------
       Five columns, left to right: its sources' sources, its sources, the funder, the grantmakers it gives to and the
       organizations like yours at the end, in a dialog that fills the window. Each entity appears once. A path shows
       where money could have gone, not that the same dollars moved; line widths use pro-rata tracing (buildFlow). */
    var flowChart = null, flow = null, flowToken = 0, dlg = $("fig-flow");
    function dropFlow() {
      flow = null;
      flowToken++;
      if (dlg.open) dlg.close();
    }
    // Esc or the Close button: the dialog's close event clears the trace (dropFlow has cleared it already)
    dlg.addEventListener("close", function () {
      // the event comes a moment after close(); by then a new trace may have opened the dialog again
      if (!flow || dlg.open) return;
      flow = null;
      flowToken++;
      writeHash();
    });
    $("flow-close").addEventListener("click", function () { dlg.close(); });
    var FLOW_COLS = ["Their sources", "Its sources", "The funder", "Grantmakers it gives to", "Organizations like yours"];
    var FLAG_REL = 1;
    function cusd(v) {
      return F.usd(v, { compact: true });
    }
    function share(v) {
      return v >= 0.01 ? F.num(100 * v, 0) + "%" : v >= 0.001 ? F.num(100 * v, 1) + "%" : "under 0.1%";
    }
    function openFlow(ein, o) {
      o = o || {};
      touched = true;
      var token = ++flowToken;
      Ex.loadData(BASE + "flow-" + ein.slice(-2) + ".json").then(function (sh) {
        var tr = sh.t[ein];
        if (!tr || token !== flowToken) return;
        var step = { ein: ein, name: nice(sh.o[ein][0]) };
        var trail = o.trail || (o.push && flow ? flow.trail.concat(step) : [step]);
        flow = { ein: ein, o: sh.o, t: tr, trail: trail };
        renderFlow();
        writeHash();
        // a keyboard pick: keep focus in the figure, on the funder
        var c = o.keyboard && $("chart-flow").querySelector(".p12-fnode--c");
        if (c) c.focus();
      }, function () {
        if (token !== flowToken) return;
        // the error replaces the chart's svg, so the next trace starts a new chart
        if (flowChart) flowChart.destroy();
        flowChart = null;
        dropFlow();
        writeHash();
        $("t-flow").textContent = "Follow the money";
        ["flow-trail", "flow-sum", "flow-panel", "flow-text"].forEach(function (id) { $(id).textContent = ""; });
        dlg.showModal();
        Ex.showError($("chart-flow"), "This funder's trace did not load. The downloads at the end of the page have its grants.");
      });
    }
    function peerOk(ein) {
      var code = flow.o[ein][4];
      return KINDS.some(function (K) { return K.code === code && S.kinds[K.k]; });
    }
    function buildFlow() {
      var tr = flow.t, o = flow.o, nodes = {}, list = [], edges = [];
      function node(ein, col) {
        if (!nodes[ein]) list.push((nodes[ein] = { id: ein, ein: ein, col: col, role: o[ein][3], amt: 0 }));
        return nodes[ein];
      }
      var seen = {};
      function edge(s, t, r) {
        // a grant to a funder that is also an organization like yours is in both the flows and the grant table
        var k = s + ">" + t;
        if (!seen[k]) edges.push((seen[k] = { s: nodes[s], t: nodes[t], amt: r[0], n: r[1], flag: r[2], back: r[3] || 0 }));
        else seen[k].back = seen[k].back || r[3] || 0;
        return seen[k];
      }
      // the order of these calls picks the column of an entity that turns up in more than one place
      var c = node(flow.ein, 2);
      c.role = "c";
      tr.in1.forEach(function (r) { node(r[0], 1); edge(r[0], flow.ein, r.slice(1)); });
      tr.mid.forEach(function (r) { node(r[0], 3); edge(flow.ein, r[0], r.slice(1)); });
      tr.peers.forEach(function (r) {
        if (!peerOk(r[0])) return;
        node(r[0], 4);
        edge(flow.ein, r[0], r.slice(1));
      });
      tr.midp.forEach(function (r) {
        if (!peerOk(r[1]) || !nodes[r[0]]) return;
        node(r[1], 4);
        edge(r[0], r[1], r.slice(2));
      });
      tr.in2.forEach(function (r) {
        if (!nodes[r[1]]) return;
        node(r[0], 0);
        edge(r[0], r[1], r.slice(2));
      });
      // a loop: the funder gives to a, a to b, b back to it; a sits with what it gives to, b with its sources
      var loops = [];
      for (var i = 0; i < tr.loop.length; i += 3) {
        node(tr.loop[i][1], 3);
        node(tr.loop[i + 1][1], 1);
        loops.push(tr.loop.slice(i, i + 3).map(function (r) { return edge(r[0], r[1], r.slice(2)); }));
      }
      // pro-rata tracing: each grantmaker passes money on in the shares it gives it out. up(x) is the share of x's
      // grants that could reach the funder, down(x) the share of x's grants that could be the funder's money; x's
      // grants are all it listed (at least what is drawn). v(x) = min(1, sum of amt * v(next) / grants(x)), v(funder)
      // = 1, solved from v = 0 upward: the values only rise and stay at most 1, so they settle whatever the order.
      function given(n) {
        return Math.max(o[n.ein][5], d3.sum(edges, function (e) { return e.s === n ? e.amt : 0; }));
      }
      function tracer(fwd) {
        var v = new Map(), g = new Map(), adj = new Map();
        list.forEach(function (n) { v.set(n, n === c ? 1 : 0); g.set(n, given(n)); adj.set(n, []); });
        edges.forEach(function (e) { adj.get(fwd ? e.s : e.t).push(e); });
        for (var moved = 1, i = 0; moved > 1e-9 && i < 500; i++) {
          moved = 0;
          list.forEach(function (n) {
            if (n === c || !g.get(n)) return;
            var x = Math.min(1, d3.sum(adj.get(n), function (e) { return e.amt * v.get(fwd ? e.t : e.s); }) / g.get(n));
            moved = Math.max(moved, x - v.get(n));
            v.set(n, x);
          });
        }
        return function (n) { return v.get(n); };
      }
      var up = tracer(true), down = tracer(false);
      edges.forEach(function (e) {
        e.up = up(e.t);
        e.down = down(e.s);
        e.reach = e.amt * Math.max(e.up, e.down);
        e.s.amt += e.reach;
        e.t.amt += e.reach;
      });
      return { nodes: list, edges: edges, loops: loops, c: c };
    }
    function renderFlow() {
      if (!flow) return;
      var tr = flow.t, tot = tr.tot, name = nice(flow.o[flow.ein][0]);
      var net = (flow.net = buildFlow());
      flow.sel = null;
      $("t-flow").textContent = "Follow the money: " + name;
      var trail = $("flow-trail");
      trail.textContent = "";
      if (flow.trail.length > 1) {
        trail.appendChild(document.createTextNode("Path: "));
        flow.trail.forEach(function (st, i) {
          if (i) trail.appendChild(document.createTextNode(" › "));
          if (i === flow.trail.length - 1) trail.appendChild(Ex.el("strong", { text: st.name }));
          else {
            var b = Ex.el("button", { class: "ex-link", type: "button", text: st.name });
            b.addEventListener("click", function (ev) { openFlow(st.ein, { trail: flow.trail.slice(0, i + 1), keyboard: ev.detail === 0 }); });
            trail.appendChild(b);
          }
        });
      }
      var s = ["In 2022 to 2025 it listed " + usd(tot[1]) + " in grants to U.S. organizations and received " + usd(tot[0]) + " from other grantmakers" +
        (tot[0] && tot[1] ? ", " + (tot[0] < tot[1] / 100 ? "under 1%" : F.num((100 * tot[0]) / tot[1], 0) + "%") + " of what it gave." : ".")];
      s.push("It gave " + usd(tot[2]) + " straight to " + F.plural(tot[3], "organization") + " like yours in all states" + (tot[4] ? ", and " + usd(tot[4]) + " to related ones." : "."));
      $("flow-sum").textContent = s.join(" ");
      net.flags = findFlags(net);
      renderFlowText(net);
      if (!dlg.open) dlg.showModal();
      if (!flowChart) {
        $("chart-flow").textContent = "";
        flowChart = Ex.chart($("chart-flow"), {
          label: "Where a funder's money comes from and where it goes",
          margin: function (w) { return { top: 34, right: w < 520 ? 12 : 190, bottom: 10, left: w < 520 ? 12 : 170 }; },
          height: function () {
            var per = [0, 0, 0, 0, 0];
            (flow ? flow.net.nodes : []).forEach(function (n) { per[n.col]++; });
            return Math.max(44 + d3.max(per) * 22, Math.min(window.innerHeight - 260, 44 + d3.max(per) * 34));
          },
          render: drawFlow,
        });
      }
      flowChart.redraw();
      view(null);
    }

    // what stands out: loops, money both ways, pass-through, conduits and one dominant source, in that order
    function findFlags(net) {
      var o = flow.o, c = net.c, tot = flow.t.tot, out = [];
      var nm = function (n) { return nice(o[n.ein][0]); };
      net.loops.slice(0, 2).forEach(function (L) {
        out.push({ title: "Money comes back round", edges: L,
          text: nm(c) + " → " + nm(L[0].t) + " (" + cusd(L[0].amt) + ") → " + nm(L[1].t) + " (" + cusd(L[1].amt) + ") → back to " + nm(c) + " (" + cusd(L[2].amt) + ")." });
      });
      var pairs = {};
      net.edges.forEach(function (e) {
        if (!e.back || (e.s !== c && e.t !== c)) return;
        var other = e.s === c ? e.t : e.s, p = (pairs[other.id] = pairs[other.id] || { n: other, edges: [] });
        p.edges.push(e);
        p.out = e.s === c ? e.amt : e.back;
        p.in = e.s === c ? e.back : e.amt;
      });
      Object.keys(pairs).map(function (k) { return pairs[k]; })
        .sort(function (a, b) { return Math.min(b.out, b.in) - Math.min(a.out, a.in); }).slice(0, 2)
        .forEach(function (p) {
          out.push({ title: "Money goes both ways", edges: p.edges,
            text: "With " + nm(p.n) + (p.edges[0].flag & FLAG_REL ? ", a related organization" : "") + ": " + cusd(p.out) + " out, " + cusd(p.in) + " back." });
        });
      if (tot[1] && tot[0] >= tot[1] / 2) {
        out.push({ title: "Much of its money passes through", edges: net.edges.filter(function (e) { return e.t === c; }),
          text: "It received " + cusd(tot[0]) + " from other grantmakers, " + share(tot[0] / tot[1]) + " of the " + cusd(tot[1]) + " it gave." });
      }
      net.edges.filter(function (e) { return e.s !== c && e.amt >= 1e6 && e.amt >= o[e.s.ein][5] / 2; })
        .sort(function (a, b) { return (a.flag & FLAG_REL) - (b.flag & FLAG_REL) || b.amt - a.amt; }).slice(0, 2)
        .forEach(function (e) {
          out.push({ title: "Most of one grantmaker's money", edges: [e],
            text: nm(e.s) + " gave " + share(Math.min(1, e.amt / o[e.s.ein][5])) + " of its grants (" + cusd(e.amt) + ") to " + nm(e.t) + (e.flag & FLAG_REL ? ", a related organization." : ".") });
        });
      var top = net.edges.filter(function (e) { return e.t === c; }).sort(function (a, b) { return b.amt - a.amt; })[0];
      if (top && tot[0] && top.amt >= tot[0] / 2 && !out.some(function (f) { return f.edges.length === 1 && f.edges[0] === top; })) {
        out.push({ title: "One source dominates", edges: [top],
          text: nm(top.s) + " supplied " + share(top.amt / tot[0]) + " of what it received from other grantmakers." });
      }
      return out;
    }
    // one item at a time is lit and described in the panel: a circle {n}, a line {e} or a flag {f}. Pointing or
    // focusing previews; selecting keeps it (flow.sel) until something else is selected.
    function same(a, b) {
      return !!a && !!b && a.n === b.n && a.e === b.e && a.f === b.f;
    }
    function pick(it) {
      flow.sel = it && !same(it, flow.sel) ? it : null;
      view(null);
    }
    // from a control in the panel, which the new panel replaces: focus goes to the new panel's title
    function panelPick(it) {
      pick(it);
      $("flow-panel").querySelector(".p12-panel__title").focus();
    }
    function view(it) {
      if (!flow) return;
      it = it || flow.sel;
      if (flow.paint) flow.paint(it);
      renderPanel(it);
      $("flow-panel").classList.toggle("is-pinned", !!flow.sel);
    }
    function renderPanel(it) {
      var host = $("flow-panel"), o = flow.o, net = flow.net, c = net.c;
      var nm = function (n) { return nice(o[n.ein][0]); };
      host.textContent = "";
      function add(tag, a, parent) {
        var x = Ex.el(tag, a);
        (parent || host).appendChild(x);
        return x;
      }
      function goTo(label, it2) {
        var b = add("button", { class: "ex-link", type: "button", text: label });
        b.addEventListener("click", function () { panelPick(it2); });
        return b;
      }
      // a short list of flows, each one selectable
      function flowList(title, es, label) {
        if (!es.length) return;
        add("p", { class: "p12-panel__h", text: title });
        var ul = add("ul", { class: "p12-panel__flows" });
        es.slice().sort(function (a, b) { return b.amt - a.amt; }).slice(0, 8).forEach(function (e) {
          var li = add("li", {}, ul), b = Ex.el("button", { class: "ex-link", type: "button", text: label(e) });
          b.addEventListener("click", function () { panelPick({ e: e }); });
          li.appendChild(b);
          li.appendChild(Ex.el("span", { class: "p12-panel__amt", text: cusd(e.amt) + (e.reach < e.amt * 0.995 ? ", traced " + cusd(e.reach) : "") }));
        });
        if (es.length > 8) add("p", { class: "ex-hint", text: "And " + (es.length - 8) + " more in the text version." });
      }
      // nothing chosen: what stands out, each one selectable
      if (!it) {
        add("h4", { class: "p12-panel__title", tabindex: "-1", text: "What stands out" });
        if (!net.flags.length) add("p", { class: "ex-hint", text: "No loops, money both ways, pass-through or single dominant source among the flows shown." });
        var ul = add("ul", { class: "p12-flags" });
        net.flags.forEach(function (f) {
          var b = add("li", {}, ul).appendChild(Ex.el("button", { class: "p12-flag", type: "button" }));
          b.appendChild(Ex.el("strong", { text: f.title + ". " }));
          b.appendChild(document.createTextNode(f.text));
          b.addEventListener("click", function () { panelPick({ f: f }); });
        });
        add("p", { class: "ex-hint", text: "Point at a circle or a line to see its money here. Select one to keep it." });
        return;
      }
      if (flow.sel) {
        var back = add("p", { class: "p12-panel__acts" }).appendChild(Ex.el("button", { class: "ex-link", type: "button", text: "‹ What stands out" }));
        back.addEventListener("click", function () { panelPick(null); });
      }
      if (it.f) {
        add("h4", { class: "p12-panel__title", tabindex: "-1", text: it.f.title });
        add("p", { text: it.f.text });
        flowList("Flows", it.f.edges, function (e) { return nm(e.s) + " to " + nm(e.t); });
        return;
      }
      if (it.e) {
        var e = it.e;
        add("p", { class: "p12-panel__kicker", text: "A flow" });
        add("h4", { class: "p12-panel__title", tabindex: "-1", text: nm(e.s) + " to " + nm(e.t) });
        var lines = [usd(e.amt) + " in " + F.plural(e.n, "grant") + ", 2022 to 2025."];
        if (e.flag & FLAG_REL) lines.push("They list each other as related organizations on Schedule R.");
        if (e.back) lines.push(nm(e.t) + " gave " + nm(e.s) + " " + usd(e.back) + " in the same years.");
        if (e.s !== c && e.t !== c) {
          lines.push(e.up >= e.down
            ? nm(e.t) + " passed " + share(e.up) + " of its grants on to " + nm(c) + ", directly or through others drawn here, so about " + cusd(e.reach) + " of this could have reached it."
            : nm(c) + "'s money made up about " + share(e.down) + " of what " + nm(e.s) + " gave, so about " + cusd(e.reach) + " of this could be its money.");
        }
        lines.forEach(function (t) { add("p", { text: t }); });
        var p = add("p", { class: "p12-panel__acts" });
        p.appendChild(goTo(nm(e.s), { n: e.s }));
        p.appendChild(goTo(nm(e.t), { n: e.t }));
        return;
      }
      var n = it.n, f = o[n.ein];
      var what = n.role === "c" ? "The funder you are following" : n.role === "f" ? "A funder" : n.role === "g" ? "A grantmaker" : "An organization like yours";
      add("p", { class: "p12-panel__kicker", text: what });
      add("h4", { class: "p12-panel__title", tabindex: "-1", text: nm(n) });
      add("p", { class: "p12-panel__meta", text: [nice(f[1]), f[2]].filter(Boolean).join(", ") });
      if (f[5] || f[6]) {
        var dl = add("dl", { class: "p12-panel__stats" });
        [["Grants it listed", usd(f[5])], ["From other grantmakers", usd(f[6]) + (f[5] && f[6] ? " (" + share(f[6] / f[5]) + " of what it gave)" : "")]].forEach(function (r) {
          add("dt", { text: r[0] }, dl);
          add("dd", { text: r[1] }, dl);
        });
      }
      flowList("Money in, shown here", net.edges.filter(function (e) { return e.t === n; }), function (e) { return "From " + nm(e.s); });
      flowList("Money out, shown here", net.edges.filter(function (e) { return e.s === n; }), function (e) { return "To " + nm(e.t); });
      if (n.role === "f" || n.role === "p") {
        var b = add("p", { class: "p12-panel__acts" }).appendChild(Ex.el("button", { class: "ex-btn ex-btn--ghost", type: "button", text: n.role === "f" ? "Follow its money" : "See its funders" }));
        // detail 0: pressed from the keyboard
        b.addEventListener("click", function (ev) { flowPick(n, ev.detail === 0); });
      }
    }
    function drawFlow(c) {
      if (!flow) return;
      var net = flow.net, g = c.g, o = flow.o;
      var cols = [0, 1, 2, 3, 4].filter(function (k) { return net.nodes.some(function (n) { return n.col === k; }); });
      // names sit left of the two source columns and right of the rest, so the columns leave room on those sides
      var FR = [0, 0.26, 0.47, 0.64, 1], lo = FR[cols[0]], hi = FR[cols[cols.length - 1]];
      var x = function (k) { return cols.length === 1 ? c.width / 2 : ((FR[k] - lo) / (hi - lo)) * c.width; };
      // order within a column: sources and grantmakers by dollars; sources' sources and organizations by where their
      // links come from, so lines cross less
      var byCol = {};
      net.nodes.forEach(function (n) { (byCol[n.col] = byCol[n.col] || []).push(n); });
      var most = d3.max(cols, function (k) { return byCol[k].length; }), step = Math.min(34, c.height / Math.max(1, most - 1));
      var rank = {};
      function place(k, key) {
        var a = byCol[k] || [];
        a.sort(function (p, q) { return key(p) - key(q) || q.amt - p.amt; });
        var top = (c.height - (a.length - 1) * step) / 2;
        a.forEach(function (n, i) { n.x = x(k); n.y = top + i * step; rank[n.id] = i; });
      }
      var avg = function (n, side) {
        var r = net.edges.filter(function (e) { return e[side] === n; }).map(function (e) { return rank[(side === "t" ? e.s : e.t).id]; }).filter(function (v) { return v != null; });
        return r.length ? d3.mean(r) : 1e3;
      };
      place(2, function () { return 0; });
      place(1, function () { return 0; });
      place(3, function () { return 0; });
      place(0, function (n) { return avg(n, "s"); });
      place(4, function (n) { return net.edges.some(function (e) { return e.t === n && e.s.role === "c"; }) ? -1 : avg(n, "t"); });
      var w = d3.scaleSqrt().domain([0, d3.max(net.edges, function (e) { return e.reach; }) || 1]).range([1, 14]);
      var r = d3.scaleSqrt().domain([0, d3.max(net.nodes, function (n) { return n.amt; }) || 1]).range([3.5, 11]);
      c.svg.attr("role", "group").attr("aria-label", "Money trace for " + nice(o[flow.ein][0]) + ": " + F.plural(net.nodes.length - 1, "connected organization") + ". The details panel describes the circle in focus; the text version lists every flow.");
      g.append("g").selectAll("text").data(cols).enter().append("text").attr("class", "ex-svg-label p12-colhead")
        .attr("x", function (k) { return x(k); }).attr("y", -14).attr("text-anchor", function (k) { return k < 2 ? "end" : k > 2 ? "start" : "middle"; })
        .text(function (k) { return c.narrow ? "" : FLOW_COLS[k]; });
      var link = d3.linkHorizontal().x(function (p) { return p.x; }).y(function (p) { return p.y; });
      function curve(e) {
        if (e.s.col === e.t.col) {
          // money between two entities in one column: an arc out to the side the names are not on
          var dx = (e.s.col < 2 ? 1 : -1) * (16 + Math.abs(e.t.y - e.s.y) * 0.35);
          return "M" + e.s.x + "," + e.s.y + "C" + (e.s.x + dx) + "," + e.s.y + " " + (e.t.x + dx) + "," + e.t.y + " " + e.t.x + "," + e.t.y;
        }
        if (e.s.col - e.t.col >= 2) {
          // money that runs back over the funder (a loop) bows over the top
          var top = Math.max(-26, Math.min(e.s.y, e.t.y) - 30 - (e.s.x - e.t.x) * 0.2);
          return "M" + e.s.x + "," + e.s.y + "C" + (e.s.x + 40) + "," + top + " " + (e.t.x - 40) + "," + top + " " + e.t.x + "," + e.t.y;
        }
        return link({ source: e.s, target: e.t });
      }
      var pg = g.append("g");
      var paths = pg.selectAll("path.p12-flow").data(net.edges).enter().append("path")
        .attr("class", function (e) { return "p12-flow" + (e.flag & FLAG_REL ? " p12-flow--rel" : "") + (e.back ? " p12-flow--back" : ""); })
        .attr("stroke-width", function (e) { return w(e.reach); })
        .attr("d", curve);
      // a wider, invisible copy of each line takes the pointer
      var hits = pg.selectAll("path.p12-flowhit").data(net.edges).enter().append("path").attr("class", "p12-flowhit")
        .attr("stroke-width", function (e) { return Math.max(10, w(e.reach) + 6); }).attr("d", curve);
      var ng = g.append("g").selectAll("g").data(net.nodes).enter().append("g")
        .attr("class", function (n) { return "ex-mark p12-fnode p12-pick p12-fnode--" + n.role; })
        .attr("transform", function (n) { return "translate(" + n.x + "," + n.y + ")"; })
        .attr("role", "button")
        .attr("aria-label", function (n) {
          var f = o[n.ein], sum = function (k) { return d3.sum(net.edges, function (e) { return e[k] === n ? e.amt : 0; }); };
          var money = [sum("t") ? cusd(sum("t")) + " in" : "", sum("s") ? cusd(sum("s")) + " out" : ""].filter(Boolean).join(", ");
          return nice(f[0]) + ", " + [nice(f[1]), f[2]].filter(Boolean).join(", ") + ". " + (money ? "Shown here: " + money + ". " : "") + (n.role === "c" ? "The funder you are following." : n.role === "f" ? "A funder; select it twice to follow its money." : n.role === "g" ? "A grantmaker." : "An organization like yours; select it twice to see its funders.");
        });
      ng.each(function (n) { n.r = n.role === "c" ? 11 : r(n.amt); });
      ng.append("circle").attr("class", "ex-hit").attr("r", function (n) { return Math.max(n.r + 4, 10); }).attr("fill", "transparent");
      ng.append("circle").attr("class", "p12-dot").attr("r", function (n) { return n.r; });
      // the funder's name above it, clear of its lines; on a phone only this name is drawn
      // centred over its circle; at the first or last column, flush with the edge of the figure instead
      var ci = cols.indexOf(2), cfirst = ci === 0 && cols.length > 1, clast = ci === cols.length - 1 && cols.length > 1;
      ng.filter(function (n) { return n.role === "c"; }).append("text").attr("class", "ex-svg-label p12-flab p12-flab--c")
        .attr("y", function (n) { return -n.r - 8; }).attr("x", function (n) { return cfirst ? -n.r : clast ? n.r : 0; })
        .attr("text-anchor", cfirst ? "start" : clast ? "end" : "middle").text(function (n) { return nice(o[n.ein][0]); })
        .each(function (n) {
          var left = ci > 0 ? n.x - x(cols[ci - 1]) : n.x + c.margin.left, right = ci < cols.length - 1 ? x(cols[ci + 1]) - n.x : c.width + c.margin.right - n.x;
          var room = (cfirst ? right + n.r : clast ? left + n.r : 2 * Math.min(left, right)) - 24, t = this.textContent;
          while (t.length > 4 && this.getComputedTextLength() > room) this.textContent = (t = t.slice(0, -2).trimEnd()) + "…";
        });
      if (!c.narrow) {
        ng.filter(function (n) { return n.role !== "c"; }).append("text").attr("class", "ex-svg-label p12-flab").attr("dy", "0.32em")
          .attr("x", function (n) { return n.col < 2 ? -(n.r + 6) : n.r + 6; })
          .attr("text-anchor", function (n) { return n.col < 2 ? "end" : "start"; })
          .text(function (n) { return nice(o[n.ein][0]); })
          .each(function (n) {
            // trim a name to the room before the next column (or the edge of the figure)
            var i = cols.indexOf(n.col), room = n.col < 2 ? n.x - (i > 0 ? x(cols[i - 1]) : -c.margin.left) : (i < cols.length - 1 ? x(cols[i + 1]) : c.width + c.margin.right) - n.x;
            room -= n.r + 14;
            var t = this.textContent;
            while (t.length > 4 && this.getComputedTextLength() > room) this.textContent = (t = t.slice(0, -2).trimEnd()) + "…";
          });
      }
      // a circle lights every path through it, back to the sources and on to the organizations; a line lights the
      // paths through it; a flag lights its own flows
      function reach(n, side, seen) {
        net.edges.forEach(function (e) {
          var from = side === "up" ? e.t : e.s, to = side === "up" ? e.s : e.t;
          if (from === n && !seen.e.has(e)) {
            seen.e.add(e);
            seen.n.add(to);
            reach(to, side, seen);
          }
        });
        return seen;
      }
      flow.paint = function (it) {
        g.classed("p12-hl", !!it);
        ng.classed("is-sel", function (n) { return !!flow.sel && flow.sel.n === n; });
        if (!it) return;
        var lit = { e: new Set(), n: new Set() };
        if (it.f) it.f.edges.forEach(function (e) { lit.e.add(e); lit.n.add(e.s); lit.n.add(e.t); });
        else {
          // two walks, each with its own record: a two-way pair would otherwise stop the second walk
          var from = it.n || it.e.s, to = it.n || it.e.t;
          [reach(from, "up", { e: new Set(), n: new Set() }), reach(to, "down", { e: new Set(), n: new Set() })].forEach(function (w) {
            w.e.forEach(function (e) { lit.e.add(e); });
            w.n.forEach(function (n) { lit.n.add(n); });
          });
          lit.n.add(from).add(to);
          if (it.e) lit.e.add(it.e);
        }
        ng.classed("is-on", function (n) { return lit.n.has(n); });
        paths.classed("is-on", function (e) { return lit.e.has(e); });
      };
      ng.on("pointerenter.hl focus.hl", function (ev, n) { view({ n: n }); })
        .on("pointerleave.hl", function () { view(null); })
        .on("blur.hl", function (ev) { if (!$("flow-panel").contains(ev.relatedTarget)) view(null); })
        .on("click.pick", function (ev, n) { flowSelect(n, false); })
        .on("keydown.pick", function (ev, n) {
          if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); flowSelect(n, true); }
        });
      hits.on("pointerenter", function (ev, e) { view({ e: e }); }).on("pointerleave", function () { view(null); })
        .on("click", function (ev, e) { pick({ e: e }); });
      flow.paint(flow.sel);
      Ex.roving(g.node(), ".ex-mark");
    }
    // the first selection keeps a circle in the panel; selecting it again follows a funder's money or opens an
    // organization's own network
    function flowSelect(n, keyboard) {
      if (flow.sel && flow.sel.n === n && n.role !== "c" && n.role !== "g") return flowPick(n, keyboard);
      pick({ n: n });
    }
    function flowPick(n, keyboard) {
      if (n.role === "f") return openFlow(n.ein, { push: true, keyboard: keyboard });
      // an organization like yours: its own network, in its state
      var st = flow.o[n.ein][2];
      if (!byAbbr[st]) return;
      dropFlow();
      show(st, n.ein, function () {
        $("fig-net").scrollIntoView({ block: "start" });
        var m = keyboard && $("chart-net").querySelector(".p12-node--o");
        if (m) m.focus();
      });
    }
    function renderFlowText(net) {
      var o = flow.o, host = $("flow-text");
      host.textContent = "";
      var flags = function (e) { return (e.flag & FLAG_REL ? " (related organizations)" : "") + (e.back ? " (" + usd(e.back) + " went the other way)" : "") + (e.reach < e.amt * 0.995 ? "; about " + usd(Math.round(e.reach)) + " traced to this funder" : ""); };
      // each flow once: money into the funder's side under its giver's column, money out under its receiver's
      var col = function (e) { return e.s.col < 2 ? e.s.col : e.t.col; };
      [0, 1, 2, 3, 4].forEach(function (k) {
        var es = net.edges.filter(function (e) { return col(e) === k; });
        if (!es.length) return;
        host.appendChild(Ex.el("p", { class: "p12-nettext__h", text: k === 2 ? "Back to the funder" : FLOW_COLS[k] }));
        var ul = Ex.el("ul");
        es.forEach(function (e) { ul.appendChild(Ex.el("li", { text: nice(o[e.s.ein][0]) + " to " + nice(o[e.t.ein][0]) + ": " + usd(e.amt) + " in " + F.plural(e.n, "grant") + flags(e) })); });
        host.appendChild(ul);
      });
    }

    /* ---------- findings: bars ---------- */
    function barChart(hostId, tableId, o) {
      var host = $(hostId);
      var rh = 42;
      Ex.chart(host, {
        label: o.label + ": " + o.rows.map(function (r) { return r.label + " " + r.text; }).join("; "),
        margin: { top: 2, right: 2, bottom: 2, left: 2 },
        height: function () { return o.rows.length * rh + 4; },
        render: function (c) {
          var x = d3.scaleLinear().domain([0, o.max || 100]).range([0, c.width]);
          var row = c.g.selectAll("g").data(o.rows).enter().append("g").attr("transform", function (r, i) { return "translate(0," + i * rh + ")"; });
          row.append("text").attr("class", "ex-svg-label").attr("x", 0).attr("y", 12).text(function (r) { return r.label; });
          row.append("text").attr("class", "ex-svg-value").attr("x", c.width).attr("y", 12).attr("text-anchor", "end").text(function (r) { return r.text; });
          row.append("rect").attr("class", "p12-track").attr("x", 0).attr("y", 20).attr("width", c.width).attr("height", 10);
          row.append("rect").attr("class", function (r) { return "p12-bar p12-bar--" + (r.cls || "obs"); }).attr("x", 0).attr("y", 20).attr("height", 10).attr("width", function (r) { return Math.max(1, x(r.v)); });
        },
      });
      Ex.dataTable($(tableId), {
        caption: o.label,
        label: "Scrollable table: " + o.label,
        columns: [{ key: "label", label: o.col || "Group" }, { key: "text", label: o.val || "Share", text: true }],
        rows: o.rows,
      });
    }
    var FD = N.findings || {};
    var DL = { "1": "One organization", "2": "Two", "3-5": "Three to five", "6+": "Six or more" };
    var ppf = FD.peers_per_funder, tot = d3.sum(Object.keys(ppf), function (k) { return ppf[k]; });
    barChart("chart-degree", "table-degree", {
      label: "Share of funders by the number of organizations like yours they gave to",
      rows: Object.keys(ppf).map(function (k) {
        var v = (100 * ppf[k]) / tot;
        return { label: DL[k] || k, v: v, text: F.num(v, 0) + "% (" + F.int(ppf[k]) + ")", cls: "obs" };
      }),
      col: "Organizations funded", val: "Funders",
    });

    var TL = { charity: "Community foundations and charities", daf: "Charities that hold donor-advised funds", hospital: "Hospitals and health systems", private: "Private foundations" };
    var dbt = FD.dollars_by_type || {}, dtot = d3.sum(Object.keys(dbt), function (k) { return dbt[k]; });
    barChart("chart-type", "table-type", {
      label: "Share of grant dollars by kind of funder",
      rows: Object.keys(dbt).sort(function (a, b) { return dbt[b] - dbt[a]; }).map(function (k) {
        return { label: TL[k] || k, v: (100 * dbt[k]) / dtot, text: F.usd(dbt[k], { compact: true }) + ", " + F.num((100 * dbt[k]) / dtot, 0) + "%", cls: "obs" };
      }),
      col: "Kind of funder", val: "Dollars and share",
    });

    barChart("chart-pre", "table-pre", {
      label: "Share of private foundations that fund only preselected organizations",
      rows: [
        { label: "Fund only preselected organizations", v: FD.private_preselected_pct, text: F.num(FD.private_preselected_pct, 0) + "%", cls: "obs" },
        { label: "Others", v: 100 - FD.private_preselected_pct, text: F.num(100 - FD.private_preselected_pct, 0) + "%", cls: "dim" },
      ],
      col: "Private foundations", val: "Share",
    });

    var KL = { general: "General support", program: "A program", capital: "Capital", in_kind: "Donated goods", event: "Events and sponsorships", unclear: "Unclear" };
    var gk = FD.grant_kinds_pct;
    barChart("chart-kinds", "table-kinds", {
      label: "Share of grants by purpose",
      rows: D.kinds.filter(function (k) { return gk[k] != null; }).map(function (k) {
        return { label: KL[k] || k, v: gk[k], text: F.num(gk[k], 0) + "%", cls: "est" };
      }),
      col: "Purpose", val: "Share of grants",
    });
    var gs = N.checks.grant.general_share;
    $("kinds-note").textContent = F.num(gk.general, 0) + "% of grants are labeled general support. Corrected for the label errors found in the check, the share is " + fmtBy("share", gs) + ".";

    /* ---------- go ---------- */
    var q = readHash(), s0 = q ? fromHash(q) : fresh();
    S = s0;
    show(s0.st, s0.org, s0.f && function () { openFlow(s0.f); });
    if (q) {
      // a shared link lands on the tool
      requestAnimationFrame(function () { $("tool").scrollIntoView(); });
    }
  }
});
