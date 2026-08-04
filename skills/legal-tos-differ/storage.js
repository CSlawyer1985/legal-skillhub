const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const REGISTRY_FILE = 'registry.json';

function slugify(url) {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/\./g, '-') + parsed.pathname.replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
  } catch {
    return url.replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-');
  }
}

function timestampSlug() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

function computeHash(text) {
  return 'sha256:' + crypto.createHash('sha256').update(text).digest('hex');
}

function dataDir(baseDir) {
  return path.join(baseDir, 'snapshots');
}

function registryPath(baseDir) {
  return path.join(dataDir(baseDir), REGISTRY_FILE);
}

function loadRegistry(baseDir) {
  const dir = dataDir(baseDir);
  const file = registryPath(baseDir);
  if (!fs.existsSync(file)) {
    return { tracked_urls: [] };
  }
  return JSON.parse(fs.readFileSync(file, 'utf-8'));
}

function saveRegistry(registry, baseDir) {
  const dir = dataDir(baseDir);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  const tmp = registryPath(baseDir) + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(registry, null, 2));
  fs.renameSync(tmp, registryPath(baseDir));
}

function findEntry(registry, url) {
  return registry.tracked_urls.find(e => e.url === url);
}

function saveSnapshot(baseDir, url, label, text, metadata = {}) {
  const registry = loadRegistry(baseDir);
  let entry = findEntry(registry, url);

  const hash = computeHash(text);
  const slug = slugify(url);
  const ts = timestampSlug();
  const filename = `${slug}-${ts}.json`;

  const snapshot = {
    url,
    label: label || (entry && entry.label) || url,
    fetched_at: new Date().toISOString(),
    source_hash: hash,
    text_length: text.length,
    extraction_method: 'cheerio',
    metadata,
    text
  };

  const dir = dataDir(baseDir);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(path.join(dir, filename), JSON.stringify(snapshot, null, 2));

  if (entry) {
    entry.last_fetched_at = snapshot.fetched_at;
    entry.last_snapshot_file = filename;
    entry.snapshot_count = (entry.snapshot_count || 0) + 1;
  } else {
    registry.tracked_urls.push({
      url,
      label: label || url,
      added_at: snapshot.fetched_at,
      last_fetched_at: snapshot.fetched_at,
      last_snapshot_file: filename,
      snapshot_count: 1
    });
  }
  saveRegistry(registry, baseDir);
  return { snapshot, filename };
}

function loadLatestSnapshot(baseDir, url) {
  const dir = dataDir(baseDir);
  const slug = slugify(url);
  if (!fs.existsSync(dir)) return null;

  const files = fs.readdirSync(dir)
    .filter(f => f.startsWith(slug) && f.endsWith('.json') && f !== REGISTRY_FILE)
    .sort();

  if (files.length === 0) return null;
  return JSON.parse(fs.readFileSync(path.join(dir, files[files.length - 1]), 'utf-8'));
}

function loadPreviousSnapshot(baseDir, url) {
  const dir = dataDir(baseDir);
  const slug = slugify(url);
  if (!fs.existsSync(dir)) return null;

  const files = fs.readdirSync(dir)
    .filter(f => f.startsWith(slug) && f.endsWith('.json') && f !== REGISTRY_FILE)
    .sort();

  if (files.length < 2) return null;
  return JSON.parse(fs.readFileSync(path.join(dir, files[files.length - 2]), 'utf-8'));
}

function listSnapshotsForUrl(baseDir, url) {
  const dir = dataDir(baseDir);
  const slug = slugify(url);
  if (!fs.existsSync(dir)) return [];

  return fs.readdirSync(dir)
    .filter(f => f.startsWith(slug) && f.endsWith('.json') && f !== REGISTRY_FILE)
    .sort()
    .map(f => {
      const data = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf-8'));
      return { filename: f, fetched_at: data.fetched_at, text_length: data.text_length, source_hash: data.source_hash };
    });
}

function removeUrlData(baseDir, url) {
  const registry = loadRegistry(baseDir);
  const entry = findEntry(registry, url);
  if (!entry) return false;

  const dir = dataDir(baseDir);
  const slug = slugify(url);
  if (fs.existsSync(dir)) {
    fs.readdirSync(dir)
      .filter(f => f.startsWith(slug) && f.endsWith('.json') && f !== REGISTRY_FILE)
      .forEach(f => fs.unlinkSync(path.join(dir, f)));
  }

  registry.tracked_urls = registry.tracked_urls.filter(e => e.url !== url);
  saveRegistry(registry, baseDir);
  return true;
}

module.exports = {
  loadRegistry,
  saveRegistry,
  saveSnapshot,
  loadLatestSnapshot,
  loadPreviousSnapshot,
  listSnapshotsForUrl,
  removeUrlData,
  computeHash,
  findEntry,
  slugify
};
