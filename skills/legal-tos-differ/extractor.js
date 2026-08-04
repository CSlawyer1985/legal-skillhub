const cheerio = require('cheerio');

const NOISE_TAGS = ['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript', 'svg', 'form', 'button'];

const NOISE_SELECTOR = NOISE_TAGS.map(t => t).join(', ') +
  ', [role="navigation"], [role="banner"], [role="contentinfo"], [role="complementary"], [role="search"]' +
  ', [class*="nav"], [class*="menu"], [class*="sidebar"], [class*="footer"], [class*="header"]' +
  ', [class*="cookie"], [class*="popup"], [class*="modal"], [class*="banner"]' +
  ', [class*="advertisement"], [class*="social"], [class*="share"], [class*="comment"]' +
  ', [id*="nav"], [id*="menu"], [id*="sidebar"], [id*="footer"], [id*="header"]' +
  ', [id*="cookie"], [id*="popup"]';

const LEGAL_KEYWORDS = [
  'terms', 'conditions', 'agreement', 'service', 'privacy', 'liability',
  'governing law', 'arbitration', 'intellectual property', 'indemnif',
  'warrant', 'disclaimer', 'termination', 'license', 'user agreement',
  'data collection', 'third party', 'third-party', 'class action',
  'jurisdiction', 'confidential', 'cookie', 'consent', 'opt-out',
  'subscription', 'refund', 'payment', 'fee', 'charge'
];

const LEGAL_HINTS = ['terms', 'tos', 'legal', 'agreement', 'policy', 'conditions', 'privacy', 'eula'];

function textDensity(el) {
  const text = el.text().trim();
  const html = el.html() || '';
  if (html.length === 0) return 0;
  return text.length / html.length;
}

function linkDensityPenalty(el) {
  const links = el.find('a');
  if (links.length === 0) return 0;
  const textLen = el.text().trim().length;
  if (textLen === 0) return 1;
  return links.length / textLen;
}

function legalKeywordScore(text) {
  const lower = text.toLowerCase();
  return LEGAL_KEYWORDS.reduce((score, kw) => {
    const matches = lower.split(kw).length - 1;
    return score + matches;
  }, 0);
}

function structuralBonus(el) {
  const tag = el.get(0)?.tagName?.toLowerCase();
  let bonus = 0;
  if (tag === 'main' || tag === 'article') bonus += 2;
  if (tag === 'section') bonus += 1;

  const id = (el.attr('id') || '').toLowerCase();
  const cls = (el.attr('class') || '').toLowerCase();
  const combined = id + ' ' + cls;

  LEGAL_HINTS.forEach(hint => {
    if (combined.includes(hint)) bonus += 3;
  });

  return bonus;
}

function scoreBlock(el) {
  const text = el.text().trim();
  if (text.length < 100) return -1;

  const density = textDensity(el);
  const linkPenalty = linkDensityPenalty(el);
  const keywords = legalKeywordScore(text);
  const structural = structuralBonus(el);

  return (density * 10) + (keywords * 2) - (linkPenalty * 50) + structural;
}

async function extractLegalText(html, url = '') {
  const $ = cheerio.load(html);

  // Pass 1: Remove noise elements
  $(NOISE_SELECTOR).remove();

  // Pass 2: Find best legal content block
  const candidates = $('main, article, section, div, [role="main"]').toArray();
  let bestScore = -Infinity;
  let bestEl = null;

  for (const node of candidates) {
    const el = $(node);
    const score = scoreBlock(el);
    if (score > bestScore) {
      bestScore = score;
      bestEl = el;
    }
  }

  // Fallback: use body if no good candidate found
  if (!bestEl || bestScore < 0) {
    bestEl = $('body');
  }

  const text = bestEl.text()
    .replace(/\s+/g, ' ')
    .replace(/\n\s*\n/g, '\n\n')
    .trim();

  return {
    text,
    metadata: {
      page_title: $('title').text().trim() || '',
      content_length: text.length,
      extraction_method: 'cheerio'
    }
  };
}

module.exports = { extractLegalText };
