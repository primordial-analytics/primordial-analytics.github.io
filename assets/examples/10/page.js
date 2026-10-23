/* Example 10: overdose rates where counts are hidden. Every number drawn here comes from data.json,
   which analysis/10-hidden-overdose-counties/web_data.py builds from output/. Plain ES2019. */
Ex.ready(function () {
  "use strict";
  var F = Ex.fmt;
  var $ = function (id) {
    return document.getElementById(id);
  };
  var r1 = function (v) {
    return v == null ? "n/a" : F.num(v, 1);
  };
  var pc = function (frac) {
    return frac == null ? "n/a" : F.num(frac * 100, 0) + "%";
  };
  var plural = function (n, one, many) {
    return F.int(n) + " " + (n === 1 ? one : many);
  };
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var PAGE_HOSTS = ["chart-map", "chart-strip", "chart-total", "chart-class", "chart-above", "chart-agg", "chart-mae", "chart-cal"];
  var FAIL = "The charts did not load. The CSV in the downloads has every county.";
  // names the CDC file still uses, or that the Census renamed: search finds both
  var ALIASES = { "02158": "Kusilvak", "02261": "Chugach Copper River Census Area", "46102": "Oglala Lakota" };

  function failAll(msg) {
    PAGE_HOSTS.forEach(function (id) {
      if ($(id)) Ex.showError($(id), msg);
    });
    ["pick-state", "card"].forEach(function (id) {
      Ex.showError($(id), msg);
    });
  }
  if (typeof d3 === "undefined") return failAll(FAIL);
  Ex.loadData().then(init, function (err) {
    failAll("The data did not load. The CSV in the downloads has every county.");
    if (window.console) console.error(err);
  });

  function wrap(text, max) {
    var lines = [],
      cur = "";
    String(text)
      .split(" ")
      .forEach(function (w) {
        if (cur && (cur + " " + w).length > max) {
          lines.push(cur);
          cur = w;
        } else cur = cur ? cur + " " + w : w;
      });
    if (cur) lines.push(cur);
    return lines;
  }
  function cut(s, max) {
    return s.length > max ? s.slice(0, Math.max(1, max - 1)) + "…" : s;
  }
  function textLines(g, lines, x, y, lh, cls, anchor) {
    var t = g.append("text").attr("class", cls || null).attr("x", x).attr("y", y).attr("text-anchor", anchor || "start");
    lines.forEach(function (l, i) {
      t.append("tspan")
        .attr("x", x)
        .attr("dy", i ? lh : 0)
        .text(l);
    });
    return t;
  }
  // table shown in a <details>; built on first open and rebuilt on demand when the rows change
  function liveTable(host, spec) {
    var d = host.closest("details");
    function build() {
      Ex.dataTable(host, spec());
    }
    if (d)
      d.addEventListener("toggle", function () {
        if (d.open) build();
      });
    return function refresh() {
      if (!d || d.open) build();
    };
  }
  function csvCell(v) {
    var s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function init(D) {
    /* ---------- data ---------- */
    var N = D.numbers;
    var cols = D.counties;
    var S = D.states;
    var sByAbbr = {};
    S.forEach(function (s, i) {
      s.i = i;
      s.list = [];
      sByAbbr[s.a] = s;
    });
    var C = [];
    var byFips = {};
    for (var i = 0; i < cols.f.length; i++) {
      var s = S[cols.s[i]];
      var c = {
        i: i,
        fips: cols.f[i],
        name: cols.n[i],
        si: s.i,
        st: s.a,
        pop: cols.p[i],
        urc: cols.u[i],
        t: cols.t[i],
        deaths: cols.d[i],
        pub: cols.r[i],
        med: cols.m[i],
        lo: cols.l[i],
        hi: cols.h[i],
        pa: s.nc === 1 ? null : cols.a[i] / 1000, // a state with one county is its own reference
        pq: cols.q[i] / 1000,
        kl: cols.kl[i],
        kh: cols.kh[i],
        bl: cols.bl[i],
        bh: cols.bh[i],
      };
      C.push(c);
      byFips[c.fips] = c;
      s.list.push(c);
    }
    var NC = C.length;
    var isHidden = function (c) {
      return c.t >= 2;
    };
    var windowLabel = (function () {
      var p = D.window_ending.split("-");
      return MONTHS[+p[1] - 1] + " " + p[0];
    })();
    var nBlank = C.filter(isHidden).length;
    var nOneToNine = C.filter(function (c) {
      return c.t === 2;
    }).length;
    var nQuality = nBlank - nOneToNine;
    var aggByState = {};
    D.aggregate.forEach(function (a) {
      aggByState[a.state] = a;
    });
    var sel = { state: null, county: null, mode: "file", filter: "all", sort: "pa", more: false, cut: "30" };
    var touched = false; // the address bar changes only after the viewer picks something
    var INITIAL_ROWS = 30;
    var ROW = 24;
    var GAP = 24;
    var isNarrowPage = function () {
      return window.matchMedia("(max-width: 959px)").matches;
    };
    var ctaHref = (function () {
      var a = document.querySelector("#want-this a.ex-btn");
      return a ? a.getAttribute("href") : "/#contact";
    })();

    // numbers written in the prose come from numbers.json too
    [].forEach.call(document.querySelectorAll("[data-n]"), function (el) {
      var v = N[el.getAttribute("data-n")];
      if (v != null) el.textContent = F.num(v, +el.getAttribute("data-d") || 0);
    });

    /* ---------- start state, from the link only ---------- */
    (function () {
      var q = new URLSearchParams(location.search);
      var f = q.get("county");
      var a = (q.get("state") || "").toUpperCase();
      if (f && byFips[f]) {
        sel.county = byFips[f];
        sel.state = S[sel.county.si];
      } else if (a && sByAbbr[a]) sel.state = sByAbbr[a];
    })();

    /* ---------- controls ---------- */
    var stateItems = S.slice()
      .sort(function (a, b) {
        return a.n.localeCompare(b.n);
      })
      .map(function (s) {
        return { value: s.a, label: s.n, hint: s.a };
      });
    function countyItems(si) {
      return (si == null ? C : S[si].list).map(function (c) {
        var extra = ALIASES[c.fips] || "";
        if (c.st === "CT") extra = "planning region";
        return { value: c.fips, label: c.name + ", " + c.st, hint: si == null ? S[c.si].n : null, search: c.fips + " " + extra };
      });
    }
    var comboItemsFor = null;
    var stateCombo = Ex.combobox($("pick-state"), {
      id: "ov-state",
      label: "State",
      hint: "Zooms the map and lists the state's counties.",
      placeholder: "All states",
      noun: "in the list",
      items: stateItems,
      value: sel.state ? sel.state.a : null,
      onSelect: function (it) {
        setState(it ? sByAbbr[it.value] : null);
      },
    });
    var countyCombo = Ex.combobox($("pick-county"), {
      id: "ov-county",
      label: "County",
      hint: "Type a county name. FIPS codes work too.",
      placeholder: "Search 3,142 counties",
      noun: "in the list",
      items: countyItems(sel.state ? sel.state.i : null),
      value: sel.county ? sel.county.fips : null,
      maxResults: 50,
      onSelect: function (it) {
        if (it) selectCounty(byFips[it.value]);
        else {
          sel.county = null;
          touched = true;
          refresh();
        }
      },
    });
    comboItemsFor = sel.state ? sel.state.i : null;
    function syncControls() {
      stateCombo.setValue(sel.state ? sel.state.a : null, { silent: true });
      var si = sel.state ? sel.state.i : null;
      if (si !== comboItemsFor) {
        comboItemsFor = si;
        countyCombo.setItems(countyItems(si));
      }
      countyCombo.setValue(sel.county ? sel.county.fips : null, { silent: true });
    }
    function setState(s) {
      sel.state = s;
      if (sel.county && (!s || sel.county.si !== s.i)) sel.county = null;
      sel.more = false;
      touched = true;
      syncControls();
      refresh();
      Ex.live(s ? s.n + ": " + s.nh + " of " + plural(s.nc, "county", "counties") + " blank in the CDC file." : "Showing all states.");
    }
    function selectCounty(c, fromMap) {
      var hadFocus = $("chart-strip").contains(document.activeElement);
      sel.county = c;
      var newState = sel.state !== S[c.si];
      sel.state = S[c.si];
      if (newState) sel.more = false;
      touched = true;
      syncControls();
      refresh(!newState);
      if (hadFocus) {
        var m = $("chart-strip").querySelector(".ex-mark.is-sel");
        if (m) m.focus();
      }
      Ex.live(summary(c));
      if (fromMap && isNarrowPage()) {
        var r = cardHost.getBoundingClientRect();
        if (r.top > window.innerHeight * 0.7) window.scrollBy({ top: r.top - window.innerHeight * 0.45, behavior: Ex.reducedMotion() ? "auto" : "smooth" });
      }
    }
    function radios(name, fn) {
      [].forEach.call(document.querySelectorAll('input[name="' + name + '"]'), function (r) {
        r.addEventListener("change", function () {
          if (r.checked) fn(r.value);
        });
      });
    }
    function setRadio(name, value) {
      var r = document.querySelector('input[name="' + name + '"][value="' + value + '"]');
      if (r) r.checked = true;
    }
    setRadio("mapmode", sel.mode);
    radios("mapmode", function (v) {
      sel.mode = v;
      legendUpdate();
      paintMap(true);
      if (mapChart) mapChart.svg.attr("aria-label", mapLabel());
    });
    radios("stripfilter", function (v) {
      sel.filter = v;
      sel.more = false;
      redrawStrip();
    });
    $("stripsort").addEventListener("change", function () {
      sel.sort = this.value;
      redrawStrip();
    });

    /* ---------- wording for one county ---------- */
    function statusText(c) {
      if (c.t === 2) return "Blank in the CDC file: 1 to 9 deaths";
      if (c.t === 3) return "Blank in the CDC file: data quality";
      if (c.t === 1) return "Published: 0 deaths";
      return "Published: " + F.int(c.deaths) + " deaths";
    }
    function summary(c) {
      return c.name + ", " + c.st + ": estimated " + r1(c.med) + " deaths per 100,000, 90% interval " + r1(c.lo) + " to " + r1(c.hi) + ". " + statusText(c) + ".";
    }
    function stateRateText(s) {
      return s.n + " rate in the model: " + r1(s.r) + (s.sr != null ? " (rate from the CDC state total: " + r1(s.sr) + ")" : "") + ".";
    }
    function memo(c) {
      var s = S[c.si];
      var t = c.name + ", " + c.st + ": estimated " + r1(c.med) + " overdose deaths per 100,000 people per year (90% interval " + r1(c.lo) + " to " + r1(c.hi) + "), 12 months ending " + windowLabel + ". ";
      if (c.t === 2) t += "The CDC county file hides this county's count (1 to 9 deaths). ";
      else if (c.t === 3) t += "The CDC county file hides this county's count for data quality. ";
      else t += "The CDC file publishes " + F.int(c.deaths) + " deaths (" + r1(c.pub) + " per 100,000). ";
      if (c.pa != null) t += "Chance the rate is above " + s.n + "'s modeled rate (" + r1(s.r) + "): " + pc(c.pa) + ". ";
      t += "The interval is for the underlying rate and is probably too narrow. Source: CDC NCHS provisional counts and a Primordial Analytics model on public data (example, not client work), run " + D.run_date + ".";
      return t;
    }
    function tipFor(c) {
      var rows = [{ name: "Estimated rate", value: r1(c.med), color: "est" }, { name: "90% interval", value: r1(c.lo) + " to " + r1(c.hi) }];
      if (c.t <= 1) rows.push({ name: "Published rate", value: r1(c.pub) + " (" + F.int(c.deaths) + (c.deaths === 1 ? " death)" : " deaths)"), color: "obs" });
      else if (c.t === 2) rows.push({ name: "File allows", value: r1(c.bl) + " to " + r1(c.bh) });
      if (c.pa != null) rows.push({ name: "Above state rate", value: pc(c.pa) });
      rows.push({ name: "Rank range", value: F.int(c.kl) + " to " + F.int(c.kh) });
      return { title: c.name + ", " + c.st, rows: rows, note: isHidden(c) ? statusText(c) : null };
    }
    /* ---------- map ---------- */
    var topo = null;
    var mapChart = null;
    var mapSel = null;
    var feats = [];
    var mapData = [];
    var dStr = [];
    var meshD = "";
    var stateBox = {};
    var stateD = {};
    var INSET = { "02": 1, "15": 1 };
    var seqRate = Ex.scaleSeq([0, 45]);
    var seqProb = Ex.scaleSeq([0, 1]);
    var mapTag = $("map-tag");
    $("map-reset").addEventListener("click", function () {
      setState(null);
      stateCombo.focus();
    });

    function modeText() {
      if (sel.mode === "file")
        return {
          title: "The file is blank for " + F.int(nOneToNine) + " counties, plus " + nQuality + " for data quality",
          legend: "Blank in the CDC file",
          ramp: "Published rate per 100,000",
          cap: "Published rate per 100,000 people per year, 12 months ending " + windowLabel + ". Blank counties are hatched: " + F.int(nOneToNine) + " at 1 to 9 deaths and " + nQuality + " for data quality. Switch to estimates to fill them in.",
        };
      if (sel.mode === "above")
        return {
          title: "Darker counties are more likely above their state's rate",
          legend: "Blank in the CDC file: modeled",
          ramp: "Chance the rate is above the state's",
          cap: "Share of model draws in which the county's rate is above its state's. District of Columbia has no state to compare with and is gray.",
        };
      return {
        title: "The model fills in the " + F.int(nOneToNine) + " blank counties, plus " + nQuality + " more",
        legend: "Blank in the CDC file: modeled",
        ramp: "Estimated rate per 100,000",
        cap: "Modeled deaths per 100,000 people per year, 12 months ending " + windowLabel + ". Hatched counties are blank in the national file (" + F.int(nOneToNine) + " at 1 to 9 deaths, plus " + nQuality + " for data quality) and still get an estimate.",
      };
    }
    function fillFor(c) {
      if (sel.mode === "file") return c.t >= 2 ? "#ffffff" : seqRate(c.pub);
      if (sel.mode === "above") return c.pa == null ? "#d9d7e6" : seqProb(c.pa);
      return seqRate(c.med);
    }
    function legendUpdate() {
      var m = modeText();
      $("map-title").textContent = m.title;
      $("legend-hatch").textContent = m.legend;
      $("map-caption").textContent = m.cap;
      if (sel.mode === "above")
        Ex.ramp($("ramp-map"), {
          title: m.ramp,
          domain: [0, 1],
          format: function (v) {
            return pc(v);
          },
        });
      else
        Ex.ramp($("ramp-map"), {
          title: m.ramp,
          domain: [0, 45],
          format: function (v) {
            return v >= 45 ? "45 or more" : F.int(v);
          },
        });
    }
    function mapLabel() {
      var m = modeText();
      return "Map of US counties. " + m.title + ". " + (sel.state ? "Zoomed to " + sel.state.n + ". " : "") + (sel.county ? "Selected: " + summary(sel.county) + " " : "") + "Use the State and County boxes to read any county; the data table has all of them.";
    }
    function paintMap(animate) {
      if (!mapSel) return;
      var ms = animate && !Ex.reducedMotion() ? 260 : 0;
      var base = mapSel.base.interrupt();
      if (ms)
        base
          .transition()
          .duration(ms)
          .attr("fill", function (d) {
            return fillFor(d.c);
          });
      else
        base.attr("fill", function (d) {
          return fillFor(d.c);
        });
      mapSel.over.style("fill", sel.mode === "file" ? "url(#ov-hatch-file)" : "url(#ov-hatch-lines)");
    }
    function drawMap() {
      Ex.tooltip.hide();
      legendUpdate();
      mapTag.hidden = !sel.state;
      if (sel.state) $("map-tag-name").textContent = sel.state.n;
      if (mapChart) mapChart.redraw();
    }
    function buildMap() {
      var all = topojson.feature(topo, topo.objects.counties).features;
      feats = all.filter(function (f) {
        return byFips[f.id];
      });
      var gp = d3.geoPath();
      feats.forEach(function (f, j) {
        f.c = byFips[f.id];
        mapData.push({ c: f.c, j: j, st: f.id.slice(0, 2) });
      });
      dStr = feats.map(function (f) {
        return gp(f);
      });
      meshD = gp(
        topojson.mesh(topo, topo.objects.states, function (a, b) {
          return a !== b;
        })
      );
      topojson.feature(topo, topo.objects.states).features.forEach(function (f) {
        stateBox[f.id] = gp.bounds(f);
        stateD[f.id] = gp(f);
      });
      mapChart = Ex.chart($("chart-map"), {
        label: mapLabel(),
        maxHeight: 900,
        height: function (w) {
          if (w < 520) return Math.round(w * (sel.state ? 1 : 0.72));
          return Math.round(w * (sel.state ? 0.72 : 0.626));
        },
        margin: { top: 0, right: 0, bottom: 0, left: 0 },
        render: function (c) {
          c.svg.attr("aria-label", mapLabel());
          var s = c.w / 975;
          var Hu = c.h / s;
          var z = 1;
          var tx = 0;
          var ty = (Hu - 610) / 2;
          if (sel.state) {
            var b = stateBox[sel.state.f];
            var bw = b[1][0] - b[0][0];
            var bh = b[1][1] - b[0][1];
            z = Math.min(12, (975 * 0.88) / bw, (Hu * 0.88) / bh);
            tx = 975 / 2 - (z * (b[0][0] + b[1][0])) / 2;
            ty = Hu / 2 - (z * (b[0][1] + b[1][1])) / 2;
          }
          var k = s * z;
          var sp = sel.state ? 6 : 4;
          var defs = c.g.append("defs");
          [["ov-hatch-lines", "#191445", 0.7, 1.1], ["ov-hatch-file", "#6f6c93", 1, 1.3]].forEach(function (p) {
            var pt = defs.append("pattern").attr("id", p[0]).attr("width", sp / k).attr("height", sp / k).attr("patternUnits", "userSpaceOnUse").attr("patternTransform", "rotate(45)");
            pt.append("line").attr("x1", 0).attr("y1", 0).attr("x2", 0).attr("y2", sp / k).attr("stroke", p[1]).attr("stroke-opacity", p[2]).attr("stroke-width", p[3] / k);
          });
          var root = c.g.append("g").attr("transform", "scale(" + s + ") translate(" + tx + "," + ty + ") scale(" + z + ")");
          // zoomed to a lower-48 state: drop the Alaska and Hawaii insets; zoomed to one of them: show only it
          var shown = mapData.filter(function (d) {
            if (!sel.state) return true;
            return INSET[sel.state.f] ? d.st === sel.state.f : !INSET[d.st];
          });
          var fadeCls = function (d) {
            return sel.state && d.c.si !== sel.state.i ? " ov-fade" : "";
          };
          var base = root
            .append("g")
            .selectAll("path")
            .data(shown)
            .join("path")
            .attr("class", function (d) {
              return "ex-county ov-base" + fadeCls(d);
            })
            .attr("d", function (d) {
              return dStr[d.j];
            });
          var hid = shown.filter(function (d) {
            return isHidden(d.c);
          });
          var over = root
            .append("g")
            .selectAll("path")
            .data(hid)
            .join("path")
            .attr("class", function (d) {
              return "ex-county--hidden" + fadeCls(d);
            })
            .attr("d", function (d) {
              return dStr[d.j];
            });
          mapSel = { base: base, over: over };
          paintMap(false);
          root.append("path").attr("class", "ex-state-line").attr("d", meshD);
          if (sel.state) root.append("path").attr("class", "ov-statebox").attr("d", stateD[sel.state.f]);
          var hover = root.append("path").attr("class", "ov-hover");
          if (sel.county) {
            var j = feats.findIndex(function (f) {
              return f.c === sel.county;
            });
            if (j >= 0) root.append("path").attr("class", "ex-county is-active").attr("fill", "none").style("pointer-events", "none").attr("d", dStr[j]);
          }
          c.svg
            .on("pointermove.tip", function (e) {
              var d = e.target.__data__;
              if (e.pointerType !== "mouse" || !d || !d.c) {
                hover.attr("d", null);
                return Ex.tooltip.hide();
              }
              hover.attr("d", dStr[d.j]);
              Ex.tooltip.show(tipFor(d.c), { x: e.clientX, y: e.clientY }, c.svg.node());
            })
            .on("pointerleave.tip", function () {
              hover.attr("d", null);
              Ex.tooltip.hide();
            })
            .on("click.pick", function (e) {
              var d = e.target.__data__;
              if (d && d.c) selectCounty(d.c, true);
            });
        },
      });
    }
    Ex.loadData(Ex.assetUrl("us-counties-albers-10m.json")).then(
      function (t) {
        topo = t;
        buildMap();
      },
      function () {
        Ex.showError($("chart-map"), "The map shapes did not load. Use the State and County boxes; the data table has every county.");
      }
    );
    legendUpdate();

    liveTable($("table-map"), function () {
      return {
        caption: "Every county: the CDC file's count, the model's estimate with a 90% interval, and the chance the rate is above its state's. Rates per 100,000 per year.",
        label: "Scrollable table of all 3,142 counties",
        columns: [
          { key: "name", label: "County" },
          { key: "status", label: "In the CDC file", text: true },
          { key: "med", label: "Estimate", format: r1 },
          { key: "lo", label: "90% low", format: r1 },
          { key: "hi", label: "90% high", format: r1 },
          { key: "pa", label: "Chance above state rate", format: pc },
          { key: "rank", label: "Rank range", text: true },
          { key: "pop", label: "Population", format: F.int },
        ],
        rows: C.map(function (c) {
          return { name: c.name + ", " + c.st, status: statusText(c), med: c.med, lo: c.lo, hi: c.hi, pa: c.pa, rank: F.int(c.kl) + " to " + F.int(c.kh), pop: c.pop };
        }),
      };
    });

    /* ---------- county card ---------- */
    var cardHost = $("card");
    function fact(label, value, sub, meter) {
      var dd = Ex.el("dd", {}, [value]);
      if (sub) dd.appendChild(Ex.el("small", { text: sub }));
      var kids = [Ex.el("dt", { text: label }), dd];
      if (meter) kids.push(meter);
      return Ex.el("div", {}, kids);
    }
    function meter(from, to) {
      var i = Ex.el("i");
      i.style.left = (from * 100).toFixed(2) + "%";
      i.style.width = Math.max(0, (to - from) * 100).toFixed(2) + "%";
      return Ex.el("div", { class: "ov-meter", "aria-hidden": "true" }, [i]);
    }
    function copyButton(label, getText, done, onDone) {
      var b = Ex.el("button", { class: "ex-btn ex-btn--ghost ex-btn--sm", type: "button" }, [label]);
      b.addEventListener("click", function () {
        Ex.copy(getText()).then(function (ok) {
          b.textContent = ok ? done : "Copy failed";
          Ex.live(ok ? done : "Copy failed. Select the text by hand.");
          if (ok && onDone) onDone();
          setTimeout(function () {
            b.textContent = label;
          }, 1800);
        });
      });
      return b;
    }
    function topPicks(s) {
      return s.list
        .filter(function (c) {
          return c.t === 2 && c.pa != null;
        })
        .sort(function (a, b) {
          return b.pa - a.pa || b.pop - a.pop;
        })
        .slice(0, 3);
    }
    function verdict(c, s) {
      if (c.pa == null) return Ex.el("div", { class: "ov-verdict" }, [Ex.el("b", { text: s.n + " is one county, so it has no state rate to compare with." })]);
      var p = c.pa;
      var w = p >= 0.8 ? "Likely above" : p >= 0.5 ? "Leans above" : p > 0.2 ? "Leans below" : "Likely below";
      return Ex.el("div", { class: "ov-verdict" }, [
        Ex.el("b", { text: w + " " + s.n + "'s rate" }),
        Ex.el("span", { text: pc(p) + " chance it is above the model's state rate of " + r1(s.r) + ". 50% is a coin flip." }),
        meter(0, p),
      ]);
    }
    function renderCard() {
      cardHost.textContent = "";
      var box = Ex.el("div", { class: "ov-card__box" });
      var c = sel.county;
      var s = sel.state;
      if (!s) {
        box.appendChild(Ex.el("h3", { class: "ov-card__name", tabindex: "-1", text: "Pick a county" }));
        box.appendChild(Ex.el("p", { class: "ov-card__note", text: "Search above or click the map. You get the estimate, a 90% interval, the chance it is above the state's rate and a rank range." }));
        var nf = Ex.el("dl", { class: "ov-facts" });
        nf.appendChild(fact("Blank in the CDC file", F.int(nOneToNine), "plus " + nQuality + " for data quality, of " + F.int(NC)));
        nf.appendChild(fact("People living there", F.compact(N.suppressed_population, 1), F.num(N.suppressed_population_share_pct, 1) + "% of the population"));
        box.appendChild(nf);
        box.appendChild(Ex.el("p", { class: "ov-card__label", id: "start-label", text: "States with the most blank counties" }));
        var sl = Ex.el("ul", { class: "ov-picks", "aria-labelledby": "start-label" });
        S.slice()
          .sort(function (a, b) {
            return b.nh - a.nh;
          })
          .slice(0, 5)
          .forEach(function (st) {
            var b = Ex.el("button", { type: "button" }, [Ex.el("span", { text: st.n }), Ex.el("b", { text: F.int(st.nh) + " of " + F.int(st.nc) })]);
            b.addEventListener("click", function () {
              setState(st);
              var h = cardHost.querySelector("h3");
              if (h) h.focus();
            });
            sl.appendChild(Ex.el("li", {}, [b]));
          });
        box.appendChild(sl);
      } else if (!c) {
        var hid = s.list.filter(function (x) {
          return x.t === 2;
        });
        var above = hid.filter(function (x) {
          return x.pa != null && x.pa > 0.8;
        }).length;
        var hidPop = s.list.filter(isHidden).reduce(function (a, x) {
          return a + x.pop;
        }, 0);
        box.appendChild(Ex.el("h3", { class: "ov-card__name", tabindex: "-1", text: s.n }));
        box.appendChild(
          Ex.el("div", { class: "ov-card__big" }, [
            Ex.el("span", { class: "ov-card__label", text: "State rate in the model, per 100,000" }),
            Ex.el("span", { class: "ov-card__value", text: r1(s.r) }),
            Ex.el("span", { class: "ov-card__range", text: s.sr != null ? "From the CDC state total: " + r1(s.sr) : "No state total to compare with" }),
          ])
        );
        var facts = Ex.el("dl", { class: "ov-facts" });
        facts.appendChild(fact("Counties blank in the file", F.int(s.nh) + " of " + F.int(s.nc)));
        facts.appendChild(fact("People in blank counties", F.int(hidPop), pc(hidPop / s.p) + " of the state"));
        if (s.nc > 1) facts.appendChild(fact("Blank counties over 80% likely above the state rate", F.int(above)));
        var ag = aggByState[s.a];
        if (ag) {
          facts.appendChild(fact("State total minus published counties", F.int(ag.residual), "deaths the files put in blank counties"));
          facts.appendChild(fact("Model without the state totals", F.int(ag.model_median), "90% interval " + F.int(ag.model_lo90) + " to " + F.int(ag.model_hi90)));
        }
        box.appendChild(facts);
        var picks = topPicks(s);
        if (picks.length) {
          box.appendChild(Ex.el("p", { class: "ov-card__label", id: "picks-label", text: "Blank counties most likely above " + s.n + "'s rate" }));
          var ul = Ex.el("ul", { class: "ov-picks", "aria-labelledby": "picks-label" });
          picks.forEach(function (p) {
            var b = Ex.el("button", { type: "button" }, [Ex.el("span", { text: p.name }), Ex.el("b", { text: pc(p.pa) })]);
            b.addEventListener("click", function () {
              selectCounty(p);
              var h = cardHost.querySelector("h3");
              if (h) h.focus();
            });
            ul.appendChild(Ex.el("li", {}, [b]));
          });
          box.appendChild(ul);
        }
        box.appendChild(Ex.el("p", { class: "ov-card__note", text: (ag ? "The model total is a check run without the state totals, so it need not match the sum of the county estimates. " : "") + "Pick a county in the box above, on the map or in the list below." }));
      } else {
        box.appendChild(Ex.el("h3", { class: "ov-card__name", tabindex: "-1", text: c.name + ", " + c.st }));
        box.appendChild(Ex.el("p", { class: "ov-card__status" }, [Ex.el("span", { class: "ex-key " + (isHidden(c) ? "ex-key--hatch" : "ex-key--obs"), "aria-hidden": "true" }), statusText(c)]));
        var nudge = Ex.el("p", { class: "ov-nudge", hidden: true }, ["Want this for your whole state? ", Ex.el("a", { href: ctaHref }, ["Tell us what you need to decide."])]);
        var actions = Ex.el("div", { class: "ov-card__actions" });
        actions.appendChild(
          copyButton("Copy for a report", function () {
            return memo(c);
          }, "Copied", function () {
            nudge.hidden = false;
          })
        );
        actions.appendChild(
          copyButton("Copy link", function () {
            return location.origin + location.pathname + "?county=" + c.fips + "#tool";
          }, "Link copied")
        );
        box.appendChild(actions);
        box.appendChild(nudge);
        box.appendChild(verdict(c, s));
        box.appendChild(
          Ex.el("div", { class: "ov-card__big" }, [
            Ex.el("span", { class: "ov-card__label", text: "Estimated rate, deaths per 100,000 per year" }),
            Ex.el("span", { class: "ov-card__value", text: r1(c.med) }),
            Ex.el("span", { class: "ov-card__range", text: "90% interval " + r1(c.lo) + " to " + r1(c.hi) }),
          ])
        );
        box.appendChild(ruler(c));
        var f = Ex.el("dl", { class: "ov-facts" });
        if (c.t === 2) f.appendChild(fact("Count in the CDC file", "1 to 9 deaths", "= " + r1(c.bl) + " to " + r1(c.bh) + " per 100,000"));
        else if (c.t === 3) f.appendChild(fact("Count in the CDC file", "Hidden", "blank for data quality"));
        else f.appendChild(fact("Count in the CDC file", F.int(c.deaths) + (c.deaths === 1 ? " death" : " deaths"), r1(c.pub) + " per 100,000"));
        f.appendChild(fact("Chance in the top 10% of counties", pc(c.pq), "rate above " + r1(N.top_decile_cut_per_100k), meter(0, c.pq)));
        f.appendChild(fact("Rank, 1 is the highest rate", F.int(c.kl) + " to " + F.int(c.kh), "of " + F.int(NC) + ", 90% interval", meter(c.kl / NC, c.kh / NC)));
        f.appendChild(fact("Population", F.int(c.pop)));
        box.appendChild(f);
        var note = c.t === 2 || c.t === 3 ? "This estimate rests on county measures, neighbors and the state total, not on the county's own count. Do not rank on it." : c.t === 1 ? "Zero published deaths in a small county can still sit on a real rate. The interval shows how much room there is." : "A published count is observed. The model estimate shrinks it toward similar counties.";
        box.appendChild(Ex.el("p", { class: "ov-card__note", text: note + " " + stateRateText(s) }));
      }
      cardHost.appendChild(box);
    }

    function ruler(c) {
      var s = S[c.si];
      var W = 320;
      var xm = d3.max([c.hi, s.r, c.pub || 0]) * 1.1;
      var x = d3.scaleLinear().domain([0, xm]).nice().range([4, W - 14]);
      var xmax = x.domain()[1];
      var wrapEl = Ex.el("div", { class: "ex-chart ov-ruler" });
      var aria = "Rate per 100,000. Model estimate " + r1(c.med) + ", 90% interval " + r1(c.lo) + " to " + r1(c.hi) + ". " + (c.t === 2 ? "The file allows " + r1(c.bl) + " to " + r1(c.bh) + ". " : c.t <= 1 ? "Published rate " + r1(c.pub) + ". " : "") + s.n + " model rate " + r1(s.r) + ".";
      var svg = d3.select(wrapEl).append("svg").attr("viewBox", "0 0 " + W + " 126").attr("role", "img").attr("aria-label", aria);
      var g = svg.append("g");
      var AX = 106;
      g.append("g").attr("class", "ex-gridlines").call(d3.axisBottom(x).ticks(4).tickSize(-(AX - 20)).tickFormat("")).attr("transform", "translate(0," + AX + ")");
      g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + AX + ")").call(d3.axisBottom(x).ticks(4).tickSize(0).tickPadding(6).tickFormat(function (d) { return F.int(d); })).select(".domain").remove();
      // state reference first, so the captions sit on top of it
      var sx = x(s.r);
      g.append("line").attr("class", "ex-ref-line").attr("x1", sx).attr("x2", sx).attr("y1", 16).attr("y2", AX);
      g.append("text").attr("class", "ov-cap").attr("x", Math.min(Math.max(sx, 44), W - 44)).attr("y", 11).attr("text-anchor", "middle").text(s.a + " " + r1(s.r));
      var t1;
      if (c.t === 2) {
        var x1 = x(Math.min(c.bh, xmax));
        g.append("rect").attr("class", "ov-hard").attr("x", x(c.bl)).attr("y", 46).attr("width", Math.max(2, x1 - x(c.bl))).attr("height", 10);
        if (c.bh > xmax) g.append("path").attr("d", "M" + (x1 - 1) + ",44 l7,7 l-7,7 z").attr("fill", "#8a87a6");
        t1 = "File allows 1 to 9 deaths: " + r1(c.bl) + " to " + r1(c.bh) + (c.bh > xmax ? " (off the scale)" : "");
      } else if (c.t === 3) t1 = "File: blank, no bounds";
      else {
        g.append("circle").attr("class", "ov-pub").attr("cx", x(c.pub)).attr("cy", 51).attr("r", 6);
        t1 = "Published rate " + r1(c.pub);
      }
      g.append("text").attr("class", "ov-cap").attr("x", 4).attr("y", 38).text(t1);
      g.append("text").attr("class", "ov-cap").attr("x", 4).attr("y", 76).text("Model " + r1(c.med) + " (" + r1(c.lo) + " to " + r1(c.hi) + ")");
      g.append("rect").attr("class", "ov-ibar").attr("x", x(c.lo)).attr("y", 83).attr("width", Math.max(2, x(c.hi) - x(c.lo))).attr("height", 7).attr("rx", 3);
      g.append("line").attr("class", "ov-hairtick").attr("x1", x(c.med)).attr("x2", x(c.med)).attr("y1", 79).attr("y2", 94);
      return wrapEl;
    }

    /* ---------- state strip ---------- */
    var stripRows = [];
    var stripAll = [];
    var stripGapAt = -1; // index of the pinned selected row when it sits below the rows shown
    var stripSkipped = 0;
    var SORTS = {
      pa: ["chance above the state rate", function (a, b) {
        return (b.pa == null ? -1 : b.pa) - (a.pa == null ? -1 : a.pa) || b.med - a.med;
      }],
      med: ["estimated rate", function (a, b) {
        return b.med - a.med;
      }],
      pop: ["population", function (a, b) {
        return b.pop - a.pop;
      }],
      name: ["name", function (a, b) {
        return a.name.localeCompare(b.name);
      }],
    };
    var rowY = function (j) {
      return j * ROW + (stripGapAt >= 0 && j >= stripGapAt ? GAP : 0);
    };
    var stripChart = Ex.chart($("chart-strip"), {
      label: "Intervals for the counties of the selected state.",
      margin: function (w) {
        return { top: 28, right: w < 520 ? 46 : 112, bottom: 40, left: w < 520 ? 118 : 160 };
      },
      height: function () {
        return stripRows.length * ROW + (stripGapAt >= 0 ? GAP : 0) + 68;
      },
      render: function (c) {
        if (!stripRows.length) return;
        var s = sel.state;
        var H = stripRows.length * ROW + (stripGapAt >= 0 ? GAP : 0);
        var xmax = d3.max(stripAll, function (d) {
          return Math.max(d.hi, d.pub || 0);
        });
        var x = d3.scaleLinear().domain([0, Math.max(xmax, s.r) * 1.04]).nice().range([0, c.width]);
        var xdom = x.domain()[1];
        var ticks = c.narrow ? 4 : 6;
        c.g.append("g").attr("class", "ex-gridlines").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).ticks(ticks).tickSize(-H).tickFormat(""));
        c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).ticks(ticks).tickSize(0).tickPadding(8).tickFormat(function (d) { return F.int(d); })).select(".domain").remove();
        c.g.append("text").attr("class", "ov-cap").attr("x", c.width).attr("y", H + 34).attr("text-anchor", "end").text("Deaths per 100,000 people per year");
        c.g.append("line").attr("class", "ex-ref-line").attr("x1", x(s.r)).attr("x2", x(s.r)).attr("y1", -4).attr("y2", H);
        c.g.append("text").attr("class", "ex-svg-label").attr("x", x(s.r)).attr("y", -10).attr("text-anchor", "middle").text(s.n + " " + r1(s.r));
        var maxChars = Math.floor((c.margin.left - 26) / 6.4);
        var showPa = !c.narrow || sel.sort === "pa";
        var rows = c.g
          .selectAll("g.ex-mark")
          .data(stripRows)
          .join("g")
          .attr("class", function (d) { return "ex-mark" + (sel.county === d ? " is-sel" : ""); })
          .attr("transform", function (d, j) { return "translate(0," + rowY(j) + ")"; });
        if (!c.narrow) {
          c.g.append("text").attr("class", "ov-cap").attr("x", c.width + 10).attr("y", -10).text("Rate");
          c.g.append("text").attr("class", "ov-cap").attr("x", c.width + 58).attr("y", -10).text("Above");
        } else c.g.append("text").attr("class", "ov-cap").attr("x", c.width + 8).attr("y", -10).text(showPa ? "Above" : "Rate");
        rows.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", ROW);
        rows.append("rect").attr("class", "ov-selbg").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", ROW).attr("rx", 4);
        rows.filter(function (d) { return isHidden(d); }).append("rect").attr("class", "ex-county--hidden").style("stroke", "var(--ex-c-axis)").attr("x", -c.margin.left + 6).attr("y", ROW / 2 - 5).attr("width", 10).attr("height", 10).attr("rx", 2);
        rows.filter(function (d) { return d.t === 2; }).append("rect").attr("class", "ov-hard").attr("x", function (d) { return x(d.bl); }).attr("y", ROW / 2 - 6).attr("height", 12).attr("width", function (d) { return Math.max(2, x(Math.min(d.bh, xdom)) - x(d.bl)); });
        rows.filter(function (d) { return d.t === 2 && d.bh > xdom; }).append("path").attr("d", "M" + (c.width - 1) + "," + (ROW / 2 - 5) + " l6,5 l-6,5 z").attr("fill", "#8a87a6");
        rows.append("rect").attr("class", "ov-ibar").attr("x", function (d) { return x(d.lo); }).attr("y", ROW / 2 - 3).attr("height", 6).attr("rx", 3).attr("width", function (d) { return Math.max(3, x(d.hi) - x(d.lo)); });
        rows.append("line").attr("class", "ov-hairtick").attr("x1", function (d) { return x(d.med); }).attr("x2", function (d) { return x(d.med); }).attr("y1", ROW / 2 - 7).attr("y2", ROW / 2 + 7);
        rows.filter(function (d) { return d.t <= 1; }).append("circle").attr("class", "ov-pub").attr("cx", function (d) { return x(d.pub); }).attr("cy", ROW / 2).attr("r", 4.5);
        rows.append("text").attr("class", "ex-svg-label").attr("x", -c.margin.left + 22).attr("y", ROW / 2).attr("dy", "0.35em").style("stroke", "none").text(function (d) { return cut(d.name, maxChars); });
        if (!c.narrow) rows.append("text").attr("class", "ex-svg-value").attr("x", c.width + 10).attr("y", ROW / 2).attr("dy", "0.35em").text(function (d) { return r1(d.med); });
        rows.append("text").attr("class", "ex-svg-value").attr("x", c.narrow ? c.width + 8 : c.width + 58).attr("y", ROW / 2).attr("dy", "0.35em").text(function (d) { return c.narrow && !showPa ? r1(d.med) : pc(d.pa); });
        rows.append("rect").attr("class", "ex-selected-ring ov-ring").attr("x", -c.margin.left + 1).attr("y", 1).attr("width", c.w - 2).attr("height", ROW - 2).attr("rx", 4);
        if (stripGapAt >= 0) {
          var gy = stripGapAt * ROW + GAP / 2;
          c.g.append("line").attr("class", "ov-gap").attr("x1", -c.margin.left + 6).attr("x2", c.width).attr("y1", gy).attr("y2", gy);
          c.g.append("text").attr("class", "ov-cap").attr("x", -c.margin.left + 22).attr("y", gy - 4).text(plural(stripSkipped, "county", "counties") + " not shown");
        }
        Ex.tooltip.attach(rows, function (el) { return tipFor(el.__data__); });
        rows.each(function (d) {
          var el = this;
          el.setAttribute("role", "button");
          el.setAttribute("aria-label", el.getAttribute("aria-label") + ". Press Enter to open this county.");
          el.addEventListener("click", function () { selectCounty(d); });
          el.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              selectCounty(d);
            }
          });
        });
        Ex.roving(c.g.node(), ".ex-mark");
      },
    });
    stripChart.svg.attr("role", "group"); // its marks are buttons, so the svg cannot be an image
    var refreshStripTable = liveTable($("table-strip"), function () {
      return {
        caption: (sel.state ? sel.state.n : "") + ": every county, rates per 100,000 per year.",
        label: "Scrollable table of the counties of " + (sel.state ? sel.state.n : "the state"),
        columns: [
          { key: "name", label: "County" },
          { key: "status", label: "In the CDC file", text: true },
          { key: "pub", label: "Published rate", format: r1 },
          { key: "med", label: "Estimate", format: r1 },
          { key: "lo", label: "90% low", format: r1 },
          { key: "hi", label: "90% high", format: r1 },
          { key: "pa", label: "Chance above state rate", format: pc },
          { key: "rank", label: "Rank range", text: true },
          { key: "pop", label: "Population", format: F.int },
        ],
        rows: stripAll.map(function (c) { return Object.assign({}, c, { status: statusText(c), rank: F.int(c.kl) + " to " + F.int(c.kh) }); }),
      };
    });
    var moreBtn = $("strip-more");
    moreBtn.addEventListener("click", function () {
      sel.more = !sel.more;
      redrawStrip();
    });
    var STRIP_HEAD = ["County", "State", "In the CDC file", "Published rate per 100k", "Estimate per 100k", "90% low", "90% high", "Chance above state rate", "Chance in top decile", "Rank low", "Rank high", "Population"];
    function stripRowsOut() {
      return stripAll.map(function (c) {
        return [c.name, c.st, statusText(c), c.pub == null ? "" : c.pub, c.med, c.lo, c.hi, c.pa == null ? "" : c.pa, c.pq, c.kl, c.kh, c.pop];
      });
    }
    $("copy-table").addEventListener("click", function () {
      if (!sel.state) return;
      var lines = [STRIP_HEAD.join("\t")].concat(stripRowsOut().map(function (r) { return r.join("\t"); }));
      var b = $("copy-table");
      Ex.copy(lines.join("\n")).then(function (ok) {
        b.textContent = ok ? "Copied: paste into a sheet" : "Copy failed";
        Ex.live(ok ? "Table copied." : "Copy failed.");
        setTimeout(function () { b.textContent = "Copy table"; }, 2200);
      });
    });
    $("dl-table").addEventListener("click", function () {
      if (!sel.state) return;
      var lines = [STRIP_HEAD.map(csvCell).join(",")].concat(stripRowsOut().map(function (r) { return r.map(csvCell).join(","); }));
      var url = URL.createObjectURL(new Blob([lines.join("\n") + "\n"], { type: "text/csv" }));
      var a = Ex.el("a", { href: url, download: "overdose-rates-" + sel.state.a.toLowerCase() + ".csv" });
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      Ex.live("Downloaded the counties of " + sel.state.n + " as a CSV file.");
    });
    function passes(c) {
      return sel.filter === "all" ? true : sel.filter === "hidden" ? isHidden(c) : !isHidden(c);
    }
    function redrawStrip() {
      var s = sel.state;
      var has = !!s;
      ["strip-bar", "legend-strip", "strip-source", "strip-details"].forEach(function (id) {
        $(id).hidden = !has;
      });
      $("chart-strip").style.display = has ? "" : "none";
      stripGapAt = -1;
      if (!has) {
        $("strip-title").textContent = "Pick a state to see its counties side by side";
        $("strip-sub").textContent = "Each row is a county. The gold bar is the model's 90% interval for its rate.";
        stripRows = [];
        stripAll = [];
        return;
      }
      if (s.nh === 0 && sel.filter === "hidden") {
        sel.filter = "all";
        setRadio("stripfilter", "all");
      }
      document.querySelector('input[name="stripfilter"][value="hidden"]').disabled = s.nh === 0;
      stripAll = s.list.slice().sort(SORTS[sel.sort][1]);
      var vis = stripAll.filter(passes);
      var selIdx = sel.county ? vis.indexOf(sel.county) : -1;
      var chart = $("chart-strip");
      var old = chart.querySelector(".ov-empty");
      if (old) old.remove();
      stripRows = !sel.more && vis.length > INITIAL_ROWS ? vis.slice(0, INITIAL_ROWS) : vis;
      if (stripRows.length < vis.length && selIdx >= INITIAL_ROWS) {
        stripRows = stripRows.concat([sel.county]);
        stripGapAt = INITIAL_ROWS;
        stripSkipped = selIdx - INITIAL_ROWS;
      }
      var shownCount = stripGapAt >= 0 ? stripRows.length - 1 : stripRows.length;
      $("strip-title").textContent = s.nh ? s.n + ": " + F.int(s.nh) + " of " + plural(s.nc, "county", "counties") + (s.nh === 1 ? " is" : " are") + " blank in the CDC file" : s.n + ": none of its " + plural(s.nc, "county", "counties") + " is blank in the CDC file";
      $("strip-sub").textContent =
        "Sorted by " + SORTS[sel.sort][0] + ". The order is soft: read the gold bars, not the ranks. The estimated rate and the chance it is above the state's are on the right. " +
        (vis.length === 0 ? "No county to show." : shownCount < vis.length ? "Showing " + shownCount + " of " + vis.length + "." : "Showing " + plural(vis.length, "county", "counties") + ".");
      $("legend-state").textContent = s.n + " model rate, " + r1(s.r);
      moreBtn.hidden = vis.length <= INITIAL_ROWS;
      moreBtn.textContent = sel.more ? "Show the first " + INITIAL_ROWS + " only" : "Show all " + vis.length + " counties";
      stripChart.svg.attr("aria-label", "Intervals for " + vis.length + " counties of " + s.n + ", " + shownCount + " shown, sorted by " + SORTS[sel.sort][0] + ". " + s.nh + " are blank in the CDC file. The table below has every county.");
      stripChart.redraw();
      if (!stripRows.length) {
        chart.querySelector("svg").setAttribute("height", 0);
        chart.appendChild(Ex.el("p", { class: "ov-empty", text: sel.filter === "hidden" ? "None of " + s.n + "'s counties is blank in the CDC file." : "No county matches." }));
      }
      refreshStripTable();
    }
    function markStripSelection() {
      var marks = $("chart-strip").querySelectorAll(".ex-mark");
      [].forEach.call(marks, function (m) {
        m.classList.toggle("is-sel", m.__data__ === sel.county);
        if (m.__data__ === sel.county) m.setAttribute("aria-current", "true");
        else m.removeAttribute("aria-current");
      });
    }

    function writeUrl() {
      if (!touched) return;
      try {
        var q = sel.county ? "?county=" + sel.county.fips : sel.state ? "?state=" + sel.state.a : location.pathname;
        history.replaceState(null, "", q + location.hash);
      } catch (e) {}
    }
    function refresh(keepStrip) {
      drawMap();
      renderCard();
      if (keepStrip) {
        var pinned = stripGapAt >= 0 ? stripRows[stripGapAt] : null;
        var needRedraw = sel.county && ((stripRows.indexOf(sel.county) < 0 && passes(sel.county)) || (pinned && pinned !== sel.county));
        if (needRedraw) redrawStrip();
        else markStripSelection();
      } else redrawStrip();
      writeUrl();
    }
    refresh();

    /* ---------- example counties to try, chosen by rule from the data ---------- */
    (function () {
      var biggest = function (list) {
        return list.sort(function (a, b) {
          return b.pop - a.pop;
        })[0];
      };
      var picks = [
        [biggest(C.filter(function (c) { return c.t === 2 && c.pa != null && c.pa > 0.8; })), "Blank in the file"],
        [biggest(C.filter(function (c) { return c.t === 2 && c.pa != null && c.pa < 0.2; })), "Blank in the file"],
        [
          C.filter(function (c) { return c.t === 1 && c.pa != null; }).sort(function (a, b) { return b.pa - a.pa; })[0],
          "Published zero",
        ],
      ].filter(function (p) {
        return p[0];
      });
      var ul = $("try-list");
      picks.forEach(function (p) {
        var c = p[0];
        var b = Ex.el("button", { class: "ov-chip", type: "button" }, [c.name + ", " + c.st, Ex.el("small", { text: p[1] + ", chance above state " + pc(c.pa) })]);
        b.addEventListener("click", function () {
          selectCounty(c, true);
        });
        ul.appendChild(Ex.el("li", {}, [b]));
      });
      $("try").hidden = !picks.length;
    })();

    /* ---------- finding 1: how many deaths are hidden ---------- */
    (function () {
      var rows = [
        { name: "Model's own 90% interval", lo: N.hidden_total_deaths_lo90, hi: N.hidden_total_deaths_hi90, mid: N.hidden_total_deaths_median, how: "Assumes the model is right", ticks: false },
        { name: "Widened until 90% of checked states fall inside", lo: N.hidden_total_widened_lo90, hi: N.hidden_total_widened_hi90, mid: N.hidden_total_deaths_median, how: "Use this one", ticks: false, strong: true },
        { name: "Main model and four variants: lowest and highest total", lo: N.hidden_total_variant_min, hi: N.hidden_total_variant_max, mid: null, how: "Two totals, not an interval", ticks: true },
      ];
      var AX0 = Math.floor(Math.min(rows[0].lo, rows[1].lo, rows[2].lo) / 200) * 200 - 200;
      var AX1 = Math.ceil(Math.max(rows[0].hi, rows[1].hi, rows[2].hi) / 200) * 200 + 200;
      Ex.chart($("chart-total"), {
        label: "Range plot of deaths in hidden counties. The model's own 90% interval is " + F.int(rows[0].lo) + " to " + F.int(rows[0].hi) + ", the widened planning range is " + F.int(rows[1].lo) + " to " + F.int(rows[1].hi) + ", and the lowest and highest of five model totals are " + F.int(rows[2].lo) + " and " + F.int(rows[2].hi) + ". The median is " + F.int(N.hidden_total_deaths_median) + ". The axis starts at " + F.int(AX0) + ", not zero.",
        margin: function (w) { return { top: 8, right: w < 520 ? 16 : 24, bottom: 52, left: w < 520 ? 16 : 24 }; },
        height: function () { return rows.length * 58 + 60; },
        render: function (c) {
          var x = d3.scaleLinear().domain([AX0, AX1]).range([0, c.width]);
          var H = rows.length * 58;
          var tv = d3.range(AX0, AX1 + 1, 200);
          c.g.append("g").attr("class", "ex-gridlines").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).tickValues(tv).tickSize(-H).tickFormat(""));
          c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).tickValues(tv).tickSize(0).tickPadding(8).tickFormat(F.int)).select(".domain").remove();
          c.g.append("text").attr("class", "ov-cap").attr("x", 0).attr("y", H + 40).text("Axis starts at " + F.int(AX0) + ", not zero. Deaths in hidden counties.");
          var g = c.g.selectAll("g.ex-mark").data(rows).join("g").attr("class", "ex-mark").attr("transform", function (d, j) { return "translate(0," + j * 58 + ")"; });
          g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", 58);
          g.append("text").attr("class", "ex-svg-label").style("stroke", "none").style("font-weight", function (d) { return d.strong ? 700 : 500; }).attr("x", 0).attr("y", 14).text(function (d) { return d.name; });
          g.filter(function (d) { return !d.ticks; }).append("rect").attr("class", "ex-ci-band").attr("x", function (d) { return x(d.lo); }).attr("width", function (d) { return x(d.hi) - x(d.lo); }).attr("y", 24).attr("height", 18);
          g.filter(function (d) { return !d.ticks; }).append("path").attr("class", "ex-ci-whisker").style("stroke-width", function (d) { return d.strong ? 3 : null; }).attr("d", function (d) { return "M" + x(d.lo) + ",27V39M" + x(d.lo) + ",33H" + x(d.hi) + "M" + x(d.hi) + ",27V39"; });
          g.filter(function (d) { return d.ticks; }).append("path").attr("class", "ex-ci-whisker").attr("d", function (d) { return "M" + x(d.lo) + ",26V40M" + x(d.hi) + ",26V40"; });
          g.filter(function (d) { return d.mid != null; }).append("circle").attr("class", "ov-est-dot").attr("cx", function (d) { return x(d.mid); }).attr("cy", 33).attr("r", 5);
          g.append("text").attr("class", "ex-svg-value").attr("x", function (d) { return x(d.lo) - 6; }).attr("y", 33).attr("dy", "0.35em").attr("text-anchor", "end").text(function (d) { return F.int(d.lo); });
          g.append("text").attr("class", "ex-svg-value").attr("x", function (d) { return x(d.hi) + 6; }).attr("y", 33).attr("dy", "0.35em").text(function (d) { return F.int(d.hi); });
          Ex.tooltip.attach(g, function (el) {
            var d = el.__data__;
            var r = [{ name: d.ticks ? "Lowest and highest" : "Range", value: F.int(d.lo) + " to " + F.int(d.hi) }];
            if (d.mid != null) r.push({ name: "Median", value: F.int(d.mid), color: "est" });
            return { title: d.name, rows: r, note: d.how };
          });
          Ex.roving(c.g.node(), ".ex-mark");
        },
      });
      Ex.dataTable($("table-total"), {
        caption: "Deaths in hidden counties, three ranges.",
        columns: [
          { key: "name", label: "Range" },
          { key: "lo", label: "Low", format: F.int },
          { key: "hi", label: "High", format: F.int },
          { key: "mid", label: "Median", format: function (v) { return v == null ? "" : F.int(v); } },
          { key: "how", label: "Note", text: true },
        ],
        rows: rows,
      });
    })();

    /* ---------- finding 2: urban-rural classes ---------- */
    (function () {
      var rows = D.urban_rural;
      var withHidden = rows.filter(function (d) { return d.median_model_rate_suppressed != null; });
      var hExt = d3.extent(withHidden, function (d) { return d.median_model_rate_suppressed; });
      var pExt = d3.extent(withHidden, function (d) { return d.median_published_10_plus; });
      var allBelow = withHidden.every(function (d) { return d.median_model_rate_suppressed < d.median_published_10_plus; });
      var RH = 58;
      Ex.chart($("chart-class"), {
        label: "Dot plot of median rate per 100,000 by urban-rural class. " + (allBelow ? "In each class with hidden counties, the model median for hidden counties (" + r1(hExt[0]) + " to " + r1(hExt[1]) + ") is below the published median for counties with 10 or more deaths (" + r1(pExt[0]) + " to " + r1(pExt[1]) + ")." : "Hidden-county model medians run " + r1(hExt[0]) + " to " + r1(hExt[1]) + "; published medians for counties with 10 or more deaths run " + r1(pExt[0]) + " to " + r1(pExt[1]) + "."),
        margin: function (w) { return { top: 12, right: w < 520 ? 40 : 52, bottom: 36, left: w < 520 ? 96 : 176 }; },
        height: function () { return rows.length * RH + 52; },
        render: function (c) {
          var x = d3.scaleLinear().domain([0, 40]).range([0, c.width]);
          var H = rows.length * RH;
          c.g.append("g").attr("class", "ex-gridlines").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).ticks(4).tickSize(-H).tickFormat(""));
          c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).ticks(4).tickSize(0).tickPadding(8)).select(".domain").remove();
          c.g.append("text").attr("class", "ov-cap").attr("x", c.width).attr("y", H + 32).attr("text-anchor", "end").text("Median deaths per 100,000 people per year");
          var g = c.g.selectAll("g.ex-mark").data(rows).join("g").attr("class", "ex-mark").attr("transform", function (d, j) { return "translate(0," + j * RH + ")"; });
          g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", RH);
          g.each(function (d) {
            var n = d3.select(this);
            var lines = c.narrow ? wrap(d.label, 13) : [d.label];
            textLines(n, lines, -10, RH / 2 - (lines.length - 1) * 7 - (c.narrow ? 4 : 2), 14, "ex-svg-label", "end").style("stroke", "none").attr("dy", null);
            n.append("text").attr("class", "ov-cap").attr("x", -10).attr("y", RH / 2 + (lines.length - 1) * 7 + 14).attr("text-anchor", "end").text(c.narrow ? F.int(d.suppressed) + " hidden" : F.int(d.suppressed) + " of " + F.int(d.counties) + " hidden");
            var y = RH / 2;
            var hv = d.median_model_rate_suppressed;
            if (hv != null) n.append("line").attr("x1", x(hv)).attr("x2", x(d.median_published_10_plus)).attr("y1", y).attr("y2", y).attr("stroke", "var(--ex-c-axis)").attr("stroke-width", 2);
            n.append("circle").attr("class", "ov-pub").attr("cx", x(d.median_published_10_plus)).attr("cy", y).attr("r", 6);
            if (hv != null) n.append("circle").attr("class", "ov-est-dot").attr("cx", x(hv)).attr("cy", y).attr("r", 6);
            n.append("text").attr("class", "ex-svg-value").attr("x", x(d.median_published_10_plus) + 11).attr("y", y).attr("dy", "0.35em").text(r1(d.median_published_10_plus));
            if (hv != null) n.append("text").attr("class", "ex-svg-value").attr("x", x(hv) - 11).attr("y", y).attr("dy", "0.35em").attr("text-anchor", "end").text(r1(hv));
            else n.append("text").attr("class", "ov-cap").attr("x", x(d.median_published_10_plus) - 12).attr("y", y).attr("dy", "0.35em").attr("text-anchor", "end").text(c.narrow ? "none hidden" : "no hidden counties");
          });
          Ex.tooltip.attach(g, function (el) {
            var d = el.__data__;
            var r = [];
            if (d.median_model_rate_suppressed != null) r.push({ name: "Hidden, model median", value: r1(d.median_model_rate_suppressed), color: "est" });
            r.push({ name: "Published, 10 or more", value: r1(d.median_published_10_plus), color: "obs" });
            r.push({ name: "Published, incl. zeros", value: r1(d.median_published_incl_zeros) });
            return { title: d.label, rows: r, note: F.int(d.suppressed) + " of " + F.int(d.counties) + " counties hidden; " + F.int(d.published_zero) + " of " + F.int(d.published) + " published are zero" };
          });
          Ex.roving(c.g.node(), ".ex-mark");
        },
      });
      Ex.dataTable($("table-class"), {
        caption: "Counties by NCHS urban-rural class, with suppression and median rates per 100,000.",
        columns: [
          { key: "label", label: "Urban-rural class" },
          { key: "counties", label: "Counties", format: F.int },
          { key: "suppressed", label: "Hidden (1 to 9)", format: F.int },
          { key: "share_suppressed_pct", label: "Share hidden", format: function (v) { return v + "%"; } },
          { key: "median_model_rate_suppressed", label: "Median model rate, hidden", format: r1 },
          { key: "median_published_incl_zeros", label: "Median published rate, incl. zeros", format: r1 },
          { key: "median_published_10_plus", label: "Median published rate, 10+ deaths", format: r1 },
          { key: "published_zero", label: "Published zeros", format: F.int },
        ],
        rows: rows,
      });
    })();

    /* ---------- finding 3: chance above the state rate ---------- */
    (function () {
      var BINS = [
        { name: "Under 20%", test: function (p) { return p < 0.2; }, fill: Ex.seq[1], ink: "#191445" },
        { name: "20% to 50%", test: function (p) { return p >= 0.2 && p <= 0.5; }, fill: Ex.seq[3], ink: "#191445" },
        { name: "50% to 80%", test: function (p) { return p > 0.5 && p <= 0.8; }, fill: Ex.seq[5], ink: "#fff" },
        { name: "Over 80%", test: function (p) { return p > 0.8; }, fill: Ex.seq[6], ink: "#fff" },
      ];
      var groups = [
        { name: "Hidden, 1 to 9 deaths", pick: function (c) { return c.t === 2; } },
        { name: "Published zero", pick: function (c) { return c.t === 1; } },
        { name: "Published, 10 or more", pick: function (c) { return c.t === 0; } },
      ].map(function (g) {
        var list = C.filter(function (c) { return g.pick(c) && c.pa != null; });
        g.total = list.length;
        g.bins = BINS.map(function (b) {
          return { bin: b, n: list.filter(function (c) { return b.test(c.pa); }).length };
        });
        return g;
      });
      var lg = $("legend-above");
      BINS.forEach(function (b) {
        var sw = Ex.el("span", { class: "ov-key ov-key--swatch", "aria-hidden": "true" });
        sw.style.background = b.fill;
        lg.appendChild(Ex.el("li", {}, [sw, b.name]));
      });
      var RH = 66;
      Ex.chart($("chart-above"), {
        label: "Stacked bars of counties by the chance their rate is above their state's. " + groups.map(function (g) { return g.name + ": " + g.bins.map(function (b) { return F.int(b.n) + " " + b.bin.name.toLowerCase(); }).join(", "); }).join(". ") + ".",
        margin: function (w) { return { top: 6, right: 12, bottom: 34, left: w < 520 ? 96 : 176 }; },
        height: function () { return groups.length * RH + 40; },
        render: function (c) {
          var x = d3.scaleLinear().domain([0, 1]).range([0, c.width]);
          var H = groups.length * RH;
          c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).ticks(c.narrow ? 4 : 5).tickSize(0).tickPadding(8).tickFormat(function (d) { return pc(d); })).select(".domain").remove();
          c.g.append("text").attr("class", "ov-cap").attr("x", c.width).attr("y", H + 30).attr("text-anchor", "end").text("Share of the group's counties");
          var rows = c.g.selectAll("g.row").data(groups).join("g").attr("class", "row").attr("transform", function (d, j) { return "translate(0," + j * RH + ")"; });
          rows.each(function (g) {
            var n = d3.select(this);
            var lines = c.narrow ? wrap(g.name, 13) : [g.name];
            textLines(n, lines, -10, RH / 2 - 8 - (lines.length - 1) * 7, 14, "ex-svg-label", "end").style("stroke", "none");
            n.append("text").attr("class", "ov-cap").attr("x", -10).attr("y", RH / 2 + 8 + (lines.length - 1) * 7).attr("text-anchor", "end").text(F.int(g.total) + " counties");
            var acc = 0;
            var segs = n.selectAll("g.ex-mark").data(g.bins).join("g").attr("class", "ex-mark");
            segs.each(function (b) {
              var x0 = x(acc / g.total);
              var w = x(b.n / g.total);
              acc += b.n;
              d3.select(this).datum(Object.assign({ group: g.name, total: g.total }, b));
              var sg = d3.select(this);
              sg.append("rect").attr("class", "ex-hit").attr("x", x0).attr("y", 8).attr("width", Math.max(w, 24)).attr("height", RH - 16);
              sg.append("rect").attr("x", x0).attr("y", 14).attr("width", w).attr("height", RH - 28).attr("fill", b.bin.fill).attr("stroke", "#fff").attr("stroke-width", 2).style("pointer-events", "none");
              if (w > 30) sg.append("text").attr("class", "ov-seg-text").attr("x", x0 + w / 2).attr("y", RH / 2).attr("dy", "0.35em").attr("text-anchor", "middle").style("fill", b.bin.ink).text(F.int(b.n));
            });
          });
          Ex.tooltip.attach(c.g.selectAll("g.ex-mark"), function (el) {
            var d = el.__data__;
            return { title: d.group, rows: [{ name: "Chance above state rate: " + d.bin.name.toLowerCase(), value: F.int(d.n) + " counties" }, { name: "Share of group", value: pc(d.n / d.total) }] };
          });
          Ex.roving(c.g.node(), ".ex-mark");
        },
      });
      Ex.dataTable($("table-above"), {
        caption: "Counties by the chance their rate is above their state's. District of Columbia is left out.",
        columns: [{ key: "name", label: "Group" }, { key: "total", label: "Counties", format: F.int }].concat(
          BINS.map(function (b, j) {
            return { key: "b" + j, label: b.name, format: F.int };
          })
        ),
        rows: groups.map(function (g) {
          var r = { name: g.name, total: g.total };
          g.bins.forEach(function (b, j) { r["b" + j] = b.n; });
          return r;
        }),
      });
    })();

    /* ---------- check 1: state totals ---------- */
    function STATE_NAME(a) {
      return sByAbbr[a] ? sByAbbr[a].n : a;
    }
    (function () {
      var pts = D.aggregate.map(function (a) {
        var used = a.within_bounds && !a.has_dq;
        return Object.assign({ used: used, inside: a.residual >= a.model_lo90 && a.residual <= a.model_hi90, plotted: a.residual >= 1 }, a);
      });
      var plotted = pts.filter(function (p) { return p.plotted; });
      var nUsed = pts.filter(function (p) { return p.used; }).length;
      var nHold = pts.filter(function (p) { return p.used && p.inside; }).length;
      var far = plotted
        .filter(function (p) { return !p.used; })
        .sort(function (a, b) { return Math.abs(Math.log(b.residual / Math.max(1, b.model_median))) - Math.abs(Math.log(a.residual / Math.max(1, a.model_median))); })
        .slice(0, 4)
        .map(function (p) { return STATE_NAME(p.state); });
      var farText = far.length > 1 ? far.slice(0, -1).join(", ") + " and " + far[far.length - 1] : far.join("");
      Ex.chart($("chart-agg"), {
        label: "Log-log scatter of each state's modeled deaths in hidden counties against its state total minus published county counts. " + F.int(nHold) + " of " + nUsed + " states in the check have a 90% interval that holds the state difference. " + (far.length ? "Among the states left out of the fit, " + farText + " sit furthest from the equal line." : ""),
        aspect: 0.5,
        minHeight: 320,
        maxHeight: 560,
        margin: function (w) { return { top: 14, right: 18, bottom: 50, left: w < 520 ? 44 : 60 }; },
        render: function (c) {
          var x = d3.scaleLog().domain([1, 1000]).range([0, c.width]);
          var y = d3.scaleLog().domain([1, 1000]).range([c.height, 0]);
          var tv = [1, 10, 100, 1000];
          c.g.append("g").attr("class", "ex-gridlines").call(d3.axisLeft(y).tickValues(tv).tickSize(-c.width).tickFormat(""));
          c.g.append("g").attr("class", "ex-gridlines").attr("transform", "translate(0," + c.height + ")").call(d3.axisBottom(x).tickValues(tv).tickSize(-c.height).tickFormat(""));
          c.g.append("g").attr("class", "ex-axis ex-axis--y").call(d3.axisLeft(y).tickValues(tv).tickSize(0).tickPadding(8).tickFormat(F.int));
          c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + c.height + ")").call(d3.axisBottom(x).tickValues(tv).tickSize(0).tickPadding(8).tickFormat(F.int)).select(".domain").remove();
          c.g.append("text").attr("class", "ov-cap").attr("x", c.width / 2).attr("y", c.height + 42).attr("text-anchor", "middle").text("State total minus published county counts");
          c.g.append("text").attr("class", "ov-cap").attr("transform", "rotate(-90)").attr("x", -c.height / 2).attr("y", -(c.margin.left - 14)).attr("text-anchor", "middle").text("Model total in hidden counties");
          c.g.append("line").attr("class", "ex-ref-line").attr("x1", x(1)).attr("y1", y(1)).attr("x2", x(1000)).attr("y2", y(1000));
          var g = c.g.selectAll("g.ex-mark").data(plotted).join("g").attr("class", "ex-mark").attr("transform", function (d) { return "translate(" + x(d.residual) + "," + y(Math.max(1, d.model_median)) + ")"; });
          g.append("circle").attr("class", "ex-hit").attr("r", 13);
          g.append("path").attr("class", function (d) { return "ex-ci-whisker" + (d.used && !d.inside ? " ov-miss" : d.used ? " ov-hold" : ""); }).attr("d", function (d) {
            var a = y(Math.max(1, d.model_lo90)) - y(Math.max(1, d.model_median));
            var b = y(d.model_hi90) - y(Math.max(1, d.model_median));
            return "M-3," + a + "H3M0," + a + "V" + b + "M-3," + b + "H3";
          }).style("stroke", function (d) { return d.used ? null : "var(--ex-ink-3)"; });
          g.filter(function (d) { return d.used; }).append("circle").attr("class", "ov-circle").attr("r", 4.5);
          g.filter(function (d) { return !d.used; }).append("rect").attr("class", "ov-diamond").attr("x", -4.5).attr("y", -4.5).attr("width", 9).attr("height", 9).attr("transform", "rotate(45)");
          g.filter(function (d) { return !d.used || (!c.narrow && !d.inside); }).append("text").attr("class", "ex-svg-label").attr("x", 10).attr("y", 0).attr("dy", "0.35em").text(function (d) { return d.state; });
          Ex.tooltip.attach(g, function (el) {
            var d = el.__data__;
            var rows = [
              { name: "State total minus published", value: F.int(d.residual) },
              { name: "Model total", value: F.int(d.model_median), color: "est" },
              { name: "90% interval", value: F.int(d.model_lo90) + " to " + F.int(d.model_hi90) },
            ];
            var note = d.used ? (d.inside ? "Interval holds the state difference" : "Interval misses the state difference") : d.has_dq ? "Left out of the fit: data-quality counties" : "Left out of the fit: difference outside the 1-to-9 bounds";
            return { title: STATE_NAME(d.state), rows: rows, note: note };
          });
          Ex.roving(c.g.node(), ".ex-mark");
        },
      });
      Ex.dataTable($("table-agg"), {
        caption: "Deaths in hidden counties by state: the state total minus published county counts, and the model's total (fit without the state totals) with its 90% interval.",
        columns: [
          { key: "name", label: "State" },
          { key: "n_suppressed", label: "Hidden counties", format: F.int },
          { key: "residual", label: "State difference", format: F.int },
          { key: "model", label: "Model total (90% interval)", text: true },
          { key: "used", label: "In the check?", text: true },
        ],
        rows: pts.map(function (p) {
          return { name: STATE_NAME(p.state), n_suppressed: p.n_suppressed, residual: p.residual, model: F.int(p.model_median) + " (" + F.int(p.model_lo90) + " to " + F.int(p.model_hi90) + ")", used: p.used ? "Yes" : p.has_dq ? "No (data-quality counties)" : "No (difference outside bounds)" };
        }),
      });
    })();

    /* ---------- check 2: hide and score ---------- */
    (function () {
      var NAMES = {
        spatial: ["Spatial model (this page)", "Spatial model"],
        covariates_only: ["Same model, no spatial term", "No spatial term"],
        poisson_gamma: ["Poisson-gamma, no covariates, no state constraint", "Poisson-gamma, no covariates"],
        midpoint: ["Midpoint of the hidden range", "Midpoint of the range"],
        residual_split: ["State difference split by population", "State split by population"],
      };
      var ORDER = ["spatial", "covariates_only", "poisson_gamma", "midpoint", "residual_split"];
      var IS_MODEL = { spatial: 1, covariates_only: 1, poisson_gamma: 1 };
      var LV = D.levels;
      var CH = 300;
      var cur = function () { return D.hide_and_score[sel.cut]; };
      var maeRows = function () {
        var m = cur().models;
        return ORDER.map(function (k) { return { key: k, model: !!IS_MODEL[k], mae: m[k].mae }; });
      };
      var mae = Ex.chart($("chart-mae"), {
        label: "Bars of average miss in deaths per county.",
        margin: function () { return { top: 6, right: 48, bottom: 30, left: 8 }; },
        height: function () { return CH; },
        render: function (c) {
          var rows = maeRows();
          var RH = c.height / rows.length;
          c.svg.attr("aria-label", "Bar chart of average miss in deaths per county when counts under " + sel.cut + " are hidden. " + rows.map(function (r) { return NAMES[r.key][1] + " " + F.num(r.mae, 2); }).join(", ") + ". Lower is better.");
          var x = d3.scaleLinear().domain([0, 6]).range([0, c.width]);
          var H = c.height;
          c.g.append("g").attr("class", "ex-gridlines").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).ticks(6).tickSize(-H).tickFormat(""));
          c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + H + ")").call(d3.axisBottom(x).ticks(6).tickSize(0).tickPadding(8)).select(".domain").remove();
          c.g.append("text").attr("class", "ov-cap").attr("x", c.width).attr("y", H + 28).attr("text-anchor", "end").text("Deaths per county");
          var g = c.g.selectAll("g.ex-mark").data(rows).join("g").attr("class", "ex-mark").attr("transform", function (d, j) { return "translate(0," + j * RH + ")"; });
          g.append("rect").attr("class", "ex-hit").attr("x", -c.margin.left).attr("y", 0).attr("width", c.w).attr("height", RH);
          g.append("text").attr("class", "ex-svg-label").style("stroke", "none").style("font-weight", function (d) { return d.key === "spatial" ? 700 : 500; }).attr("x", 0).attr("y", 16).text(function (d) { return NAMES[d.key][c.narrow ? 1 : 0]; });
          g.append("path").attr("class", function (d) { return d.model ? "ex-fill--est" : "ov-rule"; }).attr("d", function (d) {
            var w = x(d.mae), r = 4, y0 = 24, h = 16;
            return "M0," + y0 + "H" + (w - r) + "a" + r + "," + r + " 0 0 1 " + r + "," + r + "V" + (y0 + h - r) + "a" + r + "," + r + " 0 0 1 " + -r + "," + r + "H0Z";
          });
          g.append("text").attr("class", "ex-svg-value").attr("x", function (d) { return x(d.mae) + 8; }).attr("y", 32).attr("dy", "0.35em").text(function (d) { return F.num(d.mae, 2); });
          Ex.tooltip.attach(g, function (el) {
            var d = el.__data__;
            var m = cur().models[d.key];
            var r = [{ name: "Average miss", value: F.num(d.mae, 2) + " deaths", color: d.model ? "est" : null }];
            if (m.rps != null) r.push({ name: "Ranked probability score", value: F.num(m.rps, 2) });
            if (m.coverage) r.push({ name: "90% interval holds", value: pc(m.coverage[4]) });
            return { title: NAMES[d.key][0], rows: r, note: d.model ? "Model" : "Simple rule, no interval" };
          });
          Ex.roving(c.g.node(), ".ex-mark");
        },
      });
      var LINES = [["spatial", "ex-line ex-line--est", "Spatial model"], ["covariates_only", "ov-l2", "No spatial term"], ["poisson_gamma", "ov-l3", "Poisson-gamma"]];
      // coverage minus the interval level, in percentage points; one axis for both cutoffs so the toggle does not rescale it
      var gapOf = function (T, key, j) { return (D.hide_and_score[T].models[key].coverage[j] - LV[j]) * 100; };
      var allGaps = [];
      ["20", "30"].forEach(function (T) {
        LINES.forEach(function (L) { LV.forEach(function (lv, j) { allGaps.push(gapOf(T, L[0], j)); }); });
      });
      var gExt = d3.extent(allGaps);
      var gLo = Math.floor(Math.min(gExt[0], 0) - 1);
      var gHi = Math.ceil(Math.max(gExt[1], 0) + 1);
      var signed = function (v) { return F.signed(v, 0); };
      var cal = Ex.chart($("chart-cal"), {
        label: "Line chart of calibration.",
        height: function () { return CH; },
        margin: function () { return { top: 12, right: 14, bottom: 46, left: 46 }; },
        render: function (c) {
          var m = cur().models;
          var other = d3.max(LV, function (lv, j) { return Math.max(Math.abs(gapOf(sel.cut, "covariates_only", j) - gapOf(sel.cut, "spatial", j)), Math.abs(gapOf(sel.cut, "poisson_gamma", j) - gapOf(sel.cut, "spatial", j))); });
          c.svg.attr("aria-label", "Line chart of how far each interval falls short of its level, in percentage points, when counts under " + sel.cut + " are hidden. For the spatial model, the 50% interval holds " + pc(m.spatial.coverage[0]) + ", the 90% interval " + pc(m.spatial.coverage[4]) + " and the 95% interval " + pc(m.spatial.coverage[5]) + ". The other two models are within " + F.num(other, 1) + " points of it at every level.");
          var x = d3.scaleLinear().domain([0.5, 0.95]).range([0, c.width]);
          var y = d3.scaleLinear().domain([gLo, gHi]).range([c.height, 0]);
          c.g.append("g").attr("class", "ex-gridlines").call(d3.axisLeft(y).ticks(6).tickSize(-c.width).tickFormat(""));
          c.g.append("g").attr("class", "ex-axis ex-axis--y").call(d3.axisLeft(y).ticks(6).tickSize(0).tickPadding(8).tickFormat(signed));
          c.g.append("g").attr("class", "ex-axis").attr("transform", "translate(0," + c.height + ")").call(d3.axisBottom(x).tickValues(LV).tickSize(0).tickPadding(8).tickFormat(function (d) { return F.num(d * 100, 0); })).select(".domain").remove();
          c.g.append("text").attr("class", "ov-cap").attr("x", c.width / 2).attr("y", c.height + 40).attr("text-anchor", "middle").text("Interval level, percent");
          c.g.append("text").attr("class", "ov-cap").attr("transform", "rotate(-90)").attr("x", -c.height / 2).attr("y", -(c.margin.left - 12)).attr("text-anchor", "middle").text("Share held minus level, points");
          c.g.append("line").attr("class", "ex-ref-line").attr("x1", 0).attr("y1", y(0)).attr("x2", c.width).attr("y2", y(0));
          c.g.append("text").attr("class", "ov-cap").attr("x", 4).attr("y", y(0) - 6).text("Exactly right");
          LINES.forEach(function (L) {
            var pts = LV.map(function (lv, j) { return [x(lv), y(gapOf(sel.cut, L[0], j))]; });
            c.g.append("path").attr("class", L[1]).attr("d", d3.line()(pts));
          });
          c.g.selectAll("circle.sp").data(LV).join("circle").attr("class", "ov-est-dot").attr("cx", function (d) { return x(d); }).attr("cy", function (d, j) { return y(gapOf(sel.cut, "spatial", j)); }).attr("r", 4);
          var cross = c.g.append("line").attr("class", "ex-crosshair").attr("y1", 0).attr("y2", c.height).style("display", "none");
          var node = c.svg.node();
          var xs = LV.map(x);
          c.cleanup(
            Ex.scrub(node, {
              xs: xs,
              offset: c.margin.left,
              onChange: function (j) {
                if (j == null) {
                  cross.style("display", "none");
                  return Ex.tooltip.hide();
                }
                var r = node.getBoundingClientRect();
                cross.attr("x1", xs[j]).attr("x2", xs[j]).style("display", null);
                Ex.tooltip.show(
                  {
                    title: F.num(LV[j] * 100, 0) + "% intervals",
                    rows: [
                      { name: "Spatial model", value: pc(m.spatial.coverage[j]), color: "est", dash: true },
                      { name: "No spatial term", value: pc(m.covariates_only.coverage[j]) },
                      { name: "Poisson-gamma", value: pc(m.poisson_gamma.coverage[j]) },
                    ],
                    note: "Exactly right would be " + F.num(LV[j] * 100, 0) + "%",
                  },
                  { x: r.left + c.margin.left + xs[j], y: r.top + c.margin.top + y(gapOf(sel.cut, "spatial", j)) },
                  node
                );
              },
            })
          );
        },
      });
      var refreshCalTable = liveTable($("table-cal"), function () {
        return {
          caption: "Share of true counts inside the model interval, by interval level, when counts under " + sel.cut + " are hidden. The chart plots this share minus the level.",
          columns: [{ key: "level", label: "Interval level" }].concat(
            LINES.map(function (L) {
              return { key: L[0], label: L[2], format: function (v) { return pc(v); } };
            })
          ),
          rows: LV.map(function (lv, j) {
            var r = { level: F.num(lv * 100, 0) + "%" };
            LINES.forEach(function (L) { r[L[0]] = D.hide_and_score[sel.cut].models[L[0]].coverage[j]; });
            return r;
          }),
        };
      });
      function update() {
        var h = cur();
        var m = h.models;
        var T = h.T;
        $("hide-sub").textContent = "Every county below " + T + " deaths is treated as suppressed. We refit, then score the " + F.int(h.n_scored) + " counties whose true count is 10 to " + (T - 1) + ".";
        var gainCov = ((m.covariates_only.rps - m.spatial.rps) / m.covariates_only.rps) * 100;
        $("hide-caption").textContent =
          "Spatial model, counts under " + T + ": ranked probability score " + F.num(m.spatial.rps, 2) + " (lower is better), against " + F.num(m.covariates_only.rps, 2) + " for the same model without the spatial term (" + F.num(gainCov, 1) + "% lower) and " + F.num(m.poisson_gamma.rps, 2) + " for a Poisson-gamma model with no covariates and no state constraint. Its 90% interval holds " + pc(m.spatial.coverage[4]) + " of true counts, against " + pc(m.covariates_only.coverage[4]) + " without it. Its average miss is " + F.num(m.spatial.mae, 2) + " deaths, against " + F.num(m.residual_split.mae, 2) + " for splitting the state difference by population and " + F.num(m.midpoint.mae, 2) + " for the range midpoint.";
        mae.redraw();
        cal.redraw();
        refreshCalTable();
      }
      radios("hidecut", function (v) {
        sel.cut = v;
        update();
      });
      update();
      Ex.dataTable($("table-mae"), {
        caption: "Average miss (deaths per county), ranked probability score and 90% interval coverage, with counts hidden below 20 and below 30.",
        columns: [{ key: "name", label: "Method" }].concat(
          ["20", "30"].reduce(function (a, T) {
            return a.concat([
              { key: "mae" + T, label: "Average miss, under " + T, format: function (v) { return v == null ? "n/a" : F.num(v, 2); } },
              { key: "rps" + T, label: "Score, under " + T, format: function (v) { return v == null ? "n/a" : F.num(v, 2); } },
              { key: "cov" + T, label: "90% holds, under " + T, format: function (v) { return v == null ? "n/a" : pc(v); } },
            ]);
          }, [])
        ),
        rows: ORDER.map(function (k) {
          var r = { name: NAMES[k][0] };
          ["20", "30"].forEach(function (T) {
            var m = D.hide_and_score[T].models[k];
            r["mae" + T] = m.mae;
            r["rps" + T] = m.rps == null ? null : m.rps;
            r["cov" + T] = m.coverage ? m.coverage[4] : null;
          });
          return r;
        }),
      });
    })();

    /* ---------- methods: every validation number ---------- */
    (function () {
      var host = $("table-val");
      var f = D.forecast;
      var SENS = [["main", "Main model"], ["no_constraint", "No state constraint"], ["no_covariates", "No covariates"], ["no_spatial", "No spatial term"], ["pending_adjusted", "Adjusted for pending records"]];
      var specs = [
        {
          caption: "Forecast check: fit to March 2025, predict March 2026 (CRPS, lower is better; average miss in deaths per county).",
          columns: [
            { key: "name", label: "Method" },
            { key: "crps", label: "Score, " + F.int(f.n_scored) + " counties", format: function (v) { return v == null ? "n/a" : F.num(v, 2); } },
            { key: "mae", label: "Average miss, " + F.int(f.same_n) + " counties in both years", format: function (v) { return F.num(v, 2); } },
          ],
          rows: [
            { name: "Spatial model", crps: f.spatial_crps, mae: f.spatial_mae },
            { name: "Poisson-gamma", crps: f.gamma_crps, mae: f.gamma_mae },
            { name: "Last year's count, same state adjustment", crps: null, mae: f.last_year_mae },
          ],
        },
        {
          caption: "Sensitivity of hidden-county results to model changes.",
          columns: [
            { key: "name", label: "Variant" },
            { key: "total", label: "Deaths in hidden counties", format: F.int },
            { key: "abs_pct", label: "Median change in a hidden county's rate", format: function (v) { return F.num(v, 1) + "%"; } },
          ],
          rows: SENS.map(function (k) { return { name: k[1], total: D.sensitivity[k[0]].total, abs_pct: D.sensitivity[k[0]].abs_pct }; }),
        },
      ];
      specs.forEach(function (sp) {
        var h = Ex.el("div", { class: "ov-valtable" });
        host.appendChild(h);
        Ex.dataTable(h, sp);
      });
      host.appendChild(Ex.el("p", { class: "ex-caption", text: "The hide-and-score table is under the charts in the check section." }));
    })();
  }
});
