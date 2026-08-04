---
name: SOX Compliance Checker
description: Enterprise-grade Sarbanes-Oxley assessment platform that evaluates organizational compliance with SOX requirements across multiple control domains.
---

# Overview

The SOX Compliance Checker is an enterprise-grade assessment platform designed to evaluate organizational compliance with Sarbanes-Oxley (SOX) requirements. Built for financial institutions, public companies, and their service providers, this tool provides comprehensive compliance evaluation across multiple control sections and assessment tiers.

This platform enables security and compliance teams to systematically assess their SOX control environment, document compliance status across various domains, and generate actionable insights for remediation. The multi-tier assessment approach (basic, standard, enterprise) allows organizations to scale their compliance evaluation from initial scoping through detailed enterprise-wide assessments.

Ideal users include Chief Compliance Officers, Internal Audit teams, IT Security professionals, and managed service providers supporting SOX-regulated organizations who need standardized, repeatable compliance assessment capabilities integrated into their operational workflows.

## Usage

### Sample Request

```json
{
  "tier": "standard",
  "sessionId": "sess_20250117_audit_001",
  "controls": {
    "financial_reporting": [
      {
        "controlId": "FR-001",
        "compliant": true,
        "notes": "Monthly reconciliation process documented and tested"
      },
      {
        "controlId": "FR-002",
        "compliant": false,
        "notes": "Missing evidence of Q3 review sign-off"
      }
    ],
    "it_general_controls": [
      {
        "controlId": "IT-101",
        "compliant": true,
        "notes": "Access reviews performed quarterly"
      },
      {
        "controlId": "IT-102",
        "compliant": true
      }
    ]
  }
}
```

### Sample Response

```json
{
  "assessmentId": "assess_20250117_001",
  "sessionId": "sess_20250117_audit_001",
  "tier": "standard",
  "timestamp": "2025-01-17T14:32:18Z",
  "overallCompliance": 75,
  "sectionResults": {
    "financial_reporting": {
      "compliant": 1,
      "total": 2,
      "compliancePercentage": 50,
      "findings": [
        {
          "controlId": "FR-002",
          "status": "non_compliant",
          "severity": "medium",
          "recommendation": "Obtain missing review evidence for Q3 period"
        }
      ]
    },
    "it_general_controls": {
      "compliant": 2,
      "total": 2,
      "compliancePercentage": 100
    }
  },
  "remediationActions": [
    {
      "priority": "high",
      "action": "Collect and document FR-002 review sign-off",
      "dueDate": "2025-02-14"
    }
  ]
}
```

## Endpoints

### GET /health

**Description:** Health check endpoint to verify service availability.

**Method:** GET

**Path:** `/health`

**Parameters:** None

**Response:**
- **Status:** 200 OK
- **Content-Type:** application/json
- **Schema:** Object (service status information)

---

### POST /api/sox/assess

**Description:** Perform comprehensive SOX compliance assessment across multiple control domains and sections.

**Method:** POST

**Path:** `/api/sox/assess`

**Request Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tier` | string | Yes | Assessment tier level: `basic`, `standard`, or `enterprise` |
| `sessionId` | string | Yes | Unique session identifier for tracking and audit trail purposes |
| `controls` | object | Yes | Controls organized by section; each section contains an array of ControlInput objects |

**ControlInput Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `controlId` | string | Yes | Unique identifier for the control (e.g., "FR-001", "IT-101") |
| `compliant` | boolean | Yes | Compliance status of the control: `true` if compliant, `false` if non-compliant |
| `notes` | string | No | Optional notes or evidence supporting the compliance determination |

**Response:**
- **Status:** 200 OK
- **Content-Type:** application/json
- **Schema:** Assessment result object containing:
  - `assessmentId`: Unique identifier for the assessment
  - `sessionId`: Echo of the request session identifier
  - `tier`: Assessment tier used
  - `timestamp`: ISO 8601 timestamp of assessment
  - `overallCompliance`: Aggregate compliance percentage (0-100)
  - `sectionResults`: Detailed results per control section with compliance counts and findings
  - `remediationActions`: Prioritized list of remediation recommendations

**Error Response (422 Validation Error):**
- **Status:** 422 Unprocessable Entity
- **Content-Type:** application/json
- **Schema:** HTTPValidationError containing validation error details

---

### OPTIONS /api/sox/assess

**Description:** Handle CORS preflight requests for cross-origin assessment submissions.

**Method:** OPTIONS

**Path:** `/api/sox/assess`

**Parameters:** None

**Response:**
- **Status:** 200 OK
- **Content-Type:** application/json

## Pricing

| Plan | Calls/Day | Calls/Month | Price |
|------|-----------|-------------|-------|
| Free | 5 | 50 | Free |
| Developer | 20 | 500 | $39/mo |
| Professional | 200 | 5,000 | $99/mo |
| Enterprise | 100,000 | 1,000,000 | $299/mo |

## About

ToolWeb.in - 200+ security APIs, CISSP & CISM, platforms: Pay-per-run, API Gateway, MCP Server, OpenClaw, RapidAPI, YouTube.

- [toolweb.in](https://toolweb.in)
- [portal.toolweb.in](https://portal.toolweb.in)
- [hub.toolweb.in](https://hub.toolweb.in)
- [toolweb.in/openclaw/](https://toolweb.in/openclaw/)
- [rapidapi.com/user/mkrishna477](https://rapidapi.com/user/mkrishna477)
- [youtube.com/@toolweb-009](https://youtube.com/@toolweb-009)

## References

- **Kong Route:** https://api.mkkpro.com/compliance/sox-compliance
- **API Docs:** https://api.mkkpro.com:8039/docs
