/* Example 09: coverage loss and health center revenue. Every number comes from data.json
   (built by analysis/09-health-center-coverage-loss-stress-test/web_data.py). Plain ES2019. */
Ex.ready(function () {
  "use strict";
  var F = Ex.fmt;
  var NARROW = 520;
  var HAS_D3 = typeof d3 !== "undefined";
  var TOP_DRIVERS = 6;
  var LONG_LABELS = 680; /* below this chart width the long row labels sit above their rows */
  var CHART_IDS = ["chart-states", "chart-peers", "chart-sobol", "chart-tornado", "chart-ne"];
  /* All 50 states and DC, to tell "not covered by the model" from a typo. Names only. */
  var ALL = "Alabama:AL,Alaska:AK,Arizona:AZ,Arkansas:AR,California:CA,Colorado:CO,Connecticut:CT,Delaware:DE,District of Columbia:DC,Florida:FL,Georgia:GA,Hawaii:HI,Idaho:ID,Illinois:IL,Indiana:IN,Iowa:IA,Kansas:KS,Kentucky:KY,Louisiana:LA,Maine:ME,Maryland:MD,Massachusetts:MA,Michigan:MI,Minnesota:MN,Mississippi:MS,Missouri:MO,Montana:MT,Nebraska:NE,Nevada:NV,New Hampshire:NH,New Jersey:NJ,New Mexico:NM,New York:NY,North Carolina:NC,North Dakota:ND,Ohio:OH,Oklahoma:OK,Oregon:OR,Pennsylvania:PA,Rhode Island:RI,South Carolina:SC,South Dakota:SD,Tennessee:TN,Texas:TX,Utah:UT,Vermont:VT,Virginia:VA,Washington:WA,West Virginia:WV,Wisconsin:WI,Wyoming:WY"
    .split(",")
    .map(function (p) {
      var a = p.split(":");
      return { n: a[0], a: a[1] };
    });

  function $(id) {
    return document.getElementById(id);
  }
  function set(id, text) {
    var el = $(id);
    if (el) el.textContent = text;
  }

  Ex.loadData().then(init, function (err) {
    CHART_IDS.forEach(function (id) {
      var el = $(id);
      if (el) Ex.showError(el, "The data did not load. Reload the page, or use the CSV in the downloads.");
    });
    ["r2-val", "r3-val", "r4-val"].forEach(function (id) {
      set(id, "n/a");
    });
    set("p9-summary", "The data did not load. Reload the page.");
    if (window.console) console.error(err);
  });

  /* ---------- formatting ---------- */
  function money(v) {
    var a = Math.abs(v),
      u = [[1e9, "B"], [1e6, "M"], [1e3, "K"]];
    for (var i = 0; i < u.length; i++) {
      if (a >= u[i][0] * 0.9995) return (v < 0 ? "−" : "") + "$" + +(a / u[i][0]).toPrecision(3) + u[i][1];
    }
    return (v < 0 ? "−" : "") + "$" + Math.round(a);
  }
  function count(v) {
    if (v === 0) return "0";
    if (v < 10) return F.num(v, 1);
    var mag = Math.pow(10, Math.max(0, Math.floor(Math.log10(v)) - 2));
    return F.int(Math.round(v / mag) * mag);
  }
  function p1(v) {
    return F.pct(v, 1);
  }
  function p0(v) {
    return F.pct(v, 0);
  }
  function pv(v) {
    return F.pctValue(v, 1);
  }
  function pvc(v) {
    return v > 100 ? "100%+" : pv(v);
  }
  function rng(a, b, f) {
    return f(a) + " to " + f(b);
  }
  function usdWords(v) {
    if (v >= 1e9) return "$" + F.num(v / 1e9, 1) + " billion";
    if (v >= 1e6) return "$" + F.num(v / 1e6, 1) + " million";
    return "$" + F.int(v);
  }
  function plain(s) {
    return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
  }
  /* "5,000-14,999" -> [5000, 15000); "Under 5,000" -> [0, 5000); "40,000+" -> [40000, Infinity) */
  function sizeRange(sz) {
    var d = sz.replace(/,/g, "");
    if (/^Under/.test(sz)) return [0, +d.replace(/\D/g, "")];
    if (/\+$/.test(sz)) return [+d.replace(/\D/g, ""), Infinity];
    var m = d.match(/(\d+)-(\d+)/);
    return [+m[1], +m[2] + 1];
  }
  function sizeWords(sz) {
    return sz === "40,000+" ? "40,000 or more" : sz.indexOf("Under") === 0 ? "under 5,000" : sz.replace("-", " to ");
  }
  /* "12,000", "800k", "$30M", "1.5m" -> number; "" -> null; junk -> NaN */
  function parseNum(raw) {
    var t = String(raw).replace(/[\s,$]/g, "").toLowerCase();
    if (t === "") return null;
    var m = t.match(/^(\d*\.?\d+)([kmb]?)$/);
    if (!m) return NaN;
    return Math.round(parseFloat(m[1]) * ({ k: 1e3, m: 1e6, b: 1e9 }[m[2]] || 1) * 1e6) / 1e6;
  }
  function chart(id, opts) {
    if (!HAS_D3) {
      Ex.showError($(id), "The chart did not load. The data table has the same numbers.");
      return { redraw: function () {} };
    }
    return Ex.chart($(id), opts);
  }

  function init(D) {
    var M = D.meta,
      states = D.states,
      byA = {},
      inputBy = {};
    states.forEach(function (s) {
      byA[s.a] = s;
    });
    D.inputs.forEach(function (i, ix) {
      i.ix = ix;
      inputBy[i.k] = i;
    });
    var alpha = states.slice().sort(function (a, b) {
      return a.n.localeCompare(b.n);
    });
    var NONEXP = ALL.filter(function (s) {
      return !byA[s.a];
    });
    var NS = states.length;
    var S = { abbr: M.typical, picked: false, pts: null, rev: null, bad: false, size: "", set: "", peerManual: false, metric: "t", out: "L", tout: "L", all: false };
    try {
      var q = new URLSearchParams(window.location.search).get("state");
      if (q && byA[q.toUpperCase()]) {
        S.abbr = q.toUpperCase();
        S.picked = true;
      }
    } catch (e) {}
    /* never name Oregon in headings or labels; it stays an ordinary row */
    function N(s) {
      return s.a === "OR" ? "one state" : s.n;
    }

    var SIZES = [],
      RANGE = {},
      MS = {};
    D.bands.forEach(function (b) {
      if (SIZES.indexOf(b.size) < 0) SIZES.push(b.size);
    });
    SIZES.forEach(function (sz) {
      var bs = D.bands.filter(function (b) {
        return b.size === sz;
      });
      RANGE[sz] = sizeRange(sz);
      MS[sz] =
        d3Sum(bs, function (b) {
          return b.ms * b.n;
        }) /
        d3Sum(bs, function (b) {
          return b.n;
        });
    });
    function d3Sum(a, f) {
      return a.reduce(function (t, x) {
        return t + f(x);
      }, 0);
    }
    var SIZE_SHORT = { "Under 5,000": "<5K", "5,000-14,999": "5-15K", "15,000-39,999": "15-40K", "40,000+": "40K+" };

    /* live tables: rebuilt on update, drawn only while the <details> is open */
    function liveTable(hostId, make) {
      var host = $(hostId),
        d = host.closest("details");
      function refresh() {
        if (d.open) Ex.dataTable(host, make());
      }
      d.addEventListener("toggle", refresh);
      return refresh;
    }

    /* ---------- the tool ---------- */
    function calc(abbr) {
      var s = byA[abbr || S.abbr],
        has = S.pts != null,
        pts = has ? S.pts : s.c,
        k = pts / 1000,
        o = { s: s, pts: pts, avg: !has, k: k };
      o.lost = s.l.map(function (v) {
        return v * k;
      });
      o.exp = s.e * k;
      o.usd = s.d.map(function (v) {
        return v * k;
      });
      if (S.rev != null && has) {
        if (o.usd[2] > S.rev) {
          o.from = "revbad";
          o.pct = s.r.slice();
        } else {
          o.from = "rev";
          o.pct = o.usd.map(function (v) {
            return (v / S.rev) * 100;
          });
        }
      } else if (S.pts === 0) {
        o.from = "zero";
        o.pct = [0, 0, 0];
      } else {
        o.from = "state";
        o.pct = s.r.slice();
      }
      return o;
    }
    function who(c) {
      return c.avg ? "an average " + c.s.n + " center" : "your center";
    }
    function shareBelow(v) {
      var tot = 0,
        below = 0;
      D.hist.forEach(function (h) {
        tot += h[2];
        if (v >= h[1]) below += h[2];
        else if (v > h[0]) below += (h[2] * (v - h[0])) / (h[1] - h[0]);
      });
      return below / tot;
    }
    function percentile(c) {
      return Math.round(shareBelow(c.pct[1]) * 20) * 5;
    }
    function ordinal(n) {
      return n + "th";
    }

    var errState = { pts: "", rev: "" };
    function showErr(which, msg) {
      var el = $("err-" + which),
        inp = $("in-" + which);
      el.hidden = !msg;
      el.textContent = msg;
      if (msg) inp.setAttribute("aria-invalid", "true");
      else inp.removeAttribute("aria-invalid");
    }
    var KYME = { KY: 1, ME: 1 };
    var KYME_NOTE = "The state reports near-zero procedural terminations, a pause or a reporting artifact, so the administrative share is among the least certain.";

    function renderTool() {
      var c = calc(),
        s = c.s;

      var NINE = "9 in 10: ";
      set("r3-label", (S.picked ? "" : "Example: ") + "net revenue at risk a year, " + (c.avg ? "average " + s.n + " center" : "your center in " + s.n));
      set("r3-val", money(c.usd[1]));
      set("r3-range", "9 in 10 outcomes: " + rng(money(c.usd[0]), money(c.usd[2]), String));

      set("r2-label", "Adults who lose coverage");
      set("r2-val", count(c.lost[1]));
      set("r2-range", NINE + rng(count(c.lost[0]), count(c.lost[2]), String));

      set("r4-label", c.from === "rev" ? "Share of your revenue" : "Share of revenue");
      if (c.from === "rev") {
        set("r4-val", pvc(c.pct[1]));
        set("r4-range", NINE + rng(c.pct[0], c.pct[2], pvc));
      } else if (c.from === "revbad") {
        set("r4-val", "n/a");
        set("r4-range", "Check the revenue you entered.");
      } else if (c.from === "zero") {
        set("r4-val", pv(0));
        set("r4-range", "No Medicaid patients, so no loss.");
      } else {
        set("r4-val", pv(c.pct[1]));
        set("r4-range", NINE + rng(c.pct[0], c.pct[2], pv));
      }

      set("r1-note", "In " + s.n + ", " + p1(s.t[1]) + " of expansion adults lose coverage (" + rng(s.t[0], s.t[2], p1) + ", 5th to 95th percentile)." + (KYME[s.a] ? " " + KYME_NOTE : ""));
      set("r2-note", "Adults at " + who(c) + ": out of about " + count(c.exp) + " expansion adults. Medians of separate quantities, so the ratio can differ a little from the state share.");
      set("r3-note", "Net revenue lost is about " + pv(s.m[1]) + " of Medicaid payments (" + rng(s.m[0], s.m[2], pv) + "). Middle of 20,000 simulated outcomes." + (c.from === "state" ? " Add your revenue to use yours." : ""));
      var pc = percentile(c);
      set(
        "r5-note",
        "Compared with peer centers: " + (pc <= 0 ? "below the 5th percentile of " : pc >= 100 ? "above the 95th percentile of " : "about the " + ordinal(pc) + " percentile of ") + M.bench.n + " centers (" +
          (pc <= 0 ? "fewer than 5% lose less" : pc >= 100 ? "fewer than 5% lose more" : "about " + (100 - pc) + "% of them lose more") + " of their revenue). Approximate, read from the peer counts."
      );

      var ptsEl = $("in-pts");
      set(
        "hint-pts",
        S.pts == null
          ? "Blank uses the average " + s.n + " center: " + F.int(s.c) + " Medicaid patients. Medicaid and CHIP, all ages (UDS Table 4)."
          : "Medicaid and CHIP patients of all ages, from UDS Table 4."
      );
      set("hint-rev", S.rev != null && S.pts == null ? "Add your Medicaid patients to use this revenue." : S.rev != null ? usdWords(S.rev) + " a year." : "Revenue is optional. It gives your share of revenue.");
      var rw = errState.rev || (c.from === "revbad" ? "This is smaller than the modeled loss. Enter total revenue in dollars per year, not thousands." : "");
      showErr("pts", errState.pts);
      showErr("rev", rw);
      ptsEl.placeholder = F.int(s.c) + " (average)";

      var wh = c.avg ? "an average " + s.n + " center with " + F.int(c.pts) + " Medicaid patients" : "a center with " + F.int(c.pts) + " Medicaid patients";
      var tail = c.from === "rev" ? ", or " + pvc(c.pct[1]) + " of total revenue." : c.from === "zero" || c.from === "revbad" ? "." : ", or " + pv(c.pct[1]) + " of total revenue for a typical center in the state.";
      var sum =
        "In " + s.n + ", we estimate " + p1(s.t[1]) + " of expansion adults (" + rng(s.t[0], s.t[2], p1) + ") could lose Medicaid in a year under the 2027 work-requirement rule, and " + p0(s.s) +
        " of that loss is administrative." + (KYME[s.a] ? " " + KYME_NOTE : "") + " For " + wh + ", that is about " + count(c.lost[1]) + " adults and " + money(c.usd[1]) + " a year in net revenue (" +
        rng(money(c.usd[0]), money(c.usd[2]), String) + ")" + tail + " Model output on public data, not a forecast.";
      set("p9-summary", S.bad ? "Fix the highlighted field to update these numbers." : sum);
      $("p9-results").classList.toggle("is-stale", S.bad);
      ["btn-copy", "btn-tsv", "btn-png"].forEach(function (id) {
        $(id).disabled = S.bad;
      });
      $("btn-tsv").setAttribute("data-ex-copy", tsv(c));

      Ex.navReadout(S.picked || S.pts != null ? s.n + ": " + money(c.usd[1]) + " a year" + (c.from === "rev" ? ", " + pvc(c.pct[1]) + " of revenue" : "") : "");
      return c;
    }
    function tsv(c) {
      var s = c.s,
        rows = [
          ["Measure", "Unit", "5th percentile", "Median", "95th percentile"],
          ["Expansion adults in " + s.n + " who lose coverage", "% of expansion adults", (s.t[0] * 100).toFixed(1), (s.t[1] * 100).toFixed(1), (s.t[2] * 100).toFixed(1)],
          ["Expansion adults at " + (c.avg ? "an average center (" + F.int(c.pts) + " Medicaid patients)" : "your center (" + F.int(c.pts) + " Medicaid patients)") + " who lose coverage", "adults", Math.round(c.lost[0]), Math.round(c.lost[1]), Math.round(c.lost[2])],
          ["Net revenue lost per year", "dollars", Math.round(c.usd[0]), Math.round(c.usd[1]), Math.round(c.usd[2])],
          ["Share of total revenue" + (c.from === "rev" ? " (yours)" : " (typical center in state)"), "%", c.pct[0].toFixed(2), c.pct[1].toFixed(2), c.pct[2].toFixed(2)],
          ["Administrative share of the loss", "% of loss", "", (s.s * 100).toFixed(0), ""],
          ["Source: Primordial Analytics model on public data. Example, not client work. Not a forecast."],
        ];
      return rows
        .map(function (r) {
          return r.join("\t");
        })
        .join("\n");
    }

    /* ---------- inputs ---------- */
    var errTimer = 0;
    function readField(id, kind) {
      var el = $(id),
        raw = el.value.trim(),
        msg = "",
        v = parseNum(raw);
      if (raw !== "" && isNaN(v)) msg = kind === "pts" ? "Enter a whole number, such as 8,000 or 8K." : "Enter an amount in dollars, such as 30,000,000 or 30M.";
      else if (v != null) {
        if (kind === "pts") {
          if (v < 0 || Math.floor(v) !== v || v > 1e6) msg = "Enter a whole number from 0 to 1,000,000.";
        } else if (v <= 0 || v > 5e9) msg = "Enter an amount from $1 to $5,000,000,000.";
      }
      return msg ? { err: msg } : { v: v };
    }
    function applyFields() {
      var a = readField("in-pts", "pts"),
        b = readField("in-rev", "rev");
      errState.pts = a.err || "";
      errState.rev = b.err || "";
      S.bad = !!(a.err || b.err);
      if (!S.bad) {
        S.pts = a.v;
        S.rev = b.v;
      }
      autoPeer();
      renderTool();
      splitText();
      redrawPeers();
      peerText();
    }
    function onField() {
      clearTimeout(errTimer);
      errTimer = setTimeout(applyFields, 200);
    }
    function liveFormat(el) {
      var v = el.value;
      if (!/^[\d,]*$/.test(v) || v.replace(/,/g, "").length > 15) return;
      var pos = el.selectionStart,
        before = v.slice(0, pos).replace(/,/g, "").length,
        d = v.replace(/,/g, ""),
        f = d ? Number(d).toLocaleString("en-US") : "";
      if (f === v) return;
      el.value = f;
      var n = 0,
        i = 0;
      for (; i < f.length && n < before; i++) if (f[i] !== ",") n++;
      try {
        el.setSelectionRange(i, i);
      } catch (e) {}
    }
    ["in-pts", "in-rev"].forEach(function (id) {
      var el = $(id);
      el.addEventListener("input", function () {
        liveFormat(el);
        onField();
      });
      el.addEventListener("blur", function () {
        var r = readField(id, id === "in-pts" ? "pts" : "rev");
        if (r.v != null && !r.err) el.value = F.int(r.v);
        clearTimeout(errTimer);
        applyFields();
      });
      el.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          clearTimeout(errTimer);
          applyFields();
        }
      });
    });
    $("btn-avg").addEventListener("click", function () {
      $("in-pts").value = F.int(byA[S.abbr].c);
      clearTimeout(errTimer);
      applyFields();
      $("in-pts").focus();
    });

    /* ---------- state pickers ---------- */
    var combos = [];
    function sayNotCovered(note, names) {
      note.textContent = "";
      if (!names || !names.length) {
        note.hidden = true;
        return;
      }
      var who2 = names.length === 1 ? names[0] + " is" : names.slice(0, -1).join(", ") + " and " + names[names.length - 1] + " are";
      note.appendChild(document.createTextNode(who2 + " not one of the " + (NS - 1) + " expansion states and DC this model covers, so there is no 2027 estimate for " + (names.length === 1 ? "it" : "them") + " here. "));
      note.appendChild(Ex.el("a", { href: "#compare", text: "See the states we cover" }));
      note.hidden = false;
    }
    function resolve(text) {
      var t = plain(text);
      if (!t) return null;
      var hit = null;
      alpha.forEach(function (s) {
        if (plain(s.n) === t || plain(s.a) === t) hit = s;
      });
      if (hit) return { item: hit };
      var non = NONEXP.filter(function (s) {
        return plain(s.n) === t || plain(s.a) === t;
      });
      if (non.length) return { non: [non[0].n] };
      if (t.length >= 3) {
        var cov = alpha.filter(function (s) {
          return plain(s.n).indexOf(t) === 0;
        });
        var nn = NONEXP.filter(function (s) {
          return plain(s.n).indexOf(t) === 0;
        });
        if (!cov.length && nn.length) return { non: nn.slice(0, 3).map(function (s) { return s.n; }) };
      }
      return null;
    }
    function restoreCombos() {
      if (!S.picked) return;
      combos.forEach(function (c) {
        if (c.combo.getValue() !== S.abbr) c.combo.setValue(S.abbr, { silent: true });
      });
    }
    function makeCombo(hostId, id, label) {
      var host = $(hostId);
      var rec = { host: host };
      rec.combo = Ex.combobox(host, {
        id: id,
        label: label || "State",
        placeholder: "Type a state",
        noun: "of " + NS + " states",
        maxResults: 60,
        items: alpha.map(function (s) {
          return { value: s.a, label: s.n, hint: s.a };
        }),
        value: S.picked ? S.abbr : undefined,
        onSelect: function (it) {
          if (it) setState(it.value, { from: id });
          else restoreCombos();
        },
      });
      var note = Ex.el("div", { class: "p9-note", role: "status", hidden: true });
      host.parentNode.insertBefore(note, host.nextSibling);
      rec.note = note;
      var input = host.querySelector("input");
      input.addEventListener("input", function () {
        var r = resolve(input.value);
        sayNotCovered(note, r && r.non);
      });
      function commit() {
        var r = resolve(input.value);
        if (r && r.item) {
          if (r.item.a !== S.abbr || !S.picked) setState(r.item.a, { from: id });
        } else if (r && r.non) sayNotCovered(note, r.non);
      }
      host.addEventListener(
        "keydown",
        function (e) {
          if (e.key === "Tab" || e.key === "Enter") commit();
        },
        true
      );
      host.addEventListener(
        "blur",
        function (e) {
          if (e.target === input) commit();
        },
        true
      );
      combos.push(rec);
    }
    makeCombo("pick-state", "state-tool", "State");

    function setState(abbr, o) {
      o = o || {};
      if (!byA[abbr]) return;
      var same = abbr === S.abbr && S.picked;
      S.abbr = abbr;
      S.picked = true;
      combos.forEach(function (c) {
        sayNotCovered(c.note, null);
        var st = c.host.querySelector(".ex-vh[role=status]");
        if (st) st.textContent = "";
        if (c.combo.getValue() !== abbr) c.combo.setValue(abbr, { silent: true });
      });
      if (same) return;
      updateAll();
      try {
        var u = new URL(window.location.href);
        if (abbr === M.typical && !S.picked) u.searchParams.delete("state");
        else u.searchParams.set("state", abbr);
        window.history.replaceState(null, "", u.pathname + u.search + u.hash);
      } catch (e) {}
      if (o.from === "chart") Ex.live(byA[abbr].n + " selected. The tool above now shows it.");
    }

    /* ---------- drawing helpers ---------- */
    function whisk(x0, x1, m) {
      return "M" + x0 + "," + (m - 4) + "V" + (m + 4) + "M" + x0 + "," + m + "H" + x1 + "M" + x1 + "," + (m - 4) + "V" + (m + 4);
    }
    /* bottom axis, no gridlines: the marks carry their own values */
    function xAxis(c, x, h, ticks, fmt) {
      c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + h + ")").call(d3.axisBottom(x).ticks(ticks).tickSize(0).tickPadding(8).tickFormat(fmt)).select(".domain").remove();
    }
    function activate(sel, fn) {
      sel.on("click", function (e, d) {
        fn(d, e);
      });
      sel.on("keydown", function (e, d) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          fn(d, e);
        }
      });
    }
    function rowGeom(w, wideRow, narRow, min) {
      var nar = w < (min || NARROW);
      return { nar: nar, ROW: nar ? narRow || 44 : wideRow || 26 };
    }
    function rowText(g, G, mid, text, cls) {
      return g
        .append("text")
        .attr("class", cls || "p9-lab")
        .attr("x", -8)
        .attr("y", G.nar ? 13 : mid)
        .attr("dy", G.nar ? 0 : "0.35em")
        .attr("text-anchor", G.nar ? "start" : "end")
        .text(text);
    }
    function lcFirst(s) {
      return /^(Medicaid|CMS|UDS|ACS)\b/.test(s) ? s : s.charAt(0).toLowerCase() + s.slice(1);
    }
    function d3Min(a) {
      return Math.min.apply(null, a);
    }
    function d3Max(a) {
      return Math.max.apply(null, a);
    }

    /* ---------- where the loss comes from (one thin bar, labeled in place) ---------- */
    function splitText() {
      var s = byA[S.abbr],
        ad = s.s,
        nc = 1 - s.s;
      set("split-title", p0(ad) + " of the loss in " + N(s) + " is paperwork, not eligibility");
      var warn = $("split-warn");
      warn.hidden = !KYME[s.a];
      warn.textContent = KYME[s.a] ? "Among the least certain: this state reports near-zero procedural terminations, so its administrative share may be too low." : "";
      set("split-sub", "Of the median coverage loss in " + s.n + " (" + p1(s.t[1]) + " of expansion adults), the share that comes from each cause.");
      var stack = $("p9-stack");
      stack.textContent = "";
      stack.setAttribute("aria-label", "Of the loss in " + s.n + ", " + p0(nc) + " is non-compliance and " + p0(ad) + " is administrative, dropped over paperwork.");
      stack.appendChild(Ex.el("div", { class: "p9-stack__labels", "aria-hidden": "true" }, [Ex.el("span", { text: "Do not meet the rule " + p0(nc) }), Ex.el("span", { text: "Dropped over paperwork " + p0(ad) })]));
      stack.appendChild(
        Ex.el("div", { class: "p9-stack__bar", "aria-hidden": "true" }, [
          Ex.el("span", { class: "p9-stack__nc", style: "width:" + (nc * 100).toFixed(2) + "%" }),
          Ex.el("span", { class: "p9-stack__ad", style: "width:" + (ad * 100).toFixed(2) + "%" }),
        ])
      );
      var list = $("p9-split-list");
      list.textContent = "";
      function item(title, text) {
        list.appendChild(Ex.el("div", {}, [Ex.el("dt", { text: title }), Ex.el("dd", { text: text })]));
      }
      item("Non-compliance", "People who do not meet the rule. Median " + p1(s.w[1]) + " of expansion adults (" + rng(s.w[0], s.w[2], p1) + ", 5th to 95th).");
      item("Administrative", "People who qualify or are exempt but get dropped anyway. Median " + p1(s.p[1]) + " of expansion adults (" + rng(s.p[0], s.p[2], p1) + ", 5th to 95th). A better renewal process could in principle reduce this part.");
      var cap = "The two medians need not add up to the median total, so the bar splits the median loss by each cause's median share of it.";
      if (KYME[S.abbr]) cap += " In " + s.n + ", " + lcFirst(KYME_NOTE);
      set("split-cap", cap);
    }
    var splitTable = liveTable("table-split", function () {
      var s = byA[S.abbr];
      return {
        caption: "Share of expansion adults in " + s.n + " who lose Medicaid in a year, by reason.",
        columns: [
          { key: "n", label: "Reason" },
          { key: "p5", label: "5th percentile", format: p1 },
          { key: "p50", label: "Median", format: p1 },
          { key: "p95", label: "95th percentile", format: p1 },
        ],
        rows: [
          { n: "Total", p5: s.t[0], p50: s.t[1], p95: s.t[2] },
          { n: "Non-compliance", p5: s.w[0], p50: s.w[1], p95: s.w[2] },
          { n: "Administrative", p5: s.p[0], p50: s.p[1], p95: s.p[2] },
        ],
      };
    });

    /* ---------- notes that move out of the way (all from data.json) ---------- */
    function li(host, text) {
      host.appendChild(Ex.el("li", { text: text }));
    }
    var byTotal = states.slice().sort(function (a, b) {
      return a.t[1] - b.t[1];
    });
    var LO = byTotal[0],
      HI = byTotal[byTotal.length - 1];
    var WIDE = states.reduce(function (a, b) {
      return b.t[2] - b.t[0] > a.t[2] - a.t[0] ? b : a;
    });
    set("compare-h", "Coverage loss runs from " + p0(LO.t[1]) + " to " + p0(HI.t[1]) + " across states");
    (function compareNotes() {
      var host = $("compare-notes"),
        ncs = states.map(function (s) {
          return s.w[1];
        }),
        ads = states.slice().sort(function (a, b) {
          return a.p[1] - b.p[1];
        });
      li(host, "The national median is " + p1(M.nat[1] / 100) + " (" + rng(M.nat[0] / 100, M.nat[2] / 100, p1) + " across draws). CMS's central case is " + p1(M.cms) + "; our median is " + F.num(M.vs_cms, 1) + " points above it because state noise does not preserve the mean. CMS supplied the levels, so this is a consistency check, not a finding. " + p0(M.below_cms) + " of national draws fall below CMS. Model output, not a forecast.");
      li(host, "Non-compliance loss barely varies by state (" + rng(d3Min(ncs), d3Max(ncs), p1) + "). Administrative loss, people who comply or are exempt and are dropped anyway, runs from " + p1(ads[0].p[1]) + " (" + N(ads[0]) + ") to " + p1(ads[ads.length - 1].p[1]) + " (" + N(ads[ads.length - 1]) + ") and is " + p0(M.ref.adm_share) + " of the loss in the median state. That is the part a better renewal process could in principle reduce.");
      li(host, "Across the " + F.int(M.centers.n) + " expansion-state centers, about " + F.approx(M.centers.lost[1], 3) + " of " + F.approx(M.centers.adults, 2) + " expansion adults lose coverage (" + F.approx(M.centers.lost[0], 3) + " to " + F.approx(M.centers.lost[2], 3) + "), " + p0(M.centers.admin_share) + " of them for administrative reasons. Net revenue falls $" + F.num(M.centers.usd_b[1], 1) + " billion a year ($" + F.num(M.centers.usd_b[0], 1) + " to $" + F.num(M.centers.usd_b[2], 1) + " billion). The totals treat each state's verification scenario and paperwork shock as independent, so the ranges are somewhat narrow.");
    })();
    (function limits() {
      set("lim-exp", p0(M.uds.exp_share));
      set("lim-exp1", p0(M.uds.exp_share));
      set("lim-kyme", p1(byA.KY.p[1]) + " and " + p1(byA.ME.p[1]));
      set("lim-nr", F.int(M.uds.not_reporting));
      set("lim-all", F.int(M.uds.centers));
      set("lim-rep", F.int(M.uds.reporting));
    })();

    /* ---------- ranked states: a dot plot, the chosen state in bold ---------- */
    var METRICS = {
      t: {
        short: "coverage loss",
        get: function (s) {
          return s.t;
        },
        whisk: true,
        f: p1,
        ax: function (d) {
          return F.pct(d, 0);
        },
        ref: { v: M.cms, t: "CMS central case " + p1(M.cms) },
        title: "Expansion adults who lose Medicaid in a year",
        noun: "Share of expansion adults who lose Medicaid in a year",
        sub: "Median of 20,000 simulated outcomes per state.",
        top: function (hi, lo) {
          return N(hi) + " has the highest coverage loss (" + p1(hi.t[1]) + ") and " + N(lo) + " the lowest (" + p1(lo.t[1]) + ")";
        },
        note: function () {
          return "State medians run from " + p1(LO.t[1]) + " in " + N(LO) + " to " + p1(HI.t[1]) + " in " + N(HI) + ". " + N(WIDE) + "'s own range is " + rng(WIDE.t[0], WIDE.t[2], p1) + ".";
        },
      },
      s: {
        short: "administrative share",
        get: function (s) {
          return [s.s, s.s, s.s];
        },
        whisk: false,
        f: p0,
        ax: function (d) {
          return F.pct(d, 0);
        },
        ref: { v: M.ref.adm_share, t: "Median state " + p0(M.ref.adm_share) },
        title: "Administrative share of the loss",
        noun: "Administrative share of the loss",
        sub: "People who comply or are exempt and are dropped anyway, as a share of everyone who loses coverage. Median of 20,000 simulated outcomes. No range is shown: only the median of this share is modeled.",
        top: function (hi, lo) {
          return "Administrative loss is " + p0(hi.s) + " of the total in " + N(hi) + " and " + p0(lo.s) + " in " + N(lo);
        },
        note: function (hi, lo) {
          return "Administrative loss is " + p0(hi.s) + " of the total in " + N(hi) + " and " + p0(lo.s) + " in " + N(lo) + ".";
        },
      },
      r: {
        short: "% of revenue",
        get: function (s) {
          return s.r;
        },
        whisk: true,
        f: pv,
        ax: function (d) {
          return F.pctValue(d, 0);
        },
        ref: { v: M.ref.r, t: "Median state " + pv(M.ref.r) },
        title: "Net revenue lost, % of revenue",
        noun: "Net revenue loss as a share of total revenue",
        sub: "For a center with the state's average Medicaid patient count, middle of 20,000 simulated outcomes. Revenue includes grants.",
        top: function (hi, lo) {
          return "Revenue effect runs from " + pv(lo.r[1]) + " of revenue in " + N(lo) + " to " + pv(hi.r[1]) + " in " + N(hi);
        },
        note: function (hi, lo) {
          return "Revenue effect runs from " + pv(lo.r[1]) + " of revenue in " + N(lo) + " to " + pv(hi.r[1]) + " in " + N(hi) + ".";
        },
      },
    };
    var ROW = 22;
    var NEAR = 5;
    var sortedFor = function (m) {
      var M0 = METRICS[m];
      return states.slice().sort(function (a, b) {
        return M0.get(b)[1] - M0.get(a)[1];
      });
    };
    function rankOf(abbr, m) {
      return (
        sortedFor(m).findIndex(function (s) {
          return s.a === abbr;
        }) + 1
      );
    }
    /* by default: the five highest, the five lowest and the chosen state; "Show all" adds the rest */
    function viewRows(rows) {
      if (S.all) return rows;
      var keep = rows.map(function (s, i) {
        return i < NEAR || i >= rows.length - NEAR || s.a === S.abbr;
      });
      var out = [],
        skipped = 0;
      rows.forEach(function (s, i) {
        if (keep[i] || (keep[i - 1] && keep[i + 1])) {
          if (skipped) out.push({ gap: skipped });
          skipped = 0;
          out.push(s);
        } else skipped++;
      });
      return out;
    }
    var statesChart;
    function chartRowNode(abbr) {
      var n = null;
      d3.select($("chart-states"))
        .selectAll("g.ex-mark")
        .each(function (d) {
          if (d.a === abbr) n = this;
        });
      return n;
    }
    function scrollRow() {
      var n = chartRowNode(S.abbr);
      if (n && n.scrollIntoView) n.scrollIntoView({ block: "nearest" });
    }
    function sideTip(sel, c, endX) {
      function place(e, el) {
        if (c.narrow) return;
        if (e && e.type === "pointermove" && e.pointerType !== "mouse") return;
        var d = el.__data__,
          sv = c.svg.node().getBoundingClientRect(),
          r = el.getBoundingClientRect();
        Ex.tooltip.move({ x: sv.left + c.margin.left + endX(d) + 20, y: r.top + r.height / 2 });
      }
      sel.each(function () {
        var el = this;
        ["pointerenter", "pointermove", "focus"].forEach(function (t) {
          el.addEventListener(t, function (e) {
            place(e, el);
          });
        });
      });
    }
    if (HAS_D3)
      statesChart = Ex.chart($("chart-states"), {
        label: "Ranked dot plot",
        margin: function (w) {
          return { top: 26, right: w < NARROW ? 46 : 176, bottom: 30, left: w < NARROW ? 108 : 150 };
        },
        height: function () {
          return viewRows(sortedFor(S.metric)).length * ROW + 56;
        },
        render: function (c) {
          c.svg.attr("role", "group");
          var M0 = METRICS[S.metric],
            all = sortedFor(S.metric),
            view = viewRows(all),
            rows = view.filter(function (d) {
              return !d.gap;
            }),
            H = view.length * ROW;
          var maxv = d3.max(all, function (s) {
            return M0.get(s)[2];
          });
          var x = d3.scaleLinear().domain([0, maxv]).nice().range([0, c.width]);
          c.svg.attr(
            "aria-label",
            "Ranked dot plot of " + lcFirst(M0.noun) + ", " + (S.all ? "all " + all.length + " states" : "showing " + rows.length + " of " + all.length + " states: the highest, the lowest and the one you chose") + ". " + M0.top(all[0], all[all.length - 1]) + ". Use the arrow keys to move between states and Enter to use one in the tool."
          );
          xAxis(c, x, H, c.narrow ? 4 : 5, M0.ax);
          var rx = x(M0.ref.v);
          c.g.append("line").attr("class", "ex-ref-line").attr("x1", rx).attr("x2", rx).attr("y1", -3).attr("y2", H);
          c.g.append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", rx).attr("y", -10).attr("text-anchor", rx < 80 ? "start" : rx > c.width - 80 ? "end" : "middle").text(M0.ref.t);
          c.g.append("line").attr("class", "ex-baseline").attr("y1", 0).attr("y2", H);
          var rank = {},
            pos = {};
          all.forEach(function (s, i) {
            rank[s.a] = i + 1;
          });
          view.forEach(function (d, i) {
            if (!d.gap) pos[d.a] = i;
          });
          view.forEach(function (d, i) {
            if (d.gap)
              c.g
                .append("text")
                .attr("class", "ex-svg-label p9-gap")
                .attr("aria-hidden", "true")
                .attr("x", -8)
                .attr("y", i * ROW + ROW / 2)
                .attr("dy", "0.35em")
                .attr("text-anchor", "end")
                .text(d.gap + " more states");
          });
          var isSel = function (d) {
            return d.a === S.abbr;
          };
          var g = c.g
            .selectAll("g.ex-mark")
            .data(rows, function (d) {
              return d.a;
            })
            .join("g")
            .attr("class", function (d) {
              return "ex-mark" + (isSel(d) ? " is-sel" : "");
            })
            .attr("transform", function (d) {
              return "translate(0," + pos[d.a] * ROW + ")";
            });
          g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", ROW);
          var mid = ROW / 2;
          if (M0.whisk)
            g.filter(isSel)
              .append("path")
              .attr("class", "ex-ci-whisker")
              .attr("d", function (d) {
                var v = M0.get(d);
                return whisk(x(v[0]), x(v[2]), mid);
              });
          g.append("path")
            .attr("class", function (d) {
              return "ex-stem ex-stem--est" + (isSel(d) ? " ex-sel" : "");
            })
            .attr("d", function (d) {
              return "M0," + mid + "H" + x(M0.get(d)[1]);
            });
          g.append("circle")
            .attr("class", function (d) {
              return "ex-dot ex-dot--est" + (isSel(d) ? " ex-sel" : "");
            })
            .attr("r", 4.5)
            .attr("cx", function (d) {
              return x(M0.get(d)[1]);
            })
            .attr("cy", mid);
          g.append("text")
            .attr("class", function (d) {
              return "p9-lab" + (c.narrow ? " p9-lab--sm" : "") + (isSel(d) ? " ex-sel" : "");
            })
            .attr("x", -8)
            .attr("y", mid)
            .attr("dy", "0.35em")
            .attr("text-anchor", "end")
            .text(function (d) {
              return c.narrow && d.n.length > 14 ? d.a : d.n;
            });
          var val = g
            .append("text")
            .attr("class", function (d) {
              return "ex-svg-value" + (isSel(d) ? " ex-sel" : "");
            })
            .attr("x", function (d) {
              return x(M0.get(d)[isSel(d) && M0.whisk ? 2 : 1]) + 8;
            })
            .attr("y", mid)
            .attr("dy", "0.35em");
          val.append("tspan").text(function (d) {
            return M0.f(M0.get(d)[1]);
          });
          if (!c.narrow && M0.whisk)
            val
              .filter(isSel)
              .append("tspan")
              .attr("class", "p9-range")
              .attr("dx", 6)
              .text(function (d) {
                return "(" + rng(M0.get(d)[0], M0.get(d)[2], M0.f) + ")";
              });
          Ex.tooltip.attach(g, function (el) {
            var d = el.__data__,
              v = M0.get(d),
              r = [];
            if (S.metric === "s") {
              r.push({ name: "Administrative share", value: p0(d.s), color: "est" });
              r.push({ name: "Non-compliance (median)", value: p1(d.w[1]) });
              r.push({ name: "Administrative (median)", value: p1(d.p[1]) });
            } else {
              r.push({ name: "Median", value: M0.f(v[1]), color: "est" });
              r.push({ name: "5th to 95th percentile", value: rng(v[0], v[2], M0.f) });
            }
            r.push({ name: "Rank", value: "#" + rank[d.a] + " of " + all.length });
            return { title: d.n, rows: r, note: d.a === S.abbr && S.picked ? "Your state" : "Click, tap or press Enter to use this state" };
          });
          sideTip(g, c, function (d) {
            return x(M0.get(d)[M0.whisk ? 2 : 1]);
          });
          activate(g, function (d) {
            Ex.tooltip.hide();
            setState(d.a, { from: "chart" });
            var n = chartRowNode(d.a);
            if (n && n.focus) n.focus({ preventScroll: true });
          });
          Ex.roving(c.g.node(), ".ex-mark");
          var cur = g.filter(isSel);
          if (cur.size()) {
            g.attr("tabindex", "-1");
            cur.attr("tabindex", "0");
          }
        },
      });
    else statesChart = chart("chart-states");
    var statesTable = liveTable("table-states", function () {
      return {
        caption: "Modeled loss by state, highest median coverage loss first. Shares of expansion adults who lose Medicaid in a year; dollars are net revenue per year per 1,000 Medicaid patients.",
        label: "Scrollable table of state results",
        columns: [
          { key: "n", label: "State" },
          { key: "t5", label: "Loss, 5th percentile", format: p1 },
          { key: "t50", label: "Loss, median", format: p1 },
          { key: "t95", label: "Loss, 95th percentile", format: p1 },
          { key: "w50", label: "Non-compliance, median", format: p1 },
          { key: "p50", label: "Administrative, median", format: p1 },
          { key: "s", label: "Administrative share of loss", format: p0 },
          { key: "r50", label: "% of total revenue, median", format: pv },
          { key: "d50", label: "$ per 1,000 patients, median", format: money },
          { key: "d5", label: "$ per 1,000, 5th percentile", format: money },
          { key: "d95", label: "$ per 1,000, 95th percentile", format: money },
        ],
        rows: sortedFor("t").map(function (s) {
          return { n: s.n, t5: s.t[0], t50: s.t[1], t95: s.t[2], w50: s.w[1], p50: s.p[1], s: s.s, r50: s.r[1], d50: s.d[1], d5: s.d[0], d95: s.d[2] };
        }),
      };
    });
    function statesText() {
      var M0 = METRICS[S.metric],
        rows = sortedFor(S.metric);
      set("states-title", M0.title);
      set("states-sub", M0.noun + ". " + M0.sub);
      set("states-hint", (S.picked ? "" : N(byA[S.abbr]) + " is shown as an example. ") + "Click a state to use it above.");
      set("btn-all", S.all ? "Show fewer states" : "Show all " + NS + " states");
      $("btn-all").setAttribute("aria-expanded", S.all ? "true" : "false");
      set("note-spread", "");
      var n1 = $("note-spread");
      n1.appendChild(Ex.el("strong", { text: "Spread. " }));
      n1.appendChild(document.createTextNode(M0.note(rows[0], rows[rows.length - 1]) + (M0.whisk ? "" : " No range is shown for this share.")));
      var n2 = $("note-cms");
      n2.textContent = "";
      n2.appendChild(Ex.el("strong", { text: "CMS. " }));
      n2.appendChild(document.createTextNode("CMS's central case is " + p1(M.cms) + ". Our median is " + F.num(M.vs_cms, 1) + " points above it, from the unrounded figures."));
      n2.hidden = S.metric !== "t";
    }
    [].forEach.call(document.querySelectorAll("input[name=metric]"), function (r) {
      r.addEventListener("change", function () {
        if (!r.checked) return;
        S.metric = r.value;
        statesText();
        statesChart.redraw();
        scrollRow();
        Ex.live(byA[S.abbr].n + " is now #" + rankOf(S.abbr, S.metric) + " of " + NS + " by " + METRICS[S.metric].short + ". " + METRICS[S.metric].top(sortedFor(S.metric)[0], sortedFor(S.metric)[NS - 1]) + ".");
      });
    });
    $("btn-all").addEventListener("click", function () {
      S.all = !S.all;
      statesText();
      statesChart.redraw();
      Ex.live(S.all ? "Showing all " + NS + " states." : "Showing the highest, the lowest and your state.");
    });

    /* ---------- peers ---------- */
    function inferSize(pts) {
      var best = SIZES[0],
        bd = Infinity;
      SIZES.forEach(function (sz) {
        var r = RANGE[sz],
          tot = pts / MS[sz],
          d = tot < r[0] ? r[0] - tot : tot >= r[1] ? tot - r[1] + 1 : 0;
        if (d < bd) {
          bd = d;
          best = sz;
        }
      });
      return best;
    }
    function autoPeer() {
      if (S.peerManual) return;
      var c = calc();
      S.size = inferSize(c.pts);
      var bs = D.bands
        .filter(function (b) {
          return b.size === S.size;
        })
        .sort(function (a, b) {
          return b.n - a.n;
        });
      S.set = bs[0].set;
    }
    function inPeer(b) {
      return b.size === S.size && b.set === S.set;
    }
    function bandLabel(b, nar) {
      return nar ? SIZE_SHORT[b.size] + " " + b.set.toLowerCase() : b.size + ", " + b.set.toLowerCase();
    }
    var PEER_MAX = 8,
      BAND_MAX = 7;
    /* the visitor's own mark: a dashed line through the plot and one label */
    function drawYou(c, calcd, x, h, max, label) {
      var off = calcd.pct[1] > max,
        X = x(Math.min(calcd.pct[1], max)),
        right = X > c.width - 150;
      c.g.append("line").attr("class", "p9-you-line").attr("x1", X).attr("x2", X).attr("y1", -4).attr("y2", h);
      c.g
        .append("text")
        .attr("class", "ex-svg-label ex-svg-label--direct")
        .attr("x", right ? X - 8 : X + 8)
        .attr("y", -10)
        .attr("text-anchor", right ? "end" : "start")
        .text((off ? label + ", off the scale: " : label + " ") + pvc(calcd.pct[1]));
    }
    var peersChart = chart("chart-peers", {
      label: "Chart",
      margin: function (w) {
        return { top: 30, right: w < NARROW ? 46 : 56, bottom: 30, left: w < NARROW ? 22 : 150 };
      },
      height: function (w) {
        return D.bands.length * (w < NARROW ? 44 : 30) + 60;
      },
      render: function (c) {
        c.svg.attr("role", "group");
        var G = rowGeom(c.w, 30),
          me = calc(),
          H = D.bands.length * G.ROW;
        var x = d3.scaleLinear().domain([0, BAND_MAX]).range([0, c.width]);
        var lo = D.bands.reduce(function (a, b) {
          return b.r[1] < a.r[1] ? b : a;
        });
        var top = D.bands.reduce(function (a, b) {
          return b.r[1] > a.r[1] ? b : a;
        });
        c.svg.attr(
          "aria-label",
          "Chart of net revenue loss as a share of total revenue for eight peer groups. Medians run from " + pv(lo.r[1]) + " for " + bandLabel(lo).toLowerCase() + " centers to " + pv(top.r[1]) + " for " + bandLabel(top).toLowerCase() + " centers. Your center: " + pvc(me.pct[1]) + "."
        );
        xAxis(c, x, H, c.narrow ? 4 : 7, function (d) {
          return F.pctValue(d, 0);
        });
        c.g.append("line").attr("class", "ex-baseline").attr("y1", 0).attr("y2", H);
        var g = c.g
          .selectAll("g.ex-mark")
          .data(D.bands)
          .join("g")
          .attr("class", "ex-mark")
          .attr("transform", function (d, i) {
            return "translate(0," + i * G.ROW + ")";
          });
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", G.ROW);
        var mid = G.nar ? 30 : G.ROW / 2;
        g.append("path").attr("class", function (d) {
          return "ex-ci-whisker ex-ci-whisker--est" + (inPeer(d) ? " ex-sel" : "");
        }).attr("d", function (d) {
          return whisk(x(d.r[0]), x(d.r[2]), mid);
        });
        g.append("circle").attr("class", function (d) {
          return "ex-dot ex-dot--est" + (inPeer(d) ? " ex-sel" : "");
        }).attr("r", 5).attr("cx", function (d) {
          return x(d.r[1]);
        }).attr("cy", mid);
        rowText(g, G, mid, function (d) {
          return bandLabel(d, G.nar);
        }).attr("class", function (d) {
          return "p9-lab" + (inPeer(d) ? " ex-sel" : "");
        });
        g.append("text").attr("class", function (d) {
          return "ex-svg-value" + (inPeer(d) ? " ex-sel" : "");
        }).attr("x", function (d) {
          return x(d.r[2]) + 8;
        }).attr("y", mid).attr("dy", "0.35em").text(function (d) {
          return pv(d.r[1]);
        });
        drawYou(c, me, x, H, BAND_MAX, "You");
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: bandLabel(d) + " (" + d.n + " centers)",
            rows: [
              { name: "Middle estimate", value: pv(d.r[1]), color: "est" },
              { name: "5th to 95th percentile", value: rng(d.r[0], d.r[2], pv) },
              { name: "Net loss per year", value: rng(money(d.d[0]), money(d.d[2]), String) },
              { name: "Medicaid share of patients", value: p0(d.ms) },
              { name: "Lose more than 3%", value: p0(d.o3) + " of centers" },
            ],
            note: "Click or press Enter to use this peer group",
          };
        });
        activate(g, function (d) {
          S.size = d.size;
          S.set = d.set;
          S.peerManual = true;
          redrawPeers();
          peerText();
        });
        Ex.roving(c.g.node(), ".ex-mark");
      },
    });
    var peersTable = liveTable("table-peers", function () {
      return {
        caption: "Net revenue loss at the " + M.bench.n + " of " + M.bench.reporting + " expansion-state centers that report Table 9D and pass the filters (" + M.bench.dropped + " are left out: under 200 Medicaid patients or no revenue), by size and setting. Medians within each group.",
        label: "Scrollable table of peer groups",
        columns: [
          { key: "g", label: "Group" },
          { key: "n", label: "Centers", format: F.int },
          { key: "ms", label: "Medicaid share of patients", format: p0 },
          { key: "d", label: "Net loss per year (5th / middle / 95th)", text: true },
          { key: "r", label: "% of total revenue (5th / middle / 95th)", text: true },
          { key: "o3", label: "Centers losing over 3%", format: p0 },
        ],
        rows: D.bands.map(function (b) {
          return { g: bandLabel(b), n: b.n, ms: b.ms, d: b.d.map(money).join(" / "), r: b.r.map(pv).join(" / "), o3: b.o3 };
        }),
      };
    });
    var histTable = liveTable("table-hist", function () {
      return {
        caption: "Number of centers by middle-estimate net loss as a share of total revenue.",
        columns: [
          { key: "b", label: "Net loss, % of total revenue" },
          { key: "n", label: "Centers", format: F.int },
        ],
        rows: D.hist.map(function (h) {
          return { b: h[1] >= PEER_MAX ? h[0].toFixed(1) + " or more" : h[0].toFixed(1) + " to under " + h[1].toFixed(1), n: h[2] };
        }),
      };
    });
    (function peerStatic() {
      var hi = states.reduce(function (a, b) {
        return b.r[1] > a.r[1] ? b : a;
      });
      var lo = states.reduce(function (a, b) {
        return b.r[1] < a.r[1] ? b : a;
      });
      set(
        "peers-lede",
        "Of the " + M.bench.reporting + " expansion-state centers that report UDS Table 9D, " + M.bench.n + " pass our filters (" + M.bench.dropped + " have under 200 Medicaid patients or no revenue). The median of them loses " + pv(M.bench.med) +
          " of total revenue (" + rng(M.bench.p10, M.bench.p90, pv) + " from the 10th to the 90th percentile of centers), and " + p0(M.bench.o3) + " lose more than 3%. By state the middle estimate runs from " + pv(lo.r[1]) + " (" + N(lo) + ") to " + pv(hi.r[1]) + " (" + N(hi) + "). Revenue includes grants."
      );
    })();
    function peerText() {
      var c = calc(),
        s = c.s,
        pc = percentile(c);
      var b = D.bands.filter(inPeer)[0];
      set(
        "peer-basis",
        "Your peer group: " + S.size + " patients, " + S.set.toLowerCase() + (S.peerManual ? "" : " (our guess)") + ". " +
          (S.peerManual
            ? "You chose this group. Total patients means all payers, not only Medicaid."
            : "We guessed it from your Medicaid count of " + F.int(c.pts) + ", assuming Medicaid is about " + p0(MS[S.size]) + " of patients, the typical share for centers this size. Change it if you know your own.")
      );
      var from = c.from === "rev" ? "from your revenue" : "for a typical center in " + s.n;
      var line = "Your middle estimate is " + pvc(c.pct[1]) + " of total revenue (" + rng(c.pct[0], c.pct[2], pvc) + "), " + from + ". ";
      if (c.from === "revbad") line = "Check the revenue you entered. Using a typical " + s.n + " center instead: " + pv(c.pct[1]) + " of total revenue. ";
      if (b) line += "The median " + b.set.toLowerCase() + " center with " + sizeWords(b.size) + " patients (" + b.n + " centers) loses " + pv(b.r[1]) + " of revenue (" + rng(b.r[0], b.r[2], pv) + "), about " + rng(money(b.d[0]), money(b.d[2]), String) + " a year. " + p0(b.o3) + " of centers like it lose more than 3%.";
      set("peer-more", line);
      var me = c.avg ? "An average " + s.n + " center" : "Your center";
      set(
        "peers-title",
        pc <= 0
          ? "Fewer than 5% of " + M.bench.n + " centers lose less of their revenue than " + (c.avg ? "an average " + s.n + " center" : "you")
          : pc >= 100
          ? "Fewer than 5% of " + M.bench.n + " centers lose more of their revenue than " + (c.avg ? "an average " + s.n + " center" : "you")
          : me + " is at about the " + ordinal(pc) + " percentile of " + M.bench.n + " centers"
      );
    }
    function redrawPeers() {
      peersChart.redraw();
      peersTable();
      histTable();
    }

    /* ---------- drivers ---------- */
    var OUT = { L: "coverage loss", R: "revenue effect" };
    /* short names for the section headline; the full names stay in the chart and table */
    var SHORT = {
      eps_pd: "Paperwork loss",
      regime: "How the state checks the rule",
      nc_noise: "Non-compliance",
      eps_ex: "Renewals from data the state holds",
      ex_nat: "Share verifiable from data",
      excl_mult: "Exemptions",
      theta: "Loss among data-matched members",
      hardship: "The hardship exception",
      eps_M: "Medicaid payment per patient",
      eps_S: "Self-pay per patient",
      kappa: "Adult Medicaid pay",
      f_ref: "The expansion share",
      r_keep: "The share who keep coming",
      v_rel: "Visit rate once uninsured",
    };
    var PLURAL = { excl_mult: 1, eps_ex: 1 };
    function sobolRows() {
      return D.inputs
        .map(function (i, ix) {
          var v = D.sobol[S.abbr][S.out][ix];
          return { k: i.k, n: i.n, h: i.h, a: i.a, s1: v[0], st: v[1] };
        })
        .sort(function (a, b) {
          return b.st - a.st || b.s1 - a.s1;
        });
    }
    function shownRows() {
      return sobolRows().slice(0, TOP_DRIVERS);
    }
    var sobolChart = chart("chart-sobol", {
      label: "Chart",
      margin: function (w) {
        return { top: 38, right: w < LONG_LABELS ? 48 : 60, bottom: 54, left: w < LONG_LABELS ? 22 : 350 };
      },
      height: function (w) {
        return shownRows().length * (w < LONG_LABELS ? 44 : 30) + 92;
      },
      render: function (c) {
        var G = rowGeom(c.w, 30, 44, LONG_LABELS),
          rows = shownRows(),
          all = sobolRows(),
          H = rows.length * G.ROW,
          s = byA[S.abbr];
        var x = d3.scaleLinear().domain([0, Math.max(0.1, all[0].st * 1.1)]).nice().range([0, c.width]);
        c.svg.attr(
          "aria-label",
          "Chart of how much of the uncertainty in " + OUT[S.out] + " for " + s.n + " each input explains, showing " + rows.length + " of " + all.length + " inputs. Largest: " + all[0].n + " (" + p0(all[0].st) + "), " + all[1].n + " (" + p0(all[1].st) + "), " + all[2].n + " (" + p0(all[2].st) + ")."
        );
        xAxis(c, x, H, G.nar ? 4 : 5, function (d) {
          return F.pct(d, 0);
        });
        c.g.append("text").attr("class", "ex-svg-label").attr("x", G.nar ? -8 : 0).attr("y", H + 42).text("share of the uncertainty in the answer");
        c.g.append("line").attr("class", "ex-baseline").attr("y1", 0).attr("y2", H);
        var g = c.g
          .selectAll("g.ex-mark")
          .data(rows, function (d) {
            return d.k;
          })
          .join("g")
          .attr("class", "ex-mark ex-mark--static")
          .attr("transform", function (d, i) {
            return "translate(0," + i * G.ROW + ")";
          });
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", G.ROW);
        var mid = G.nar ? 30 : G.ROW / 2;
        g.append("line").attr("class", "p9-link").attr("x1", function (d) {
          return x(d.s1);
        }).attr("x2", function (d) {
          return x(d.st);
        }).attr("y1", mid).attr("y2", mid);
        g.append("path").attr("class", "ex-stem ex-stem--est").attr("d", function (d) {
          return d.s1 > 0 ? "M0," + mid + "H" + x(d.s1) : "";
        });
        g.append("circle").attr("class", "p9-dot-ink").attr("r", 5).attr("cx", function (d) {
          return x(d.st);
        }).attr("cy", mid);
        rowText(g, G, mid, function (d) {
          return d.n;
        });
        g.append("text").attr("class", "ex-svg-value").attr("x", function (d) {
          return x(d.st) + 10;
        }).attr("y", mid).attr("dy", "0.35em").text(function (d) {
          return p0(d.st);
        });
        /* two direct labels on the first row; on a narrow chart one left-aligned line says the same */
        if (G.nar) c.g.append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", -8).attr("y", -14).text("Stem: input alone. Dot: plus interactions.");
        else {
          var xs = x(rows[0].s1),
            xt = x(rows[0].st),
            fitsRight = xt + 124 < c.width + c.margin.right,
            sameRow = fitsRight && xs > 80;
          Ex.directLabels(c.g, [{ y: sameRow ? -12 : -26, text: "input alone", x: sameRow ? xs - 4 : xs + 4 }], { anchor: "end" });
          Ex.directLabels(c.g, [{ y: -12, text: "plus interactions", x: xt + 4 }], { anchor: fitsRight ? "start" : "end" });
        }
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.n,
            rows: [
              { name: "On its own", value: p0(d.s1), color: "est" },
              { name: "Including interactions", value: p0(d.st) },
            ],
            note: d.h,
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
      },
    });
    var sobolTable = liveTable("table-sobol", function () {
      var s = byA[S.abbr];
      return {
        caption: "Share of the uncertainty in " + OUT[S.out] + " for " + s.n + " that each input explains (first-order and total Sobol indices), all " + D.inputs.length + " inputs.",
        columns: [
          { key: "n", label: "Input" },
          { key: "s1", label: "On its own", format: p0 },
          { key: "st", label: "Including interactions", format: p0 },
          { key: "h", label: "What it is", text: true },
        ],
        rows: sobolRows(),
      };
    });
    function sobolText() {
      var s = byA[S.abbr],
        rows = sobolRows();
      set("drv-h", SHORT[rows[0].k] + (PLURAL[rows[0].k] ? " explain " : " explains ") + p0(rows[0].st) + " of the uncertainty in " + N(s) + "'s " + OUT[S.out]);
      set("sobol-title", "Share of uncertainty explained, by input" + (S.picked ? "" : " (example state)"));
      set("sobol-sub", "In " + s.n + ", two inputs matter most for " + OUT[S.out] + ": " + lcFirst(rows[0].n) + ", and " + lcFirst(rows[1].n) + ". On their own they explain about " + Math.round((rows[0].s1 + rows[1].s1) * 100) + "% of the uncertainty in the answer. Showing " + TOP_DRIVERS + " of " + rows.length + ", largest first; the data table has all " + rows.length + ".");
      set("sobol-cap", "Largest three: " + rows.slice(0, 3).map(function (r) {
        return r.n + " (" + p0(r.st) + ")";
      }).join(", ") + ". About the largest: " + lcFirst(rows[0].h));
      var host = $("drv-notes");
      host.textContent = "";
      host.appendChild(Ex.el("p", { class: "ex-note" }, [Ex.el("strong", { text: "Reading it. " }), "Stem: the input alone. Dot: with its interactions."]));
      rows.filter(function (r) {
        return r.a;
      }).slice(0, 2).forEach(function (r) {
        host.appendChild(Ex.el("p", { class: "ex-note" }, [Ex.el("strong", { text: SHORT[r.k] + ". " }), r.a]));
      });
      var dl = M.drivers.loss,
        dr = M.drivers.revenue;
      host.appendChild(
        Ex.el("p", { class: "ex-note" }, [
          Ex.el("strong", { text: "All states. " }),
          S.out === "L"
            ? "Paperwork loss leads in " + dl.eps_pd + " of " + NS + " states; the checking method in the other " + dl.regime + "."
            : "Paperwork loss or the checking method leads in " + (dr.eps_pd + dr.regime) + " states; Medicaid payment per patient leads in " + dr.eps_M + ".",
        ])
      );
    }
    (function driversMore() {
      var ix = inputBy.r_keep.ix;
      var over = states.filter(function (s) {
        return D.sobol[s.a].R[ix][1] >= 0.01;
      }).length;
      set(
        "drv-more",
        "The share who keep coming barely registers for revenue (under 1% of the uncertainty in all but " + over + " states). An uninsured patient who keeps coming pays $" + F.int(M.val.self_rep) + " a year, against $" + F.int(M.val.pay_rep) + " for a Medicaid patient. Margin would differ, since that patient still costs care to deliver."
      );
    })();

    var tName = byA[M.typical].n;
    var tornadoRows = function () {
      return D.tornado[S.tout].rows
        .map(function (r) {
          return { k: r.k, n: inputBy[r.k].n, h: inputBy[r.k].h, lo: r.lo, hi: r.hi, sw: Math.abs(r.hi - r.lo) };
        })
        .sort(function (a, b) {
          return b.sw - a.sw;
        });
    };
    var tornadoChart = chart("chart-tornado", {
      label: "Chart",
      margin: function (w) {
        return { top: 44, right: w < LONG_LABELS ? 14 : 110, bottom: 30, left: w < LONG_LABELS ? 22 : 350 };
      },
      height: function (w) {
        return D.inputs.length * (w < LONG_LABELS ? 54 : 28) + 74;
      },
      render: function (c) {
        var G = rowGeom(c.w, 28, 54, LONG_LABELS),
          rows = tornadoRows(),
          T = D.tornado[S.tout],
          H = rows.length * G.ROW;
        var vals = [T.base];
        rows.forEach(function (r) {
          vals.push(r.lo, r.hi);
        });
        var x = d3.scaleLinear().domain([d3.min(vals) * 0.92, d3.max(vals) * 1.05]).nice().range([0, c.width]);
        c.svg.attr(
          "aria-label",
          "Chart of how " + OUT[S.tout] + " changes in " + tName + ", the typical state, when one input moves from its 10th to its 90th percentile. Middle estimate " + pv(T.base) + ". Largest swing: " + rows[0].n + ", from " + pv(rows[0].lo) + " to " + pv(rows[0].hi) + "."
        );
        xAxis(c, x, H, G.nar ? 4 : 6, function (d) {
          return F.pctValue(d, 0);
        });
        var bx = x(T.base);
        c.g.append("line").attr("class", "ex-ref-line").attr("x1", bx).attr("x2", bx).attr("y1", -3).attr("y2", H);
        c.g.append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", bx).attr("y", -28).attr("text-anchor", "middle").text("Middle estimate " + pv(T.base));
        var g = c.g
          .selectAll("g.ex-mark")
          .data(rows, function (d) {
            return d.k;
          })
          .join("g")
          .attr("class", "ex-mark ex-mark--static")
          .attr("transform", function (d, i) {
            return "translate(0," + i * G.ROW + ")";
          });
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", G.ROW);
        var mid = G.nar ? 30 : G.ROW / 2;
        g.append("line").attr("class", "p9-swing").attr("x1", function (d) {
          return x(d.lo);
        }).attr("x2", function (d) {
          return x(d.hi);
        }).attr("y1", mid).attr("y2", mid);
        g.append("circle").attr("class", "p9-dot-hollow").attr("r", 5).attr("cx", function (d) {
          return x(d.lo);
        }).attr("cy", mid);
        g.append("circle").attr("class", "p9-dot-ink").attr("r", 5).attr("cx", function (d) {
          return x(d.hi);
        }).attr("cy", mid);
        rowText(g, G, mid, function (d) {
          return d.n;
        });
        g.append("text").attr("class", "ex-svg-value").attr("text-anchor", G.nar ? "end" : "start").attr("x", function (d) {
          return G.nar ? c.width : x(Math.max(d.lo, d.hi)) + 10;
        }).attr("y", G.nar ? 48 : mid).attr("dy", G.nar ? 0 : "0.35em").text(function (d) {
          return d.sw < 0.0005 ? "no effect" : pv(d.lo) + " to " + pv(d.hi);
        });
        /* direct labels for the two dots, on the first row only */
        var shortLab = c.width < 300;
        Ex.directLabels(c.g, [{ y: -12, text: shortLab ? "10th" : "10th percentile", x: x(rows[0].lo) }], { anchor: "middle" });
        Ex.directLabels(c.g, [{ y: -12, text: shortLab ? "90th" : "90th percentile", x: x(rows[0].hi) }], { anchor: "middle" });
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.n,
            rows: [
              { name: "Input at 10th percentile", value: pv(d.lo) },
              { name: "Input at 90th percentile", value: pv(d.hi) },
              { name: "Middle estimate", value: pv(T.base), color: "ref" },
            ],
            note: d.h,
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
      },
    });
    var tornadoTable = liveTable("table-tornado", function () {
      return {
        caption: OUT[S.tout].charAt(0).toUpperCase() + OUT[S.tout].slice(1) + " in " + tName + ", the typical state, when one input moves and the rest sit at their middle values.",
        columns: [
          { key: "n", label: "Input" },
          { key: "lo", label: "Input at 10th percentile", format: pv },
          { key: "hi", label: "Input at 90th percentile", format: pv },
          { key: "h", label: "What it is", text: true },
        ],
        rows: tornadoRows(),
      };
    });
    function tornadoText() {
      var rows = tornadoRows(),
        T = D.tornado[S.tout],
        mid = S.tout === "L" ? byA[M.typical].t[1] * 100 : byA[M.typical].r[1];
      set("tornado-tag", "Typical state: " + tName + ". This chart does not change with your state. The hollow dot is the input at its 10th percentile, the filled dot at its 90th.");
      set("tornado-title", "In " + tName + ", " + lcFirst(rows[0].n) + " moves " + OUT[S.tout] + " from " + pv(Math.min(rows[0].lo, rows[0].hi)) + " to " + pv(Math.max(rows[0].lo, rows[0].hi)));
      set(
        "tornado-sub",
        "Each dot is the " + OUT[S.tout] + " when one input sits at its 10th or 90th percentile and the rest at their middle values. With every input at its middle the answer is " + pv(T.base) + ", " + (T.base < mid ? "a little under" : "a little over") + " the " + pv(mid) + " median of the draws, because the model is not linear."
      );
    }
    [].forEach.call(document.querySelectorAll("input[name=out]"), function (r) {
      r.addEventListener("change", function () {
        if (!r.checked) return;
        S.out = r.value;
        driversUpdate();
        Ex.live($("drv-h").textContent);
      });
    });
    [].forEach.call(document.querySelectorAll("input[name=tout]"), function (r) {
      r.addEventListener("change", function () {
        if (!r.checked) return;
        S.tout = r.value;
        tornadoText();
        tornadoChart.redraw();
        tornadoTable();
        Ex.live($("tornado-title").textContent);
      });
    });
    function driversUpdate() {
      sobolText();
      sobolChart.redraw();
      sobolTable();
    }

    /* ---------- Nebraska check (inside the methods) ---------- */
    var neRows = [
      { n: "Model, one year", v: M.ne.subj, kind: "est" },
      { n: "Model, halved to half a year", v: M.ne.half, kind: "est" },
      { n: "KFF, Nebraska, observed", v: [M.ne.obs, M.ne.obs, M.ne.obs], kind: "obs" },
    ];
    var inside = M.ne.obs >= M.ne.half[0] && M.ne.obs <= M.ne.half[2];
    set("ne-title", "Nebraska's " + F.pctValue(M.ne.obs, 0) + (inside ? " falls inside our half-year range (" + rng(M.ne.half[0], M.ne.half[2], pv) + ")" : " compared with our half-year range (" + rng(M.ne.half[0], M.ne.half[2], pv) + ")"));
    set(
      "ne-sub",
      "Share of people subject to the rule who lose coverage. KFF reported " + F.pctValue(M.ne.obs, 0) + " of renewing enrollees subject to the rule in Nebraska, over a few months (May to September 2026) and including ordinary attrition. Our figure covers a year of operation, so we also show it halved to a rough half-year equivalent. The two are not comparable, so " + F.pctValue(M.ne.obs, 0) + " is not evidence for or against the low end. The dots are medians and the lines run from the 5th to the 95th percentile."
    );
    chart("chart-ne", {
      label:
        "Chart comparing the model with KFF's Nebraska figure. KFF observed " + F.pctValue(M.ne.obs, 0) + " of renewing enrollees subject to the rule lost coverage. The model's half-year equivalent has a median of " + pv(M.ne.half[1]) + ", from " + rng(M.ne.half[0], M.ne.half[2], pv) + ".",
      margin: function (w) {
        return { top: 8, right: 54, bottom: 30, left: w < NARROW ? 22 : 196 };
      },
      height: function (w) {
        return 3 * (w < NARROW ? 44 : 36) + 38;
      },
      render: function (c) {
        var G = rowGeom(c.w, 36),
          H = 3 * G.ROW;
        var x = d3.scaleLinear().domain([0, 35]).range([0, c.width]);
        xAxis(c, x, H, c.narrow ? 4 : 7, function (d) {
          return F.pctValue(d, 0);
        });
        c.g.append("line").attr("class", "ex-baseline").attr("y1", 0).attr("y2", H);
        var g = c.g
          .selectAll("g.ex-mark")
          .data(neRows)
          .join("g")
          .attr("class", "ex-mark ex-mark--static")
          .attr("transform", function (d, i) {
            return "translate(0," + i * G.ROW + ")";
          });
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", G.ROW);
        var mid = G.nar ? 30 : G.ROW / 2;
        g.filter(function (d) {
          return d.kind === "est";
        }).append("path").attr("class", "ex-ci-whisker").attr("d", function (d) {
          return whisk(x(d.v[0]), x(d.v[2]), mid);
        });
        g.append("circle").attr("class", function (d) {
          return d.kind === "obs" ? "p9-dot-obs" : "p9-dot-est";
        }).attr("r", 6).attr("cx", function (d) {
          return x(d.v[1]);
        }).attr("cy", mid);
        rowText(g, G, mid, function (d) {
          return d.n;
        });
        g.append("text").attr("class", "ex-svg-value").attr("x", function (d) {
          return x(d.v[2]) + 10;
        }).attr("y", mid).attr("dy", "0.35em").text(function (d) {
          return pv(d.v[1]);
        });
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.n,
            rows: d.kind === "obs" ? [{ name: "Observed", value: pv(d.v[1]), color: "obs" }] : [{ name: "Median", value: pv(d.v[1]), color: "est" }, { name: "5th to 95th percentile", value: rng(d.v[0], d.v[2], pv) }],
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
      },
    });
    Ex.dataTable($("table-ne"), {
      caption: "Share of people subject to the rule who lose coverage, Nebraska.",
      columns: [
        { key: "n", label: "Figure" },
        { key: "lo", label: "5th percentile", format: pv },
        { key: "mid", label: "Median or observed", format: pv },
        { key: "hi", label: "95th percentile", format: pv },
      ],
      rows: neRows.map(function (r) {
        return { n: r.n, lo: r.kind === "obs" ? null : r.v[0], mid: r.v[1], hi: r.kind === "obs" ? null : r.v[2] };
      }),
    });

    /* ---------- slide download (canvas, 1600 x 900) ---------- */
    function wrap(ctx, text, x, y, maxW, lh) {
      var words = text.split(" "),
        line = "";
      words.forEach(function (w) {
        var t = line ? line + " " + w : w;
        if (ctx.measureText(t).width > maxW && line) {
          ctx.fillText(line, x, y);
          line = w;
          y += lh;
        } else line = t;
      });
      if (line) ctx.fillText(line, x, y);
      return y + lh;
    }
    function drawSlide() {
      var c = calc(),
        s = c.s,
        cv = document.createElement("canvas");
      cv.width = 1600;
      cv.height = 900;
      var x = cv.getContext("2d"),
        sans = '"IBM Plex Sans", system-ui, sans-serif',
        disp = '"Sansation Regular", "IBM Plex Sans", system-ui, sans-serif';
      x.fillStyle = "#ffffff";
      x.fillRect(0, 0, 1600, 900);
      x.fillStyle = "#191445";
      x.fillRect(0, 0, 1600, 150);
      x.fillStyle = "#b3a369";
      x.fillRect(0, 150, 1600, 6);
      x.fillStyle = "#ffffff";
      x.font = "400 52px " + disp;
      x.fillText(s.n + ": Medicaid coverage loss in 2027", 80, 78);
      x.font = "400 26px " + sans;
      x.fillStyle = "#e9e3c6";
      x.fillText(c.avg ? "An average " + s.n + " center, " + F.int(c.pts) + " Medicaid patients" : "Your center, " + F.int(c.pts) + " Medicaid patients (as you entered)", 80, 122);
      x.fillStyle = "#4a4a68";
      x.font = "600 28px " + sans;
      x.fillText("Net revenue lost per year", 80, 235);
      x.fillStyle = "#191445";
      x.font = "400 150px " + disp;
      x.fillText(money(c.usd[1]), 80, 380);
      x.font = "400 34px " + sans;
      x.fillStyle = "#35305e";
      x.fillText("5th to 95th percentile: " + rng(money(c.usd[0]), money(c.usd[2]), String), 80, 440);
      var cols = [
        ["Expansion adults in " + s.n + " who lose coverage", p1(s.t[1]), rng(s.t[0], s.t[2], p1)],
        ["Adults at " + (c.avg ? "an average center" : "your center") + " who lose coverage", count(c.lost[1]), rng(count(c.lost[0]), count(c.lost[2]), String)],
        [c.from === "rev" ? "Share of your total revenue" : "Share of revenue, typical center", c.from === "revbad" ? "n/a" : pvc(c.pct[1]), c.from === "revbad" ? "" : rng(c.pct[0], c.pct[2], pvc)],
      ];
      cols.forEach(function (col, i) {
        var cx = 80 + i * 500;
        x.fillStyle = "#f6f5fa";
        x.fillRect(cx, 500, 460, 210);
        x.fillStyle = "#b3a369";
        x.fillRect(cx, 500, 460, 5);
        x.fillStyle = "#35305e";
        x.font = "600 22px " + sans;
        wrap(x, col[0], cx + 24, 545, 410, 28);
        x.fillStyle = "#191445";
        x.font = "400 64px " + disp;
        x.fillText(col[1], cx + 24, 650);
        x.fillStyle = "#4a4a68";
        x.font = "400 22px " + sans;
        x.fillText(col[2], cx + 24, 690);
      });
      x.fillStyle = "#35305e";
      x.font = "400 24px " + sans;
      var pc = percentile(c);
      var line = p0(s.s) + " of the loss is administrative. #" + rankOf(S.abbr, "t") + " of " + NS + " states by coverage loss. " + (pc > 0 && pc < 100 ? "About the " + ordinal(pc) + " percentile among " + M.bench.n + " peer centers." : "");
      wrap(x, line, 80, 760, 1440, 30);
      x.fillStyle = "#4a4a68";
      x.font = "400 20px " + sans;
      x.fillText("Example on public data, not client work. Primordial Analytics model on CMS 2027 rule parameters, ACS 2024, CMS renewal data and HRSA UDS 2025. Not a forecast.", 80, 850);
      return cv;
    }
    $("btn-png").addEventListener("click", function () {
      var msg = $("p9-png-msg");
      var fonts = document.fonts && document.fonts.load ? Promise.all([document.fonts.load('600 24px "IBM Plex Sans"'), document.fonts.load('400 24px "IBM Plex Sans"'), document.fonts.load('400 24px "Sansation Regular"')]).catch(function () {}) : Promise.resolve();
      fonts.then(function () {
        var cv = drawSlide();
        cv.toBlob(function (blob) {
          if (!blob) {
            msg.textContent = "The slide could not be made in this browser. Use Copy summary instead.";
            return;
          }
          var a = document.createElement("a");
          a.href = URL.createObjectURL(blob);
          a.download = "medicaid-coverage-loss-" + S.abbr.toLowerCase() + ".png";
          document.body.appendChild(a);
          a.click();
          a.remove();
          setTimeout(function () {
            URL.revokeObjectURL(a.href);
          }, 2000);
          msg.textContent = "Slide saved.";
          Ex.live("Slide downloaded");
        }, "image/png");
      });
    });

    /* ---------- wire up ---------- */
    function updateAll() {
      autoPeer();
      renderTool();
      splitText();
      splitTable();
      statesText();
      statesChart.redraw();
      redrawPeers();
      peerText();
      sobolText();
      sobolChart.redraw();
      sobolTable();
    }
    statesText();
    autoPeer();
    renderTool();
    splitText();
    peerText();
    sobolText();
    tornadoText();
    statesTable();
    peersTable();
    histTable();
    splitTable();
    sobolTable();
    tornadoTable();
  }
});
