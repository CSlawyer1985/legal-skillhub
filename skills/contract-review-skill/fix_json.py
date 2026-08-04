import json
import os

data = {
  "confidentiality": {
    "title": "Missing Confidentiality Clause",
    "description": "Contract lacks explicit confidentiality obligations for protecting proprietary information",
    "pattern": "(confidential|confidentiality|non-disclosure|nda).*?(obligation|duty|responsibility|requirement)|(proprietary|confidential).*?(information|data|knowledge).*?(shall be|must be|is required to be).*?(kept confidential|maintained in confidence)",
    "risk_level": "MEDIUM",
    "suggestion": "Add a standard confidentiality clause defining what information is confidential and obligations to protect it",
    "reference": "Standard Business Practice and Trade Secret Protection Laws"
  },
  "intellectual_property": {
    "title": "Missing Intellectual Property Clause",
    "description": "Contract does not address ownership, licensing, or use of intellectual property",
    "pattern": "(intellectual property|ip|copyright|patent|trademark|trade secret|proprietary).*?(ownership|title|interest|rights|license|usage).*?(retains|retain|remains with|belongs to)|(work product|deliverables|materials).*?(created|developed|produced).*?(shall be|is|are).*?(the exclusive property of|owned by)",
    "risk_level": "MEDIUM",
    "suggestion": "Add IP clause specifying ownership of pre-existing IP, ownership of work product, and license grants",
    "reference": "Copyright Law and Patent Act Principles"
  },
  "payment_terms": {
    "title": "Unclear Payment Terms",
    "description": "Payment amount, schedule, or method is not clearly defined",
    "pattern": "(payment|pay|fee|charge|compensation|remuneration).*?(amount|sum|fee|rate).*?(shall be|is|will be|equals|totals).*?\\$?\\d+(\\.\\d+)?(?:\s*(USD|dollars|RMB|yuan|EUR|euros|GBP|pounds))?|(invoice|bill).*?(submit|send|issue).*?(monthly|quarterly|upon completion|net \\d+)",
    "risk_level": "MEDIUM",
    "suggestion": "Specify exact payment amounts, schedule (e.g., monthly, milestone-based), method, and late payment penalties",
    "reference": "Standard Contract Payment Practices"
  },
  "term_and_termination": {
    "title": "Unclear Term and Termination",
    "description": "Contract duration, renewal terms, or termination conditions are not clearly specified",
    "pattern": "(term|duration).*?(shall be|is|will be|equals).*?\\d+.*?(day|days|week|weeks|month|months|year|years)|(termination|terminate|end|cancel).*?(for cause|without cause|with notice).*?(notice|notification).*?\\d+.*?(day|days|week|weeks|month|months)",
    "risk_level": "MEDIUM",
    "suggestion": "Clearly define initial term, renewal options, termination for cause and without cause procedures, and required notice periods",
    "reference": "Standard Contract Duration and Termination Practices"
  },
  "dispute_resolution": {
    "title": "Missing Dispute Resolution Clause",
    "description": "Contract does not specify how disputes will be resolved (negotiation, mediation, arbitration, litigation)",
    "pattern": "(dispute|disagreement|controversy|claim).*?(resolution|settled|resolved).*?(through|via|by means of).*?(negotiation|mediation|arbitration|litigation|court)|(arbitration).*?(shall be|is|will be).*?(final|binding)|(governing law).*?(shall be|is|will be).*?[A-Z][a-z]+",
    "risk_level": "MEDIUM",
    "suggestion": "Add dispute resolution clause specifying negotiation first, then mediation, then binding arbitration or litigation with specified jurisdiction",
    "reference": "Standard Dispute Resolution Practices and Arbitration Law"
  },
  "force_majeure": {
    "title": "Missing Force Majeure Clause",
    "description": "Contract lacks provision for unforeseen circumstances preventing performance",
    "pattern": "(force majeure|act of god|unforeseeable circumstances|beyond reasonable control).*?(shall excuse|excuses|releases from liability)|(neither party).*?(shall be liable|is responsible).*?(for any failure|for any delay).*?(caused by|due to|resulting from).*?(force majeure|act of god|natural disaster|war|terrorism|government action)",
    "risk_level": "LOW",
    "suggestion": "Add standard force majeure clause covering natural disasters, war, terrorism, government actions, and other uncontrollable events",
    "reference": "Standard Force Majeure Principles and Civil Code Articles"
  },
  "governing_law": {
    "title": "Missing Governing Law Clause",
    "description": "Contract does not specify which jurisdiction's laws will govern interpretation",
    "pattern": "(governing law|this agreement shall be governed by|interpreted in accordance with).*?the laws of.*?[A-Z][a-z]+.*?(state|province|country)|(this agreement).*?(shall be|is|will be).*?(subject to|governed by).*?the laws.*?of",
    "risk_level": "LOW",
    "suggestion": "Specify governing law (e.g., laws of the State of California, Peoples Republic of China) and optionally jurisdiction for disputes",
    "reference": "Standard Choice of Law Principles"
  },
  "entire_agreement": {
    "title": "Missing Entire Agreement Clause",
    "description": "Contract lacks clause stating that the written document constitutes the complete agreement between parties",
    "pattern": "(entire agreement|whole agreement|complete agreement).*?(this agreement|this document|this instrument).*?(constitutes|is|represents).*?(the|the full|the complete).*?(agreement|understanding|arrangement).*?(between|among).*?(the parties|party a and party b)|(supersedes|replaces|cancels).*?(all|any).*?(prior|previous|preceding).*?(agreements|understandings|arrangements|representations).*?(whether|whether oral|whether written)",
    "risk_level": "LOW",
    "suggestion": "Add entire agreement clause to prevent reliance on prior oral or written statements not included in the written contract",
    "reference": "Standard Integration Clause Principles and Parol Evidence Rule"
  }
}

with open('C:/Users/pc/.laosi/skills/contract-review-skill/legal_patterns/required_clauses.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("JSON file written successfully.")