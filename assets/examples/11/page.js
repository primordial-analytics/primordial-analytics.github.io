/* Free clinic demand planner (example 11).
   The planner reproduces the formulas of the Excel download (analysis/11-free-clinic-surge-planner/workbook.py, "Planner" and
   "Need statement" sheets) over the county results in data.json (built by web_data.py). No number is typed in here.
   Plain ES2019, no modules. Uses d3, topojson and window.Ex. */
Ex.ready(function () {
  "use strict";
  var F = Ex.fmt;
  var $ = function (id) {
    return document.getElementById(id);
  };
  var CHARTS = ["chart-sessions", "chart-map", "chart-states", "chart-tornado"];

  Ex.loadData().then(init, function (err) {
    console.error(err);
    CHARTS.forEach(function (id) {
      Ex.showError($(id), "The data did not load. The Excel planner in the downloads gives the same answers.");
    });
  });

  function init(D) {
    var SCEN = ["Lower", "Central", "Higher"];
    var GLOSS = [
      "Fewer people lose coverage, and fewer of them end up uninsured.",
      "The middle of our assumptions.",
      "More people lose coverage, most of them end up uninsured, and Medicaid work requirements are at their strongest.",
    ];
    var LAYER = ["with the Medicaid layer", "marketplace losses only"];
    var CERT = [
      { p: 50, row: "Even odds (50%)", short: "50%", word: "even odds", fit: "5 of 10" },
      { p: 80, row: "80% sure", short: "80%", word: "80%", fit: "8 of 10" },
      { p: 95, row: "95% sure", short: "95%", word: "95%", fit: "19 of 20" },
    ];
    var FIELDS = [
      { k: "patients", min: 0, max: 1e7, name: "patients" },
      { k: "visits", min: 0, max: 1e7, name: "visits" },
      { k: "perSession", min: 1, max: 1000, name: "patients a session" },
      { k: "weeks", min: 1, max: 52, name: "weeks" },
      { k: "volPerSession", min: 0, max: 1000, name: "volunteers a session" },
      { k: "hoursPerShift", min: 0, max: 24, name: "hours a shift" },
      { k: "shiftsPerVol", min: 1, max: 365, name: "shifts a year" },
      { k: "medPerVisit", min: 0, max: 100000, name: "dollars per visit" },
    ];

    /* ---------- data access ---------- */
    var byFips = {};
    var stFips = {}; // state index -> 2-digit FIPS
    D.counties.forEach(function (c) {
      byFips[c[0]] = c;
      c.exp = D.states[c[2]].exp === 1;
      stFips[c[2]] = c[0].slice(0, 2);
    });
    var OUT = D.outside;
    var STINFO = {}; // postal code -> {st, name, covered}
    OUT.states.forEach(function (s) {
      STINFO[s[0]] = { st: s[0], name: s[1], covered: !!s[2] };
    });
    function label(c) {
      return c[1] + ", " + D.states[c[2]].st;
    }
    // G, C and A arrays hold only the marketplace half for counties in states that did not expand Medicaid
    function gi(c, sc, lay, q) {
      return c.exp ? (sc * 2 + lay) * 3 + q : sc * 3 + q;
    }
    function G(c, sc, lay, q) {
      return c[10][gi(c, sc, lay, q)] / 10000;
    }
    function C(c, sc, lay, q) {
      return c[11][gi(c, sc, lay, q)] / 10000;
    }
    function A(c, sc, lay, q) {
      return c[12][gi(c, sc, lay, q)];
    }

    /* Excel rounding: ROUNDUP away from zero (with a little float tolerance), ROUND and TEXT half away from zero */
    function ru(x) {
      var r = Math.round(x * 1e9) / 1e9;
      return r < 0 ? -Math.ceil(-r) : Math.ceil(r);
    }
    function hu(x) {
      return x < 0 ? -Math.round(-x) : Math.round(x);
    }
    function xInt(n) {
      var r = hu(n);
      return (r < 0 ? "-" : "") + Math.abs(r).toLocaleString("en-US");
    }
    function xUsd(n) {
      var r = hu(n);
      return (r < 0 ? "-$" : "$") + Math.abs(r).toLocaleString("en-US");
    }
    function xPct(x, d) {
      var m = Math.pow(10, d);
      var r = hu(x * 100 * m) / m;
      return (r < 0 ? "-" : "") + Math.abs(r).toFixed(d) + "%";
    }
    function minus(s) {
      return s.replace(/-(?=\d)/g, "−");
    }
    function moreThan(n) {
      return n >= 0 ? xInt(n) + " more than today" : xInt(-n) + " fewer than today";
    }

    /* ---------- state ---------- */
    var S = {
      fips: D.defaults.fips,
      unc: null, // a place outside the file the director picked: {st, name, county, covered}
      scen: 1,
      layers: 0,
      cert: 1,
      rho: D.defaults.rho,
      metric: "growth",
      sort: "paid",
      zoom: "",
      zoomLocked: false, // the director chose "All states" on purpose, so a county search does not zoom the map
      vals: {},
      errors: 0,
    };
    var cur = null; // the current plan, or null when the inputs are not usable
    var combo = null;
    var chMap = null;

    /* ---------- the planner ---------- */
    function column(v, visits, g, growth) {
      var sessions = ru(visits / v.perSession);
      var shifts = sessions * v.volPerSession;
      return {
        g: g,
        growth: growth,
        visits: visits,
        sessions: sessions,
        weekly: sessions / v.weeks,
        shifts: shifts,
        vol: ru(shifts / v.shiftsPerVol),
        hours: shifts * v.hoursPerShift,
        med: visits * v.medPerVisit,
        newPat: growth == null ? null : v.patients * growth,
      };
    }
    // columns: today, 50%, 80%, 95% (Planner sheet, section 4)
    function plan(c, sc, lay) {
      var v = S.vals;
      var cols = [column(v, v.visits, null, null)];
      for (var q = 0; q < 3; q++) {
        var growth = S.rho * C(c, sc, lay, q);
        cols.push(column(v, v.visits * (1 + growth), G(c, sc, lay, q), growth));
      }
      cols.forEach(function (k) {
        k.extra = k.sessions - cols[0].sessions;
      });
      return cols;
    }

    /* ---------- which places the file covers ---------- */
    function list(a) {
      return a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1];
    }
    var poolBy = d3.rollup(D.counties, function (v) { return d3.sum(v, function (c) { return c[3]; }); }, function (c) { return D.states[c[2]].st; });
    var bigIn = Array.from(poolBy).sort(function (a, b) { return b[1] - a[1]; }).slice(0, 5).map(function (r) { return r[0]; });
    var bigOut = ["CA", "NY", "IL", "PA", "GA"].filter(function (st) { return STINFO[st] && !STINFO[st].covered; });
    var coverText = "Covers the " + D.states.length + " HealthCare.gov states, including " + list(bigIn) + ". Not " + bigOut.map(function (st) { return STINFO[st].name; }).join(", ") + " or the other " + (OUT.states.filter(function (s) { return !s[2]; }).length - bigOut.length) + " places that are not on HealthCare.gov.";
    /* ---------- controls ---------- */
    function readFields() {
      S.errors = 0;
      FIELDS.forEach(function (f) {
        var input = $("f-" + f.k);
        var err = $("e-" + f.k);
        var raw = input.value.trim();
        var n = raw === "" ? NaN : Number(raw);
        var msg = "";
        if (raw === "" || isNaN(n) || input.validity.badInput) msg = "Enter a number.";
        else if (n < f.min || n > f.max) msg = "Enter a number from " + F.num(f.min) + " to " + F.num(f.max) + ".";
        S.vals[f.k] = msg ? null : n;
        if (msg) S.errors++;
        input.setAttribute("aria-invalid", msg ? "true" : "false");
        err.hidden = !msg;
        err.textContent = msg;
      });
    }
    function setFields() {
      FIELDS.forEach(function (f) {
        $("f-" + f.k).value = D.defaults[f.k];
      });
    }
    setFields();
    FIELDS.forEach(function (f) {
      $("f-" + f.k).addEventListener("input", updateTool);
    });

    var refreshRho = Ex.range($("f-rho"), {
      format: function (v) {
        return v.toFixed(2) + "x";
      },
      onInput: function (v) {
        S.rho = v;
        updateTool();
      },
    });
    $("f-rho").value = S.rho;
    refreshRho();
    var certInput = $("f-cert");
    Ex.range(certInput, {
      format: function (v) {
        return CERT[v].short;
      },
      onInput: function (v) {
        S.cert = v;
        updateTool();
      },
    });

    function setRadio(name, value) {
      [].forEach.call(document.querySelectorAll('input[name="' + name + '"]'), function (r) {
        r.checked = r.value === String(value);
      });
    }
    function onScen(v) {
      S.scen = +v;
      setRadio("scen", v);
      setRadio("scen2", v);
      refreshModelCharts();
      updateTool();
    }
    [].forEach.call(document.querySelectorAll('input[name="scen"], input[name="scen2"]'), function (r) {
      r.addEventListener("change", function () {
        onScen(r.value);
      });
    });
    [].forEach.call(document.querySelectorAll('input[name="layers"]'), function (r) {
      r.addEventListener("change", function () {
        S.layers = +r.value;
        refreshModelCharts();
        updateTool();
      });
    });
    [].forEach.call(document.querySelectorAll('input[name="metric"]'), function (r) {
      r.addEventListener("change", function () {
        S.metric = r.value;
        refreshModelCharts();
        updatePin();
      });
    });
    $("sort-states").addEventListener("change", function () {
      S.sort = this.value;
      chStates.redraw();
    });
    $("toggle-steps").addEventListener("click", function () {
      var open = $("plan-steps").hidden;
      $("plan-steps").hidden = !open;
      this.setAttribute("aria-expanded", String(open));
      this.textContent = open ? "Hide how we got there" : "Show how we got there";
    });
    $("toggle-cols").addEventListener("click", function () {
      var all = $("plan-table").getAttribute("data-view") === "pick";
      $("plan-table").setAttribute("data-view", all ? "all" : "pick");
      this.setAttribute("aria-pressed", String(all));
      this.textContent = all ? "Show only my certainty level" : "Show all certainty levels";
    });
    // the printout is the plan: open its two closed disclosures for the print, then put them back
    var printOpened = [];
    window.addEventListener("beforeprint", function () {
      [].forEach.call(document.querySelectorAll("details[data-p11-print]"), function (d) {
        if (!d.open && !d.hidden) {
          d.open = true;
          printOpened.push(d);
        }
      });
    });
    window.addEventListener("afterprint", function () {
      printOpened.splice(0).forEach(function (d) {
        d.open = false;
      });
    });
    $("print-plan").addEventListener("click", function () {
      window.print();
    });

    /* county search: the 2,054 counties in the file, then the places the file does not cover, so a search never ends in
       "check the spelling" for a county that is simply missing */
    var items = D.counties.map(function (c) {
      return { value: c[0], label: label(c), hint: D.states[c[2]].name, search: c[0] };
    });
    OUT.states.forEach(function (s) {
      if (!s[2]) items.push({ value: "u:" + s[0], label: s[1] + " (state not covered)", hint: "not in this file", search: s[0], unc: { st: s[0], name: s[1] } });
    });
    Object.keys(OUT.counties).forEach(function (st) {
      OUT.counties[st].forEach(function (n) {
        var cov = STINFO[st].covered;
        items.push({ value: "u:" + st + ":" + n, label: n + ", " + st, hint: cov ? "no data in this file" : STINFO[st].name + ": not covered", search: "", unc: { st: st, name: STINFO[st].name, county: n, covered: cov } });
      });
    });
    // shortest name first: "Cook" finds Cook before Cooke
    items.sort(function (a, b) {
      var ka = a.label.replace(/ County,/, ",").length, kb = b.label.replace(/ County,/, ",").length;
      return ka - kb || !!a.unc - !!b.unc || d3.ascending(a.label, b.label);
    });
    var itemBy = {};
    items.forEach(function (it) {
      itemBy[it.value] = it;
    });

    function selectCounty(it, from) {
      if (!it) {
        S.fips = null;
        S.unc = null;
      } else if (it.unc) {
        S.fips = null;
        S.unc = it.unc;
      } else {
        S.fips = it.value;
        S.unc = null;
      }
      if (from !== "main") combo.setValue(it ? it.value : null, { silent: true });
      if (it && !it.unc && from !== "map" && window.innerWidth < 640 && !S.zoomLocked) setZoom(byFips[it.value][2]);
      refreshModelCharts();
      updateTool();
      updatePin();
      if (from === "map" && it) announce("Planner set to " + it.label);
    }
    function makeCombo(host, id, lbl, from) {
      return Ex.combobox(host, {
        id: id,
        label: lbl,
                placeholder: "Search counties",
        noun: "places",
        items: items,
        value: S.fips,
        maxResults: 50,
        onSelect: function (it) {
          selectCounty(it, from);
        },
      });
    }
    combo = makeCombo($("pick-county"), "county", "County", "main");

    // four of the biggest counties in the file, one tap each
    (function () {
      var host = $("try-row");
      host.setAttribute("role", "group");
      host.setAttribute("aria-label", "Example counties");
      host.appendChild(Ex.el("span", { text: "Try" }));
      D.counties.slice().sort(function (a, b) { return b[3] - a[3]; }).slice(0, 4).forEach(function (c) {
        var b = Ex.el("button", { class: "ex-link", type: "button", "aria-label": label(c), text: c[1].replace(/ (County|Parish)$/, "") });
        b.addEventListener("click", function () {
          combo.setValue(c[0]);
        });
        host.appendChild(b);
      });
      setText("cover-note", coverText);
      var sl = $("states-list");
      sl.appendChild(Ex.el("p", { text: "Covered (" + D.states.length + "): " + D.states.map(function (s) { return s.name; }).join(", ") + "." }));
      var no = OUT.states.filter(function (s) { return !s[2]; });
      sl.appendChild(Ex.el("p", { text: "Not covered (" + no.length + "): " + no.map(function (s) { return s[1]; }).join(", ") + "." }));
    })();

    $("reset").addEventListener("click", function () {
      setFields();
      S.rho = D.defaults.rho;
      $("f-rho").value = S.rho;
      refreshRho();
      S.scen = 1;
      S.layers = 0;
      S.cert = 1;
      certInput.value = 1;
      certInput.dispatchEvent(new Event("input"));
      setRadio("scen", 1);
      setRadio("scen2", 1);
      setRadio("layers", 0);
      combo.setValue(D.defaults.fips);
      Ex.live("Reset to the example clinic");
    });

    /* ---------- results ---------- */
    function setText(id, t) {
      $(id).textContent = t;
    }
    var liveTimer = 0;
    function announce(t) {
      clearTimeout(liveTimer);
      liveTimer = setTimeout(function () {
        Ex.live(t);
      }, 700);
    }
    function moreFewer(n) {
      return n === 0 ? "Same as today" : (n > 0 ? F.int(n) + " more" : F.int(-n) + " fewer") + " than today";
    }
    var dockEls = null;
    function buildDock() {
      var d = Ex.el("div", { class: "p11-dock", "aria-hidden": "true" });
      ["sessions", "volunteers", "medication"].forEach(function (n) {
        d.appendChild(Ex.el("div", {}, [Ex.el("b", { id: "dock-" + n, text: "–" }), Ex.el("span", { text: n })]));
      });
      document.body.appendChild(d);
      dockEls = d;
      if ("IntersectionObserver" in window) {
        var seen = { c: false, r: false };
        var io = new IntersectionObserver(function (es) {
          es.forEach(function (e) {
            seen[e.target.id === "results" ? "r" : "c"] = e.isIntersecting;
          });
          d.classList.toggle("is-on", seen.c && !seen.r);
        });
        io.observe($("results"));
        io.observe(document.querySelector(".ex-tool__controls"));
      }
    }
    buildDock();

    function paragraph(text) {
      return Ex.el("p", { text: text });
    }
    function setCopy(sel, text) {
      [].forEach.call(document.querySelectorAll(sel), function (b) {
        b.setAttribute("data-ex-copy", text);
      });
    }
    function uncNote(note) {
      var u = S.unc;
      var st = STINFO[u.st];
      var where = u.county ? u.county + ", " + u.st : st.name;
      var head, body;
      if (!st.covered) {
        head = where + " is not in this file.";
        body = "The planner uses CMS county files for the " + D.states.length + " states whose marketplace runs on HealthCare.gov. " + st.name + " is not one of them, so we have no county numbers for it.";
      } else {
        head = where + " has no data in this file.";
        body = "The state is covered, but the Census and CMS files have no usable row for this county.";
      }
      var cta = document.querySelector('.ex-cta a[href*="#contact"]');
      var p = Ex.el("p", { class: "p11-note" }, [Ex.el("strong", { text: head }), " " + body + " Pick a county in a covered state to see how the planner works, or ", Ex.el("a", { href: cta ? cta.getAttribute("href") : "/#contact", text: "tell us your county" }), "."]);
      note(p);
    }

    function updateTool() {
      readFields();
      var c = S.fips ? byFips[S.fips] : null;
      var notes = $("tool-notes");
      notes.textContent = "";
      function note(t, cls) {
        notes.appendChild(typeof t === "string" ? Ex.el("p", { class: "p11-note" + (cls ? " " + cls : ""), text: t }) : t);
      }
      setText("gloss-scen", SCEN[S.scen] + ": " + GLOSS[S.scen]);
      $("layers-field").hidden = !!(c && !c.exp);
      var ok = !!c && !S.errors;
      $("tool-body").hidden = !ok;
      [].forEach.call(document.querySelectorAll("[data-needs-plan]"), function (n) {
        n.hidden = !ok;
      });
      if (S.unc) uncNote(note);
      else if (!c) note("Pick a county to see results.", "p11-note--error");
      if (S.errors) note("Fix the highlighted fields to see results. Zero is fine for patients and visits.", "p11-note--error");
      if (!ok) {
        cur = null;
        ["r1", "r2", "r3"].forEach(function (id) {
          setText(id, "–");
          setText(id + "-range", "");
          setText(id + "-note", "");
        });
        ["sessions", "volunteers", "medication"].forEach(function (n) {
          setText("dock-" + n, "–");
        });
        $("plan-main").textContent = "";
        $("plan-steps").textContent = "";
        setText("choose-line", "");
        setText("choose-text", "");
        setText("need-check", "");
        $("need-text").textContent = "";
        setCopy("[data-p11-need], #copy-line", "");
        announce(S.unc ? "No county numbers for this place" : S.errors ? "Fix the highlighted fields" : "Pick a county");
        return;
      }
      var plans = [0, 1, 2].map(function (sc) {
        return plan(c, sc, S.layers);
      });
      var cols = plans[S.scen];
      cur = { c: c, plans: plans, cols: cols };
      var k = cols[S.cert + 1];
      var t = cols[0];
      var cp = CERT[S.cert].p;
      var certWord = cp === 50 ? "even odds (50%)" : cp + "% certainty";
      setText("h-cert", CERT[S.cert].fit + " possible futures fit inside this plan, under our assumptions." + (cp === 50 ? " That is even odds, not a safe number for a request." : ""));

      var across = plans.map(function (p) { return p[S.cert + 1].sessions; });
      setText("r1-label", "Sessions a year at " + certWord);
      setText("r1", F.int(k.sessions));
      setText("r1-range", moreFewer(k.extra) + "; " + F.int(d3.min(across)) + " to " + F.int(d3.max(across)) + " across scenarios");
      setText("r1-note", "Sessions: " + F.int(t.sessions) + " today, " + F.num(k.weekly, 1) + " a week over " + F.num(S.vals.weeks) + " weeks. Other levels: " + CERT.filter(function (ce, q) { return q !== S.cert; }).map(function (ce) { return ce.word + " " + F.int(cols[CERT.indexOf(ce) + 1].sessions); }).join(", ") + ".");
      setText("r2-label", "Volunteers needed");
      setText("r2", F.int(k.vol));
      setText("r2-range", moreFewer(k.vol - t.vol));
      setText("r2-note", "Volunteers: " + F.int(t.vol) + " today, " + F.int(k.hours) + " volunteer hours a year, " + F.int(S.vals.volPerSession) + " on each session.");
      setText("r3-label", "Medication dollars");
      setText("r3", F.usd(k.med));
      var md = hu(k.med) - hu(t.med);
      setText("r3-range", md === 0 ? "Same as today" : F.usd(Math.abs(md)) + (md > 0 ? " more" : " fewer") + " than today");
      setText("r3-note", "Medication: " + F.usd(t.med) + " today, " + F.int(k.visits) + " visits a year at " + F.usd(S.vals.medPerVisit, { digits: 2 }) + " each.");
      setText("dock-sessions", F.int(k.sessions));
      setText("dock-volunteers", F.int(k.vol));
      setText("dock-medication", F.usd(k.med, { compact: true }));
      var line = "Plan " + xInt(k.sessions) + " sessions, " + xInt(k.vol) + " volunteers and " + xUsd(k.med) + " in medication for 2027 at " + certWord + " (" + SCEN[S.scen] + " scenario, " + label(c) + ").";
      setCopy("#copy-line", line);
      announce("Sessions " + F.int(k.sessions) + ", volunteers " + F.int(k.vol) + ", medication " + F.usd(k.med));

      // notes about this county
      var st = D.states[c[2]];
      if (cp === 50) note("Even odds (50%) is not a safe number for a request. Use 80% or 95%.");
      if (c[5] & 1) note("Under 500 uninsured low-income adults here in 2024. Growth rates this small are unstable: treat the result as a rough guide.");
      if (c[5] & 2) note("The Census margin of error here is more than 20% of the estimate.");
      if (c[3] === 0) note("Census estimates no uninsured low-income adults in this county, so the model has little to work with. Do not put the Need paragraph below in a request without your own count.", "p11-note--error");
      if (!st.exp) note(st.name + " did not expand Medicaid, so there is no Medicaid layer here.");
      if (cols[2].g < 0) note("Paid marketplace coverage rose here between 2025 and 2026, so the model shows the pool and your visits growing less, or shrinking.");

      renderPlanTable(cols);
      var diff = cols[3].sessions - cols[2].sessions;
      var hoursDiff = cols[3].hours - cols[2].hours;
      setText("choose-line", "Going from 80% to 95% adds " + diff + " sessions and " + xInt(hoursDiff) + " volunteer hours a year.");
      setText("choose-text", "At 80%, " + CERT[1].fit + " possible futures fit inside your plan. At 95%, " + CERT[2].fit + " do.");
      renderNeed(c, cols);
      renderSessionsTable(plans);
      chSess.redraw();
    }

    function renderPlanTable(cols) {
      var pctRow = function (x) { return xPct(x, 1); };
      var main = [
        ["Sessions a year", "sessions", xInt],
        ["Volunteers needed", "vol", xInt],
        ["Medication dollars", "med", xUsd],
        ["Extra sessions compared with today", "extra", xInt],
        ["Sessions a week", "weekly", function (x) { return (Math.round(x * 10) / 10).toFixed(1); }],
        ["Visits a year", "visits", xInt],
        ["Volunteer shifts a year", "shifts", xInt],
        ["Volunteer hours", "hours", xInt],
      ];
      var steps = [
        ["Growth in the county's uninsured pool since 2024", "g", pctRow],
        ["Growth in your visits (only the part not already in your last 12 months)", "growth", pctRow],
        ["New patients expected", "newPat", xInt],
      ];
      function fill(tb, rows) {
        rows.forEach(function (r) {
          var tr = Ex.el("tr");
          tr.appendChild(Ex.el("th", { scope: "row", text: r[0] }));
          cols.forEach(function (k, i) {
            var v = k[r[1]];
            var td = Ex.el("td", { text: v == null ? "–" : minus(r[2](v)), "data-q": String(i) });
            if (i === S.cert + 1) td.className = "is-pick";
            tr.appendChild(td);
          });
          tb.appendChild(tr);
        });
      }
      var tm = $("plan-main"), ts = $("plan-steps");
      tm.textContent = "";
      ts.textContent = "";
      fill(tm, main);
      ts.appendChild(Ex.el("tr", { class: "p11-grp" }, [Ex.el("th", { colspan: "5", scope: "colgroup", text: "How we got there" })]));
      fill(ts, steps);
      var heads = $("plan-table").tHead.rows[0].cells;
      for (var i = 0; i < heads.length; i++) heads[i].className = i === S.cert + 2 ? "is-pick" : "";
    }

    // The Need statement sheet, with three wording fixes the workbook has not got: the scenario is named, "median" replaces
    // "central" (the figure is the median of the scenario's draws), and a drop reads "fewer than today". Numbers match the workbook.
    function renderNeed(c, cols) {
      var host = $("need-text");
      host.textContent = "";
      var qa = function (q) {
        return A(c, S.scen, S.layers, q);
      };
      // A holds the 10th, 50th and 90th percentiles; gi() indexes them the same way as the 50th, 80th and 95th of G
      var v = S.vals;
      var scen = SCEN[S.scen].toLowerCase();
      var p1 =
        c[3] === 0
          ? "Need. In " + label(c) + ", the Census Small Area Health Insurance Estimates show no uninsured adults with incomes at or below 200% of the federal poverty level in 2024, so our county estimate is too small to state a rate. Replace this paragraph with our own count of uninsured patients and new arrivals."
          : "Need. In " + label(c) + ", about " + xInt(c[3]) + " adults with incomes at or below 200% of the federal poverty level were uninsured in 2024 (Census Small Area Health Insurance Estimates). " +
            "We estimate that between " + xInt(qa(0)) + " and " + xInt(qa(2)) + " more adults (an 80% interval: the 10th to 90th percentile of our " + scen + " scenario draws) " +
            "will be uninsured in 2027 than in 2024, counting losses of paid marketplace coverage from February 2025 on (median estimate " + xInt(qa(1)) + "), " +
            "a rise of " + xPct(cols[1].g, 0) + " at the median.";
      var p2 =
        "Our capacity. In the last 12 months our clinic provided " + xInt(v.visits) + " visits to " + xInt(v.patients) + " uninsured adults, in " + xInt(cols[0].sessions) + " sessions. " +
        "To meet 2027 demand with 80% probability we plan " + xInt(cols[2].sessions) + " sessions (" + moreThan(cols[2].extra) + "), " + xInt(cols[2].vol) + " volunteers and about " + xUsd(cols[2].med) + " in medication. " +
        "With 95% probability, " + xInt(cols[3].sessions) + " sessions, " + xInt(cols[3].vol) + " volunteers and " + xUsd(cols[3].med) + ".";
      var p3 =
        "Method and limits. The range comes from public data (CMS Open Enrollment files for 2025 and 2026, CMS effectuated enrollment, Census SAHIE 2024, Medicaid.gov enrollment) " +
        "and stated assumptions about how many people lose coverage and end up uninsured. It is a planning range, not a forecast, and it has not been checked against 2027 outcomes. " +
        "The interval and the session counts hold within the " + scen + " scenario; they do not include the spread between scenarios. " +
        "Plan selections are not paid coverage. We will replace the assumption about new arrivals with our own intake counts.";
      [p1, p2, p3].forEach(function (t) {
        host.appendChild(paragraph(t));
      });
      setCopy("[data-p11-need]", [p1, p2, p3].join("\n\n"));
      var share = v.patients / c[3];
      setText(
        "need-check",
        c[3] === 0
          ? "Check: the county has no estimated uninsured low-income adults, so your patients cannot be compared with it."
          : "Check: your patients are " + xPct(share, 1) + " of the county's uninsured low-income adults. " + (share > 0.25 ? "That is high; check that the county and patient counts match." : share < 0.01 ? "That is low; the planner assumes you draw new patients in proportion to your current share." : "That is a plausible share.")
      );
    }

    /* ---------- chart helpers ---------- */
    function whisker(x0, x1, m) {
      return "M" + x0 + "," + (m - 4) + "V" + (m + 4) + "M" + x0 + "," + m + "H" + x1 + "M" + x1 + "," + (m - 4) + "V" + (m + 4);
    }
    // the value is on the mark, so the axis is a hairline with a few labels and no gridlines
    function axisX(c, x, ticks, h, fmt) {
      c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + h + ")").call(d3.axisBottom(x).ticks(ticks).tickSize(0).tickPadding(8).tickFormat(fmt));
    }
    function noData(c, msg) {
      c.svg.attr("aria-label", msg);
      c.g.append("text").attr("class", "ex-svg-label").attr("x", 0).attr("y", 20).text(msg);
    }
    function median(a) {
      return d3.median(a);
    }
    var pct1 = function (v) {
      return F.pct(v, 1);
    };

    /* ---------- chart: sessions by certainty ---------- */
    var chSess = Ex.chart($("chart-sessions"), {
      label: "Chart of sessions to plan for.",
      margin: function (w) {
        return { top: 30, right: w < 520 ? 64 : 140, bottom: 30, left: w < 520 ? 42 : 112 };
      },
      height: function () {
        return 3 * 44 + 30 + 30;
      },
      render: function (c) {
        if (!cur) return noData(c, "Enter your county and numbers to see the chart.");
        var rows = CERT.map(function (ce, q) {
          var vals = cur.plans.map(function (p) {
            return p[q + 1].sessions;
          });
          return { q: q, name: c.narrow ? ce.short : ce.row, full: ce.row, bar: cur.cols[q + 1].sessions, lo: d3.min(vals), hi: d3.max(vals), vals: vals };
        });
        var today = cur.cols[0].sessions;
        var max = Math.max(today, d3.max(rows, function (r) { return r.hi; }), 1);
        var x = d3.scaleLinear().domain([0, max * 1.05]).nice().range([0, c.width]);
        var ROW = 44, h = 3 * ROW;
        axisX(c, x, c.narrow ? 4 : 5, h, function (d) { return F.int(d); });
        c.g.append("line").attr("class", "ex-ref-line").attr("x1", x(today)).attr("x2", x(today)).attr("y1", -6).attr("y2", h);
        Ex.directLabels(c.g, [{ y: -14, x: x(today), text: "Today " + F.int(today) }], { anchor: "middle" });
        var g = c.g.selectAll("g.ex-mark").data(rows).join("g").attr("class", "ex-mark").attr("transform", function (d) { return "translate(0," + (d.q * ROW + ROW / 2) + ")"; });
        var sel = function (d) { return d.q === S.cert ? " ex-sel" : ""; };
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", -ROW / 2).attr("width", c.w).attr("height", ROW);
        g.append("path").attr("class", "ex-ci-whisker").attr("d", function (d) { return whisker(x(d.lo), x(d.hi), 0); });
        g.append("circle").attr("class", function (d) { return "ex-dot ex-dot--est" + sel(d); }).attr("cx", function (d) { return x(d.bar); }).attr("cy", 0).attr("r", 6);
        g.append("text").attr("class", function (d) { return "ex-svg-label" + sel(d); }).attr("x", -10).attr("y", 0).attr("dy", "0.35em").attr("text-anchor", "end").text(function (d) { return d.name; });
        g.append("text").attr("class", function (d) { return "ex-svg-value" + sel(d); }).attr("x", function (d) { return x(d.hi) + 10; }).attr("y", 0).attr("dy", "0.35em")
          .text(function (d) { return d.q === S.cert && !c.narrow ? F.int(d.bar) + " (" + F.int(d.lo) + " to " + F.int(d.hi) + ")" : F.int(d.bar); });
        // the one label for the line: first row only
        g.filter(function (d) { return d.q === 0; }).append("text").attr("class", "ex-svg-label").attr("x", function (d) { return x(d.lo); }).attr("y", -13).text(c.narrow ? "Dot: " + SCEN[S.scen] + "; line: lower to higher" : "Dot: " + SCEN[S.scen] + " scenario. Line: lower to higher scenario");
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.full,
            rows: [
              { name: SCEN[S.scen] + " scenario (selected)", value: F.int(d.bar) + " sessions", color: "est" },
              { name: "Lower to higher scenario", value: F.int(d.lo) + " to " + F.int(d.hi) },
              { name: "Sessions today", value: F.int(today), color: "ref" },
            ],
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
        c.svg.attr("aria-label", "Chart of sessions a year to plan for at 50%, 80% and 95% certainty for " + label(cur.c) + ", " + SCEN[S.scen].toLowerCase() + " scenario " + LAYER[S.layers] + ": " + rows.map(function (r) { return F.int(r.bar) + " at " + CERT[r.q].short; }).join(", ") + ". Today: " + F.int(today) + ".");
        setText("t-sessions", "Sessions a year in " + label(cur.c));
      },
    });
    function renderSessionsTable(plans) {
      var host = $("table-sessions");
      host.textContent = "";
      var rows = CERT.map(function (ce, q) {
        return { cert: ce.row, lo: plans[0][q + 1].sessions, ce: plans[1][q + 1].sessions, hi: plans[2][q + 1].sessions, today: plans[0][0].sessions };
      });
      Ex.dataTable(host, {
        caption: "Sessions a year to plan for, by certainty and scenario, " + LAYER[S.layers] + ".",
        columns: [
          { key: "cert", label: "Certainty" },
          { key: "lo", label: "Lower scenario", format: F.int },
          { key: "ce", label: "Central scenario", format: F.int },
          { key: "hi", label: "Higher scenario", format: F.int },
          { key: "today", label: "Today", format: F.int },
        ],
        rows: rows,
      });
    }

    /* ---------- model-driven tables: the state ranking, the histogram and the national scenarios (the map carries the picture) ---------- */
    function stateMedians() {
      var by = d3.group(D.counties, function (c) { return c[2]; });
      return D.states.map(function (s, i) {
        var cs = by.get(i) || [];
        return { st: s.st, name: s.name, exp: s.exp, n: cs.length, med: median(cs.map(function (c) { return G(c, S.scen, S.layers, 0); })) };
      });
    }
    function myState() {
      return S.fips && byFips[S.fips] ? D.states[byFips[S.fips][2]].st : null;
    }

    var HB = d3.range(-10, 105, 5); // bin edges, 5 points wide; below -5 and 95 or more fall in the end bins
    function histCounts(lay) {
      var counts = HB.slice(0, -1).map(function () { return 0; });
      D.counties.forEach(function (c) {
        var v = G(c, S.scen, lay, 0) * 100;
        var i = Math.floor((v - HB[0]) / 5);
        counts[Math.max(0, Math.min(counts.length - 1, i))]++;
      });
      return counts;
    }
    function binLabel(lo, hi) {
      return lo === HB[0] ? minus("Below " + hi + "%") : hi === HB[HB.length - 1] ? lo + "% and above" : lo + "% to " + hi + "%";
    }
    function renderModelTables() {
      var all = stateMedians().sort(function (a, b) { return b.med - a.med; });
      var tbl = $("table-rank");
      tbl.textContent = "";
      Ex.dataTable(tbl, {
        caption: "Median county growth in the uninsured pool by state. " + SCEN[S.scen] + " scenario, " + LAYER[S.layers] + ".",
        columns: [
          { key: "name", label: "State" },
          { key: "med", label: "Median county growth", format: function (v) { return minus(pct1(v)); } },
          { key: "n", label: "Counties", format: F.int },
          { key: "expansion", label: "Medicaid expansion", text: true },
        ],
        rows: all.map(function (r) { return { name: r.name, med: r.med, n: r.n, expansion: r.exp ? "Yes" : "No" }; }),
      });
      var withM = histCounts(0), mkt = histCounts(1);
      var bins = withM.map(function (n, i) { return { lo: HB[i], hi: HB[i + 1], all: n, mkt: mkt[i] }; });
      var th = $("table-hist");
      th.textContent = "";
      Ex.dataTable(th, {
        caption: "Counties by growth in the uninsured pool, " + SCEN[S.scen].toLowerCase() + " scenario.",
        columns: [
          { key: "range", label: "Growth", text: true },
          { key: "all", label: "With the Medicaid layer", format: F.int },
          { key: "mkt", label: "Marketplace losses only", format: F.int },
        ],
        rows: bins.map(function (b) { return { range: binLabel(b.lo, b.hi), all: b.all, mkt: b.mkt }; }),
      });
    }
    (function () {
      var keys = ["lower", "central", "higher"];
      Ex.dataTable($("table-nat"), {
        caption: "Additional uninsured adults at or below 200% of poverty in 2027 compared with 2024, 2,054 counties (10th, 50th and 90th percentiles).",
        columns: [
          { key: "name", label: "Scenario" },
          { key: "mkt", label: "Marketplace only", text: true },
          { key: "mcd", label: "Medicaid layer only", text: true },
          { key: "tot", label: "Both layers", text: true },
        ],
        rows: keys.map(function (k, i) {
          var n = D.nat[k];
          var tri = function (p) { return F.int(n[p + "_p10"]) + " / " + F.int(n[p + "_p50"]) + " / " + F.int(n[p + "_p90"]); };
          return { name: SCEN[i], mkt: tri("marketplace"), mcd: tri("medicaid"), tot: tri("total") };
        }),
      });
    })();
    // the 80% range for all 30 states, for the scenario and layer on the map: "1.0 to 2.5 million"
    function renderNatNote() {
      var n = D.nat[["lower", "central", "higher"][S.scen]];
      var key = S.layers === 0 ? "total" : "marketplace";
      var lo = n[key + "_p10"], hi = n[key + "_p90"];
      var both = lo >= 1e6 && hi >= 1e6;
      var span = both ? (lo / 1e6).toFixed(1) + " to " + (hi / 1e6).toFixed(1) + " million" : F.approx(lo) + " to " + F.approx(hi);
      var host = $("nat-note");
      host.textContent = "";
      host.appendChild(Ex.el("strong", { text: "All 30 states." }));
      host.appendChild(document.createTextNode(" The 80% range is " + span + " more uninsured adults, " + SCEN[S.scen].toLowerCase() + " scenario."));
    }

    var lastMapKey = "";
    function mapKey() {
      return S.metric + S.scen + S.layers + S.zoom;
    }
    // the map has 3,142 shapes: redraw it only when its colors or zoom change, and just move the outline when the county does
    var lastTableKey = "";
    function refreshModelCharts() {
      if (S.scen + "/" + S.layers !== lastTableKey) {
        lastTableKey = S.scen + "/" + S.layers;
        renderModelTables();
        renderNatNote();
      }
      if (!chMap) return;
      if (mapKey() !== lastMapKey) chMap.redraw();
      else chMap.ring();
    }
    function setZoom(i) {
      S.zoom = i === "" || i == null ? "" : String(i);
      $("zoom-state").value = S.zoom;
    }
    D.states.forEach(function (s, i) {
      $("zoom-state").appendChild(Ex.el("option", { value: String(i), text: s.name }));
    });
    $("zoom-state").addEventListener("change", function () {
      S.zoom = this.value;
      S.zoomLocked = this.value === "";
      refreshModelCharts();
    });

    /* ---------- map ---------- */
    var mapFeats = [];
    var shapeCounties = {};
    var stOfFips = {}; // 2-digit FIPS -> postal code, from the map file's state names
    D.counties.forEach(function (c) {
      // Alaska: the map file still has Valdez-Cordova; the data has its two successors
      var sid = c[0] === "02063" || c[0] === "02066" ? "02261" : c[0];
      (shapeCounties[sid] = shapeCounties[sid] || []).push(c);
    });
    function mval(c) {
      if (S.metric === "growth") return G(c, S.scen, S.layers, 0) * 100;
      return A(c, S.scen, S.layers, 1);
    }
    function mflag(c) {
      return S.metric === "growth" ? c[5] & 1 : 0;
    }
    var METRIC = {
      growth: { fmt: function (v) { return F.pctValue(v, 0); }, unit: "Growth in the uninsured pool, 2027 vs 2024", hatch: "Under 500 adults in the pool: growth rate is unstable" },
      added: { fmt: function (v) { return F.compact(v, v < 1000 ? 0 : 1); }, unit: "Additional uninsured adults, 2027 vs 2024", hatch: "" },
    };
    function mapHeads(vals) {
      var exp = [], oth = [];
      D.counties.forEach(function (c) {
        (c.exp ? exp : oth).push(mval(c));
      });
      var t, def;
      if (S.metric === "growth") {
        t = "Median county growth: " + F.pctValue(median(exp), 1) + " in expansion states, " + F.pctValue(median(oth), 1) + " elsewhere";
        def = "Growth in the uninsured pool (adults 18 to 64 at or below 200% of poverty), 2027 compared with 2024, median of draws.";
      } else {
        var top = d3.greatest(D.counties, mval);
        t = "The median county adds " + F.int(median(vals)) + " uninsured adults; " + label(top) + " adds the most, " + F.approx(mval(top));
        def = "Additional uninsured adults at or below 200% of poverty in 2027 compared with 2024, median of draws.";
      }
      setText("t-map", t);
      setText("map-def", def + " " + SCEN[S.scen] + " scenario, " + LAYER[S.layers] + ".");
      return t;
    }
    function outsideTip(d) {
      var st = STINFO[stOfFips[d.id.slice(0, 2)]];
      return { title: d.properties.name + (st ? ", " + st.st : ""), rows: [], note: st && st.covered ? "No data in this file for this county" : "Not in this file: " + (st ? st.name : "this state") + " is not one of the " + D.states.length + " HealthCare.gov states" };
    }
    function tipFor(d) {
      var cs = shapeCounties[d.id];
      if (!cs) return outsideTip(d);
      if (cs.length > 1) {
        return {
          title: "Chugach and Copper River, Alaska",
          rows: cs.map(function (c) { return { name: c[1], value: S.metric === "added" ? F.int(mval(c)) : F.pctValue(mval(c), 1), color: "est" }; }),
          note: "The map shape covers two areas. Search for either one in the planner.",
        };
      }
      var c = cs[0];
      var rows = [
        { name: "Growth in the pool", value: F.pctValue(G(c, S.scen, S.layers, 0) * 100, 1), color: "est" },
        { name: "Adults added, median", value: F.int(A(c, S.scen, S.layers, 1)), color: "est" },
        { name: "Uninsured adults, 2024", value: F.int(c[3]) },
      ];
      var note = mflag(c) ? METRIC[S.metric].hatch : "";
      return { title: label(c), rows: rows, note: note };
    }
    // one line under the map: the county the planner is set to, and a way back to the answer
    function updatePin() {
      var c = S.fips ? byFips[S.fips] : null;
      var pin = $("map-pin");
      if (!c && !S.unc) {
        pin.hidden = true;
        return;
      }
      pin.hidden = false;
      var go = $("pin-go");
      if (S.unc) {
        var where = S.unc.county ? S.unc.county + ", " + S.unc.st : S.unc.name;
        setText("pin-title", where + ":");
        setText("pin-text", STINFO[S.unc.st].covered ? "No data in this file for this county." : S.unc.name + " is not one of the " + D.states.length + " HealthCare.gov states, so the file has no numbers for it.");
        go.textContent = "See the note in the planner";
        return;
      }
      setText("pin-title", label(c) + ":");
      setText("pin-text", "growth " + F.pctValue(G(c, S.scen, S.layers, 0) * 100, 1) + ", about " + F.approx(A(c, S.scen, S.layers, 1)) + " more uninsured adults.");
      go.textContent = "See the plan for this county";
    }
    $("pin-go").addEventListener("click", function (e) {
      e.preventDefault();
      $("tool").scrollIntoView({ behavior: Ex.reducedMotion() ? "auto" : "smooth" });
      setTimeout(function () {
        $("f-visits").focus({ preventScroll: true });
      }, Ex.reducedMotion() ? 0 : 450);
    });

    function drawMap(topo) {
      mapFeats = topojson.feature(topo, topo.objects.counties).features;
      var abbrByName = {};
      OUT.states.forEach(function (s) {
        abbrByName[s[1]] = s[0];
      });
      topo.objects.states.geometries.forEach(function (g) {
        stOfFips[g.id] = abbrByName[g.properties.name];
      });
      var mesh = topojson.mesh(topo, topo.objects.states, function (a, b) { return a !== b; });
      var path = d3.geoPath();
      var ring = null, halo = null, tag = null, lead = null;
      var view = null;
      var featById = {};
      mapFeats.forEach(function (f) { featById[f.id] = f; });
      function setRing() {
        if (!ring) return;
        var c = S.fips ? byFips[S.fips] : null;
        var sid = c ? (c[0] === "02063" || c[0] === "02066" ? "02261" : c[0]) : null;
        var d = sid && featById[sid] ? path(featById[sid]) : null;
        ring.attr("d", d).style("display", sid ? null : "none");
        halo.attr("d", d).style("display", sid ? null : "none");
        // the selected county is named on the map, so the map needs no key for the ring
        var m = d && c && view ? path.centroid(featById[sid]) : null;
        var show = !!m && m[0] > view.minX && m[0] < view.maxX && m[1] > view.minY && m[1] < view.maxY;
        tag.style("display", show ? null : "none");
        lead.style("display", show ? null : "none");
        if (show) {
          var k = view.k, name = c[1].replace(/ (County|Parish)$/, "");
          var up = m[1] - 22 / k > view.minY;
          var half = (name.length * 3.4 + 4) / k;
          var x = Math.max(view.minX + half, Math.min(view.maxX - half, m[0]));
          var y = up ? m[1] - 14 / k : m[1] + 22 / k;
          lead.attr("x1", m[0]).attr("x2", m[0]).attr("y1", m[1]).attr("y2", up ? y + 3 / k : y - 10 / k).attr("stroke-width", 1 / k);
          tag.attr("x", x).attr("y", y).style("font-size", 12 / k + "px").attr("stroke-width", 3 / k).text(name);
        }
        updatePin();
      }
      chMap = Ex.chart($("chart-map"), {
        label: "Map of US counties.",
        minHeight: 0,
        maxHeight: 4000,
        height: function (w) {
          return Math.round(S.zoom === "" ? (w * 610) / 975 : w < 520 ? w : w * 0.62);
        },
        margin: { top: 0, right: 0, bottom: 0, left: 0 },
        render: function (c) {
          var vals = D.counties.map(mval);
          var sorted = vals.slice().sort(d3.ascending);
          var hi = Math.max(d3.quantile(sorted, 0.95), 1e-6);
          var sqrt = S.metric === "added";
          var scale = Ex.scaleSeq(sqrt ? [0, Math.sqrt(hi)] : [0, hi]);
          var color = function (v) { return scale(sqrt ? Math.sqrt(Math.max(0, v)) : Math.max(0, v)); };
          var m = METRIC[S.metric];
          var rampHost = $("ramp-map");
          rampHost.textContent = "";
          Ex.ramp(rampHost, { title: m.unit + " (modeled" + (S.layers ? ", marketplace losses only" : "") + ")", domain: [0, hi], format: m.fmt });
          var ends = rampHost.querySelectorAll(".ex-ramp__ends span");
          if (ends.length) ends[ends.length - 1].textContent += " or more";
          var leg = $("legend-map");
          leg.textContent = "";
          function key(cls, text) {
            leg.appendChild(Ex.el("li", {}, [Ex.el("span", { class: cls, "aria-hidden": "true" }), text]));
          }
          if (m.hatch) key("ex-key ex-key--hatch", m.hatch);
          var k = c.width / 975, tx = 0, ty = 0;
          if (S.zoom !== "") {
            var fp = stFips[+S.zoom];
            var b = path.bounds({ type: "FeatureCollection", features: mapFeats.filter(function (f) { return f.id.slice(0, 2) === fp; }) });
            k = Math.min(c.width / (b[1][0] - b[0][0]), c.height / (b[1][1] - b[0][1])) * 0.92;
            tx = (c.width - k * (b[0][0] + b[1][0])) / 2;
            ty = (c.height - k * (b[0][1] + b[1][1])) / 2;
          }
          view = { k: k, minX: -tx / k, maxX: (c.width - tx) / k, minY: -ty / k, maxY: (c.height - ty) / k };
          c.svg.classed("is-zoomed", S.zoom !== "");
          var root = c.g.append("g").attr("transform", "translate(" + tx + "," + ty + ") scale(" + k + ")");
          root.append("g").selectAll("path").data(mapFeats).join("path")
            .attr("class", function (d) { var cs = shapeCounties[d.id]; return !cs ? "p11-nodata p11-pick" : cs.length > 1 ? "p11-shared" : "ex-county p11-pick"; })
            .attr("d", path)
            .attr("fill", function (d) { var cs = shapeCounties[d.id]; return cs && cs.length === 1 ? color(mval(cs[0])) : null; });
          root.append("g").selectAll("path").data(mapFeats.filter(function (d) { var cs = shapeCounties[d.id]; return cs && cs.length === 1 && mflag(cs[0]); })).join("path").attr("class", "ex-county--hidden").attr("d", path);
          root.append("path").attr("class", "ex-state-line").attr("d", path(mesh));
          halo = root.append("path").attr("class", "ex-county is-halo");
          ring = root.append("path").attr("class", "ex-county is-active").attr("fill", "none").style("pointer-events", "none");
          lead = root.append("line").attr("class", "p11-maplead");
          tag = root.append("text").attr("class", "p11-maptag").attr("text-anchor", "middle");
          lastMapKey = mapKey();
          setRing();
          var t = mapHeads(vals);
          c.svg.attr("aria-label", "Map of US counties shaded by " + m.unit.toLowerCase() + ". " + t + ". Use the county search in the planner to read any county.");
          c.svg.on("pointermove.tip", function (e) {
            var d = e.target.__data__;
            if (!d || !d.properties) { Ex.tooltip.hide(); return; }
            Ex.tooltip.show(tipFor(d), { x: e.clientX, y: e.clientY }, c.svg.node());
          }).on("pointerleave.tip", function () { Ex.tooltip.hide(); })
            .on("click.pick", function (e) {
              var d = e.target.__data__;
              if (!d || !d.properties) return;
              Ex.tooltip.show(tipFor(d), { x: e.clientX, y: e.clientY }, c.svg.node());
              var cs = shapeCounties[d.id];
              if (!cs) {
                var it = itemBy["u:" + stOfFips[d.id.slice(0, 2)] + ":" + d.properties.name];
                if (it) selectCounty(it, "map");
              } else if (cs.length === 1) selectCounty(itemBy[cs[0][0]], "map");
              else Ex.live("This shape covers two Alaska areas. Search for Chugach or Copper River in the planner.");
            });
          renderMapTable();
        },
      });
      chMap.ring = setRing;
    }
    function renderMapTable() {
      var host = $("table-map");
      host.textContent = "";
      Ex.dataTable(host, {
        caption: "Every county in the file. Growth and adults added are medians for the " + SCEN[S.scen].toLowerCase() + " scenario, " + LAYER[S.layers] + ".",
        label: "Scrollable table of 2,054 counties",
        columns: [
          { key: "name", label: "County", text: true },
          { key: "pool", label: "Uninsured adults, 2024", format: F.int },
          { key: "growth", label: "Growth in the pool", format: function (v) { return minus(F.pct(v, 1)); } },
          { key: "added", label: "Adults added", format: function (v) { return minus(F.int(v)); } },
          { key: "s25", label: "Selections 2025", format: F.int },
          { key: "s26", label: "Selections 2026", format: F.int },
          { key: "chg", label: "Adjusted change", format: function (v) { return minus(F.pctValue(v, 1)); } },
        ],
        rows: D.counties.map(function (c) {
          return { name: label(c), pool: c[3], growth: G(c, S.scen, S.layers, 0), added: A(c, S.scen, S.layers, 1), s25: c[6], s26: c[7], chg: c[9] };
        }),
      });
    }
    function loadMap() {
      Ex.loadData(Ex.assetUrl("us-counties-albers-10m.json")).then(drawMap, function () {
        Ex.showError($("chart-map"), "The map did not load. The county table below has the same numbers.");
      });
    }
    // the 800 KB map file loads when the map is about to scroll into view
    if ("IntersectionObserver" in window) {
      var mapIo = new IntersectionObserver(function (es) {
        if (es.some(function (e) { return e.isIntersecting; })) {
          mapIo.disconnect();
          loadMap();
        }
      }, { rootMargin: "900px 0px" });
      mapIo.observe($("fig-map"));
    } else loadMap();

    /* ---------- observed: states ---------- */
    var chStates = Ex.chart($("chart-states"), {
      label: "Dumbbell chart of the share of plan selections paid up, by state.",
      margin: function (w) {
        return { top: 8, right: w < 520 ? 52 : 90, bottom: 30, left: w < 520 ? 32 : 112 };
      },
      height: function () {
        return D.states.length * 20 + 38;
      },
      render: function (c) {
        var rows = D.states.map(function (s) {
          return { st: s.st, name: s.name, s25: s.s25, s26: s.s26, chg: (s.s26 / s.s25 - 1) * 100, r25: s.r25, r26: s.r26 };
        });
        if (S.sort === "paid") rows.sort(function (a, b) { return b.r26 - a.r26; });
        else if (S.sort === "drop") rows.sort(function (a, b) { return b.r25 - b.r26 - (a.r25 - a.r26); });
        else rows.sort(function (a, b) { return d3.ascending(a.name, b.name); });
        var ROW = 20, h = rows.length * ROW;
        var rmin = d3.min(rows, function (r) { return Math.min(r.r25, r.r26); });
        var x = d3.scaleLinear().domain([Math.floor(rmin / 10) * 10, 100]).range([0, c.width]);
        axisX(c, x, c.narrow ? 3 : 4, h, function (d) { return d + "%"; });
        var mine = S.fips && byFips[S.fips] ? D.states[byFips[S.fips][2]].st : null;
        var g = c.g.selectAll("g.ex-mark").data(rows).join("g").attr("class", "ex-mark").attr("transform", function (d, i) { return "translate(0," + (i * ROW + ROW / 2) + ")"; });
        var sel = function (d) { return d.st === mine ? " ex-sel" : ""; };
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", -ROW / 2).attr("width", c.w).attr("height", ROW);
        g.append("line").attr("class", "p11-lead").attr("x1", 0).attr("x2", function (d) { return x(Math.min(d.r25, d.r26)); }).attr("y1", 0).attr("y2", 0);
        g.append("text").attr("class", function (d) { return "ex-svg-label" + sel(d); }).attr("x", -10).attr("y", 0).attr("dy", "0.35em").attr("text-anchor", "end").text(function (d) { return c.narrow ? d.st : d.name; });
        g.append("line").attr("class", function (d) { return "ex-stem" + sel(d); }).attr("x1", function (d) { return x(d.r25); }).attr("x2", function (d) { return x(d.r26); }).attr("y1", 0).attr("y2", 0);
        g.append("circle").attr("class", function (d) { return "ex-dot p11-dot-open" + sel(d); }).attr("cx", function (d) { return x(d.r25); }).attr("cy", 0).attr("r", 4.5);
        g.append("circle").attr("class", function (d) { return "ex-dot ex-dot--obs" + sel(d); }).attr("cx", function (d) { return x(d.r26); }).attr("cy", 0).attr("r", 4.5);
        // the two dots are named once, on the first row; the chosen state also gets its two values
        var first = rows[0];
        var ends = [
          { d: first, k: "r25", name: "Feb 2025" },
          { d: first, k: "r26", name: "Feb 2026" },
        ];
        function endLabel(e, others) {
          var left = e.d[e.k] < e.d[others];
          return { x: x(e.d[e.k]) + (left ? -9 : 9), anchor: left ? "end" : "start", text: e.name };
        }
        var firstSel = first.st === mine;
        ends.forEach(function (e) {
          var o = e.k === "r25" ? "r26" : "r25";
          var l = endLabel(e, o);
          var t = l.text + (firstSel ? " " + e.d[e.k].toFixed(1) + "%" : "");
          g.filter(function (d) { return d === first; }).append("text").attr("class", "ex-svg-label ex-svg-label--direct").attr("x", l.x).attr("y", 0).attr("dy", "0.35em").attr("text-anchor", l.anchor).text(t);
        });
        if (!firstSel) {
          g.filter(function (d) { return d.st === mine; }).each(function (d) {
            var node = d3.select(this);
            [["r25", "r26"], ["r26", "r25"]].forEach(function (p) {
              var left = d[p[0]] < d[p[1]];
              node.append("text").attr("class", "ex-svg-value ex-sel").attr("x", x(d[p[0]]) + (left ? -9 : 9)).attr("y", 0).attr("dy", "0.35em").attr("text-anchor", left ? "end" : "start").text(d[p[0]].toFixed(1) + "%");
            });
          });
        }
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.name,
            rows: [
              { name: "Selections, 2025", value: F.int(d.s25), color: "obs" },
              { name: "Selections, 2026", value: F.int(d.s26), color: "obs" },
              { name: "Change", value: minus((d.chg > 0 ? "+" : "") + d.chg.toFixed(1) + "%"), color: "obs" },
              { name: "Paid share, Feb 2025", value: d.r25.toFixed(1) + "%" },
              { name: "Paid share, Feb 2026", value: d.r26.toFixed(1) + "%" },
            ],
            note: "Low-income selections (100 to 200% of poverty)",
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
        var fell = rows.filter(function (r) { return r.r26 < r.r25; }).length;
        var down = rows.filter(function (r) { return r.chg < 0; }).length;
        var low = d3.least(rows, function (r) { return r.r26; });
        var t = "Paid share fell in " + fell + " of " + rows.length + " states, and low-income selections fell in " + down;
        var mrow = mine ? rows.filter(function (r) { return r.st === mine; })[0] : null;
        var sl = $("state-line");
        sl.hidden = !mrow;
        sl.textContent = "";
        if (mrow) {
          sl.appendChild(Ex.el("strong", { text: mrow.name + "." }));
          sl.appendChild(document.createTextNode(" Low-income selections " + minus((mrow.chg > 0 ? "+" : "") + mrow.chg.toFixed(1) + "%") + ", paid share " + mrow.r26.toFixed(1) + "% (" + mrow.r25.toFixed(1) + "% in 2025)."));
        }
        setText("state-facts", t + ". " + low.name + " has the lowest paid share in February 2026, " + low.r26.toFixed(1) + "%.");
        c.svg.attr("aria-label", "Dumbbell chart for " + rows.length + " HealthCare.gov states: share of plan selections paid up in February 2025 and February 2026. " + t + ". " + low.name + " has the lowest paid share in February 2026, " + low.r26.toFixed(1) + "%. Full numbers are in the data table.");
        var tbl = $("table-states");
        tbl.textContent = "";
        Ex.dataTable(tbl, {
          caption: "Low-income plan selections and share paid up, by state, 2025 and 2026.",
          columns: [
            { key: "name", label: "State" },
            { key: "s25", label: "Selections 2025", format: F.int },
            { key: "s26", label: "Selections 2026", format: F.int },
            { key: "chg", label: "Change", format: function (v) { return minus((v > 0 ? "+" : "") + v.toFixed(1) + "%"); } },
            { key: "r25", label: "Paid share Feb 2025", format: function (v) { return v.toFixed(1) + "%"; } },
            { key: "r26", label: "Paid share Feb 2026", format: function (v) { return v.toFixed(1) + "%"; } },
          ],
          rows: rows,
        });
      },
    });

    /* top ten counties (static table from data) */
    (function () {
      var tb = $("top10-table").tBodies[0];
      D.top10.forEach(function (r) {
        var tr = Ex.el("tr");
        tr.appendChild(Ex.el("th", { scope: "row", text: r[0] + ", " + r[1] }));
        [F.int(r[2]), F.int(r[3]), minus(F.pctValue(r[4], 1)), minus(F.pctValue(r[5], 1))].forEach(function (t) {
          tr.appendChild(Ex.el("td", { text: t }));
        });
        tb.appendChild(tr);
      });
    })();

    /* ---------- drivers: what moves the 80% answer ---------- */
    var chTor = Ex.chart($("chart-tornado"), {
      label: "Dot plot of how far each assumption moves the sessions needed.",
      margin: function (w) {
        return { top: 28, right: 30, bottom: 44, left: w < 560 ? 0 : 270 };
      },
      height: function (w) {
        return D.tornado.rows.length * (w < 560 ? 48 : 34) + 28 + 44;
      },
      render: function (c) {
        var base = D.tornado.base;
        var rows = D.tornado.rows.map(function (r) {
          return { name: r[0].replace(/\s*\(.*$/, ""), range: (r[0].match(/\((.*)\)/) || ["", ""])[1].replace(/(\d)-(?=\d)/g, "$1 to ").replace(/x-(?=\d)/, "x to "), lo: r[1], hi: r[2] };
        });
        rows.forEach(function (r) { r.swing = Math.abs(r.hi - r.lo); });
        var all = [base];
        rows.forEach(function (r) { all.push(r.lo, r.hi); });
        var x = d3.scaleLinear().domain([Math.floor((d3.min(all) - 12) / 10) * 10, Math.ceil((d3.max(all) + 12) / 10) * 10]).range([0, c.width]);
        var ROW = c.w < 560 ? 48 : 34, above = c.w < 560;
        var h = rows.length * ROW;
        axisX(c, x, c.narrow ? 4 : 7, h, function (d) { return F.int(d); });
        c.g.append("line").attr("class", "ex-ref-line").attr("x1", x(base)).attr("x2", x(base)).attr("y1", -6).attr("y2", h);
        Ex.directLabels(c.g, [{ y: -14, x: x(base), text: "Central " + F.int(base) }], { anchor: "middle" });
        c.g.append("text").attr("class", "ex-svg-label").attr("x", c.width / 2).attr("y", h + 40).attr("text-anchor", "middle").text("Sessions a year at 80% certainty, example clinic");
        var big = function (d) { return d.swing >= 50 ? " ex-sel" : ""; };
        var g = c.g.selectAll("g.ex-mark").data(rows).join("g").attr("class", "ex-mark").attr("transform", function (d, i) { return "translate(0," + (i * ROW + ROW / 2 + (above ? 8 : 0)) + ")"; });
        g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", -ROW / 2 - (above ? 8 : 0)).attr("width", c.w).attr("height", ROW);
        g.append("line").attr("class", function (d) { return "ex-stem ex-stem--est" + big(d); }).attr("x1", function (d) { return x(d.lo); }).attr("x2", function (d) { return x(d.hi); }).attr("y1", 0).attr("y2", 0);
        ["lo", "hi"].forEach(function (k) {
          g.append("circle").attr("class", function (d) { return "ex-dot ex-dot--est" + big(d); }).attr("cx", function (d) { return x(d[k]); }).attr("cy", 0).attr("r", 5.5);
          g.append("text").attr("class", function (d) { return "ex-svg-value" + big(d); }).attr("y", 0).attr("dy", "0.35em")
            .attr("x", function (d) { return d[k] >= base ? x(d[k]) + 11 : x(d[k]) - 11; }).attr("text-anchor", function (d) { return d[k] >= base ? "start" : "end"; }).text(function (d) { return F.int(d[k]); });
        });
        if (above) g.append("text").attr("class", function (d) { return "ex-svg-label" + big(d); }).attr("x", 0).attr("y", -16).text(function (d) { return d.range ? d.name + " (" + d.range + ")" : d.name; });
        else {
          g.append("text").attr("class", function (d) { return "ex-svg-label" + big(d); }).attr("x", -14).attr("y", 0).attr("dy", "-0.15em").attr("text-anchor", "end").text(function (d) { return d.name; });
          g.append("text").attr("class", "ex-svg-label p11-sub").attr("x", -14).attr("y", 0).attr("dy", "1.15em").attr("text-anchor", "end").text(function (d) { return d.range; });
        }
        Ex.tooltip.attach(g, function (el) {
          var d = el.__data__;
          return {
            title: d.name,
            rows: [{ name: "At the low end (" + d.range.split(" to ")[0] + ")", value: F.int(d.lo) + " sessions", color: "est" }, { name: "At the high end", value: F.int(d.hi) + " sessions", color: "est" }],
            note: "Central case: " + F.int(base) + " sessions",
          };
        });
        Ex.roving(c.g.node(), ".ex-mark");
        var a = rows[0], b = rows[1];
        var lc = function (n) { return n.charAt(0).toLowerCase() + n.slice(1); };
        var t = a.name + " moves the 80% answer from " + F.int(a.lo) + " to " + F.int(a.hi) + " sessions; " + lc(b.name) + " from " + F.int(b.lo) + " to " + F.int(b.hi);
        c.svg.attr("aria-label", "Dot plot of sessions at 80% certainty for the example clinic when one assumption moves. Central case " + F.int(base) + ". " + t + ".");
        setText("t-tornado", "Two assumptions move the 80% answer by about " + F.int(Math.round(((a.swing + b.swing) / 2) / 10) * 10) + " sessions each");
        var tbl = $("table-tornado");
        tbl.textContent = "";
        Ex.dataTable(tbl, {
          caption: "Sessions a year at 80% certainty when one assumption moves from its low to its high end (central case: " + F.int(base) + ").",
          columns: [
            { key: "name", label: "Assumption", text: true },
            { key: "range", label: "Low to high", text: true },
            { key: "lo", label: "Sessions at the low end", format: F.int },
            { key: "hi", label: "Sessions at the high end", format: F.int },
          ],
          rows: rows,
        });
      },
    });

    refreshModelCharts();
    updateTool();
  }
});
