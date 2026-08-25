/* Shared interaction layer: pointer-driven 3D tilt + scroll reveal.
   Kept dependency-free so it runs identically on every page. */
(function () {
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function initTilt() {
    if (reduceMotion) return;
    var els = document.querySelectorAll(".tilt");
    els.forEach(function (el) {
      el.addEventListener("mousemove", function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5;
        var py = (e.clientY - r.top) / r.height - 0.5;
        el.style.setProperty("--rx", (py * -5.5).toFixed(2) + "deg");
        el.style.setProperty("--ry", (px * 7).toFixed(2) + "deg");
        el.style.setProperty("--mx", (px * 100 + 50).toFixed(1) + "%");
        el.style.setProperty("--my", (py * 100 + 50).toFixed(1) + "%");
      });
      el.addEventListener("mouseleave", function () {
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      });
    });
  }

  function initReveal() {
    var els = document.querySelectorAll(".reveal");
    if (!els.length) return;
    if (!("IntersectionObserver" in window) || reduceMotion) {
      els.forEach(function (el) { el.classList.add("in-view"); });
      return;
    }
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry, idx) {
          if (entry.isIntersecting) {
            entry.target.style.transitionDelay = Math.min(idx * 60, 240) + "ms";
            entry.target.classList.add("in-view");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    els.forEach(function (el) { io.observe(el); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTilt();
    initReveal();
  });
})();
