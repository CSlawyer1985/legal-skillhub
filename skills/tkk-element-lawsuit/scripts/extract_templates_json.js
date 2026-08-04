/**
 * Extract CLAIMS and FACTS template definitions from app.js as JSON.
 * Usage: node extract_templates_json.js
 * Output: JSON containing all case type templates.
 */
const fs = require('fs');
const path = require('path');

// Read app.js
const appJs = fs.readFileSync(
  path.join(__dirname, '..', 'assets', 'js', 'app.js'),
  'utf-8'
);

// We need to evaluate the functions getClaimFields and getFactsFields
// Use a sandbox approach: extract the function bodies and evaluate

// Find all CASE_TYPE_NAMES for the lookup table
const caseTypeNamesMatch = appJs.match(/const CASE_TYPE_NAMES\s*=\s*(\{[\s\S]*?\n\};)/);
let CASE_TYPE_NAMES = {};
if (caseTypeNamesMatch) {
  try {
    CASE_TYPE_NAMES = eval('(' + caseTypeNamesMatch[1].replace(/;$/, '') + ')');
  } catch(e) {
    console.error('Failed to parse CASE_TYPE_NAMES:', e.message);
  }
}

// Extract getClaimFields function body
function extractFunction(source, funcName) {
  const regex = new RegExp(`function ${funcName}\\(typeId\\)\\s*\\{([\\s\\S]*?)\\n\\}`, 'm');
  const match = source.match(regex);
  if (!match) {
    console.error(`Could not find function ${funcName}`);
    return null;
  }
  return match[1];
}

// Build a standalone evaluation context
function getFieldsForType(typeId, claimsBody, factsBody) {
  const CLAIMS = {};
  const FACTS = {};
  
  // Parse CLAIMS
  const claimsMatch = claimsBody.match(/const CLAIMS\s*=\s*(\{[\s\S]*?\n\s*\};)/);
  if (claimsMatch) {
    try {
      Object.assign(CLAIMS, eval('(' + claimsMatch[1].replace(/;\s*$/, '') + ')'));
    } catch(e) {
      console.error('Failed to parse CLAIMS:', e.message);
    }
  }
  
  // Parse FACTS  
  const factsMatch = factsBody.match(/const FACTS\s*=\s*(\{[\s\S]*?\n\s*\};)/);
  if (factsMatch) {
    try {
      Object.assign(FACTS, eval('(' + factsMatch[1].replace(/;\s*$/, '') + ')'));
    } catch(e) {
      console.error('Failed to parse FACTS:', e.message);
    }
  }
  
  return {
    claims: CLAIMS[typeId] || CLAIMS['general'] || [],
    facts: FACTS[typeId] || FACTS['general'] || [],
    typeName: CASE_TYPE_NAMES[typeId] || typeId
  };
}

// Extract the function bodies
const claimsBody = extractFunction(appJs, 'getClaimFields');
const factsBody = extractFunction(appJs, 'getFactsFields');

if (!claimsBody || !factsBody) {
  console.error('Failed to extract function bodies');
  process.exit(1);
}

// Get all known type IDs from CASE_TYPE_NAMES
const allTypeIds = Object.keys(CASE_TYPE_NAMES);

// Build output
const output = {};
for (const typeId of allTypeIds) {
  const fields = getFieldsForType(typeId, claimsBody, factsBody);
  output[typeId] = fields;
}

// Also output the TYPE_ID_TO_NAME_MAP for reference
const result = {
  TYPE_ID_TO_NAME: CASE_TYPE_NAMES,
  TEMPLATES: output
};

console.log(JSON.stringify(result, null, 2));
