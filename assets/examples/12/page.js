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
  var PAGE = 20, FEW = 10, TOP_SUGGEST = 8, TOP_PEERS = 12, MAX_FUNDERS = 16;

  /* columns of the state files (see web_data.py) */
  var P_EIN = 0, P_NAME = 1, P_CITY = 2, P_KIND = 3, P_TOP = 6, P_ZIP3 = 7;
  var F_EIN = 0, F_NAME = 1, F_CITY = 2, F_ST = 3, F_TYPE = 4, F_CHAN = 5, F_PRE = 6, F_WEB = 7, F_ALL = 8, F_MED = 10, F_LAST = 11, F_GEN = 12, F_NEW = 13;
  var G_F = 0, G_P = 1, G_YEAR = 2, G_AMT = 3, G_PURPOSE = 5;

  var KINDS = [
    { k: "free_clinic", code: "fc", label: "free clinics" },
    { k: "health_center", code: "hc", label: "health centers" },
    { k: "care_provider", code: "cp", label: "other care nonprofits" },
  ];
  var TYPE_LABEL = { private: "Private foundation", charity: "Community foundation or charity", hospital: "Hospital or health system" };
  var NAMES = {
    AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California", CO: "Colorado", CT: "Connecticut", DE: "Delaware", DC: "District of Columbia", FL: "Florida", GA: "Georgia",
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
      try { history.replaceState(null, "", location.pathname + location.search + "#" + p.join("&")); } catch (e) { /* no history API: the choices still work */ }
    }

    /* ---------- pickers ---------- */
    var stateCombo = Ex.combobox($("pick-state"), {
      id: "state", label: "State", placeholder: "Search states", noun: "states", noun_one: "state",
      items: STATES.map(function (s) { return { value: s.st, label: NAMES[s.st] || s.st, hint: s.st }; }).sort(function (a, b) { return a.label < b.label ? -1 : 1; }),
      onSelect: function (it) {
        if (!it) return;
        touched = true;
        show(it.value, null);
      },
    });
    var orgCombo = Ex.combobox($("pick-org"), {
      id: "org", label: "Your organization", hint: "Optional. Leave it empty to see every funder in the state.", placeholder: "Search by name", noun: "organizations", noun_one: "organization", items: [],
      emptyText: "Not in the list. Leave this empty to see every funder.",
      onSelect: function (it) {
        touched = true;
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
      d.nDaf = d.funders.filter(function (f) { return f[F_CHAN] !== "direct"; }).length;
      d.nPre = d.funders.filter(function (f) { return f[F_PRE]; }).length;
      d.kindN = {};
      d.peers.forEach(function (p) { d.kindN[p[P_KIND]] = (d.kindN[p[P_KIND]] || 0) + 1; });
      return d;
    }
    function show(abbr, org) {
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
        orgCombo.setItems(d.peers.map(function (p) { return { value: p[P_EIN], label: nice(p[P_NAME]), hint: nice(p[P_CITY]), search: p[P_EIN] }; }));
        orgCombo.setValue(S.org, { silent: true });
        stateCombo.setValue(abbr, { silent: true });
        $("results").removeAttribute("aria-busy");
        syncControls();
        update();
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
      return { ok: ok, n: n };
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
      show(s.st, s.org);
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
      $("r1").textContent = F.int(rows.length);
      $("r1-range").textContent = rows.length ? "The top funder gave to " + F.int(rows[0].n) + " of the " + F.int(p.nPeers) + "." : "";
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
        return { peer: nice(pe[P_NAME]) + (pe[P_CITY] ? ", " + nice(pe[P_CITY]) : ""), year: g[G_YEAR], amount: g[G_AMT], purpose: purposeText(d.purposes[g[G_PURPOSE]]) };
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
      var acts = Ex.el("div", { class: "p12-acts" }, [btn]);
      if (/^\d{9}$/.test(ein)) acts.appendChild(link("https://projects.propublica.org/nonprofits/organizations/" + ein, "Form 990s", "ProPublica Nonprofit Explorer"));
      if (site) acts.appendChild(link(site.href, "Website: " + site.text, "website"));
      var main = Ex.el("div", { class: "p12-main" }, [
        Ex.el("strong", { class: "p12-name", text: nice(f[F_NAME]) }),
        Ex.el("span", { class: "p12-meta", text: [nice(f[F_CITY]), f[F_ST]].filter(Boolean).join(", ") + " · " + typeLabel(f) }),
      ]);
      if (f[F_PRE]) main.appendChild(Ex.el("span", { class: "p12-badge", text: "Funds only preselected organizations" }));
      var stats = Ex.el("dl", { class: "p12-stats" }, [
        cur.p.oi >= 0 ? stat("Funded nearby", F.int(r.near)) : null,
        stat("Organizations funded here", F.int(r.n)),
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
      host.appendChild(Ex.el("div", { class: "p12-head", "aria-hidden": "true" }, [
        Ex.el("span", { text: "Funder" }), Ex.el("span", { text: "Organizations like yours funded here" }), Ex.el("span", { text: "Median grant" }), Ex.el("span", { text: "Latest year" }),
        Ex.el("span", { text: "For general support" }), Ex.el("span", { text: "Grantees new to it" }),
      ]));
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

    /* ---------- the network figure: computed once per choice, no animation ---------- */
    var netChart = null;
    function buildNet(p) {
      var d = cur.d, oi = p.oi;
      if (oi < 0 || !p.cf.length) return null;
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
      return { nodes: nodes, links: links, cf: cf, moreCf: p.cf.length - cf.length, peers: peers, shared: shared, sugg: sugg };
    }
    function renderNet(p) {
      var net = (cur.net = buildNet(p));
      $("fig-net").hidden = !net;
      if (!net) return;
      $("t-net").textContent = "Who funds " + orgName() + ", and who funds its peers";
      renderNetText(net);
      if (!netChart) {
        netChart = Ex.chart($("chart-net"), {
          label: "Network of your organization, its funders, peers that share a funder with it and suggested funders",
          margin: function (w) { return { top: 14, right: w < 520 ? 14 : 130, bottom: 14, left: w < 520 ? 14 : 130 }; },
          height: function (w) { return Math.round(Math.min(580, Math.max(w < 520 ? 420 : 400, w * (w < 520 ? 1.05 : 0.62)))); },
          render: drawNet,
        });
      }
      netChart.redraw();
    }
    function layout(net, w, h) {
      var cx = w / 2, cy = h / 2, R = Math.min(cx, cy) - 14;
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
    function nodeTip(n) {
      var d = cur.d, p = cur.p, net = cur.net;
      if (n.t === "o") return { title: orgName(), rows: [{ name: "Current funders", value: F.int(p.cf.length), color: "obs" }, { name: "Peers sharing a funder", value: F.int(Object.keys(net.shared).length), color: "ref" }], note: F.int(net.peers.length) + " with the most shared funders are shown." };
      if (n.t === "f") {
        var f = d.funders[n.fi], shared = net.peers.filter(function (q) { return d.fp[n.fi + "|" + q.pi]; }).length;
        return { title: nice(f[F_NAME]), rows: [{ name: "Gave to you", value: usd(n.c.total), color: "obs" }, { name: "Years", value: Object.keys(n.c.years).sort().join(", ") }, { name: "Also gave to peers shown", value: F.int(shared) }], note: typeLabel(f) };
      }
      if (n.t === "p") {
        var pe = d.peers[n.pi];
        return { title: nice(pe[P_NAME]), rows: [{ name: "Funders it shares with you", value: F.int(n.n), color: "obs" }], note: nice(pe[P_CITY]) };
      }
      var sf = d.funders[n.fi];
      return { title: n.rank + ". " + nice(sf[F_NAME]), rows: [{ name: "Organizations like yours funded here", value: F.int(n.s.n), color: "est" }], note: typeLabel(sf) + ". Suggested; it does not fund you now." };
    }
    function short(s, n) {
      return s.length > n ? s.slice(0, n - 1).trimEnd() + "…" : s;
    }
    function drawNet(c) {
      var net = cur.net, d = cur.d;
      if (!net) return;
      var L = layout(net, c.width, c.height), g = c.g;
      c.svg.attr("aria-label", "Network of " + orgName() + ": " + F.plural(net.cf.length, "current funder") + ", " + F.plural(net.peers.length, "peer") + " that share a funder with it and " + F.plural(net.sugg.length, "suggested funder") + ". The text version below lists the same connections.");
      g.append("g").selectAll("line").data(L.links).enter().append("line")
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
          .attr("x", function (n) { return n.x < L.cx ? -(n.r + 6) : n.r + 6; }).attr("text-anchor", function (n) { return n.x < L.cx ? "end" : "start"; }).text(text);
      };
      if (!c.narrow) label(ng.filter(function (n) { return n.t === "s"; }), function (n) { return short(nice(d.funders[n.fi][F_NAME]), 26); });
      ng.filter(function (n) { return n.t === "o"; }).append("text").attr("class", "ex-svg-label ex-svg-label--direct p12-lab").attr("y", 26).attr("text-anchor", "middle").text(short(orgName(), c.narrow ? 24 : 34));
      c.cleanup(Ex.tooltip.attach(ng, function (el) { return nodeTip(el.__data__); }));
      Ex.roving(g.node(), ".ex-mark");
    }
    function renderNetText(net) {
      var d = cur.d, host = $("net-text");
      host.textContent = "";
      function list(title, items, ordered) {
        host.appendChild(Ex.el("p", { class: "p12-nettext__h", text: title }));
        var ul = Ex.el(ordered ? "ol" : "ul");
        items.forEach(function (t) { ul.appendChild(Ex.el("li", { text: t })); });
        host.appendChild(ul);
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
    show(s0.st, s0.org);
    if (q) {
      // a shared link lands on the tool
      requestAnimationFrame(function () { $("tool").scrollIntoView(); });
    }
  }
});
