/* legal-meta-skill 专题页：机制说明 + 完整文件包浏览器 */
(function () {
  const ID = "legal-meta-skill";
  const $ = s => document.querySelector(s);
  const HIDDEN_FILES = [
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
    ".gitignore",
  ];
  let files = [];

  function fileLabel(path) {
    return path.includes("/") ? path.slice(path.lastIndexOf("/") + 1) : path;
  }

  function renderTree() {
    const root = $("#meta-file-tree");
    let lastDir = null;
    const html = files.map(path => {
      const dir = path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : ".";
      const dirLine = dir === lastDir ? "" : `<div class="meta-file-dir">${escHtml(dir === "." ? "root/" : dir + "/")}</div>`;
      lastDir = dir;
      return `${dirLine}<button class="meta-file-item" type="button" data-file="${escHtml(path)}" aria-pressed="false"><span>${escHtml(fileLabel(path))}</span><small>${escHtml(path.includes("/") ? path : "SKILL ROOT")}</small></button>`;
    }).join("");
    root.innerHTML = `<div class="meta-file-tree-head">${files.length} FILES · BROWSE</div>${html}`;
    root.querySelectorAll(".meta-file-item").forEach(btn => btn.addEventListener("click", () => openFile(btn.dataset.file)));
  }

  function selectTreeItem(path) {
    document.querySelectorAll(".meta-file-item").forEach(btn => {
      const active = btn.dataset.file === path;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  function renderFile(path, text) {
    const ext = path.split(".").pop().toLowerCase();
    const body = ["md", "markdown"].includes(ext)
      ? `<div class="md meta-file-md">${renderMd(text)}</div>`
      : `<pre>${escHtml(text)}</pre>`;
    $("#meta-file-content").innerHTML = `<div class="meta-file-path">legal-meta-skill/${escHtml(path)}</div>${body}`;
  }

  async function openFile(path) {
    selectTreeItem(path);
    $("#meta-file-content").innerHTML = `<div class="meta-file-loading">读取 ${escHtml(path)} …</div>`;
    try {
      renderFile(path, await fetchSkillFile(`skills/${ID}/${path}`));
    } catch (error) {
      const c = await siteConfig().catch(() => ({ owner: "CSlawyer1985", repo: "legal-skillhub", branch: "main" }));
      const href = `https://github.com/${c.owner}/${c.repo}/blob/${c.branch || "main"}/skills/${ID}/${path}`;
      $("#meta-file-content").innerHTML = `<div class="meta-file-error">文件读取失败：${escHtml(error.message)}<br><a href="${escHtml(href)}" target="_blank" rel="noopener">在 GitHub 上查看 →</a></div>`;
    }
  }

  async function load() {
    try {
      const [fileIndex, skillIndex] = await Promise.all([
        fetch("data/files.json").then(r => r.json()),
        fetch("data/skills.json").then(r => r.json()),
      ]);
      const record = skillIndex.find(item => item.id === ID);
      const indexed = fileIndex[ID] || [];
      files = [...new Set([...indexed, ...HIDDEN_FILES])].sort((a, b) => {
        const dirA = a.includes("/") ? a.slice(0, a.lastIndexOf("/")) : ".";
        const dirB = b.includes("/") ? b.slice(0, b.lastIndexOf("/")) : ".";
        const dirRank = (dirA === "." ? 0 : 1) - (dirB === "." ? 0 : 1);
        return dirRank || dirA.localeCompare(dirB) || a.localeCompare(b);
      });
      renderTree();
      const author = record && record.provenance ? record.provenance.author : "CSlawyer";
      const version = record && record.provenance ? record.provenance.version : "1.0.0";
      $("#meta-file-count").textContent = `${files.length} files · ${author} · ${version}`;
      await openFile(files.includes("SKILL.md") ? "SKILL.md" : files[0]);
    } catch (error) {
      $("#meta-file-tree").innerHTML = `<div class="meta-file-error">文件索引加载失败：${escHtml(error.message)}</div>`;
      $("#meta-file-content").innerHTML = `<div class="meta-file-error">请直接访问 <a href="https://github.com/CSlawyer1985/legal-skillhub/tree/main/skills/${ID}" target="_blank" rel="noopener">GitHub 源码 ↗</a></div>`;
    }
  }

  load();
})();
