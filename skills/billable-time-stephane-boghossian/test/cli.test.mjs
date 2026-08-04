// billable-time — CLI invariant tests.
//
// Run with: node --test test/
// Zero deps. The CLI is executed as a child process so tests verify the
// real surface (exit codes, files written, embedded hashes), not internals.

import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  mkdtempSync,
  writeFileSync,
  readFileSync,
  rmSync,
  existsSync,
} from "node:fs";
import { join, resolve, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CLI = join(REPO_ROOT, "draft-entries.mjs");
const SELF_HASH_SENTINEL = "PENDING_SELF_HASH_REPLACE_AT_RENDER";

function sha256(text) {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

// Build a minimal session JSONL with two cwds, several events tightly
// clustered so they form one substantive on-matter interval, and named
// files that the verb table should pick up.
function buildSessionJsonl(cwd1, cwd2) {
  const events = [
    // On-matter interval — drafted motion, read affidavit. All within 4 min,
    // so well under the default 5-min idle-gap; ~4 min duration with 3 prompts
    // and 3 assistant turns puts it above the trivial threshold.
    {
      timestamp: "2026-05-15T10:00:00.000Z",
      type: "user",
      sessionId: "s1",
      cwd: cwd1,
      message: {
        content:
          "Please draft the motion to dismiss for personal jurisdiction.",
      },
    },
    {
      timestamp: "2026-05-15T10:00:30.000Z",
      type: "assistant",
      sessionId: "s1",
      cwd: cwd1,
      message: {
        content: [
          { type: "text", text: "Drafting now." },
          {
            type: "tool_use",
            name: "Edit",
            input: { file_path: `${cwd1}/motion-to-dismiss.docx` },
          },
        ],
      },
    },
    {
      timestamp: "2026-05-15T10:02:00.000Z",
      type: "user",
      sessionId: "s1",
      cwd: cwd1,
      message: {
        content: "Now read the supporting affidavit and adjust the motion.",
      },
    },
    {
      timestamp: "2026-05-15T10:02:30.000Z",
      type: "assistant",
      sessionId: "s1",
      cwd: cwd1,
      message: {
        content: [
          {
            type: "tool_use",
            name: "Read",
            input: { file_path: `${cwd1}/affidavit-of-jane-doe.pdf` },
          },
          {
            type: "tool_use",
            name: "Write",
            input: { file_path: `${cwd1}/motion-to-dismiss.docx` },
          },
        ],
      },
    },
    {
      timestamp: "2026-05-15T10:04:00.000Z",
      type: "user",
      sessionId: "s1",
      cwd: cwd1,
      message: { content: "Looks good — finalize." },
    },
    {
      timestamp: "2026-05-15T10:04:20.000Z",
      type: "assistant",
      sessionId: "s1",
      cwd: cwd1,
      message: {
        content: [
          {
            type: "tool_use",
            name: "Edit",
            input: { file_path: `${cwd1}/motion-to-dismiss.docx` },
          },
        ],
      },
    },
    // Big idle gap, then off-matter session on cwd2
    {
      timestamp: "2026-05-15T13:00:00.000Z",
      type: "user",
      sessionId: "s2",
      cwd: cwd2,
      message: { content: "Different project work." },
    },
    {
      timestamp: "2026-05-15T13:00:30.000Z",
      type: "assistant",
      sessionId: "s2",
      cwd: cwd2,
      message: { content: [{ type: "tool_use", name: "Bash", input: {} }] },
    },
  ];
  return events.map((e) => JSON.stringify(e)).join("\n");
}

function buildMatterYaml(overrides = {}) {
  const base = {
    matter: {
      id: "TEST-001",
      client: "Test Client",
      caption: "Test Matter",
      jurisdiction: "FL",
      practice_area: "litigation",
    },
    attorney: {
      name: "Jane Doe",
      bar_id: "FL-1234567",
      bar_jurisdiction: "FL",
    },
    billing: { rate_per_hour: 450, minimum_increment_hours: 0.1 },
    ethics: {
      ai_disclosure_required: true,
      disclosure_text: "AI used; reviewed and adopted by attorney of record.",
    },
    routes: [],
  };
  const merged = mergeDeep(base, overrides);
  return serializeYaml(merged);
}

function mergeDeep(a, b) {
  const out = { ...a };
  for (const k of Object.keys(b)) {
    if (
      b[k] &&
      typeof b[k] === "object" &&
      !Array.isArray(b[k]) &&
      a[k] &&
      typeof a[k] === "object"
    ) {
      out[k] = mergeDeep(a[k], b[k]);
    } else {
      out[k] = b[k];
    }
  }
  return out;
}

// Minimal YAML serializer matching the parser's shape (top-level keys, nested
// objects one level deep, arrays of strings).
function serializeYaml(obj, indent = 0) {
  const pad = " ".repeat(indent);
  const lines = [];
  for (const [k, v] of Object.entries(obj)) {
    if (v == null) continue;
    if (Array.isArray(v)) {
      lines.push(`${pad}${k}:`);
      for (const item of v) lines.push(`${pad}  - "${item}"`);
    } else if (typeof v === "object") {
      lines.push(`${pad}${k}:`);
      lines.push(serializeYaml(v, indent + 2));
    } else if (typeof v === "string") {
      lines.push(`${pad}${k}: "${v.replace(/"/g, '\\"')}"`);
    } else {
      lines.push(`${pad}${k}: ${v}`);
    }
  }
  return lines.join("\n");
}

function runCli(extraArgs, { sessionFile, matterFile, outFile }) {
  const args = [
    CLI,
    "--session",
    sessionFile,
    "--matter",
    matterFile,
    "--out",
    outFile,
    "--since",
    "2026-05-15",
    "--until",
    "2026-05-15",
    ...extraArgs,
  ];
  const res = spawnSync("node", args, { encoding: "utf8" });
  return { stdout: res.stdout, stderr: res.stderr, exitCode: res.status };
}

function setup(matterOverrides = {}) {
  const dir = mkdtempSync(join(tmpdir(), "billable-time-test-"));
  const matterDir = join(dir, "matter-a");
  const offMatterDir = join(dir, "other-project");
  const sessionFile = join(dir, "session.jsonl");
  const matterFile = join(dir, "matter.yml");
  const outFile = join(dir, "out", "draft.md");

  // Ensure subdirs exist for cwd validity (the CLI doesn't actually check)
  writeFileSync(sessionFile, buildSessionJsonl(matterDir, offMatterDir));
  const matterYaml = buildMatterYaml({
    routes: [matterDir],
    ...matterOverrides,
  });
  writeFileSync(matterFile, matterYaml);

  return { dir, sessionFile, matterFile, outFile, matterDir, offMatterDir };
}

function cleanup(dir) {
  try {
    rmSync(dir, { recursive: true, force: true });
  } catch {}
}

// ============================================================================
// Invariant 1: chain of evidence — the artifact self-hash is reproducible.
// This is the audit-defense bedrock.
// ============================================================================

test("self-hash is reproducible by stripping and re-hashing", () => {
  const ctx = setup();
  try {
    const res = runCli([], ctx);
    assert.equal(res.exitCode, 0, `CLI exited ${res.exitCode}: ${res.stderr}`);
    assert.ok(existsSync(ctx.outFile), "expected .md output to exist");

    const md = readFileSync(ctx.outFile, "utf8");
    const m = md.match(/Artifact self-hash[^`]*`sha256:([a-f0-9]{64})`/);
    assert.ok(m, "expected an artifact self-hash line in the markdown");
    const embedded = m[1];

    const restored = md.replaceAll(embedded, SELF_HASH_SENTINEL);
    const recomputed = sha256(restored);
    assert.equal(
      recomputed,
      embedded,
      "self-hash must equal sha256 of sentinel-restored document",
    );
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// Invariant 2: --strict refuses broad routes.
// ============================================================================

test("--strict refuses when matter.yml.routes includes the home directory", () => {
  const home = process.env.HOME || process.env.USERPROFILE;
  const ctx = setup({ routes: [home] });
  try {
    const res = runCli(["--strict"], ctx);
    assert.equal(res.exitCode, 3, "expected strict refusal exit code 3");
    assert.match(res.stderr, /STRICT-MODE REFUSAL/);
    assert.match(res.stderr, /Broad route refused/);
  } finally {
    cleanup(ctx.dir);
  }
});

test("--strict refuses when matter.yml.routes includes a 1-2 segment path", () => {
  const ctx = setup({ routes: ["/tmp"] });
  try {
    const res = runCli(["--strict"], ctx);
    assert.equal(res.exitCode, 3);
    assert.match(res.stderr, /too broad/);
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// Invariant 3: --strict refuses missing attorney.
// ============================================================================

test("--strict refuses when matter.attorney.name is missing", () => {
  const ctx = setup({
    attorney: { name: null, bar_id: "F-1", bar_jurisdiction: "FL" },
  });
  try {
    const res = runCli(["--strict"], ctx);
    assert.equal(res.exitCode, 3);
    assert.match(res.stderr, /attorney\.name/);
  } finally {
    cleanup(ctx.dir);
  }
});

test("--strict refuses when matter.attorney.bar_id is missing", () => {
  const ctx = setup({
    attorney: { name: "X", bar_id: null, bar_jurisdiction: "FL" },
  });
  try {
    const res = runCli(["--strict"], ctx);
    assert.equal(res.exitCode, 3);
    assert.match(res.stderr, /attorney\.bar_id/);
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// Invariant 4: --strict refuses missing disclosure when required.
// ============================================================================

test("--strict refuses when ai_disclosure_required and no disclosure_text", () => {
  const ctx = setup({
    ethics: { ai_disclosure_required: true, disclosure_text: null },
  });
  try {
    const res = runCli(["--strict"], ctx);
    assert.equal(res.exitCode, 3);
    assert.match(res.stderr, /AI disclosure is required/);
  } finally {
    cleanup(ctx.dir);
  }
});

test("--strict refuses TODO/placeholder disclosure text", () => {
  const ctx = setup({
    ethics: {
      ai_disclosure_required: true,
      disclosure_text: "TODO: fill in disclosure",
    },
  });
  try {
    const res = runCli(["--strict"], ctx);
    assert.equal(res.exitCode, 3);
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// Invariant 5: privacy default — prompt snippet OFF unless explicitly opted in.
// ============================================================================

test("prompt snippet is OFF by default and prompt text does not appear in narrative", () => {
  const ctx = setup();
  try {
    runCli([], ctx);
    const md = readFileSync(ctx.outFile, "utf8");
    // The fixture prompt contains "personal jurisdiction" — this must NOT
    // appear in the rendered narrative line by default.
    assert.doesNotMatch(
      md,
      /Narrative \(draft, lawyer edits\):[^\n]*personal jurisdiction/,
    );
  } finally {
    cleanup(ctx.dir);
  }
});

test("--include-prompt-snippet ON puts prompt text into the narrative", () => {
  const ctx = setup();
  try {
    runCli(["--include-prompt-snippet"], ctx);
    const md = readFileSync(ctx.outFile, "utf8");
    assert.match(
      md,
      /Narrative \(draft, lawyer edits\):[^\n]*personal jurisdiction/,
    );
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// Invariant 6: chain of evidence — source SHA-256 in output matches real file.
// ============================================================================

test("source JSONL SHA-256 in the artifact matches the actual file hash", () => {
  const ctx = setup();
  try {
    runCli([], ctx);
    const md = readFileSync(ctx.outFile, "utf8");
    const actualHash = createHash("sha256")
      .update(readFileSync(ctx.sessionFile))
      .digest("hex");
    const m = md.match(
      new RegExp(
        `${ctx.sessionFile.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")}[^\\n]*sha256 \`([a-f0-9]{64})\``,
      ),
    );
    assert.ok(m, "expected source-file hash row to mention the fixture path");
    assert.equal(
      m[1],
      actualHash,
      "embedded sha256 must equal actual sha256 of source file",
    );
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// Invariant 7: narrative content layer — filename verb table fires.
// ============================================================================

test("filename verbs fire — motion.docx renders 'drafted and revised motion'", () => {
  const ctx = setup();
  try {
    runCli([], ctx);
    const md = readFileSync(ctx.outFile, "utf8");
    // The Edit + Write on motion-to-dismiss.docx should fire the motion verb.
    assert.match(md, /drafted and revised motion/i);
  } finally {
    cleanup(ctx.dir);
  }
});

test("filename verbs fire — affidavit.pdf Read renders 'reviewed affidavit'", () => {
  const ctx = setup();
  try {
    runCli([], ctx);
    const md = readFileSync(ctx.outFile, "utf8");
    assert.match(md, /reviewed affidavit/i);
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// Audit packet
// ============================================================================

test("default run emits a .audit.html companion", () => {
  const ctx = setup();
  try {
    runCli([], ctx);
    const auditPath = ctx.outFile.replace(/\.md$/, "") + ".audit.html";
    assert.ok(existsSync(auditPath), "expected .audit.html to be written");
    const html = readFileSync(auditPath, "utf8");
    assert.match(html, /<title>Audit packet/);
    assert.match(html, /Attorney signoff/);
    assert.match(html, /Chain of evidence/);
  } finally {
    cleanup(ctx.dir);
  }
});

test("--no-audit-packet skips the HTML companion", () => {
  const ctx = setup();
  try {
    runCli(["--no-audit-packet"], ctx);
    const auditPath = ctx.outFile.replace(/\.md$/, "") + ".audit.html";
    assert.equal(
      existsSync(auditPath),
      false,
      "expected no .audit.html with --no-audit-packet",
    );
  } finally {
    cleanup(ctx.dir);
  }
});

// ============================================================================
// --strict-clean path actually passes when all invariants hold
// ============================================================================

test("--strict passes when routes are narrow, attorney is set, and disclosure_text is set", () => {
  const ctx = setup();
  try {
    const res = runCli(["--strict"], ctx);
    assert.equal(
      res.exitCode,
      0,
      `expected strict-clean exit 0, got ${res.exitCode}: ${res.stderr}`,
    );
    assert.doesNotMatch(res.stderr, /STRICT-MODE REFUSAL/);
  } finally {
    cleanup(ctx.dir);
  }
});
