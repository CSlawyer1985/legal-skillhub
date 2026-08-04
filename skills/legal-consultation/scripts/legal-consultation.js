/**
 * Legal Consultation
 * 
 * General legal consultation entry point
 */

function consult(input) {
  if (!input || typeof input !== 'string') {
    return {
      error: 'Please describe your legal question or situation',
      result: null
    };
  }

  const text = input.toLowerCase();
  
  // Classify the legal area
  let area = 'general';
  let suggestions = [];
  
  if (text.includes('合同') || text.includes('违约') || text.includes('协议')) {
    area = 'contract';
    suggestions = ['contract-risk-scan', 'clause-redraft'];
  } else if (text.includes('辞退') || text.includes('工资') || text.includes('加班') || text.includes('劳动')) {
    area = 'labor';
    suggestions = ['labor-dispute-check'];
  } else if (text.includes('起诉') || text.includes('被告') || text.includes('官司')) {
    area = 'litigation';
    suggestions = ['complaint-draft', 'defense-draft', 'evidence-organizer'];
  } else if (text.includes('离婚') || text.includes('抚养') || text.includes('继承')) {
    area = 'family';
    suggestions = ['Consult a family law attorney'];
  } else if (text.includes('证据') || text.includes('材料')) {
    area = 'evidence';
    suggestions = ['evidence-organizer'];
  }

  return {
    area: area,
    input: input,
    classification: classifyArea(area),
    suggestions: suggestions,
    disclaimer: 'This is general guidance only. Consult a qualified attorney for specific advice.'
  };
}

function classifyArea(area) {
  const areas = {
    'contract': 'Contract Law - Issues related to agreements and obligations',
    'labor': 'Labor Law - Employment-related matters',
    'litigation': 'Civil Procedure - Dispute resolution and court proceedings',
    'family': 'Family Law - Marriage, divorce, custody, inheritance',
    'evidence': 'Evidence - Document and proof organization',
    'general': 'General Legal Matter - Requires further assessment'
  };
  return areas[area] || areas['general'];
}

module.exports = { consult };