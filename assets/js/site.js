/* ==========================================================================
   TrueNorth Living — site.js
   No dependencies. Everything here is progressive enhancement: if this file
   fails to load, the site still reads, navigates, calls, and submits.
   ========================================================================== */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- Header: scrolled state + mobile nav ------------------------------ */
  function initHeader() {
    var header = document.querySelector(".site-header");
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.querySelector(".nav");
    if (!header) return;

    var onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    // Position the mobile drawer directly under the header, whatever its height.
    var setOffset = function () {
      var r = header.getBoundingClientRect();
      document.documentElement.style.setProperty("--header-offset", r.bottom + "px");
    };
    setOffset();
    window.addEventListener("resize", setOffset);
    window.addEventListener("scroll", setOffset, { passive: true });

    if (!toggle || !nav) return;

    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
      document.body.style.overflow = open ? "hidden" : "";
    };

    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });

    // Close the drawer if the viewport grows past the mobile breakpoint.
    window.matchMedia("(min-width: 901px)").addEventListener("change", function (e) {
      if (e.matches) setOpen(false);
    });
  }

  /* ---- Reveal on scroll ------------------------------------------------- */
  function initReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-in"); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        // Stagger siblings slightly so grids cascade instead of popping.
        var siblings = Array.prototype.slice.call(
          entry.target.parentElement ? entry.target.parentElement.children : []
        );
        var i = Math.max(0, siblings.indexOf(entry.target));
        entry.target.style.transitionDelay = Math.min(i * 70, 350) + "ms";
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.1 });

    items.forEach(function (el) { io.observe(el); });
  }

  /* ---- The Path North --------------------------------------------------- *
   * Draws the amber route line as the section scrolls through the viewport
   * and lights each waypoint as it passes the read line (~62% down screen).
   * ---------------------------------------------------------------------- */
  function initPath() {
    var grid = document.querySelector(".path-grid");
    if (!grid) return;

    var trace = grid.querySelector(".path-trace");
    var steps = Array.prototype.slice.call(grid.querySelectorAll(".path-step"));
    if (!trace || !steps.length) return;

    if (reduceMotion) {
      trace.style.setProperty("--trace", "1");
      steps.forEach(function (s) { s.classList.add("is-lit"); });
      return;
    }

    var ticking = false;

    var update = function () {
      ticking = false;
      var rect = grid.getBoundingClientRect();
      var readLine = window.innerHeight * 0.62;

      // How far the read line has travelled through the grid, clamped 0..1.
      var progress = (readLine - rect.top) / rect.height;
      progress = Math.max(0, Math.min(1, progress));
      trace.style.setProperty("--trace", progress.toFixed(4));

      steps.forEach(function (step) {
        var s = step.getBoundingClientRect();
        step.classList.toggle("is-lit", s.top < readLine);
      });
    };

    var onScroll = function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
  }

  /* ---- Application form ------------------------------------------------- *
   * Posts to Netlify Forms via fetch so the visitor never leaves the page.
   * Falls back to a normal form POST if fetch is unavailable or errors.
   * ---------------------------------------------------------------------- */
  function initForm() {
    var form = document.querySelector("form[data-ajax]");
    if (!form) return;

    var status = document.querySelector(".form-status");
    var submit = form.querySelector('[type="submit"]');
    var successBlock = document.querySelector("[data-success]");

    var say = function (msg, isError) {
      if (!status) return;
      status.hidden = false;
      status.classList.toggle("is-error", !!isError);
      status.textContent = msg;
      status.setAttribute("role", "status");
    };

    form.addEventListener("submit", function (e) {
      if (!window.fetch || !form.reportValidity) return; // let it POST normally
      if (!form.reportValidity()) return;

      e.preventDefault();
      var original = submit ? submit.textContent : "";
      if (submit) { submit.disabled = true; submit.textContent = "Sending…"; }
      say("Sending your application…");

      fetch(form.getAttribute("action") || "/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams(new FormData(form)).toString()
      })
        .then(function (res) {
          if (!res.ok) throw new Error("HTTP " + res.status);
          form.hidden = true;
          if (status) status.hidden = true;
          if (successBlock) {
            successBlock.hidden = false;
            successBlock.setAttribute("tabindex", "-1");
            successBlock.focus();
            successBlock.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
          }
        })
        .catch(function () {
          if (submit) { submit.disabled = false; submit.textContent = original; }
          say(
            "That didn't go through — the internet's fault, not yours. Please call us instead: " +
              (form.dataset.phone || ""),
            true
          );
        });
    });
  }

  /* ---- Mark the current page in the nav --------------------------------- */
  function initCurrentNav() {
    var here = window.location.pathname.replace(/index\.html$/, "");
    if (!here.endsWith("/")) here += "/";
    document.querySelectorAll(".nav a, .footer-grid a").forEach(function (a) {
      var href = a.getAttribute("href") || "";
      if (!href.startsWith("/")) return;
      var target = href.endsWith("/") ? href : href + "/";
      if (target === here) a.setAttribute("aria-current", "page");
    });
  }

  /* ---- Boot ------------------------------------------------------------- */
  var boot = function () {
    initHeader();
    initCurrentNav();
    initReveal();
    initPath();
    initForm();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
