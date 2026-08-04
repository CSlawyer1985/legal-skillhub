const prompts = require('./prompts');

function buildAnalysisOutput(oldSnapshot, newSnapshot, label) {
  if (!oldSnapshot) {
    return prompts.buildFirstSnapshotPrompt(newSnapshot.text, label);
  }

  if (oldSnapshot.source_hash === newSnapshot.source_hash) {
    return `**No changes detected** in "${label}".\n\nThe document content is identical to the previous snapshot (${oldSnapshot.fetched_at}).`;
  }

  return prompts.buildUserPrompt(oldSnapshot.text, newSnapshot.text, label);
}

module.exports = { buildAnalysisOutput };
