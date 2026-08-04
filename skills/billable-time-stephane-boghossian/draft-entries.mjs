#!/usr/bin/env node
// billable-time v0.2.0 — draft reviewable time entries from Claude Code session logs.
//
// The tool never bills. It produces an audit-defensible artifact a lawyer
// reviews and signs off on before anything reaches a billing system. This is
// the defense if a bar grievance later asks "show me how you billed
// AI-assisted work."
//
// Chain of evidence:
//   - SHA-256 of each source JSONL embedded in the artifact
//   - SHA-256 of matter.yml embedded
//   - Self-hash of the artifact embedded (verifiable post-edit)
//   - matter.yml snapshot embedded verbatim
//   - Tool version + UTC timestamp + attorney identity stamped
//
// Privacy invariant:
//   - Narratives default to tool-shape + filename-shape verbs (deterministic,
//     content-aware). Verbatim prompt text is OFF by default because Claude
//     Code history is typically shared across many matters.
//
// Usage:
//   node draft-entries.mjs --session <PATH|DIR> --matter <matter.yml> [options]
//
// See --help for the full flag list.

import { readFile, writeFile, readdir, stat, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { resolve, join, dirname, basename, extname } from "node:path";
import { homedir } from "node:os";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

// ---------- constants ----------

const TOOL_NAME = "billable-time";
const TOOL_VERSION = "0.2.0";
const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));

// Sentinel embedded in the artifact body before self-hashing; replaced with
// the real hex hash after sha256 of the rendered document. A verifier strips
// the embedded hash back to this sentinel and re-hashes to confirm.
const SELF_HASH_SENTINEL = "PENDING_SELF_HASH_REPLACE_AT_RENDER";

// File-extension + filename verb table. Deterministic, no LLM. The lawyer
// sees the filename in their own work product — no new information leaks.
const FILENAME_VERBS = [
  // [regex, verb_when_edited, verb_when_read]
  [
    /motion[^/]*\.(docx|doc|pdf)/i,
    "drafted and revised motion",
    "reviewed motion",
  ],
  [
    /oppos(ition|e)[^/]*\.(docx|doc|pdf)/i,
    "drafted opposition",
    "reviewed opposition",
  ],
  [
    /reply[^/]*\.(docx|doc|pdf)/i,
    "drafted reply brief",
    "reviewed reply brief",
  ],
  [
    /(appellate-?)?brief[^/]*\.(docx|doc|pdf)/i,
    "drafted and revised brief",
    "reviewed brief",
  ],
  [
    /memo(randum)?[^/]*\.(docx|doc|pdf)/i,
    "drafted memorandum",
    "reviewed memorandum",
  ],
  [
    /complaint[^/]*\.(docx|doc|pdf)/i,
    "drafted complaint",
    "reviewed complaint",
  ],
  [/answer[^/]*\.(docx|doc|pdf)/i, "drafted answer", "reviewed answer"],
  [
    /(proposed[-_])?order[^/]*\.(docx|doc|pdf)/i,
    "drafted proposed order",
    "reviewed order",
  ],
  [
    /affidavit[^/]*\.(docx|doc|pdf)/i,
    "drafted affidavit",
    "reviewed affidavit",
  ],
  [
    /declaration[^/]*\.(docx|doc|pdf)/i,
    "drafted declaration",
    "reviewed declaration",
  ],
  [
    /discovery[^/]*\.(docx|doc|pdf)/i,
    "prepared discovery",
    "reviewed discovery",
  ],
  [
    /interrogator(y|ies)[^/]*\.(docx|doc|pdf)/i,
    "drafted interrogatories",
    "reviewed interrogatories",
  ],
  [
    /deposition[^/]*\.(docx|doc|pdf|txt)/i,
    "prepared for deposition",
    "reviewed deposition materials",
  ],
  [
    /exhibit[^/]*\.(pdf|docx|doc|jpg|png|tiff)/i,
    "prepared exhibit",
    "reviewed exhibit",
  ],
  [
    /(engagement-?)?letter[^/]*\.(docx|doc|pdf)/i,
    "drafted correspondence",
    "reviewed correspondence",
  ],
  [
    /(contract|agreement)[^/]*\.(docx|doc|pdf)/i,
    "drafted and revised agreement",
    "reviewed agreement",
  ],
  [
    /lease[^/]*\.(docx|doc|pdf)/i,
    "drafted and revised lease",
    "reviewed lease",
  ],
  [
    /(nda|non-?disclosure)[^/]*\.(docx|doc|pdf)/i,
    "drafted NDA",
    "reviewed NDA",
  ],
  [
    /term[-_ ]?sheet[^/]*\.(docx|doc|pdf)/i,
    "drafted term sheet",
    "reviewed term sheet",
  ],
  [/pleading[^/]*\.(docx|doc|pdf)/i, "drafted pleading", "reviewed pleading"],
  [
    /settlement[^/]*\.(docx|doc|pdf)/i,
    "drafted settlement document",
    "reviewed settlement document",
  ],
  [/will[^/]*\.(docx|doc|pdf)/i, "drafted will", "reviewed will"],
  [
    /(power[-_]of[-_]attorney|poa)[^/]*\.(docx|doc|pdf)/i,
    "drafted power of attorney",
    "reviewed power of attorney",
  ],
  [
    /trust[^/]*\.(docx|doc|pdf)/i,
    "drafted trust document",
    "reviewed trust document",
  ],
  [
    /(transcript|hearing)[^/]*\.(pdf|txt|docx)/i,
    "reviewed transcript",
    "reviewed transcript",
  ],
];

// Directory-shape verbs (lower priority than filename matches).
const DIRECTORY_VERBS = [
  [/\/briefs?\//i, "drafted brief"],
  [/\/motions?\//i, "drafted motion"],
  [/\/pleadings?\//i, "prepared pleadings"],
  [/\/exhibits?\//i, "prepared exhibits"],
  [/\/discovery\//i, "prepared discovery"],
  [/\/correspondence\//i, "drafted correspondence"],
  [/\/research\//i, "conducted legal research"],
  [/\/memos?\//i, "drafted memorandum"],
  [/\/contracts?\//i, "drafted and revised agreement"],
  [/\/deposition[s_-]?prep\//i, "prepared for deposition"],
  [/\/trial[s_-]?prep\//i, "prepared for trial"],
];

// ---------- args ----------

function parseArgs(argv) {
  const args = {
    idleGapMin: 5,
    out: "out/draft.md",
    auditPacket: true,
    strict: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    const v = argv[i + 1];
    if (k === "--session") {
      args.session = v;
      i++;
    } else if (k === "--matter") {
      args.matter = v;
      i++;
    } else if (k === "--since") {
      args.since = v;
      i++;
    } else if (k === "--until") {
      args.until = v;
      i++;
    } else if (k === "--idle-gap-min") {
      args.idleGapMin = Number(v);
      i++;
    } else if (k === "--out") {
      args.out = v;
      i++;
    } else if (k === "--out-audit") {
      args.outAudit = v;
      i++;
    } else if (k === "--skill-base") {
      args.skillBase = v;
      i++;
    } else if (k === "--include-prompt-snippet") {
      args.includePromptSnippet = true;
    } else if (k === "--strict") {
      args.strict = true;
    } else if (k === "--no-audit-packet") {
      args.auditPacket = false;
    } else if (k === "--version") {
      args.version = true;
    } else if (k === "--help" || k === "-h") {
      args.help = true;
    }
  }
  return args;
}

function usage() {
  console.log(`${TOOL_NAME} v${TOOL_VERSION} — draft reviewable time entries from Claude Code session logs.

REQUIRED
  --session PATH       JSONL file or directory of JSONL files
  --matter PATH        matter.yml describing the matter to bill against

OPTIONAL
  --since YYYY-MM-DD   inclusive start date (default: 24h ago)
  --until YYYY-MM-DD   inclusive end date   (default: today)
  --idle-gap-min N     minutes of inactivity that close an interval (default: 5)
  --out PATH           output markdown file (default: out/draft.md)
  --out-audit PATH     output audit-packet HTML (default: <out>.audit.html)
  --skill-base PATH    where disclosures/ lives (default: this script's directory)
  --include-prompt-snippet
                       include a short prompt headline in each narrative.
                       OFF by default — prompts from unrelated sessions can
                       leak across matters when Claude history is shared.
  --strict             refuse to generate when audit invariants fail
                       (broad routes, missing disclosure, missing attorney).
                       Use this on the audit-final pass before signing.
  --no-audit-packet    skip the .audit.html output
  --version            print version and exit
  --help, -h           print this help

The output is a markdown artifact + a self-contained printable HTML audit
packet. The lawyer reviews every row. Nothing is auto-billed.`);
}

// ---------- minimal YAML loader for matter.yml + disclosures ----------

function parseYaml(text) {
  const root = {};
  const stack = [{ indent: -1, obj: root, key: null }];
  let arrayCtx = null;
  const lines = text.split(/\r?\n/);
  for (let raw of lines) {
    const line = raw.replace(/\s+#.*$/, "");
    if (!line.trim()) continue;
    if (line.trim().startsWith("#")) continue;
    const indent = line.match(/^(\s*)/)[1].length;
    const trimmed = line.trim();

    if (trimmed.startsWith("- ")) {
      const val = coerce(trimmed.slice(2).trim());
      if (arrayCtx && arrayCtx.indent < indent) {
        arrayCtx.arr.push(val);
        continue;
      }
    }
    arrayCtx = null;

    while (stack.length > 1 && stack[stack.length - 1].indent >= indent)
      stack.pop();
    const top = stack[stack.length - 1].obj;

    const m = trimmed.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!m) continue;
    const key = m[1];
    const valPart = m[2];

    if (valPart === "") {
      top[key] = {};
      const peekIdx = lines.indexOf(raw) + 1;
      const next = lines.slice(peekIdx).find((l) => l.trim());
      if (next && next.trim().startsWith("- ")) {
        top[key] = [];
        arrayCtx = { indent, arr: top[key] };
      } else {
        stack.push({ indent, obj: top[key], key });
      }
    } else {
      top[key] = coerce(valPart);
    }
  }
  return root;
}

function coerce(v) {
  v = v.trim();
  if (/^"(.*)"$/.test(v)) return v.slice(1, -1);
  if (/^'(.*)'$/.test(v)) return v.slice(1, -1);
  if (v === "true") return true;
  if (v === "false") return false;
  if (v === "null") return null;
  if (/^-?\d+(\.\d+)?$/.test(v)) return Number(v);
  return v;
}

// ---------- hashing ----------

function sha256(text) {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

async function hashFile(path) {
  const buf = await readFile(path);
  return createHash("sha256").update(buf).digest("hex");
}

// ---------- session log parsing ----------

async function loadJsonlFiles(sessionArg) {
  const p = resolve(expandHome(sessionArg));
  const s = await stat(p);
  if (s.isFile()) return [p];
  const entries = await readdir(p);
  return entries.filter((f) => f.endsWith(".jsonl")).map((f) => join(p, f));
}

function expandHome(p) {
  if (p.startsWith("~/")) return join(homedir(), p.slice(2));
  return p;
}

function parseJsonlLine(line) {
  try {
    return JSON.parse(line);
  } catch {
    return null;
  }
}

async function extractEventsWithHashes(files) {
  const events = [];
  const fileHashes = [];
  for (const f of files) {
    const buf = await readFile(f);
    fileHashes.push({
      path: f,
      sha256: createHash("sha256").update(buf).digest("hex"),
      bytes: buf.length,
    });
    const text = buf.toString("utf8");
    for (const raw of text.split(/\r?\n/)) {
      if (!raw.trim()) continue;
      const obj = parseJsonlLine(raw);
      if (!obj || !obj.timestamp) continue;
      const ts = new Date(obj.timestamp);
      if (isNaN(+ts)) continue;
      const base = {
        ts,
        sessionId: obj.sessionId,
        cwd: obj.cwd || null,
      };
      if (obj.type === "user" && obj.message?.content) {
        events.push({
          ...base,
          kind: "user_prompt",
          text: extractText(obj.message.content),
        });
      } else if (obj.type === "assistant" && obj.message?.content) {
        const tools = extractTools(obj.message.content);
        events.push({
          ...base,
          kind: "assistant_turn",
          tools: tools.map((t) => t.name),
          fileOps: classifyFileOps(tools),
        });
      }
    }
  }
  events.sort((a, b) => +a.ts - +b.ts);
  return { events, fileHashes };
}

function extractText(content) {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return content
    .filter((c) => c && c.type === "text" && typeof c.text === "string")
    .map((c) => c.text)
    .join("\n")
    .trim();
}

function extractTools(content) {
  if (!Array.isArray(content)) return [];
  return content
    .filter((c) => c && c.type === "tool_use" && c.name)
    .map((c) => ({ name: c.name, input: c.input || {} }));
}

// Returns [{ path, mode: "read" | "write" }]. Distinguishing read vs write
// lets the narrative use "reviewed motion" vs "drafted motion" correctly.
function classifyFileOps(tools) {
  const ops = [];
  for (const t of tools) {
    const fp = t.input?.file_path || t.input?.path;
    if (typeof fp !== "string") continue;
    const writers = new Set(["Edit", "Write", "NotebookEdit"]);
    const readers = new Set(["Read"]);
    const mode = writers.has(t.name)
      ? "write"
      : readers.has(t.name)
        ? "read"
        : null;
    if (mode) ops.push({ path: fp, mode });
  }
  return ops;
}

// ---------- matter routing ----------

function routesFor(matter, matterFilePath) {
  const explicit = (matter.routes || []).map(expandHome).map((p) => resolve(p));
  const fromDir = resolve(dirname(matterFilePath));
  return [...new Set([...explicit, fromDir])];
}

function cwdMatchesMatter(cwd, routes) {
  if (!cwd) return false;
  const c = resolve(cwd);
  return routes.some((r) => c === r || c.startsWith(r + "/"));
}

// Routes are flagged as dangerously broad if they match $HOME, "/", or a
// 1-2 segment path (e.g. /Users/x, /home/x, /tmp). The default mode generates
// with a banner. --strict mode refuses entirely.
function checkRoutes(routes) {
  const warnings = [];
  const home = resolve(homedir());
  for (const r of routes) {
    const segs = r.split("/").filter(Boolean);
    if (r === "/" || r === home || segs.length <= 2) {
      const why =
        r === "/"
          ? "matches your entire filesystem"
          : r === home
            ? "matches your home directory exactly"
            : `is only ${segs.length} path segment(s) deep — too broad`;
      warnings.push({
        route: r,
        message: `Route \`${r}\` ${why}. Every Claude Code session in this window will be treated as on-matter — including work for other clients or non-billable side projects. Narrow \`matter.yml.routes\` to a specific matter directory before relying on this output.`,
      });
    }
  }
  return warnings;
}

// ---------- disclosure pack ----------

const PLACEHOLDER_DISCLOSURE_PATTERNS = [
  /\bTODO\b/i,
  /\[fill\s*in\]/i,
  /\[your.*here\]/i,
  /^\s*$/,
];

async function loadDisclosurePack(skillBase, code) {
  if (!code) return null;
  const path = resolve(skillBase, "disclosures", `${code}.yml`);
  if (!existsSync(path)) {
    return { error: `disclosure pack not found: ${path}` };
  }
  const text = await readFile(path, "utf8");
  const parsed = parseYaml(text);
  return {
    code,
    path,
    sha256: sha256(text),
    rawText: text,
    ...parsed,
  };
}

function disclosureIsPlaceholder(text) {
  if (typeof text !== "string") return true;
  return PLACEHOLDER_DISCLOSURE_PATTERNS.some((re) => re.test(text));
}

// ---------- attorney validation ----------

function validateAttorney(matter) {
  const a = matter.attorney || {};
  const errors = [];
  if (!a.name || typeof a.name !== "string")
    errors.push("matter.yml.attorney.name is required (attorney of record)");
  if (!a.bar_id)
    errors.push(
      "matter.yml.attorney.bar_id is required (bar admission identifier)",
    );
  if (!a.bar_jurisdiction)
    errors.push(
      "matter.yml.attorney.bar_jurisdiction is required (e.g. 'CT', 'NY-State')",
    );
  return errors;
}

// ---------- intervals ----------

function clusterIntervals(events, idleGapMs) {
  const intervals = [];
  let cur = null;
  for (const e of events) {
    if (!cur) {
      cur = newInterval(e);
      continue;
    }
    const gap = +e.ts - +cur.lastTs;
    if (gap > idleGapMs) {
      intervals.push(cur);
      cur = newInterval(e);
    } else {
      addToInterval(cur, e);
    }
  }
  if (cur) intervals.push(cur);
  return intervals;
}

function newInterval(e) {
  const i = {
    start: e.ts,
    end: e.ts,
    lastTs: e.ts,
    sessionId: e.sessionId,
    cwd: e.cwd,
    prompts: [],
    tools: new Map(),
    fileOps: [],
    promptCount: 0,
    turnCount: 0,
  };
  addToInterval(i, e);
  return i;
}

function addToInterval(i, e) {
  i.end = e.ts;
  i.lastTs = e.ts;
  if (!i.cwd && e.cwd) i.cwd = e.cwd;
  if (e.kind === "user_prompt") {
    i.promptCount++;
    if (e.text) i.prompts.push(e.text);
  } else if (e.kind === "assistant_turn") {
    i.turnCount++;
    for (const t of e.tools || []) i.tools.set(t, (i.tools.get(t) || 0) + 1);
    for (const op of e.fileOps || []) i.fileOps.push(op);
  }
}

// ---------- narrative synthesis ----------
// Deterministic, content-aware. Uses filename/directory verbs first, then
// tool-shape verbs as fallback. Verbatim prompt text is OFF by default.

function synthesizeNarrative(interval, opts = {}) {
  const verbs = new Set();

  // Filename-specific verbs win
  for (const op of interval.fileOps) {
    const v = verbFromFile(op.path, op.mode);
    if (v) verbs.add(v);
  }

  // Directory-shape verbs if no filename match
  if (verbs.size === 0) {
    for (const op of interval.fileOps) {
      const v = verbFromDirectory(op.path);
      if (v) verbs.add(v);
    }
  }

  // Tool-shape fallback
  if (verbs.size === 0) {
    const toolNames = [...interval.tools.keys()];
    const has = (n) => toolNames.includes(n);
    if (has("Edit") || has("Write") || has("NotebookEdit"))
      verbs.add("drafted and revised matter-related work product");
    if (has("Read")) verbs.add("reviewed matter-related work product");
    if (has("Grep") || has("Glob") || has("WebSearch"))
      verbs.add("conducted legal research");
    if (has("Bash")) verbs.add("ran analysis on matter-related work product");
    if (verbs.size === 0)
      verbs.add("analyzed and corresponded on matter-related work product");
  }

  const verbList = [...verbs];
  const lead = capitalize(verbList.join("; "));
  const promptHint = opts.includePromptSnippet
    ? headlineFromPrompts(interval.prompts)
    : "";
  const fileHint = describeFiles(uniqFilePaths(interval.fileOps));

  const parts = [`${lead}${promptHint ? ` — ${promptHint}` : ""}.`];
  if (fileHint) parts.push(fileHint);
  parts.push("Reviewed AI-assisted output and adopted as own work product.");
  return parts.join(" ");
}

function verbFromFile(filePath, mode) {
  const name = basename(filePath);
  for (const [re, write, read] of FILENAME_VERBS) {
    if (re.test(name)) return mode === "read" ? read : write;
  }
  return null;
}

function verbFromDirectory(filePath) {
  for (const [re, verb] of DIRECTORY_VERBS) {
    if (re.test(filePath)) return verb;
  }
  return null;
}

function uniqFilePaths(fileOps) {
  const out = new Set();
  for (const op of fileOps) out.add(op.path);
  return [...out];
}

function capitalize(s) {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}

function headlineFromPrompts(prompts) {
  if (!prompts.length) return "";
  const first = prompts.find((p) => p && p.length > 8) || prompts[0];
  const oneLine = first
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const capped = oneLine.length > 100 ? oneLine.slice(0, 97) + "..." : oneLine;
  return capped.replace(/[|]/g, "/");
}

function describeFiles(files) {
  if (!files.length) return "";
  const shown = files
    .slice(0, 3)
    .map((f) => basename(f))
    .join(", ");
  const extra = files.length > 3 ? ` (+${files.length - 3} more)` : "";
  return `Files touched: ${shown}${extra}.`;
}

// ---------- rounding + date helpers ----------

function roundTenth(hours) {
  return Math.round(hours * 10) / 10;
}

function dayBound(s, end = false) {
  if (!s) return null;
  const d = new Date(s + (end ? "T23:59:59.999Z" : "T00:00:00.000Z"));
  return isNaN(+d) ? null : d;
}

function fmt(ts) {
  return new Date(ts)
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d+Z$/, "Z");
}

function fmtFull(ts) {
  return new Date(ts).toISOString();
}

function dur(ms) {
  const m = Math.round(ms / 60000);
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return h > 0 ? `${h}h${mm}m` : `${mm}m`;
}

// ---------- markdown render ----------

function render(ctx) {
  const {
    matter,
    intervals,
    excluded,
    args,
    fileHashes,
    matterHash,
    matterText,
    attorney,
    warnings,
    refusals,
    generatedAt,
    disclosurePack,
    effectiveDisclosure,
  } = ctx;
  const m = matter.matter || {};
  const ethics = matter.ethics || {};
  const billing = matter.billing || {};
  const disclosureRequired = !!ethics.ai_disclosure_required;

  const totalHours = intervals.reduce(
    (acc, i) => acc + roundTenth((+i.end - +i.start) / 3600000),
    0,
  );

  const lines = [];
  lines.push(
    `# Draft time entries — ${m.caption || m.id || "unspecified matter"}`,
  );
  lines.push("");
  lines.push(
    `> Generated by \`${TOOL_NAME}\` v${TOOL_VERSION} on ${fmtFull(generatedAt)}.  **Nothing has been billed.**  Each row below is a proposal. Mark each row \`accept\` / \`edit\` / \`reject\` before exporting to a billing system.`,
  );
  lines.push("");

  if (refusals.length) {
    lines.push(
      "> 🛑 **STRICT-MODE REFUSAL — this artifact MUST NOT be used for billing.**",
    );
    lines.push(
      "> The following invariants failed; fix each one and re-run with `--strict`:",
    );
    for (const r of refusals) lines.push(`> - ${r}`);
    lines.push("");
  }

  if (warnings.length) {
    lines.push(
      "> ⚠️ **Routing warnings — review before treating any row as on-matter:**",
    );
    for (const w of warnings) lines.push(`> - ${w.message}`);
    lines.push("");
  }

  // Matter + attorney + billing identity block
  lines.push("## Matter and attorney of record");
  lines.push("");
  lines.push(`- **Matter:** ${m.id || "—"}`);
  lines.push(`- **Client:** ${m.client || "—"}`);
  lines.push(`- **Caption:** ${m.caption || "—"}`);
  lines.push(`- **Jurisdiction (matter):** ${m.jurisdiction || "—"}`);
  lines.push(`- **Practice area:** ${m.practice_area || "—"}`);
  lines.push(
    `- **Attorney of record:** ${attorney.name || "—"}${attorney.bar_id ? ` (Bar ID ${attorney.bar_id})` : ""}${attorney.bar_jurisdiction ? `, admitted in ${attorney.bar_jurisdiction}` : ""}`,
  );
  lines.push(
    `- **Rate:** ${billing.rate_per_hour ? `$${billing.rate_per_hour}/h` : "—"}  ·  **Minimum increment:** ${billing.minimum_increment_hours || 0.1}h  ·  **Rounding:** nearest 0.1h`,
  );
  lines.push("");

  // Run parameters
  lines.push("## Run parameters");
  lines.push("");
  lines.push(
    `- **Window:** ${args.since || "(default 24h ago)"} → ${args.until || "(today)"}`,
  );
  lines.push(`- **Idle-gap threshold:** ${args.idleGapMin} min`);
  lines.push(`- **Strict mode:** ${args.strict ? "on" : "off"}`);
  lines.push(
    `- **Prompt snippet in narrative:** ${args.includePromptSnippet ? "ON (lawyer enabled)" : "off (default)"}`,
  );
  lines.push(`- **Source files:** ${fileHashes.length}`);
  lines.push(`- **Proposed total:** ${totalHours.toFixed(1)}h`);
  lines.push("");

  // AI disclosure
  lines.push("## AI disclosure");
  lines.push("");
  if (!disclosureRequired) {
    lines.push("- **Required by matter:** no");
  } else {
    lines.push("- **Required by matter:** yes");
    if (disclosurePack && !disclosurePack.error) {
      lines.push(
        `- **Pack:** \`${disclosurePack.code}\`  (jurisdiction: ${disclosurePack.jurisdiction || "—"})`,
      );
      if (disclosurePack.opinion)
        lines.push(
          `- **Opinion:** ${disclosurePack.opinion}${disclosurePack.date ? ` (${disclosurePack.date})` : ""}`,
        );
      if (disclosurePack.source_url)
        lines.push(`- **Source:** ${disclosurePack.source_url}`);
      if (disclosurePack.verified === false)
        lines.push(
          `- **Verification status:** ⚠️ **UNVERIFIED** — confirm against the source opinion before relying on this language.`,
        );
      lines.push(`- **Pack SHA-256:** \`${disclosurePack.sha256}\``);
    }
    if (effectiveDisclosure?.source === "matter") {
      lines.push(
        "- **Active text source:** lawyer override in `matter.yml.ethics.disclosure_text`",
      );
    } else if (effectiveDisclosure?.source === "pack") {
      lines.push("- **Active text source:** pack canonical");
    } else if (effectiveDisclosure?.source === "missing") {
      lines.push(
        "- **Active text source:** ⚠️ **NONE** — disclosure is required but no text was provided.",
      );
    }
    if (effectiveDisclosure?.text) {
      lines.push("- **Active text:**");
      lines.push("");
      lines.push(`  > ${effectiveDisclosure.text}`);
    }
  }
  lines.push("");

  lines.push("---");
  lines.push("");

  if (intervals.length === 0) {
    lines.push(
      "_No on-matter intervals detected in window. See **Excluded** below._",
    );
    lines.push("");
  } else {
    lines.push("## Proposed entries");
    lines.push("");
    intervals.forEach((i, idx) => {
      const hours = roundTenth((+i.end - +i.start) / 3600000);
      const minHours = billing.minimum_increment_hours || 0.1;
      const billable = Math.max(hours, minHours);
      lines.push(
        `### ${String(idx + 1).padStart(2, "0")}. ${fmt(i.start)} → ${fmt(i.end)}  ·  ${dur(+i.end - +i.start)}  ·  **${billable.toFixed(1)}h**`,
      );
      lines.push("");
      lines.push(`- **Status:** \`[ ] accept    [ ] edit    [ ] reject\``);
      lines.push(
        `- **Narrative (draft, lawyer edits):** ${synthesizeNarrative(i, { includePromptSnippet: args.includePromptSnippet })}`,
      );
      if (disclosureRequired && effectiveDisclosure?.text) {
        lines.push(`- **AI disclosure:** ${effectiveDisclosure.text}`);
      }
      lines.push(
        `- **Signals:** ${i.promptCount} prompts · ${i.turnCount} assistant turns · ${i.fileOps.length} file ops · cwd \`${i.cwd || "?"}\``,
      );
      lines.push("");
    });
  }

  lines.push("---");
  lines.push("");
  lines.push("## Excluded (for your review — not billed by default)");
  lines.push("");
  if (excluded.length === 0) {
    lines.push("_Nothing excluded in window._");
  } else {
    for (const x of excluded) lines.push(`- ${x}`);
  }
  lines.push("");

  // Chain of evidence
  lines.push("---");
  lines.push("");
  lines.push("## Chain of evidence");
  lines.push("");
  lines.push(`- **Tool:** ${TOOL_NAME} v${TOOL_VERSION}`);
  lines.push(`- **Generated at (UTC):** ${fmtFull(generatedAt)}`);
  lines.push(`- **matter.yml SHA-256:** \`${matterHash}\``);
  if (disclosurePack && disclosurePack.sha256) {
    lines.push(
      `- **disclosures/${disclosurePack.code}.yml SHA-256:** \`${disclosurePack.sha256}\``,
    );
  }
  lines.push("- **Source session files:**");
  for (const f of fileHashes) {
    lines.push(`  - \`${f.path}\` (${f.bytes} bytes) — sha256 \`${f.sha256}\``);
  }
  lines.push(
    `- **Artifact self-hash (this document):** \`sha256:${SELF_HASH_SENTINEL}\``,
  );
  lines.push("");
  lines.push(
    "Verify the self-hash by replacing the hex value above with the literal string `" +
      SELF_HASH_SENTINEL +
      "` and running `sha256` over the resulting document. The output should match the embedded hash.",
  );
  lines.push("");

  // Embedded matter.yml snapshot
  lines.push("---");
  lines.push("");
  lines.push("## matter.yml (snapshot at generation)");
  lines.push("");
  lines.push("```yaml");
  lines.push(matterText.replace(/\r\n/g, "\n").trimEnd());
  lines.push("```");
  lines.push("");

  // Ethics note
  lines.push("---");
  lines.push("");
  lines.push("## Ethics note");
  lines.push("");
  lines.push(
    "This tool does not bill. It produces a reviewable draft. Time, narrative, and AI-disclosure language are subject to attorney review. The attorney of record is responsible for the final entries submitted to the client and the billing system. The chain-of-evidence section is provided so a reviewer can verify the artifact has not been altered between generation and presentation; it does not constitute legal advice on any specific jurisdiction's rules.",
  );
  lines.push("");

  return lines.join("\n");
}

// ---------- audit packet HTML ----------

function renderAuditPacket(ctx, markdown) {
  const {
    matter,
    attorney,
    generatedAt,
    fileHashes,
    matterHash,
    disclosurePack,
    effectiveDisclosure,
    args,
    warnings,
    refusals,
  } = ctx;
  const m = matter.matter || {};
  const ethics = matter.ethics || {};
  const billing = matter.billing || {};
  const title = `Audit packet — ${m.caption || m.id || "unspecified matter"}`;

  const esc = (s) =>
    String(s ?? "").replace(
      /[&<>]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c],
    );

  // The HTML mirrors the markdown's substantive content but is print-styled
  // and includes a signature block the lawyer fills in with pen on paper.
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>${esc(title)}</title>
<style>
  @page { size: letter; margin: 0.75in; }
  body {
    font: 11pt/1.45 "Times New Roman", Georgia, serif;
    color: #111;
    max-width: 7.5in;
    margin: 0.5in auto;
    padding: 0 0.25in;
  }
  h1 { font-size: 18pt; margin: 0 0 6pt; }
  h2 { font-size: 13pt; margin: 18pt 0 6pt; border-bottom: 1px solid #888; padding-bottom: 3pt; page-break-after: avoid; }
  h3 { font-size: 11pt; margin: 12pt 0 4pt; }
  .meta { font-size: 9.5pt; color: #555; margin: 0 0 12pt; }
  .warn { background: #fff5e6; border-left: 3pt solid #b14a00; padding: 6pt 10pt; margin: 8pt 0; }
  .refuse { background: #fdecec; border-left: 3pt solid #a00; padding: 6pt 10pt; margin: 8pt 0; font-weight: bold; }
  table.kv { border-collapse: collapse; margin: 4pt 0 8pt; width: 100%; font-size: 10pt; }
  table.kv td { padding: 2pt 6pt; vertical-align: top; }
  table.kv td:first-child { font-weight: bold; width: 28%; color: #444; }
  table.evidence { border-collapse: collapse; width: 100%; font-size: 9pt; }
  table.evidence th, table.evidence td { border-bottom: 1px solid #ccc; padding: 3pt 6pt; text-align: left; vertical-align: top; }
  table.evidence th { background: #f4f4f4; }
  code, .mono { font-family: "SF Mono", Menlo, Monaco, Consolas, monospace; font-size: 9pt; word-break: break-all; }
  .entry { margin: 10pt 0; padding: 8pt 10pt; border: 1px solid #ccc; border-radius: 4pt; page-break-inside: avoid; }
  .entry header { display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 4pt; }
  .entry .narr { margin: 4pt 0; }
  .entry .signals { font-size: 9pt; color: #555; }
  .entry .status { font-size: 9.5pt; }
  .entry .status .opt { display: inline-block; min-width: 18pt; border: 1px solid #888; padding: 0 4pt; margin-right: 8pt; text-align: center; }
  .signature {
    margin-top: 24pt;
    padding: 12pt;
    border: 2pt solid #111;
    page-break-inside: avoid;
  }
  .signature .line { display: inline-block; border-bottom: 1pt solid #111; min-width: 2.5in; height: 1.1em; vertical-align: bottom; margin: 0 4pt; }
  pre.matter-yml { background: #f7f7f7; border: 1px solid #ddd; padding: 8pt 10pt; font: 9pt/1.4 "SF Mono", Menlo, Monaco, Consolas, monospace; white-space: pre-wrap; }
  .footer { margin-top: 18pt; font-size: 8.5pt; color: #777; border-top: 1px solid #ccc; padding-top: 6pt; }
  @media print {
    body { margin: 0; }
    .entry, .signature { page-break-inside: avoid; }
  }
</style>
</head>
<body>

<h1>${esc(title)}</h1>
<p class="meta">${esc(TOOL_NAME)} v${esc(TOOL_VERSION)} · generated ${esc(fmtFull(generatedAt))} · ${esc(ctx.intervals.length)} proposed entries · ${esc(ctx.totalHours.toFixed(1))}h proposed</p>

${
  refusals.length
    ? `<div class="refuse">🛑 STRICT-MODE REFUSAL. This artifact MUST NOT be presented as a final billing record. Fix and re-run:
<ul>${refusals.map((r) => `<li>${esc(r)}</li>`).join("")}</ul></div>`
    : ""
}

${
  warnings.length
    ? `<div class="warn">⚠️ Routing warnings — review before treating any row as on-matter:
<ul>${warnings.map((w) => `<li>${esc(w.message)}</li>`).join("")}</ul></div>`
    : ""
}

<h2>Matter and attorney of record</h2>
<table class="kv">
  <tr><td>Matter</td><td>${esc(m.id) || "—"}</td></tr>
  <tr><td>Client</td><td>${esc(m.client) || "—"}</td></tr>
  <tr><td>Caption</td><td>${esc(m.caption) || "—"}</td></tr>
  <tr><td>Jurisdiction (matter)</td><td>${esc(m.jurisdiction) || "—"}</td></tr>
  <tr><td>Practice area</td><td>${esc(m.practice_area) || "—"}</td></tr>
  <tr><td>Attorney of record</td><td>${esc(attorney.name) || "—"}${attorney.bar_id ? ` (Bar ID ${esc(attorney.bar_id)})` : ""}${attorney.bar_jurisdiction ? `, admitted in ${esc(attorney.bar_jurisdiction)}` : ""}</td></tr>
  <tr><td>Rate</td><td>${billing.rate_per_hour ? `$${esc(billing.rate_per_hour)}/h` : "—"} · min increment ${esc(billing.minimum_increment_hours || 0.1)}h · rounding nearest 0.1h</td></tr>
</table>

<h2>AI disclosure</h2>
${
  !ethics.ai_disclosure_required
    ? `<p>Not required for this matter.</p>`
    : `<table class="kv">
      <tr><td>Required by matter</td><td>yes</td></tr>
      ${
        disclosurePack && !disclosurePack.error
          ? `
        <tr><td>Pack</td><td><code>${esc(disclosurePack.code)}</code> · jurisdiction: ${esc(disclosurePack.jurisdiction || "—")}</td></tr>
        ${disclosurePack.opinion ? `<tr><td>Opinion</td><td>${esc(disclosurePack.opinion)}${disclosurePack.date ? ` (${esc(disclosurePack.date)})` : ""}</td></tr>` : ""}
        ${disclosurePack.source_url ? `<tr><td>Source</td><td><a href="${esc(disclosurePack.source_url)}">${esc(disclosurePack.source_url)}</a></td></tr>` : ""}
        ${disclosurePack.verified === false ? `<tr><td>Verification</td><td>⚠️ <strong>UNVERIFIED</strong> — confirm against the source opinion before relying on this language.</td></tr>` : ""}
        <tr><td>Pack SHA-256</td><td><code>${esc(disclosurePack.sha256)}</code></td></tr>
      `
          : ""
      }
      ${
        effectiveDisclosure
          ? `
        <tr><td>Active text source</td><td>${esc(effectiveDisclosure.source === "matter" ? "lawyer override in matter.yml" : effectiveDisclosure.source === "pack" ? "pack canonical" : "⚠️ NONE — disclosure required but no text provided")}</td></tr>
        ${effectiveDisclosure.text ? `<tr><td>Active text</td><td><em>${esc(effectiveDisclosure.text)}</em></td></tr>` : ""}
      `
          : ""
      }
    </table>`
}

<h2>Proposed entries</h2>
${
  ctx.intervals.length === 0
    ? `<p><em>No on-matter intervals detected in window.</em></p>`
    : ctx.intervals
        .map((i, idx) => {
          const hours = roundTenth((+i.end - +i.start) / 3600000);
          const minHours = billing.minimum_increment_hours || 0.1;
          const billable = Math.max(hours, minHours);
          const narrative = synthesizeNarrative(i, {
            includePromptSnippet: args.includePromptSnippet,
          });
          return `<div class="entry">
        <header>
          <span>${String(idx + 1).padStart(2, "0")}. ${esc(fmt(i.start))} → ${esc(fmt(i.end))}</span>
          <span>${esc(dur(+i.end - +i.start))} · <strong>${billable.toFixed(1)}h</strong></span>
        </header>
        <div class="status"><span class="opt">&nbsp;</span>accept &nbsp; <span class="opt">&nbsp;</span>edit &nbsp; <span class="opt">&nbsp;</span>reject</div>
        <div class="narr"><strong>Narrative:</strong> ${esc(narrative)}</div>
        ${ethics.ai_disclosure_required && effectiveDisclosure?.text ? `<div class="narr"><strong>AI disclosure:</strong> <em>${esc(effectiveDisclosure.text)}</em></div>` : ""}
        <div class="signals">${i.promptCount} prompts · ${i.turnCount} assistant turns · ${i.fileOps.length} file ops · cwd <code>${esc(i.cwd || "?")}</code></div>
      </div>`;
        })
        .join("")
}

<h2>Excluded (for review — not billed by default)</h2>
${ctx.excluded.length === 0 ? `<p><em>Nothing excluded in window.</em></p>` : `<ul>${ctx.excluded.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`}

<h2>Chain of evidence</h2>
<table class="kv">
  <tr><td>Tool</td><td>${esc(TOOL_NAME)} v${esc(TOOL_VERSION)}</td></tr>
  <tr><td>Generated at (UTC)</td><td>${esc(fmtFull(generatedAt))}</td></tr>
  <tr><td>matter.yml SHA-256</td><td><code>${esc(matterHash)}</code></td></tr>
  ${disclosurePack && disclosurePack.sha256 ? `<tr><td>disclosures/${esc(disclosurePack.code)}.yml SHA-256</td><td><code>${esc(disclosurePack.sha256)}</code></td></tr>` : ""}
  <tr><td>Companion markdown SHA-256</td><td><code>sha256:${SELF_HASH_SENTINEL}</code></td></tr>
</table>
<h3>Source session files</h3>
<table class="evidence">
  <thead><tr><th>Path</th><th>Bytes</th><th>SHA-256</th></tr></thead>
  <tbody>
    ${fileHashes.map((f) => `<tr><td><code>${esc(f.path)}</code></td><td>${esc(f.bytes)}</td><td><code>${esc(f.sha256)}</code></td></tr>`).join("")}
  </tbody>
</table>

<h2>matter.yml (snapshot at generation)</h2>
<pre class="matter-yml">${esc(ctx.matterText.replace(/\r\n/g, "\n").trimEnd())}</pre>

<div class="signature">
  <h2 style="margin-top:0;">Attorney signoff</h2>
  <p>I, <span class="line">&nbsp;</span> (Bar ID <span class="line" style="min-width:1.5in;">&nbsp;</span>, admitted in <span class="line" style="min-width:1.5in;">&nbsp;</span>), certify that I have reviewed every proposed entry above, marked each as accept / edit / reject, and adopt the accepted entries as my own work product as adjusted for billing the client.</p>
  <p>I further certify that the AI-assistance disclosure above accurately describes the use of generative AI tools in this matter as required by my bar admission, and that I have verified the chain-of-evidence hashes against the source files at the time of signing.</p>
  <p style="margin-top: 16pt;">Signature: <span class="line">&nbsp;</span> &nbsp; Date: <span class="line" style="min-width:1.5in;">&nbsp;</span></p>
</div>

<div class="footer">
  This audit packet is intended as a reviewable artifact for attorney signoff and bar-grievance defense. It does not constitute legal advice on any specific jurisdiction's rules. The deterministic narrative is a starting point; the attorney of record is responsible for the final narrative submitted with the bill.
</div>

</body>
</html>`;
}

// ---------- effective disclosure resolution ----------

function resolveEffectiveDisclosure(matter, pack) {
  const ethics = matter.ethics || {};
  if (!ethics.ai_disclosure_required) return null;
  const inMatter =
    typeof ethics.disclosure_text === "string" && ethics.disclosure_text.trim();
  const inPack =
    pack &&
    !pack.error &&
    typeof pack.canonical_disclosure_text === "string" &&
    pack.canonical_disclosure_text.trim();
  if (inMatter && !disclosureIsPlaceholder(ethics.disclosure_text)) {
    return { source: "matter", text: ethics.disclosure_text.trim() };
  }
  if (inPack && !disclosureIsPlaceholder(pack.canonical_disclosure_text)) {
    return { source: "pack", text: pack.canonical_disclosure_text.trim() };
  }
  return { source: "missing", text: null };
}

// ---------- main ----------

async function main() {
  const args = parseArgs(process.argv);
  if (args.version) {
    console.log(`${TOOL_NAME} v${TOOL_VERSION}`);
    process.exit(0);
  }
  if (args.help || !args.session || !args.matter) {
    usage();
    process.exit(args.help ? 0 : 1);
  }

  const matterPath = resolve(expandHome(args.matter));
  if (!existsSync(matterPath)) {
    console.error(`matter.yml not found: ${matterPath}`);
    process.exit(2);
  }
  const matterText = await readFile(matterPath, "utf8");
  const matterHash = sha256(matterText);
  const matter = parseYaml(matterText);
  const attorney = matter.attorney || {};
  const routes = routesFor(matter, matterPath);
  const routeWarnings = checkRoutes(routes);

  // Disclosure pack
  const skillBase = resolve(expandHome(args.skillBase || SCRIPT_DIR));
  const packCode = matter?.ethics?.disclosure_pack || null;
  const disclosurePack = await loadDisclosurePack(skillBase, packCode);
  const effectiveDisclosure = resolveEffectiveDisclosure(
    matter,
    disclosurePack,
  );

  // Sessions
  const sourceFiles = await loadJsonlFiles(args.session);
  if (sourceFiles.length === 0) {
    console.error(`no .jsonl files at ${args.session}`);
    process.exit(2);
  }

  const since = dayBound(args.since) || new Date(Date.now() - 24 * 3600 * 1000);
  const until = dayBound(args.until, true) || new Date();

  const { events: allEvents, fileHashes } =
    await extractEventsWithHashes(sourceFiles);
  const inWindow = allEvents.filter((e) => e.ts >= since && e.ts <= until);

  const onMatter = inWindow.filter((e) => cwdMatchesMatter(e.cwd, routes));
  const offMatter = inWindow.filter((e) => !cwdMatchesMatter(e.cwd, routes));

  const idleGapMs = args.idleGapMin * 60 * 1000;
  const intervalsAll = clusterIntervals(onMatter, idleGapMs);

  // Exclusions
  const excluded = [];
  const intervals = intervalsAll.filter((i) => {
    const hrs = (+i.end - +i.start) / 3600000;
    if (hrs < 0.05 && i.promptCount <= 1) {
      excluded.push(
        `Trivial interval at ${fmt(i.start)} — ${i.promptCount} prompt, < 0.05h. Skipped (set --idle-gap-min lower if you want these surfaced).`,
      );
      return false;
    }
    return true;
  });

  // Off-matter grouped by cwd, with a concrete fix suggestion per cwd
  const byCwd = new Map();
  for (const e of offMatter) {
    const k = e.cwd || "(no cwd)";
    byCwd.set(k, (byCwd.get(k) || 0) + 1);
  }
  for (const [k, n] of byCwd.entries()) {
    const suggestion =
      k === "(no cwd)"
        ? "session events missing cwd metadata — Claude Code session was likely launched in a context without project-root detection. Cannot route to a matter without an explicit prefix."
        : `if this cwd belongs to this matter, add \`  - "${k}"\` under \`routes:\` in matter.yml and re-run.`;
    excluded.push(`Off-matter cwd \`${k}\` — ${n} events. ${suggestion}`);
  }

  // Long gaps inside the window
  for (let idx = 1; idx < intervals.length; idx++) {
    const gap = +intervals[idx].start - +intervals[idx - 1].end;
    const gapMin = Math.round(gap / 60000);
    if (gapMin >= args.idleGapMin && gapMin >= 30) {
      excluded.push(
        `Idle gap ${gapMin} min between ${fmt(intervals[idx - 1].end)} and ${fmt(intervals[idx].start)} — not billed (over idle threshold of ${args.idleGapMin} min).`,
      );
    }
  }

  // Strict-mode refusal accumulation
  const refusals = [];
  if (args.strict) {
    for (const w of routeWarnings)
      refusals.push(`Broad route refused: ${w.message}`);
    if (matter?.ethics?.ai_disclosure_required) {
      if (!effectiveDisclosure || effectiveDisclosure.source === "missing") {
        refusals.push(
          "AI disclosure is required by this matter but no usable `disclosure_text` was found (matter.yml override or disclosure pack canonical). Set `matter.yml.ethics.disclosure_text` or `matter.yml.ethics.disclosure_pack: <code>`.",
        );
      }
    }
    if (disclosurePack && disclosurePack.error) {
      refusals.push(
        `Disclosure pack reference is invalid: ${disclosurePack.error}`,
      );
    }
    // Pack `verified: false` only refuses if the lawyer is actually relying
    // on the pack canonical (no matter.yml override). A matter-level override
    // is the lawyer's own attestation and bypasses the pack-verification gate.
    if (
      disclosurePack &&
      disclosurePack.verified === false &&
      effectiveDisclosure?.source === "pack"
    ) {
      refusals.push(
        `Disclosure pack \`${disclosurePack.code}\` is marked \`verified: false\` and is the active disclosure source — verify the canonical text against the source opinion and flip \`verified: true\` in the pack file (with your bar ID in \`verified_by\`), or override with \`matter.yml.ethics.disclosure_text\`.`,
      );
    }
    for (const e of validateAttorney(matter)) refusals.push(e);
    // Empty artifact is a valid strict outcome — the lawyer may have been
    // off-matter that day. The artifact says so plainly; no refusal needed.
  }

  const generatedAt = new Date();

  const totalHours = intervals.reduce(
    (acc, i) => acc + roundTenth((+i.end - +i.start) / 3600000),
    0,
  );

  const ctx = {
    matter,
    intervals,
    excluded,
    args,
    fileHashes,
    matterHash,
    matterText,
    attorney,
    warnings: routeWarnings,
    refusals,
    generatedAt,
    disclosurePack,
    effectiveDisclosure,
    totalHours,
  };

  const mdWithPending = render(ctx);
  const realHash = sha256(mdWithPending);
  const md = mdWithPending.replaceAll(SELF_HASH_SENTINEL, realHash);

  const outPath = resolve(expandHome(args.out));
  await mkdir(dirname(outPath), { recursive: true });
  await writeFile(outPath, md, "utf8");

  let auditPath = null;
  if (args.auditPacket) {
    const htmlWithPending = renderAuditPacket(ctx, md);
    const html = htmlWithPending.replaceAll(SELF_HASH_SENTINEL, realHash);
    auditPath = resolve(
      expandHome(args.outAudit || outPath.replace(/\.md$/, "") + ".audit.html"),
    );
    if (auditPath === outPath) auditPath = outPath + ".audit.html";
    await mkdir(dirname(auditPath), { recursive: true });
    await writeFile(auditPath, html, "utf8");
  }

  // stdout summary
  console.log(`wrote ${outPath}`);
  if (auditPath) console.log(`wrote ${auditPath}`);
  console.log(
    `intervals: ${intervals.length}  ·  on-matter events: ${onMatter.length}  ·  off-matter events: ${offMatter.length}  ·  self-hash: ${realHash.slice(0, 12)}…`,
  );
  if (refusals.length) {
    console.error("");
    console.error(
      `STRICT-MODE REFUSAL — ${refusals.length} invariant(s) failed:`,
    );
    for (const r of refusals) console.error(`  - ${r}`);
    process.exit(3);
  }
}

main().catch((e) => {
  console.error(e.stack || e.message);
  process.exit(1);
});
