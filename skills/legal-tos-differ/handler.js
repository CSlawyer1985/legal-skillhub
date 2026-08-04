const fs = require('fs');
const path = require('path');
const storage = require('./storage');
const extractor = require('./extractor');
const analyzer = require('./analyzer');

const SKILL_DIR = path.resolve(__dirname);

function parseArgs(argv) {
  const args = { command: argv[0] || '', params: {} };
  for (let i = 1; i < argv.length; i++) {
    if (argv[i].startsWith('--') && i + 1 < argv.length) {
      args.params[argv[i].slice(2)] = argv[i + 1];
      i++;
    }
  }
  return args;
}

function getDataDir() {
  const override = process.env.TOS_DATA_DIR;
  return override || SKILL_DIR;
}

async function cmdAdd(params) {
  const url = params.url;
  if (!url) return '**Error:** `--url` is required.';

  const registry = storage.loadRegistry(getDataDir());
  const existing = storage.findEntry(registry, url);
  if (existing) {
    return `Already tracking: **${existing.label}** (${url})\nLast fetched: ${existing.last_fetched_at || 'never'}`;
  }

  registry.tracked_urls.push({
    url,
    label: params.label || url,
    added_at: new Date().toISOString(),
    last_fetched_at: null,
    last_snapshot_file: null,
    snapshot_count: 0
  });
  storage.saveRegistry(registry, getDataDir());

  return `Added to tracking: **${params.label || url}**\nURL: ${url}\nRun \`fetch\` to capture the first snapshot.`;
}

function cmdList() {
  const registry = storage.loadRegistry(getDataDir());
  if (registry.tracked_urls.length === 0) {
    return 'No URLs are currently being tracked.\nUse `add --url <url> --label <name>` to start tracking.';
  }

  const lines = ['## Tracked Documents\n'];
  for (const entry of registry.tracked_urls) {
    const status = entry.last_fetched_at ? `Last fetched: ${entry.last_fetched_at} | Snapshots: ${entry.snapshot_count}` : 'Not yet fetched';
    lines.push(`- **${entry.label}** (${entry.url})\n  ${status}`);
  }
  return lines.join('\n');
}

async function cmdFetch(params) {
  const url = params.url;
  if (!url) return '**Error:** `--url` is required.';

  const registry = storage.loadRegistry(getDataDir());
  const entry = storage.findEntry(registry, url);
  const label = entry ? entry.label : url;

  const fetch = (...args) => import('node-fetch').then(m => m.default(...args));
  let response;
  try {
    response = await fetch(url, {
      headers: { 'User-Agent': 'LegalTOSDiffBot/1.0 (Terms of Service Monitor)' },
      follow: 10,
      timeout: 30000
    });
  } catch (err) {
    return `**Error fetching ${url}:** ${err.message}`;
  }

  if (!response.ok) {
    return `**Error:** HTTP ${response.status} ${response.statusText} for ${url}`;
  }

  const html = await response.text();
  const { text, metadata } = await extractor.extractLegalText(html, url);

  if (text.length < 50) {
    return `**Warning:** Extracted text is very short (${text.length} chars). The page may require JavaScript rendering. URL: ${url}`;
  }

  const result = storage.saveSnapshot(getDataDir(), url, label, text, {
    ...metadata,
    content_type: response.headers.get('content-type') || '',
    http_status: response.status
  });

  return `## Snapshot Saved\n\n- **Document:** ${label}\n- **URL:** ${url}\n- **Text length:** ${text.length.toLocaleString()} characters\n- **File:** ${result.filename}\n- **Hash:** ${result.snapshot.source_hash}`;
}

async function cmdDiff(params) {
  const url = params.url;
  if (!url) return '**Error:** `--url` is required.';

  const registry = storage.loadRegistry(getDataDir());
  const entry = storage.findEntry(registry, url);
  const label = entry ? entry.label : url;

  // Fetch current version
  const fetch = (...args) => import('node-fetch').then(m => m.default(...args));
  let response;
  try {
    response = await fetch(url, {
      headers: { 'User-Agent': 'LegalTOSDiffBot/1.0 (Terms of Service Monitor)' },
      follow: 10,
      timeout: 30000
    });
  } catch (err) {
    return `**Error fetching ${url}:** ${err.message}`;
  }

  if (!response.ok) {
    return `**Error:** HTTP ${response.status} ${response.statusText} for ${url}`;
  }

  const html = await response.text();
  const { text, metadata } = await extractor.extractLegalText(html, url);

  // Load previous snapshot (the one before the latest)
  const oldSnapshot = storage.loadLatestSnapshot(getDataDir(), url);

  // Save new snapshot
  const result = storage.saveSnapshot(getDataDir(), url, label, text, {
    ...metadata,
    content_type: response.headers.get('content-type') || '',
    http_status: response.status
  });

  const newSnapshot = result.snapshot;
  const output = analyzer.buildAnalysisOutput(oldSnapshot, newSnapshot, label);

  const header = `## Legal Document Comparison\n\n- **Document:** ${label}\n- **URL:** ${url}\n- **Previous snapshot:** ${oldSnapshot ? oldSnapshot.fetched_at : 'None (first snapshot)'}\n- **New snapshot:** ${newSnapshot.fetched_at}\n---\n\n`;

  return header + output;
}

function cmdRemove(params) {
  const url = params.url;
  if (!url) return '**Error:** `--url` is required.';

  const removed = storage.removeUrlData(getDataDir(), url);
  if (removed) {
    return `Removed **${url}** and all associated snapshots.`;
  }
  return `**${url}** was not found in the tracked list.`;
}

async function main() {
  const argv = process.argv.slice(2);
  const { command, params } = parseArgs(argv);

  try {
    let output;
    switch (command) {
      case 'add':
        output = await cmdAdd(params);
        break;
      case 'list':
        output = cmdList();
        break;
      case 'fetch':
        output = await cmdFetch(params);
        break;
      case 'diff':
        output = await cmdDiff(params);
        break;
      case 'remove':
        output = cmdRemove(params);
        break;
      default:
        output = `**Unknown command:** \`${command}\`\n\nAvailable commands: \`add\`, \`list\`, \`fetch\`, \`diff\`, \`remove\``;
    }
    console.log(output);
    process.exit(0);
  } catch (err) {
    console.log(`**Error:** ${err.message}`);
    process.exit(1);
  }
}

main();
