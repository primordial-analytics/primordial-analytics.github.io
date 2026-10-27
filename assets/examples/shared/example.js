/*
  Example pages kit: small helpers shared by the example pages. Plain ES2019, no framework.
  Loaded after d3 7.9.0 by _layouts/example.html. Everything hangs off window.Ex.

    Ex.ready(fn)                       run fn when the DOM is ready
    Ex.el(tag, attrs, kids)            build a DOM node (text goes in as text, never as HTML)
    Ex.fmt.*                           number, percent, currency formatting; approx and oneIn round for prose
    Ex.reducedMotion()                 true when the viewer asked for less motion
    Ex.css(name)                       read a CSS custom property, e.g. Ex.css("--ex-c-est")
    Ex.live(msg)                       announce a message to screen readers
    Ex.tooltip() / Ex.tooltip.attach   one accessible tooltip (pointer, keyboard focus, touch)
    Ex.chart(el, opts)                 responsive SVG chart container (redraws on resize)
    Ex.scrub(svg, opts)                snap-to-x crosshair behavior with arrow keys
    Ex.roving(el, selector)            one tab stop for many marks, arrow keys move between them
    Ex.combobox(host, opts)            searchable select for long lists (states, counties)
    Ex.seq / Ex.scaleSeq / Ex.ramp     sequential color ramp, scale and legend bar
    Ex.range(input, opts)              range slider with a live output and filled track
    Ex.copy(text)                      copy to clipboard; buttons with [data-ex-copy] are wired up
    Ex.dataTable(host, opts)           accessible table fallback, built lazily inside <details>
    Ex.directLabels(g, items, opts)    labels on the marks themselves (spread so they do not overlap), instead of a legend
    Ex.assetUrl(name)                  URL of a file in assets/examples/shared/ (e.g. the county map)
    Ex.loadData(url)                   fetch JSON (default: the page's data-ex-data file)
    Ex.showError(el, msg)              plain error message in place of a chart

  The page chrome (sticky nav, scrollspy) starts by itself.
*/
(function (global) {
  "use strict";

  var Ex = (global.Ex = {});
  var doc = document;
  var scriptSrc = doc.currentScript && doc.currentScript.src;
  /** Ex.assetUrl("us-counties-albers-10m.json") -> absolute URL of a file in assets/examples/shared/ */
  Ex.assetUrl = function (name) {
    return new URL(name, scriptSrc || global.location.href).href;
  };
  var MINUS = "−";

  /* ---------- basics ---------- */

  Ex.ready = function (fn) {
    if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", fn);
    else fn();
  };

  /** Ex.el("button", {class: "ex-btn", type: "button", "aria-label": "x"}, ["Text", otherNode]) */
  Ex.el = function (tag, attrs, kids) {
    var n = doc.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      var v = attrs[k];
      if (v === false || v == null) return;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else n.setAttribute(k, v === true ? "" : v);
    });
    [].concat(kids == null ? [] : kids).forEach(function (c) {
      n.appendChild(typeof c === "string" || typeof c === "number" ? doc.createTextNode(String(c)) : c);
    });
    return n;
  };

  var mqReduce = global.matchMedia ? global.matchMedia("(prefers-reduced-motion: reduce)") : null;
  Ex.reducedMotion = function () {
    return !!(mqReduce && mqReduce.matches);
  };
  Ex.onReducedMotionChange = function (fn) {
    if (mqReduce && mqReduce.addEventListener) mqReduce.addEventListener("change", fn);
  };

  Ex.css = function (name, scope) {
    return getComputedStyle(scope || doc.documentElement).getPropertyValue(name).trim();
  };

  var liveRegion;
  Ex.live = function (msg) {
    if (!liveRegion) {
      liveRegion = Ex.el("div", { class: "ex-vh", role: "status", "aria-live": "polite" });
      doc.body.appendChild(liveRegion);
    }
    // clear first so repeating the same message is still announced
    liveRegion.textContent = "";
    setTimeout(function () {
      liveRegion.textContent = msg;
    }, 30);
  };

  /* ---------- formatting ---------- */

  var nf = {};
  function intl(digits, min) {
    var key = digits + "/" + (min == null ? digits : min);
    if (!nf[key]) {
      nf[key] = new Intl.NumberFormat("en-US", {
        minimumFractionDigits: min == null ? digits : min,
        maximumFractionDigits: digits,
      });
    }
    return nf[key];
  }
  function fixMinus(s) {
    return s.replace("-", MINUS);
  }
  var fmt = (Ex.fmt = {
    /** 1234.5 -> "1,235"  (fmt.num(1234.5, 1) -> "1,234.5") */
    num: function (v, digits) {
      return v == null || isNaN(v) ? "n/a" : fixMinus(intl(digits || 0).format(v));
    },
    int: function (v) {
      return fmt.num(Math.round(v), 0);
    },
    /** 1234567 -> "1.2M", 340000 -> "340K", 950 -> "950". Trailing zeros are dropped. */
    compact: function (v, digits) {
      if (v == null || isNaN(v)) return "n/a";
      var d = digits == null ? 1 : digits;
      var a = Math.abs(v);
      var units = [
        [1e9, "B"],
        [1e6, "M"],
        [1e3, "K"],
      ];
      for (var i = 0; i < units.length; i++) {
        if (a >= units[i][0] * 0.9995) {
          return fixMinus(intl(d, 0).format(v / units[i][0])) + units[i][1];
        }
      }
      return fixMinus(intl(0).format(v));
    },
    /**
     * Round for prose: to `sig` significant digits (default 2), words for millions and billions.
     * approx(5818) -> "5,800"; approx(1640179, 3) -> "1.64 million"; approx(2.45e9) -> "2.5 billion".
     * Exact figures belong in tables, tooltips and downloads.
     */
    approx: function (v, sig) {
      if (v == null || isNaN(v)) return "n/a";
      var d = sig || 2;
      var a = Math.abs(v);
      var units = [
        [1e9, " billion"],
        [1e6, " million"],
      ];
      for (var i = 0; i < units.length; i++) {
        if (a >= units[i][0] * 0.9995) {
          return (v < 0 ? MINUS : "") + intl(d, 0).format(Number((a / units[i][0]).toPrecision(d))) + units[i][1];
        }
      }
      return (v < 0 ? MINUS : "") + intl(0).format(Number(a.toPrecision(d)));
    },
    /** a share in words: 0.159 -> "about 1 in 6"; 0.5 -> "about half"; 0.72 -> "about 7 in 10" */
    oneIn: function (frac) {
      if (frac == null || isNaN(frac) || frac <= 0 || frac >= 1) return "n/a";
      if (frac >= 0.45 && frac <= 0.55) return "about half";
      if (frac < 0.5) return "about 1 in " + Math.round(1 / frac);
      return "about " + Math.round(frac * 10) + " in 10";
    },
    /** fraction to percent: 0.159 -> "15.9%" */
    pct: function (frac, digits) {
      return v100(frac * 100, digits == null ? 1 : digits);
    },
    /** a value already in percent units: 15.9 -> "15.9%" */
    pctValue: function (v, digits) {
      return v100(v, digits == null ? 1 : digits);
    },
    /** 12.5 -> "12.5 points" (percentage points) */
    points: function (v, digits) {
      var d = digits == null ? 1 : digits;
      return fmt.signed(v, d) + (Math.abs(+v.toFixed(d)) === 1 ? " point" : " points");
    },
    /** 1986 -> "$1,986"; with {compact:true} 4200000 -> "$4.2M" */
    usd: function (v, o) {
      o = o || {};
      if (v == null || isNaN(v)) return "n/a";
      var s = o.compact ? fmt.compact(Math.abs(v), o.digits == null ? 1 : o.digits) : fmt.num(Math.abs(v), o.digits || 0);
      return (v < 0 ? MINUS : "") + "$" + s;
    },
    /** 3.2 -> "+3.2", -1.4 -> "−1.4" */
    signed: function (v, digits) {
      var s = fmt.num(Math.abs(v), digits || 0);
      return (v < 0 ? MINUS : v > 0 ? "+" : "") + s;
    },
    /** fmt.range(0.117, 0.216, fmt.pct) -> "11.7% to 21.6%" */
    range: function (lo, hi, f) {
      f = f || fmt.num;
      return f(lo) + " to " + f(hi);
    },
    /** fmt.plural(1, "session") -> "1 session"; fmt.plural(2, "session") -> "2 sessions" */
    plural: function (n, word, pluralWord) {
      return fmt.int(n) + " " + (Math.round(n) === 1 ? word : pluralWord || word + "s");
    },
  });
  function v100(v, d) {
    return v == null || isNaN(v) ? "n/a" : fixMinus(intl(d).format(v)) + "%";
  }

  /* ---------- tooltip ---------- */

  var tipEl, tipOn, tipTimer;
  function ensureTip() {
    if (tipEl) return tipEl;
    tipEl = Ex.el("div", { class: "ex-tip", id: "ex-tip", role: "tooltip" });
    (doc.getElementById("main") || doc.body).appendChild(tipEl);
    doc.addEventListener("keydown", function (e) {
      if (e.key === "Escape") tip.hide(true);
    });
    // touch: tapping anywhere else closes it
    doc.addEventListener("pointerdown", function (e) {
      if (tipOn && e.pointerType === "touch" && !tipOn.contains(e.target) && !tipEl.contains(e.target)) tip.hide(true);
    });
    // WCAG 1.4.13: the pointer can move onto the tooltip without it closing
    tipEl.addEventListener("pointerenter", function () {
      clearTimeout(tipTimer);
    });
    tipEl.addEventListener("pointerleave", function () {
      if (!tipOn || doc.activeElement !== tipOn) tip.hide();
    });
    return tipEl;
  }
  // bottom edge of whatever is stuck to the top of the viewport (site nav, then the section nav)
  function stuckBottom() {
    var nav = doc.getElementById("mainNav"),
      sub = doc.getElementById("ex-subnav");
    var b = nav ? nav.getBoundingClientRect().bottom : 0;
    if (sub && sub.getBoundingClientRect().top <= b + 1) b = sub.getBoundingClientRect().bottom;
    return b;
  }

  /** content: a string, a Node, or {title, rows: [{name, value, color, dash}], note}.
   *  color is "obs", "est" or "ref" (bright variants that read on the dark tooltip) or any CSS color.. All text is inserted as text. */
  function buildTip(content) {
    var frag = doc.createDocumentFragment();
    if (content instanceof Node) {
      frag.appendChild(content);
    } else if (typeof content === "string") {
      frag.appendChild(Ex.el("div", { text: content }));
    } else {
      if (content.title) frag.appendChild(Ex.el("div", { class: "ex-tip__title", text: content.title }));
      (content.rows || []).forEach(function (r) {
        var named = /^(obs|est|ref)$/.test(r.color || "");
        var key = Ex.el("span", { class: "ex-tip__key" + (r.dash ? " ex-tip__key--dash" : "") + (named ? " ex-tip__key--" + r.color : ""), "aria-hidden": "true" });
        if (r.color && !named) key.style.setProperty("--k", r.color);
        else if (!r.color) key.style.visibility = "hidden";
        frag.appendChild(
          Ex.el("div", { class: "ex-tip__row" }, [key, Ex.el("span", { class: "ex-tip__name", text: r.name }), Ex.el("span", { class: "ex-tip__val", text: r.value })])
        );
      });
      if (content.note) frag.appendChild(Ex.el("div", { class: "ex-tip__note", text: content.note }));
    }
    return frag;
  }
  function textOf(content) {
    if (content instanceof Node) return content.textContent;
    if (typeof content === "string") return content;
    var parts = [];
    if (content.title) parts.push(content.title);
    (content.rows || []).forEach(function (r) {
      parts.push(r.name + " " + r.value);
    });
    if (content.note) parts.push(content.note);
    return parts.join(", ");
  }

  var tip = {
    /** show(content, pt, owner). pt is {x, y} (client coordinates; the tooltip sits beside that point)
     *  or {rect} (a DOMRect; the tooltip sits above it, or below when there is no room). */
    show: function (content, pt, owner) {
      var t = ensureTip();
      clearTimeout(tipTimer);
      t.textContent = "";
      t.appendChild(buildTip(content));
      tipOn = owner || t;
      t.classList.add("is-on");
      tip.move(pt);
    },
    move: function (pt) {
      var t = ensureTip();
      var w = t.offsetWidth,
        h = t.offsetHeight,
        m = 8,
        top = Math.max(m, stuckBottom() + 6),
        x,
        y;
      if (pt.rect) {
        var r = pt.rect;
        x = r.left + r.width / 2 - w / 2;
        y = r.top - h - 8;
        if (y < top) y = r.bottom + 8;
      } else {
        x = pt.x + 16;
        if (x + w > global.innerWidth - m) x = pt.x - 16 - w;
        y = pt.y - h / 2;
      }
      x = Math.min(Math.max(x, m), global.innerWidth - w - m);
      y = Math.min(Math.max(y, top), Math.max(top, global.innerHeight - h - m));
      t.style.left = Math.round(x) + "px";
      t.style.top = Math.round(y) + "px";
    },
    /** hide(true) closes at once (Escape, outside tap); otherwise after a short delay so the pointer can reach the tooltip */
    hide: function (now) {
      if (!tipEl) return;
      clearTimeout(tipTimer);
      var done = function () {
        tipEl.classList.remove("is-on");
        if (tipOn && tipOn.removeAttribute) tipOn.removeAttribute("aria-describedby");
        tipOn = null;
      };
      if (now === true) done();
      else tipTimer = setTimeout(done, 140);
    },
  };

  /**
   * Ex.tooltip.attach(targets, contentFn, opts)
   *   targets: element, array, NodeList, or d3 selection
   *   contentFn(el) -> content (see above); it can read el.__data__ with d3
   *   opts.focusable (default true): give targets tabindex=0 so the keyboard can reach them
   *   opts.label (default true): set role="img" and aria-label from the same content, so screen
   *     readers get the text without the tooltip
   * Returns a function that detaches everything.
   */
  tip.attach = function (targets, contentFn, opts) {
    opts = opts || {};
    var list = targets && targets.nodes ? targets.nodes() : targets instanceof Node ? [targets] : [].slice.call(targets || []);
    var offs = [];
    list.forEach(function (el) {
      var c0 = contentFn(el);
      if (opts.focusable !== false && !el.hasAttribute("tabindex")) el.setAttribute("tabindex", "0");
      if (opts.label !== false) {
        if (!el.hasAttribute("role")) el.setAttribute("role", "img");
        el.setAttribute("aria-label", textOf(c0));
      }
      function at(e) {
        return e && e.pointerType === "mouse" ? { x: e.clientX, y: e.clientY } : { rect: el.getBoundingClientRect() };
      }
      function on(e) {
        tip.show(contentFn(el), at(e), el);
        // the aria-label already carries the same text; describing it again would be read twice
        if (opts.label === false) el.setAttribute("aria-describedby", "ex-tip");
      }
      var h = {
        pointerenter: on,
        pointermove: function (e) {
          if (e.pointerType === "mouse" && tipOn === el) tip.move(at(e));
        },
        pointerdown: function (e) {
          if (e.pointerType === "touch") on(e);
        },
        pointerleave: function (e) {
          if (e.pointerType === "mouse" && doc.activeElement !== el) tip.hide();
        },
        focus: on,
        blur: function () {
          tip.hide();
        },
      };
      Object.keys(h).forEach(function (k) {
        el.addEventListener(k, h[k]);
      });
      offs.push(function () {
        Object.keys(h).forEach(function (k) {
          el.removeEventListener(k, h[k]);
        });
      });
    });
    return function () {
      offs.forEach(function (f) {
        f();
      });
      tip.hide();
    };
  };
  Ex.tooltip = function () {
    ensureTip();
    return tip;
  };
  Ex.tooltip.attach = tip.attach;
  Ex.tooltip.show = tip.show;
  Ex.tooltip.hide = tip.hide;
  Ex.tooltip.move = tip.move;

  /* ---------- responsive chart container ---------- */

  /**
   * Ex.chart(el, {
   *   label: "Short text alternative",          // required, becomes aria-label on the <svg>
   *   desc: "Longer description of the finding", // optional, linked with aria-describedby
   *   aspect: 0.6, minHeight: 240, maxHeight: 620,  // height = width * aspect, clamped
   *   height: function (width) { return px },       // or compute the height yourself (ranked bars)
   *   margin: {top, right, bottom, left} | function (width) -> margin,
   *   render: function (ctx) { ... }
   * })
   * ctx: { svg, g, w, h, width, height, margin, narrow, motion, cleanup(fn) }
   *   svg/g are d3 selections; g is translated by the margin; width/height are the inner size.
   * Returns { redraw(), svg, destroy() }. It draws once the container has a width, so a chart inside a
   * closed <details> or a hidden tab draws when it is first shown.
   */
  var chartId = 0;
  Ex.chart = function (el, o) {
    var id = "ex-chart-" + ++chartId;
    var svg = d3.select(el).append("svg").attr("role", "img").attr("aria-label", o.label || "Chart");
    if (o.desc) {
      svg.append("desc").attr("id", id + "-desc").text(o.desc);
      svg.attr("aria-describedby", id + "-desc");
    }
    var g = svg.append("g");
    var lastW = -1;
    var cleanups = [];
    var raf = 0;

    function draw() {
      raf = 0;
      var w = Math.floor(el.clientWidth);
      if (w < 10) return;
      lastW = w;
      cleanups.splice(0).forEach(function (f) {
        f();
      });
      var m = typeof o.margin === "function" ? o.margin(w) : o.margin || { top: 12, right: 16, bottom: 28, left: 44 };
      var h = o.height ? o.height(w) : Math.max(o.minHeight || 220, Math.min(o.maxHeight || 640, w * (o.aspect || 0.6)));
      h = Math.round(h);
      svg.attr("width", w).attr("height", h).attr("viewBox", "0 0 " + w + " " + h);
      g.selectAll("*").remove();
      g.attr("transform", "translate(" + m.left + "," + m.top + ")");
      o.render({
        svg: svg,
        g: g,
        w: w,
        h: h,
        width: w - m.left - m.right,
        height: h - m.top - m.bottom,
        margin: m,
        narrow: w < 520,
        motion: !Ex.reducedMotion(),
        cleanup: function (f) {
          cleanups.push(f);
        },
      });
    }
    function schedule() {
      if (!raf) raf = requestAnimationFrame(draw);
    }
    var ro = new ResizeObserver(function () {
      // only the width matters; the svg sets its own height, so this cannot loop
      if (Math.floor(el.clientWidth) !== lastW) schedule();
    });
    ro.observe(el);
    schedule();
    return {
      svg: svg,
      redraw: function () {
        lastW = -1;
        draw();
      },
      destroy: function () {
        ro.disconnect();
        cleanups.splice(0).forEach(function (f) {
          f();
        });
        svg.remove();
      },
    };
  };

  /**
   * Ex.scrub(svgNode, {xs, offset, onChange})
   * Crosshair behavior for line and area charts. xs is the pixel x of each data position (inner
   * coordinates, sorted ascending); offset is margin.left. onChange(i) gets the nearest index, or
   * null when the pointer or focus leaves. The svg becomes focusable: Left/Right/Home/End step through
   * positions, Escape clears. Register the returned function with ctx.cleanup.
   */
  Ex.scrub = function (svgNode, o) {
    var cur = null;
    function set(i) {
      if (i !== cur) {
        cur = i;
        o.onChange(i);
      }
    }
    function nearest(clientX) {
      var r = svgNode.getBoundingClientRect();
      var x = clientX - r.left - o.offset;
      var best = 0,
        bd = Infinity;
      o.xs.forEach(function (px, i) {
        var d = Math.abs(px - x);
        if (d < bd) {
          bd = d;
          best = i;
        }
      });
      return best;
    }
    function move(e) {
      set(nearest(e.clientX));
    }
    function key(e) {
      var n = o.xs.length;
      var k = e.key;
      if (k === "ArrowRight" || k === "ArrowUp") set(cur == null ? 0 : Math.min(n - 1, cur + 1));
      else if (k === "ArrowLeft" || k === "ArrowDown") set(cur == null ? n - 1 : Math.max(0, cur - 1));
      else if (k === "Home") set(0);
      else if (k === "End") set(n - 1);
      else if (k === "Escape") set(null);
      else return;
      e.preventDefault();
    }
    function leave() {
      if (doc.activeElement !== svgNode) set(null);
    }
    svgNode.setAttribute("tabindex", "0");
    svgNode.addEventListener("pointermove", move);
    svgNode.addEventListener("pointerdown", move);
    svgNode.addEventListener("pointerleave", leave);
    svgNode.addEventListener("keydown", key);
    svgNode.addEventListener("blur", function () {
      set(null);
    });
    return function () {
      svgNode.removeEventListener("pointermove", move);
      svgNode.removeEventListener("pointerdown", move);
      svgNode.removeEventListener("pointerleave", leave);
      svgNode.removeEventListener("keydown", key);
    };
  };

  /**
   * Ex.roving(container, selector)
   * Makes many focusable marks one tab stop. The first match is tabbable; arrow keys, Home and End move
   * between them. Use it after Ex.tooltip.attach on bars, dots or cells so a 50-row chart does not cost
   * the keyboard user 50 Tab presses. Call again after a redraw.
   */
  Ex.roving = function (container, selector) {
    var items = [].slice.call(container.querySelectorAll(selector));
    if (!items.length) return;
    items.forEach(function (n, i) {
      n.setAttribute("tabindex", i === 0 ? "0" : "-1");
    });
    function go(to) {
      var cur = items.filter(function (n) {
        return n.getAttribute("tabindex") === "0";
      })[0];
      if (cur) cur.setAttribute("tabindex", "-1");
      items[to].setAttribute("tabindex", "0");
      items[to].focus();
    }
    items.forEach(function (n, i) {
      n.addEventListener("keydown", function (e) {
        var k = e.key,
          last = items.length - 1;
        var to = k === "ArrowDown" || k === "ArrowRight" ? Math.min(last, i + 1) : k === "ArrowUp" || k === "ArrowLeft" ? Math.max(0, i - 1) : k === "Home" ? 0 : k === "End" ? last : -1;
        if (to < 0) return;
        e.preventDefault();
        go(to);
      });
      n.addEventListener("focus", function () {
        items.forEach(function (m) {
          m.setAttribute("tabindex", m === n ? "0" : "-1");
        });
      });
    });
  };

  /* ---------- combobox ---------- */

  function norm(s) {
    return String(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  }

  /**
   * Ex.combobox(host, {
   *   id: "state", label: "State", hint: "Type a name or abbreviation",
   *   items: [{value: "OR", label: "Oregon", hint: "OR", search: "extra words to match"}],
   *   value: "OR",            // optional initial selection
   *   placeholder: "Search",
   *   noun: "states", noun_one: "state",   // used in the status text ("41 states", "1 state")
   *   emptyText: "No match. ...",           // shown when nothing matches
   *   maxResults: 50,         // rendered at once; typing narrows the rest
   *   onSelect: function (item) {}   // item, or null when cleared
   * })
   * Ids it creates: <id>-input (the text field), <id>-list (the listbox), <id>-hint (when hint is set).
   * WAI-ARIA 1.2 combobox with a listbox popup. Up/Down move, Enter selects, Escape closes (then clears),
   * Tab leaves. Returns { getValue(), setValue(v, {silent}), setItems(items), focus(), destroy() }.
   */
  Ex.combobox = function (host, o) {
    var id = o.id || "ex-combo-" + Math.random().toString(36).slice(2, 7);
    var max = o.maxResults || 50;
    var items = [],
      shown = [],
      selected = null,
      active = -1,
      open = false;

    var label = Ex.el("label", { class: "ex-label", for: id + "-input", text: o.label || "Search" });
    var hint = o.hint ? Ex.el("div", { class: "ex-hint", id: id + "-hint", text: o.hint }) : null;
    var input = Ex.el("input", {
      class: "ex-combo__input",
      id: id + "-input",
      type: "text",
      role: "combobox",
      "aria-expanded": "false",
      "aria-controls": id + "-list",
      "aria-autocomplete": "list",
      "aria-describedby": hint ? id + "-hint" : false,
      autocomplete: "off",
      autocapitalize: "off",
      spellcheck: "false",
      placeholder: o.placeholder || "",
    });
    var clear = Ex.el("button", { class: "ex-combo__clear", type: "button", tabindex: "-1", "aria-label": "Clear " + (o.label || "selection").toLowerCase() }, ["×"]);
    var list = Ex.el("ul", { class: "ex-combo__list", id: id + "-list", role: "listbox", "aria-label": o.label || "Results", hidden: true });
    var status = Ex.el("div", { class: "ex-vh", role: "status", "aria-live": "polite" });
    var wrap = Ex.el("div", { class: "ex-combo__wrap" }, [input, clear, list]);
    host.classList.add("ex-field", "ex-combo");
    host.textContent = "";
    [label, hint, wrap, status].forEach(function (n) {
      if (n) host.appendChild(n);
    });

    function prep(arr) {
      return arr.map(function (it) {
        var label = String(it.label);
        return { value: it.value, label: label, hint: it.hint, nl: norm(label), ns: norm(label + " " + (it.search || "") + " " + (it.hint || "")), raw: it };
      });
    }
    function filter(q) {
      var toks = norm(q).split(/\s+/).filter(Boolean);
      if (!toks.length) return items.slice();
      var out = [];
      items.forEach(function (it, idx) {
        var score = 3;
        for (var i = 0; i < toks.length; i++) {
          var t = toks[i];
          if (it.ns.indexOf(t) === -1) return;
          var s = it.nl.indexOf(t) === 0 ? 0 : it.nl.indexOf(" " + t) > -1 ? 1 : it.nl.indexOf(t) > -1 ? 2 : 3;
          score = Math.min(score, s);
        }
        out.push({ it: it, score: score, idx: idx });
      });
      out.sort(function (a, b) {
        return a.score - b.score || a.idx - b.idx;
      });
      return out.map(function (x) {
        return x.it;
      });
    }
    function highlight(li, it, tok) {
      var text = it.label;
      var i = tok && it.nl.length === text.length ? it.nl.indexOf(tok) : -1;
      if (i < 0) {
        li.appendChild(doc.createTextNode(text));
        return;
      }
      li.appendChild(doc.createTextNode(text.slice(0, i)));
      li.appendChild(Ex.el("mark", { text: text.slice(i, i + tok.length) }));
      li.appendChild(doc.createTextNode(text.slice(i + tok.length)));
    }
    function render(q) {
      var all = filter(q);
      shown = all.slice(0, max);
      var tok = norm(q).split(/\s+/).filter(Boolean)[0];
      list.textContent = "";
      shown.forEach(function (it, i) {
        var li = Ex.el("li", { class: "ex-combo__opt", role: "option", id: id + "-o" + i, "aria-selected": selected && selected.value === it.value ? "true" : "false" });
        var main = Ex.el("span");
        highlight(main, it, tok);
        li.appendChild(main);
        if (it.hint) li.appendChild(Ex.el("small", { text: it.hint }));
        li.addEventListener("pointerdown", function (e) {
          e.preventDefault(); // keep focus in the input
          choose(it);
        });
        li.addEventListener("pointermove", function () {
          if (active !== i) setActive(i);
        });
        list.appendChild(li);
      });
      if (!shown.length) list.appendChild(Ex.el("li", { class: "ex-combo__empty", role: "presentation", text: o.emptyText || "No match. Check the spelling or try fewer letters." }));
      else if (all.length > max) list.appendChild(Ex.el("li", { class: "ex-combo__more", role: "presentation", text: "Showing " + fmt.int(max) + " of " + fmt.int(all.length) + ". Keep typing to narrow." }));
      active = shown.length && q ? 0 : -1;
      if (!q && selected) active = shown.findIndex(function (s) { return s.value === selected.value; });
      setActive(active, true);
      status.textContent = shown.length ? fmt.int(all.length) + " " + (all.length === 1 && o.noun_one ? o.noun_one : o.noun || "matches") + (all.length > max ? ", showing the first " + max : "") : "No match";
    }
    function setActive(i, noScroll) {
      active = i;
      [].forEach.call(list.querySelectorAll(".ex-combo__opt"), function (n, k) {
        n.classList.toggle("is-active", k === i);
      });
      if (i >= 0 && shown[i]) {
        input.setAttribute("aria-activedescendant", id + "-o" + i);
        if (!noScroll || selected) {
          var n = doc.getElementById(id + "-o" + i);
          if (n && n.scrollIntoView) n.scrollIntoView({ block: "nearest" });
        }
      } else input.removeAttribute("aria-activedescendant");
    }
    function openList(q) {
      render(q == null ? "" : q);
      list.hidden = false;
      open = true;
      input.setAttribute("aria-expanded", "true");
    }
    function closeList() {
      list.hidden = true;
      open = false;
      active = -1;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
    }
    function showSelected() {
      input.value = selected ? selected.label : "";
      host.classList.toggle("has-value", !!selected);
    }
    function choose(it, silent) {
      selected = it;
      showSelected();
      closeList();
      if (!silent && o.onSelect) o.onSelect(it ? it.raw : null);
      if (it && !silent) Ex.live(it.label + " selected");
    }

    input.addEventListener("input", function () {
      openList(input.value);
      host.classList.toggle("has-value", !!input.value);
    });
    input.addEventListener("focus", function () {
      input.select();
    });
    input.addEventListener("click", function () {
      if (!open) {
        openList("");
        input.select();
      }
    });
    input.addEventListener("keydown", function (e) {
      var k = e.key;
      if (k === "ArrowDown" || k === "ArrowUp") {
        e.preventDefault();
        if (!open) {
          openList(input.value === (selected && selected.label) ? "" : input.value);
          return;
        }
        if (!shown.length) return;
        setActive(k === "ArrowDown" ? (active + 1) % shown.length : (active - 1 + shown.length) % shown.length);
      } else if (k === "PageDown" || k === "PageUp") {
        if (open && shown.length) {
          e.preventDefault();
          setActive(Math.max(0, Math.min(shown.length - 1, active + (k === "PageDown" ? 8 : -8))));
        }
      } else if (k === "Enter") {
        if (open && active >= 0 && shown[active]) {
          e.preventDefault();
          choose(shown[active]);
        }
      } else if (k === "Escape") {
        if (open) {
          e.preventDefault();
          closeList();
          showSelected();
        } else if (selected || input.value) {
          e.preventDefault();
          choose(null);
        }
      } else if (k === "Tab") {
        commitExact();
        closeList();
        showSelected();
      }
    });
    // typed text that is exactly one item's label or hint (OH, ohio) counts as picking it
    function commitExact() {
      var q = norm(input.value.trim());
      if (!q || (selected && norm(selected.label) === q)) return;
      var hits = items.filter(function (it) {
        return it.nl === q || (it.hint && norm(it.hint) === q);
      });
      if (hits.length === 1) choose(hits[0]);
    }
    input.addEventListener("blur", function () {
      commitExact();
      closeList();
      showSelected();
    });
    clear.addEventListener("click", function () {
      choose(null);
      input.focus();
    });

    function setItems(arr) {
      items = prep(arr);
      selected = null;
      showSelected();
      closeList();
    }
    setItems(o.items || []);
    function setValue(v, opts) {
      var it = items.find(function (x) {
        return x.value === v;
      });
      choose(it || null, opts && opts.silent);
    }
    if (o.value != null) setValue(o.value, { silent: true });
    return {
      getValue: function () {
        return selected ? selected.value : null;
      },
      setValue: setValue,
      setItems: setItems,
      focus: function () {
        input.focus();
      },
      destroy: function () {
        host.textContent = "";
      },
    };
  };

  /* ---------- color ramp ---------- */

  /** The sequential ramp (one hue, light to dark) from the kit tokens. Use it for maps and heat cells. */
  Ex.seq = ["#f3f2fb", "#dcdaf3", "#bdb9e8", "#958fd8", "#6d66c6", "#4b44b8", "#1f1b66"];
  /** Ex.scaleSeq([0, 45]) -> d3 scale returning colors from Ex.seq (continuous). For classes use d3.scaleQuantize().range(Ex.seq). */
  Ex.scaleSeq = function (domain) {
    return d3.scaleSequential(d3.interpolateRgbBasis(Ex.seq)).domain(domain).clamp(true);
  };
  /**
   * Ex.ramp(host, {domain: [0, 45], title: "Deaths per 100,000", format: fn, stops: Ex.seq})
   * Draws a gradient bar with the two end values. The map tooltip and table carry the exact values.
   */
  Ex.ramp = function (host, o) {
    var stops = o.stops || Ex.seq;
    var f = o.format || fmt.num;
    host.classList.add("ex-ramp");
    host.textContent = "";
    if (o.title) host.appendChild(Ex.el("div", { class: "ex-ramp__title", text: o.title }));
    var bar = Ex.el("div", { class: "ex-ramp__bar", "aria-hidden": "true" });
    bar.style.background = "linear-gradient(to right," + stops.join(",") + ")";
    host.appendChild(bar);
    host.appendChild(Ex.el("div", { class: "ex-ramp__ends" }, [Ex.el("span", { text: f(o.domain[0]) }), Ex.el("span", { text: f(o.domain[1]) })]));
  };

  /* ---------- interactive maps (MapLibre GL; the page loads it from cdnjs) ---------- */

  // OpenFreeMap's dark basemap (free, no key), re-tinted along the site's navy so gold data glows on top of it
  var BASEMAP = "https://tiles.openfreemap.org/styles/dark";
  var navyRamp = d3.interpolateRgb("#0c0a2a", "#b3aee6");
  function navy(c) {
    if (Array.isArray(c)) return c.map(navy); // colors inside zoom expressions
    var k = typeof c === "string" && d3.color(c);
    if (!k) return c;
    var out = d3.color(navyRamp(Math.min(1, d3.hsl(k).l * 1.7)));
    out.opacity = k.opacity;
    return out.formatRgb();
  }
  /**
   * Ex.map(host, {bounds: [[w, s], [e, n]], label}) -> a maplibregl.Map on the navy basemap. Zoom and pan by drag, pinch,
   * the +/- buttons, the keyboard, or ctrl/cmd + scroll (plain scroll keeps scrolling the page). No rotation or tilt.
   */
  Ex.map = function (host, o) {
    var map = new maplibregl.Map({
      container: host, style: BASEMAP, bounds: o.bounds, fitBoundsOptions: { padding: 28 }, maxZoom: 15,
      cooperativeGestures: true, dragRotate: false, pitchWithRotate: false, touchPitch: false, attributionControl: { compact: true },
    });
    map.touchZoomRotate.disableRotation();
    map.keyboard.disableRotation();
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.on("style.load", function () {
      map.getStyle().layers.forEach(function (l) {
        Object.keys(l.paint || {}).forEach(function (p) {
          if (/color$/.test(p)) map.setPaintProperty(l.id, p, navy(l.paint[p]));
        });
      });
    });
    // the style's town dots name an image its sprite lacks ("circle-11"); a blank one keeps them off, as dots would read as data points
    map.on("styleimagemissing", function (e) {
      if (e.id === "circle-11") map.addImage(e.id, { width: 1, height: 1, data: new Uint8Array(4) });
    });
    if (o.label) map.getCanvas().setAttribute("aria-label", o.label);
    return map;
  };
  /**
   * Ex.glow(map, id, source, {color, radius, opacity}) adds a firefly point layer: a wide blurred halo under a sharp core.
   * radius and opacity may be MapLibre expressions. Layers are named id + "-halo" and id.
   */
  Ex.glow = function (map, id, source, o) {
    var r = o.radius, op = o.opacity == null ? 1 : o.opacity;
    map.addLayer({ id: id + "-halo", type: "circle", source: source, paint: { "circle-color": o.color, "circle-radius": ["*", 2.6, r], "circle-blur": 1, "circle-opacity": ["*", 0.45, op] } });
    map.addLayer({ id: id, type: "circle", source: source, paint: { "circle-color": o.color, "circle-radius": r, "circle-opacity": op, "circle-stroke-width": 0.6, "circle-stroke-color": "rgba(255,255,255,0.55)", "circle-stroke-opacity": op } });
  };
  /** Ex.ring([lon, lat], miles) -> a GeoJSON Polygon approximating a circle of that radius on the ground. */
  Ex.ring = function (c, miles) {
    var la = (c[1] * Math.PI) / 180, dy = miles / 69.047, dx = dy / Math.cos(la), pts = [];
    for (var i = 0; i <= 72; i++) {
      var t = (i / 72) * 2 * Math.PI;
      pts.push([c[0] + dx * Math.cos(t), c[1] + dy * Math.sin(t)]);
    }
    return { type: "Polygon", coordinates: [pts] };
  };

  /* ---------- range slider ---------- */

  /**
   * Ex.range(input, {format: function (v) -> string, onInput: function (v)})
   * Expects <div class="ex-range"><input type="range"><output></output></div>. Fills the track, writes the
   * formatted value to the <output> and to aria-valuetext. Returns update(): call it after setting input.value.
   */
  Ex.range = function (input, o) {
    o = o || {};
    var out = input.parentNode.querySelector("output");
    function update() {
      var v = +input.value,
        min = +input.min || 0,
        max = +input.max || 100;
      var text = o.format ? o.format(v) : String(v);
      input.style.setProperty("--fill", ((v - min) / (max - min)) * 100 + "%");
      input.setAttribute("aria-valuetext", text);
      if (out) out.textContent = text;
    }
    input.addEventListener("input", function () {
      update();
      if (o.onInput) o.onInput(+input.value);
    });
    update();
    return update;
  };

  /* ---------- copy to clipboard ---------- */

  /** Ex.copy(text) -> Promise<boolean>. Falls back to a hidden textarea where the Clipboard API is missing. */
  Ex.copy = function (text) {
    if (navigator.clipboard && global.isSecureContext) {
      return navigator.clipboard.writeText(text).then(
        function () {
          return true;
        },
        function () {
          return fallbackCopy(text);
        }
      );
    }
    return Promise.resolve(fallbackCopy(text));
  };
  function fallbackCopy(text) {
    var ta = Ex.el("textarea", { class: "ex-vh", "aria-hidden": "true", tabindex: "-1", readonly: true });
    ta.value = text;
    doc.body.appendChild(ta);
    ta.select();
    var ok = false;
    try {
      ok = doc.execCommand("copy");
    } catch (e) {
      ok = false;
    }
    ta.remove();
    return ok;
  }
  /**
   * Buttons: <button class="ex-btn ex-btn--ghost ex-btn--sm" data-ex-copy="text to copy">Copy link</button>
   * or data-ex-copy-from="#element-id" (copies its value or text). data-ex-copy="url" copies the page URL.
   */
  function wireCopy(btn) {
    var idle = btn.textContent;
    btn.addEventListener("click", function () {
      var from = btn.getAttribute("data-ex-copy-from");
      var text = from ? (function (n) {
        return n ? (n.value != null && n.tagName !== "DIV" ? n.value : n.textContent) : "";
      })(doc.querySelector(from)) : btn.getAttribute("data-ex-copy");
      if (text === "url") text = global.location.href;
      Promise.resolve(Ex.copy(text)).then(function (ok) {
        btn.textContent = ok ? "Copied" : "Copy failed. Select the text and copy it.";
        btn.classList.toggle("is-done", !!ok);
        Ex.live(ok ? "Copied to clipboard" : "Copy failed");
        setTimeout(function () {
          btn.textContent = idle;
          btn.classList.remove("is-done");
        }, 2200);
      });
    });
  }

  /* ---------- data table fallback ---------- */

  /**
   * Ex.dataTable(host, {
   *   caption: "What the table shows",
   *   label: "Scrollable table of ...",            // aria-label for the scroll region
   *   columns: [{key: "state", label: "State", format: fn, text: true}],  // first column is the row header
   *   rows: [{state: "Utah", ...}]
   * })
   * If host sits in a closed <details>, the table is built the first time it opens (big tables stay cheap).
   * update(rows, {caption, label}) swaps the rows and, if given, the caption and region label.
   */
  Ex.dataTable = function (host, o) {
    var built = false;
    function build() {
      if (built) return;
      built = true;
      var table = Ex.el("table", { class: "ex-table" });
      if (o.caption) table.appendChild(Ex.el("caption", { text: o.caption }));
      var tr = Ex.el("tr");
      o.columns.forEach(function (c, i) {
        tr.appendChild(Ex.el("th", { scope: "col", class: c.text && i ? "is-text" : false, text: c.label }));
      });
      table.appendChild(Ex.el("thead", {}, [tr]));
      var tb = Ex.el("tbody");
      var frag = doc.createDocumentFragment();
      o.rows.forEach(function (r) {
        var row = Ex.el("tr");
        o.columns.forEach(function (c, i) {
          var v = r[c.key];
          var txt = c.format ? c.format(v, r) : v == null ? "" : String(v);
          row.appendChild(Ex.el(i === 0 ? "th" : "td", { scope: i === 0 ? "row" : false, class: c.text && i ? "is-text" : false, text: txt }));
        });
        frag.appendChild(row);
      });
      tb.appendChild(frag);
      table.appendChild(tb);
      var region = Ex.el("div", { class: "ex-table-wrap" + (o.rows.length <= 12 ? " is-short" : ""), role: "region", tabindex: "0", "aria-label": o.label || o.caption || "Data table" }, [table]);
      host.textContent = "";
      host.appendChild(region);
    }
    var d = host.closest && host.closest("details");
    if (d && !d.open) d.addEventListener("toggle", build);
    else build();
    return {
      build: build,
      /** replace the rows (the table rebuilds now if it is visible, else when it is next opened) */
      update: function (rows, text) {
        if (rows) o.rows = rows;
        if (text) {
          if (text.caption) o.caption = text.caption;
          if (text.label) o.label = text.label;
        }
        built = false;
        if (!d || d.open) build();
      },
    };
  };

  /**
   * Ex.navReadout(text) puts a short live answer in the sticky section nav (wide screens only), so it stays in
   * view while the reader scrolls the charts. Pass "" or null to hide it. aria-hidden: the page's own live region says it.
   */
  Ex.navReadout = function (text) {
    var inner = doc.querySelector(".ex-subnav__inner");
    if (!inner) return;
    var el = doc.getElementById("ex-navread");
    if (!el) el = inner.appendChild(Ex.el("p", { class: "ex-navread", id: "ex-navread", "aria-hidden": "true" }));
    el.textContent = text || "";
    el.classList.toggle("is-on", !!text);
  };

  /**
   * Ex.directLabels(g, items, {x, anchor, gap, min, max, cls})
   * Put the label on the mark instead of in a legend. items = [{y, text, x?, cls?}] in the plot's pixel space.
   * Labels are pushed apart to at least `gap` px (default 14) inside [min, max] so none overlap. Returns the d3 selection.
   * Typical use: the end of each line, one label per series, x = plot width + 8, anchor "start".
   */
  Ex.directLabels = function (g, items, o) {
    o = o || {};
    var gap = o.gap || 14;
    var list = items
      .map(function (it, i) {
        return { i: i, y: it.y, it: it };
      })
      .sort(function (a, b) {
        return a.y - b.y;
      });
    var lo = o.min == null ? -Infinity : o.min;
    var hi = o.max == null ? Infinity : o.max;
    list.forEach(function (d, k) {
      d.p = Math.max(d.y, k ? list[k - 1].p + gap : lo);
    });
    for (var k = list.length - 1; k >= 0; k--) {
      if (list[k].p > hi) list[k].p = hi;
      if (k < list.length - 1 && list[k].p > list[k + 1].p - gap) list[k].p = list[k + 1].p - gap;
    }
    return g
      .selectAll(null)
      .data(list)
      .enter()
      .append("text")
      .attr("class", function (d) {
        return "ex-svg-label ex-svg-label--direct " + (d.it.cls || o.cls || "");
      })
      .attr("x", function (d) {
        return d.it.x == null ? o.x || 0 : d.it.x;
      })
      .attr("y", function (d) {
        return d.p;
      })
      .attr("dy", "0.32em")
      .attr("text-anchor", o.anchor || "start")
      .text(function (d) {
        return d.it.text;
      });
  };

  /* ---------- data ---------- */

  var cache = {};
  /**
   * Ex.loadData([url]) -> Promise<object>. With no url it fetches the file named in the page's front matter
   * (`data:`), which the layout puts on <main data-ex-data>. Results are cached.
   */
  Ex.loadData = function (url) {
    url = url || (doc.getElementById("main") || doc.body).getAttribute("data-ex-data");
    if (!url) return Promise.reject(new Error("No data file: set `data:` in the page front matter or pass a url."));
    if (!cache[url]) {
      cache[url] = fetch(url, { credentials: "same-origin" }).then(function (r) {
        if (!r.ok) throw new Error("Could not load " + url + " (" + r.status + ")");
        return r.json();
      });
      cache[url].catch(function () {
        delete cache[url];
      });
    }
    return cache[url];
  };
  /** Replace an element's contents with a plain explanation. Never blank: say what failed. */
  Ex.showError = function (el, msg) {
    el.textContent = "";
    el.appendChild(Ex.el("div", { class: "ex-callout ex-callout--caution", role: "alert" }, [Ex.el("p", { class: "ex-callout__title", text: msg || "This chart did not load. The data table below has the same numbers." })]));
  };

  /* ---------- page chrome: nav offsets, scrollspy ---------- */

  function initChrome() {
    var root = doc.documentElement;
    var nav = doc.getElementById("mainNav");
    var sub = doc.getElementById("ex-subnav");
    var main = doc.getElementById("main");
    if (!sub || !main) return;
    var links = [].slice.call(sub.querySelectorAll("a[href^='#']"));
    var targets = links.map(function (a) {
      return doc.getElementById(a.getAttribute("href").slice(1));
    });
    var scroller = sub.querySelector("ol");
    var current = -1;
    var ticking = false;

    var navEl = sub.querySelector(".ex-subnav__nav");
    function measure() {
      navEl.classList.toggle("is-scrollable", scroller.scrollWidth > scroller.clientWidth + 1);
      if (nav) root.style.setProperty("--ex-nav-h", Math.round(nav.getBoundingClientRect().height) + "px");
      var stuck = global.getComputedStyle(sub).position === "sticky";
      root.style.setProperty("--ex-subnav-h", stuck ? Math.round(sub.getBoundingClientRect().height) + "px" : "0px");
    }
    function update() {
      ticking = false;
      measure();
      var navH = nav ? nav.getBoundingClientRect().height : 0;
      /* a section counts as current once its top passes 40% of the window (but never above the sticky bars) */
      var line = Math.max(navH + sub.getBoundingClientRect().height + 24, global.innerHeight * 0.4);
      var idx = -1;
      targets.forEach(function (t, i) {
        if (!t) return;
        var r = t.getBoundingClientRect();
        if (r.top <= line && r.bottom > line) idx = i;
      });
      if (idx !== current) {
        current = idx;
        links.forEach(function (a, i) {
          if (i === idx) a.setAttribute("aria-current", "location");
          else a.removeAttribute("aria-current");
        });
        if (idx >= 0 && scroller.scrollWidth > scroller.clientWidth) {
          var a = links[idx];
          scroller.scrollTo({ left: a.offsetLeft - (scroller.clientWidth - a.offsetWidth) / 2, behavior: Ex.reducedMotion() ? "auto" : "smooth" });
        }
      }
    }
    function onScroll() {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    }
    global.addEventListener("scroll", onScroll, { passive: true });
    global.addEventListener("resize", onScroll);
    if (nav) nav.addEventListener("transitionend", measure);
    update();
  }

  Ex.ready(function () {
    initChrome();
    [].forEach.call(doc.querySelectorAll("[data-ex-copy], [data-ex-copy-from]"), wireCopy);
  });
})(window);
