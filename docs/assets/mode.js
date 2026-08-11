/* Legal SkillHub — ink/paper 模式初始化（须在 <head> 同步加载，渲染前设置 data-mode 防闪烁） */
(function () {
  var mode = "ink";
  try {
    var saved = localStorage.getItem("lsh-mode");
    if (saved === "ink" || saved === "paper") mode = saved;
  } catch (e) {}
  document.documentElement.setAttribute("data-mode", mode);

  window.LSH_MODE = {
    get: function () { return document.documentElement.getAttribute("data-mode") || "ink"; },
    set: function (m) {
      document.documentElement.setAttribute("data-mode", m);
      try { localStorage.setItem("lsh-mode", m); } catch (e) {}
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", m === "paper" ? "#eff1f5" : "#11111b");
      document.querySelectorAll(".mode-toggle button").forEach(function (b) {
        b.setAttribute("aria-pressed", b.getAttribute("data-ground") === m ? "true" : "false");
      });
    },
    toggle: function () { this.set(this.get() === "paper" ? "ink" : "paper"); }
  };
})();
