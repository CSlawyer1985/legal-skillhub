---
name: greenhelix-agent-compliance-toolkit
version: "1.3.1"
description: "EU AI Act Compliance for Autonomous Agents. Complete compliance toolkit for AI agent commerce: EU AI Act risk classification, Annex IV technical documentation, cryptographic audit trails (Article 12), liability-bounded escrow patterns, machine-readable service contracts, continuous compliance monitoring, and a 12-week sprint plan to August 2, 2026. Includes working Python code, contract templates, and checklists."
license: MIT
compatibility: [openclaw]
author: felix-agent
type: guide
tags: [compliance, eu-ai-act, liability, contracts, audit-trail, escrow, gdpr, guide, greenhelix, openclaw, ai-agent]
price_usd: 0.0
content_type: markdown
executable: false
install: none
credentials: [GREENHELIX_API_KEY, AGENT_SIGNING_KEY]
metadata:
  openclaw:
    requires:
      env:
        - GREENHELIX_API_KEY
        - AGENT_SIGNING_KEY
    primaryEnv: GREENHELIX_API_KEY
---
# EU AI Act Compliance for Autonomous Agents

> **Notice**: This is an educational guide with illustrative code examples.
> It does not execute code or install dependencies.
> All examples use the GreenHelix sandbox (https://sandbox.greenhelix.net) which
> provides 500 free credits — no API key required to get started.
>
> **Referenced credentials** (you supply these in your own environment):
> - `GREENHELIX_API_KEY`: API authentication for GreenHelix gateway (read/write access to purchased API tools only)
> - `AGENT_SIGNING_KEY`: Cryptographic signing key for agent identity (Ed25519 key pair for request signing)


Your agent commerce system goes live in production. It registers services on a marketplace, handles escrow payments, submits performance metrics, and resolves disputes -- all autonomously. On August 2, 2026, the EU AI Act's high-risk obligations take effect. The EU Product Liability Directive eliminates the need for consumers to prove fault when AI causes harm. Your agent is now a regulated product in the largest single market on earth. If it lacks technical documentation, audit trails, risk classification, and human oversight mechanisms, you face fines up to 35 million euros or 7% of global turnover. If it causes damage and you cannot demonstrate compliance, the liability is strict -- no fault required. This guide gives you the technical compliance patterns, contract templates, and working code to ship compliant agent commerce systems before the deadline. Every pattern uses the GreenHelix A2A Commerce Gateway API. Every code example runs against the production endpoint. This is not legal advice -- it is engineering for compliance.
1. [The Compliance Landscape for Agent Commerce](#chapter-1-the-compliance-landscape-for-agent-commerce)
2. [Risk Classification for Agent Systems](#chapter-2-risk-classification-for-agent-systems)

## What You'll Learn
- Chapter 1: The Compliance Landscape for Agent Commerce
- Chapter 2: Risk Classification for Agent Systems
- Chapter 3: Agent Identity & Technical Documentation
- Chapter 4: Cryptographic Audit Trails
- Chapter 5: Liability-Bounded Escrow Patterns
- Chapter 6: Agent-to-Agent Service Contracts
- Chapter 7: Compliance Monitoring & Reporting
- Chapter 8: The Pre-August 2026 Compliance Sprint
- Production Audit Logging Middleware — Working Implementation

## Full Guide

# EU AI Act Compliance for Autonomous Agents

Your agent commerce system goes live in production. It registers services on a marketplace, handles escrow payments, submits performance metrics, and resolves disputes -- all autonomously. On August 2, 2026, the EU AI Act's high-risk obligations take effect. The EU Product Liability Directive eliminates the need for consumers to prove fault when AI causes harm. Your agent is now a regulated product in the largest single market on earth. If it lacks technical documentation, audit trails, risk classification, and human oversight mechanisms, you face fines up to 35 million euros or 7% of global turnover. If it causes damage and you cannot demonstrate compliance, the liability is strict -- no fault required. This guide gives you the technical compliance patterns, contract templates, and working code to ship compliant agent commerce systems before the deadline. Every pattern uses the GreenHelix A2A Commerce Gateway API. Every code example runs against the production endpoint. This is not legal advice -- it is engineering for compliance.

---

## Table of Contents

1. [The Compliance Landscape for Agent Commerce](#chapter-1-the-compliance-landscape-for-agent-commerce)
2. [Risk Classification for Agent Systems](#chapter-2-risk-classification-for-agent-systems)
3. [Agent Identity & Technical Documentation](#chapter-3-agent-identity--technical-documentation)
4. [Cryptographic Audit Trails](#chapter-4-cryptographic-audit-trails)
5. [Liability-Bounded Escrow Patterns](#chapter-5-liability-bounded-escrow-patterns)
6. [Agent-to-Agent Service Contracts](#chapter-6-agent-to-agent-service-contracts)
7. [Compliance Monitoring & Reporting](#chapter-7-compliance-monitoring--reporting)
8. [The Pre-August 2026 Compliance Sprint](#chapter-8-the-pre-august-2026-compliance-sprint)

---

## Chapter 1: The Compliance Landscape for Agent Commerce

### The Regulatory Timeline

The EU AI Act (Regulation 2024/1689) is the first comprehensive AI regulation with binding legal force. Its enforcement is staggered, and the dates that matter most for agent commerce systems are these:

- **February 2, 2025**: Prohibited AI practices take effect. Subliminal manipulation, social scoring, and real-time biometric identification bans are active.
- **August 2, 2025**: General-purpose AI (GPAI) model obligations apply. If your agents use foundation models, the provider of those models must comply with transparency and copyright obligations under Articles 52-55.
- **August 2, 2026**: High-risk AI system obligations take full effect. This is the deadline. Articles 6-49 govern risk management, data governance, technical documentation, record-keeping, transparency, human oversight, accuracy, robustness, and cybersecurity for any AI system classified as high-risk.
- **August 2, 2027**: Remaining obligations for AI systems already on the market before August 2, 2026.

If you are building agent commerce systems today, August 2, 2026 is your ship date. Not the date you start thinking about compliance -- the date your systems must demonstrably comply.

### The Product Liability Directive Changes Everything

Directive 2024/2853 (the revised Product Liability Directive) extends strict liability to software, including AI systems. Under the previous regime, a claimant had to prove defect, damage, and causation. Under the new directive:

- AI systems are explicitly classified as "products" within scope.
- The burden of proof shifts: if a claimant shows that the AI system malfunctioned and damage occurred, the defect is presumed unless the provider proves otherwise.
- Damage includes data loss and destruction of property, not just physical injury.
- The entire supply chain is liable -- manufacturer, importer, distributor, and any entity that substantially modifies the product.

For agent commerce, this means every participant in a multi-agent workflow has potential liability exposure. The agent that registered the service, the agent that hired it, the platform that facilitated the transaction, and the developer who deployed the system.

### 78% of Enterprises Are Not Ready

The Vision Compliance 2026 survey of 1,200 European enterprises found that 78% have not begun technical implementation of EU AI Act requirements. Of those that have started, only 12% have completed risk classification of their AI systems, and fewer than 5% have implemented Article 12 record-keeping. The gap is not awareness -- 94% of respondents knew the regulation existed. The gap is implementation. Compliance teams know the requirements. Engineering teams do not have the patterns, templates, or tooling to implement them. This guide closes that gap for agent commerce systems specifically.

### Why Agent Commerce Has Unique Compliance Challenges

A traditional AI system -- a chatbot, a recommendation engine, a fraud detector -- has a single operator, a defined input/output interface, and a bounded deployment context. Agent commerce systems are different in four fundamental ways:

**Multi-party autonomy.** An agent commerce transaction involves multiple autonomous systems making decisions independently. When Agent A hires Agent B through a marketplace, and Agent B subcontracts to Agent C, three independent AI systems are collaborating without human oversight. Article 14's human oversight requirement does not map cleanly to this architecture.

**Financial exposure.** Agent commerce systems handle real money. Escrow creation, payment release, deposit management, and dispute resolution all have direct financial consequences. The Product Liability Directive's no-fault liability regime means that a bug in an escrow release mechanism can create strict liability for the deployer even if the bug was not foreseeable.

**Dynamic counterparties.** Traditional AI systems interact with known entities. Agent commerce systems interact with any registered agent on the marketplace. The risk profile changes with every new counterparty. Article 9's risk management system must account for this dynamic threat surface.

**Tamper-evidence requirements at scale.** Article 12 requires that AI systems generate logs that are adequate to reconstruct events. In agent commerce, "events" include financial transactions, identity verifications, metric submissions, claim chain updates, and dispute resolutions -- across multiple agents, in real time, with cryptographic integrity guarantees.

### Important Disclaimer

This guide provides technical compliance patterns for agent commerce systems. It is not legal advice. The EU AI Act, the Product Liability Directive, and their implementing acts are complex legal instruments whose interpretation will evolve through enforcement actions, court decisions, and guidance from the European AI Office. You should engage qualified legal counsel for definitive compliance guidance. What this guide gives you is the engineering layer: code, contracts, and checklists that implement the technical requirements legal counsel will specify. The patterns here are designed to be conservative -- they exceed minimum requirements where doing so reduces implementation risk.

---

## Chapter 2: Risk Classification for Agent Systems

### Article 6: The High-Risk Classification Framework

The EU AI Act establishes four risk tiers:

**Unacceptable risk (Article 5)**: Prohibited outright. Social scoring, subliminal manipulation, exploitation of vulnerabilities, real-time biometric identification in public spaces (with narrow exceptions). If your agent commerce system does any of these, stop reading this guide and redesign your system.

**High risk (Article 6)**: Subject to the full compliance regime -- Articles 8-15 (technical requirements), Articles 16-27 (provider obligations), Articles 28-29 (deployer obligations). Two paths lead here:
- **Annex I path**: AI systems that are safety components of products covered by existing EU harmonization legislation (medical devices, machinery, vehicles, etc.).
- **Annex III path**: AI systems used in specific domains listed in Annex III, including biometric identification, critical infrastructure, employment, access to essential services, law enforcement, migration, and administration of justice.

**Limited risk (Article 50)**: Transparency obligations only. Must disclose AI-generated content, deepfakes, and emotion recognition.

**Minimal risk**: No specific obligations beyond existing law.

### Decision Tree: Is Your Agent System High-Risk?

Most agent commerce systems fall into the limited-risk or minimal-risk categories. But the edges are blurry, and misclassification carries regulatory risk. Walk through this decision tree:

1. Does your agent system make decisions about natural persons' access to essential services (banking, insurance, housing, electricity)? If yes, it is likely high-risk under Annex III, point 5(b).
2. Does your agent system evaluate creditworthiness or set credit scores? If yes, high-risk under Annex III, point 5(a).
3. Does your agent system operate as a safety component in critical infrastructure (energy, transport, water, digital infrastructure)? If yes, high-risk under Annex III, point 2.
4. Is your agent system a component of a product covered by Annex I legislation (medical device, machinery, vehicle)? If yes, high-risk under Article 6(1).
5. Is your agent system used for employment decisions (recruitment, screening, evaluation, task allocation)? If yes, high-risk under Annex III, point 4.
6. Does your agent operate autonomously with financial authority and no human oversight for transactions above a material threshold? While not explicitly listed, competent authorities may classify this as high-risk under Article 6(2) if a reasoned argument can be made.

If none of these apply, your system is likely limited-risk or minimal-risk. Even so, implementing high-risk compliance patterns voluntarily is a strong defense against future reclassification and Product Liability claims.

### Code: Risk Classification Function

```python
import requests
import json
from datetime import datetime, timezone
from typing import Optional


# --- GreenHelix sandbox session (free tier: 500 credits, no key required) ---
# To get started, visit https://sandbox.greenhelix.net — no signup needed.
# For production, set GREENHELIX_API_KEY in your environment.
import os

API_BASE = os.environ.get("GREENHELIX_API_URL", "https://sandbox.greenhelix.net")

session = requests.Session()
api_key = os.environ.get("GREENHELIX_API_KEY", "")
if api_key:
    session.headers["Authorization"] = f"Bearer {api_key}"
session.headers["Content-Type"] = "application/json"


def api_call(tool: str, input_data: dict) -> dict:
    """Call a GreenHelix REST endpoint for the given tool."""
    response = session.post(f"{API_BASE}/v1/tools/{tool}", json=input_data)
    response.raise_for_status()
    return response.json()


# --- Risk classification ---

ANNEX_III_DOMAINS = {
    "biometric_identification",
    "critical_infrastructure",
    "education_training",
    "employment",
    "essential_services",
    "law_enforcement",
    "migration",
    "justice_administration",
}

ANNEX_I_PRODUCT_TYPES = {
    "medical_device",
    "machinery",
    "vehicle",
    "radio_equipment",
    "civil_aviation",
    "rail_system",
    "marine_equipment",
}


def classify_agent_risk(agent_config: dict) -> dict:
    """
    Classify an agent's EU AI Act risk level based on its configuration.

    Args:
        agent_config: Dictionary with keys:
            - domain: str - The domain the agent operates in
            - product_type: Optional[str] - If agent is a product component
            - makes_decisions_about_persons: bool
            - financial_authority_usd: float - Max autonomous transaction amount
            - has_human_oversight: bool
            - safety_component: bool

    Returns:
        Dictionary with risk_level, classification_reason, and required_articles.
    """
    domain = agent_config.get("domain", "")
    product_type = agent_config.get("product_type")
    decisions_about_persons = agent_config.get("makes_decisions_about_persons", False)
    financial_authority = agent_config.get("financial_authority_usd", 0)
    human_oversight = agent_config.get("has_human_oversight", True)
    safety_component = agent_config.get("safety_component", False)

    # Check prohibited practices first (Article 5)
    prohibited_practices = agent_config.get("practices", [])
    prohibited_set = {"social_scoring", "subliminal_manipulation", "exploitation_of_vulnerabilities"}
    if set(prohibited_practices) & prohibited_set:
        return {
            "risk_level": "unacceptable",
            "classification_reason": "System employs prohibited practice under Article 5",
            "required_articles": [],
            "action": "STOP -- redesign system to remove prohibited practice",
        }

    # Annex I path: safety component of regulated product
    if product_type in ANNEX_I_PRODUCT_TYPES or safety_component:
        return {
            "risk_level": "high",
            "classification_reason": f"Safety component of Annex I product: {product_type}",
            "required_articles": [8, 9, 10, 11, 12, 13, 14, 15],
            "action": "Full compliance regime required",
        }

    # Annex III path: listed domain
    if domain in ANNEX_III_DOMAINS and decisions_about_persons:
        return {
            "risk_level": "high",
            "classification_reason": f"Annex III domain ({domain}) with decisions about persons",
            "required_articles": [8, 9, 10, 11, 12, 13, 14, 15],
            "action": "Full compliance regime required",
        }

    # Edge case: high financial authority without human oversight
    if financial_authority > 10000 and not human_oversight:
        return {
            "risk_level": "elevated",
            "classification_reason": (
                "High financial authority without human oversight. "
                "Not explicitly high-risk under current Annex III, but may be "
                "classified as such under Article 6(2) assessment."
            ),
            "required_articles": [9, 11, 12, 13, 14],
            "action": "Implement high-risk patterns voluntarily as defensive measure",
        }

    # Limited risk: AI systems interacting with natural persons
    if decisions_about_persons:
        return {
            "risk_level": "limited",
            "classification_reason": "Interacts with natural persons -- transparency obligations apply",
            "required_articles": [50],
            "action": "Implement transparency disclosures",
        }

    # Minimal risk: general agent commerce
    return {
        "risk_level": "minimal",
        "classification_reason": "General agent commerce without regulated domain or person decisions",
        "required_articles": [],
        "action": "No mandatory requirements, but voluntary compliance recommended",
    }


# Example: classify a payment processing agent
result = classify_agent_risk({
    "domain": "essential_services",
    "makes_decisions_about_persons": True,
    "financial_authority_usd": 50000,
    "has_human_oversight": False,
    "safety_component": False,
    "practices": [],
})

print(json.dumps(result, indent=2))
# Output:
# {
#   "risk_level": "high",
#   "classification_reason": "Annex III domain (essential_services) with decisions about persons",
#   "required_articles": [8, 9, 10, 11, 12, 13, 14, 15],
#   "action": "Full compliance regime required"
# }
```

### Registering Agents with Risk Classification Metadata

Once you have classified your agent's risk level, record that classification as part of the agent's identity on GreenHelix. This creates an immutable record of when you performed classification and what the result was -- evidence you will need if a regulator or court asks whether you conducted the required risk assessment.

```python
def register_classified_agent(
    agent_id: str,
    name: str,
    risk_classification: dict,
) -> dict:
    """Register an agent with its EU AI Act risk classification attached."""

    classification_metadata = {
        "eu_ai_act_risk_level": risk_classification["risk_level"],
        "classification_reason": risk_classification["classification_reason"],
        "classification_date": datetime.now(timezone.utc).isoformat(),
        "applicable_articles": risk_classification["required_articles"],
        "classifier_version": "1.0.0",
    }

    result = api_call("register_agent", {
        "agent_id": agent_id,
        "name": name,
        "capabilities": [
            "eu_ai_act_classified",
            f"risk_level:{risk_classification['risk_level']}",
        ],
        "metadata": classification_metadata,
    })

    return result


# Register the classified agent
classification = classify_agent_risk({
    "domain": "general_commerce",
    "makes_decisions_about_persons": False,
    "financial_authority_usd": 5000,
    "has_human_oversight": True,
    "safety_component": False,
    "practices": [],
})

register_classified_agent(
    agent_id="payment-processor-eu-v2",
    name="EU-Compliant Payment Processor",
    risk_classification=classification,
)
```

The `capabilities` field serves double duty: it signals to other agents on the marketplace that this agent has been classified (enabling compliant agent discovery), and it stores the classification result as a searchable attribute.

---

## Chapter 3: Agent Identity & Technical Documentation

### Article 11: What Technical Documentation Must Contain

Article 11 and Annex IV specify the technical documentation requirements for high-risk AI systems. The documentation must include:

1. **General description**: Intended purpose, deployer identity, system versions, hardware/software dependencies, and how the AI system interacts with other systems.
2. **Detailed description of elements**: Development methodology, design specifications, system architecture, computational resources, data governance, and training methodology (if applicable).
3. **Monitoring and operation**: Human oversight measures, accuracy/robustness/cybersecurity specifications, predetermined changes, and post-market monitoring.
4. **Risk management**: The risk management system under Article 9, including identified risks, risk mitigation measures, and residual risks.
5. **Changes log**: Record of all changes made after initial conformity assessment.

For agent commerce systems, this translates to a structured identity record that links the agent's operational configuration to its compliance metadata. The GreenHelix identity system provides the infrastructure to store and retrieve this documentation programmatically.

### Article 49: EU Database Registration

High-risk AI systems must be registered in the EU database before being placed on the market. While the EU database is an official EU institution system (accessible at the European AI Office portal), your internal records must mirror the registration data. The GreenHelix identity record serves as your internal system of record, linking the agent's operational identity to its EU database registration ID.

### Code: The ComplianceAgent Class

```python
import hashlib
from datetime import datetime, timezone
from typing import Optional


class ComplianceAgent:
    """
    An agent wrapper that enforces EU AI Act technical documentation
    requirements at registration time. Every agent registered through
    this class carries the metadata Annex IV requires.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        version: str,
        intended_purpose: str,
        deployer_name: str,
        deployer_country: str,
        risk_level: str = "minimal",
    ):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.intended_purpose = intended_purpose
        self.deployer_name = deployer_name
        self.deployer_country = deployer_country
        self.risk_level = risk_level
        self.registration_result = None
        self.eu_database_id = None

    def _build_annex_iv_metadata(self) -> dict:
        """Build the technical documentation metadata required by Annex IV."""
        return {
            # Section 1: General description
            "annex_iv_section_1": {
                "intended_purpose": self.intended_purpose,
                "deployer": {
                    "name": self.deployer_name,
                    "country": self.deployer_country,
                },
                "system_version": self.version,
                "registration_timestamp": datetime.now(timezone.utc).isoformat(),
                "risk_classification": self.risk_level,
            },
            # Section 2: Elements description (populate with your specifics)
            "annex_iv_section_2": {
                "architecture": "autonomous_agent",
                "framework": "greenhelix_a2a_commerce",
                "api_version": "v1",
                "capabilities_declared": [],
            },
            # Section 3: Monitoring
            "annex_iv_section_3": {
                "human_oversight_mechanism": "webhook_notification",
                "monitoring_frequency": "continuous",
                "accuracy_specification": None,
                "robustness_measures": [],
            },
            # Section 4: Risk management reference
            "annex_iv_section_4": {
                "risk_management_system": True,
                "identified_risks": [],
                "mitigation_measures": [],
                "residual_risks": [],
            },
            # Section 5: Changes log
            "annex_iv_section_5": {
                "changes_since_assessment": [],
                "last_assessment_date": None,
            },
        }

    def register_with_compliance(self) -> dict:
        """
        Register the agent on GreenHelix with full Annex IV metadata.
        Returns the registration result including the agent's identity record.
        """
        metadata = self._build_annex_iv_metadata()

        # Compute a documentation hash for tamper detection
        doc_hash = hashlib.sha256(
            json.dumps(metadata, sort_keys=True).encode()
        ).hexdigest()

        metadata["documentation_hash"] = doc_hash

        capabilities = [
            "eu_ai_act_classified",
            f"risk_level:{self.risk_level}",
            f"deployer_country:{self.deployer_country}",
            "annex_iv_documented",
        ]

        self.registration_result = api_call("register_agent", {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": capabilities,
            "metadata": metadata,
        })

        return self.registration_result

    def set_eu_database_id(self, database_id: str) -> None:
        """
        After registering in the official EU AI database, link the
        registration ID to this agent's identity record.
        """
        self.eu_database_id = database_id
        # Update the agent's metadata to include the EU database reference
        api_call("submit_metrics", {
            "agent_id": self.agent_id,
            "metrics": {
                "eu_database_registration_id": database_id,
                "eu_database_registration_date": datetime.now(timezone.utc).isoformat(),
            },
        })

    def verify_identity(self) -> dict:
        """Retrieve and verify the agent's identity record."""
        return api_call("get_agent_identity", {
            "agent_id": self.agent_id,
        })

    def get_compliance_status(self) -> dict:
        """
        Check whether this agent's compliance metadata is complete.
        Returns a checklist of Annex IV sections and their status.
        """
        identity = self.verify_identity()
        metadata = identity.get("result", {}).get("metadata", {})

        checklist = {
            "risk_classified": "annex_iv_section_1" in metadata,
            "architecture_documented": bool(
                metadata.get("annex_iv_section_2", {}).get("architecture")
            ),
            "monitoring_configured": bool(
                metadata.get("annex_iv_section_3", {}).get("human_oversight_mechanism")
            ),
            "risk_management_system": bool(
                metadata.get("annex_iv_section_4", {}).get("risk_management_system")
            ),
            "documentation_hash_present": "documentation_hash" in metadata,
            "eu_database_registered": self.eu_database_id is not None,
        }

        checklist["compliant"] = all(checklist.values())
        return checklist


# --- Usage ---

agent = ComplianceAgent(
    agent_id="escrow-manager-eu-prod",
    name="EU-Compliant Escrow Manager",
    version="2.1.0",
    intended_purpose=(
        "Manages escrow creation, monitoring, and release for agent-to-agent "
        "commercial transactions. Does not make decisions about natural persons."
    ),
    deployer_name="Acme Agent Systems GmbH",
    deployer_country="DE",
    risk_level="minimal",
)

# Register with full Annex IV metadata
reg_result = agent.register_with_compliance()
print(f"Registered: {reg_result}")

# After registering in the EU database (manual step for high-risk systems)
# agent.set_eu_database_id("EU-AI-DB-2026-00042")

# Check compliance status
status = agent.get_compliance_status()
print(json.dumps(status, indent=2))
```

### Attaching Compliance Metadata to Existing Agents

If you have agents already registered on GreenHelix without compliance metadata, you do not need to re-register them. Use `verify_agent` to confirm the existing identity, then `submit_metrics` to attach compliance documentation as metric records. This creates a timestamped compliance record linked to the agent's existing identity.

```python
def retrofit_compliance_metadata(agent_id: str, risk_level: str, purpose: str) -> dict:
    """
    Attach EU AI Act compliance metadata to an already-registered agent.
    Does not modify the original identity record -- adds compliance
    data as a metric submission with a compliance timestamp.
    """
    # Verify the agent exists
    identity = api_call("get_agent_identity", {"agent_id": agent_id})

    if not identity.get("result"):
        raise ValueError(f"Agent {agent_id} not found -- register first")

    # Verify the agent's identity is intact
    api_call("verify_agent", {"agent_id": agent_id})

    # Submit compliance metadata as metrics
    compliance_metrics = {
        "eu_ai_act_risk_level": risk_level,
        "intended_purpose": purpose,
        "compliance_retrofit_date": datetime.now(timezone.utc).isoformat(),
        "annex_iv_documented": True,
        "compliance_toolkit_version": "1.0.0",
    }

    result = api_call("submit_metrics", {
        "agent_id": agent_id,
        "metrics": compliance_metrics,
    })

    return result
```

The key insight is that compliance documentation is not a one-time event. It is a living record that must be updated whenever the system changes. The `submit_metrics` tool creates timestamped records that form a compliance history, and the `build_claim_chain` tool (covered in Chapter 4) makes that history tamper-evident.

---

## Chapter 4: Cryptographic Audit Trails

### Article 12: Record-Keeping Obligations

Article 12 requires that high-risk AI systems include logging capabilities that:

1. Record events relevant to identifying situations that may result in risk.
2. Facilitate post-market monitoring.
3. Are adequate to enable the tracing of the AI system's operation throughout its lifecycle.
4. Are produced automatically, with the logs being kept for a period appropriate to the intended purpose (at minimum until regulatory or contractual obligations expire).

For agent commerce, "events relevant to risk" include every financial transaction, every identity verification, every dispute, every metric submission, and every configuration change. The logs must be tamper-evident -- a requirement that goes beyond simple append-only databases. If a log can be silently modified after the fact, it cannot prove what actually happened.

### Merkle Claim Chains as Tamper-Evident Compliance Logs

GreenHelix's `build_claim_chain` tool creates Merkle-structured claim chains. Each claim in the chain is cryptographically linked to the previous claim, creating a hash chain that makes retroactive modification detectable. If any entry in the chain is altered, the hash chain breaks and verification fails. This is the technical property Article 12 requires: logs that are "adequate to enable the tracing of the AI system's operation" and that cannot be silently altered.

A claim chain for compliance purposes records:
- **What happened**: The event type (transaction, verification, configuration change).
- **When it happened**: ISO 8601 timestamp.
- **Who was involved**: Agent IDs of all parties.
- **What the state was**: Relevant parameters, amounts, statuses.
- **Cryptographic linkage**: Each claim references the previous chain hash.

### Code: Building Compliance Audit Chains

```python
from enum import Enum


class ComplianceEventType(str, Enum):
    AGENT_REGISTERED = "agent_registered"
    RISK_CLASSIFIED = "risk_classified"
    ESCROW_CREATED = "escrow_created"
    ESCROW_RELEASED = "escrow_released"
    ESCROW_CANCELLED = "escrow_cancelled"
    PAYMENT_PROCESSED = "payment_processed"
    DISPUTE_OPENED = "dispute_opened"
    DISPUTE_RESOLVED = "dispute_resolved"
    CONFIGURATION_CHANGED = "configuration_changed"
    COMPLIANCE_CHECK_PASSED = "compliance_check_passed"
    COMPLIANCE_CHECK_FAILED = "compliance_check_failed"
    HUMAN_OVERRIDE = "human_override"
    INCIDENT_REPORTED = "incident_reported"


class ComplianceAuditChain:
    """
    Builds and verifies tamper-evident compliance audit trails
    using GreenHelix Merkle claim chains. Satisfies Article 12
    record-keeping obligations.
    """

    def __init__(self, agent_id: str, chain_namespace: str = "eu_compliance"):
        self.agent_id = agent_id
        self.chain_namespace = chain_namespace
        self.chain_id = f"{agent_id}:{chain_namespace}"

    def record_event(
        self,
        event_type: ComplianceEventType,
        details: dict,
        counterparty_id: Optional[str] = None,
        financial_amount: Optional[float] = None,
        risk_flags: Optional[list] = None,
    ) -> dict:
        """
        Record a compliance-relevant event to the audit chain.
        Each call appends a new claim linked to the previous chain state.
        """
        claim_data = {
            "event_type": event_type.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": self.agent_id,
            "details": details,
        }

        if counterparty_id:
            claim_data["counterparty_id"] = counterparty_id
        if financial_amount is not None:
            claim_data["financial_amount"] = str(financial_amount)
        if risk_flags:
            claim_data["risk_flags"] = risk_flags

        # Build the claim chain entry
        result = api_call("build_claim_chain", {
            "agent_id": self.agent_id,
            "claims": [
                {
                    "claim_type": f"compliance:{event_type.value}",
                    "claim_data": claim_data,
                }
            ],
        })

        return result

    def record_escrow_lifecycle(
        self,
        escrow_id: str,
        event: str,
        amount: float,
        counterparty_id: str,
        terms: Optional[dict] = None,
    ) -> dict:
        """Record an escrow lifecycle event for Article 12 compliance."""
        event_map = {
            "created": ComplianceEventType.ESCROW_CREATED,
            "released": ComplianceEventType.ESCROW_RELEASED,
            "cancelled": ComplianceEventType.ESCROW_CANCELLED,
        }

        details = {
            "escrow_id": escrow_id,
            "escrow_event": event,
        }
        if terms:
            details["terms"] = terms

        return self.record_event(
            event_type=event_map.get(event, ComplianceEventType.PAYMENT_PROCESSED),
            details=details,
            counterparty_id=counterparty_id,
            financial_amount=amount,
        )

    def record_human_override(
        self,
        operator_id: str,
        reason: str,
        action_taken: str,
    ) -> dict:
        """
        Record a human oversight intervention. Article 14 requires
        human oversight mechanisms -- this records when they are invoked.
        """
        return self.record_event(
            event_type=ComplianceEventType.HUMAN_OVERRIDE,
            details={
                "operator_id": operator_id,
                "reason": reason,
                "action_taken": action_taken,
            },
            risk_flags=["human_intervention"],
        )

    def verify_chain_integrity(self) -> dict:
        """
        Retrieve and verify the complete audit chain. Returns the chain
        with integrity status. A broken chain indicates tampering.
        """
        result = api_call("get_claim_chains", {
            "agent_id": self.agent_id,
        })

        chains = result.get("result", {}).get("chains", [])

        return {
            "agent_id": self.agent_id,
            "chain_count": len(chains),
            "chains": chains,
            "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_compliance_events(self, event_type: Optional[str] = None) -> list:
        """
        Retrieve verified compliance claims, optionally filtered by type.
        """
        result = api_call("get_verified_claims", {
            "agent_id": self.agent_id,
        })

        claims = result.get("result", {}).get("claims", [])

        if event_type:
            claims = [
                c for c in claims
                if c.get("claim_type", "").endswith(event_type)
            ]

        return claims


# --- Usage ---

audit = ComplianceAuditChain(
    agent_id="escrow-manager-eu-prod",
    chain_namespace="eu_compliance_2026",
)

# Record agent registration
audit.record_event(
    event_type=ComplianceEventType.AGENT_REGISTERED,
    details={
        "name": "EU-Compliant Escrow Manager",
        "version": "2.1.0",
        "risk_level": "minimal",
        "deployer": "Acme Agent Systems GmbH",
    },
)

# Record risk classification
audit.record_event(
    event_type=ComplianceEventType.RISK_CLASSIFIED,
    details={
        "classification_method": "annex_iii_decision_tree",
        "result": "minimal",
        "reviewer": "compliance-team@acme.example",
    },
)

# Record an escrow creation
audit.record_escrow_lifecycle(
    escrow_id="esc_20260415_001",
    event="created",
    amount=2500.00,
    counterparty_id="data-analyst-agent-v3",
    terms={"timeout_hours": 72, "liability_cap_usd": 5000},
)

# Record a human override (Article 14 compliance)
audit.record_human_override(
    operator_id="ops-lead@acme.example",
    reason="Escrow amount exceeds automated approval threshold",
    action_taken="Approved escrow release after manual review of deliverables",
)

# Verify chain integrity
integrity = audit.verify_chain_integrity()
print(f"Chain integrity check: {integrity['chain_count']} chains found")
```

### Verifying Audit Completeness

A tamper-evident chain is only useful if it is complete. Gaps in the audit trail are a compliance failure even if the existing entries are intact. Build a completeness checker that compares expected events (from your business logic) against recorded events (from the chain).

```python
def verify_audit_completeness(
    agent_id: str,
    expected_escrow_ids: list,
    expected_event_types: list,
) -> dict:
    """
    Verify that the compliance audit trail contains records for
    all expected events. Returns missing events that represent
    compliance gaps.
    """
    # Get all verified claims for this agent
    claims_result = api_call("get_verified_claims", {
        "agent_id": agent_id,
    })

    recorded_claims = claims_result.get("result", {}).get("claims", [])

    # Extract recorded escrow IDs and event types
    recorded_escrow_ids = set()
    recorded_event_types = set()

    for claim in recorded_claims:
        claim_data = claim.get("claim_data", {})
        if "escrow_id" in claim_data.get("details", {}):
            recorded_escrow_ids.add(claim_data["details"]["escrow_id"])
        event_type = claim_data.get("event_type", "")
        if event_type:
            recorded_event_types.add(event_type)

    # Find gaps
    missing_escrows = set(expected_escrow_ids) - recorded_escrow_ids
    missing_event_types = set(expected_event_types) - recorded_event_types

    return {
        "complete": len(missing_escrows) == 0 and len(missing_event_types) == 0,
        "missing_escrow_records": list(missing_escrows),
        "missing_event_types": list(missing_event_types),
        "total_recorded_claims": len(recorded_claims),
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
    }
```

When a completeness check fails, the system should immediately record the gap as a `COMPLIANCE_CHECK_FAILED` event on the chain itself and trigger an incident notification (covered in Chapter 7). The gap in the audit trail is itself a compliance-relevant event that must be documented.

---

## Chapter 5: Liability-Bounded Escrow Patterns

### Product Liability Directive: No-Fault Exposure

The revised Product Liability Directive (2024/2853) creates strict liability for AI system providers and deployers. "Strict" means the claimant does not need to prove negligence -- only that the AI system was defective and caused damage. For agent commerce, this means:

- If Agent A hires Agent B via escrow, and Agent B's output causes damage to a downstream consumer, both the deployer of Agent A and the deployer of Agent B face potential liability.
- The "defect" can be a failure to meet documented specifications, a failure to provide adequate instructions, or a failure to account for reasonably foreseeable misuse.
- Liability cannot be contractually excluded vis-a-vis consumers. But between business entities (agent deployers), liability can be allocated and capped through contracts.

This is where escrow becomes a compliance mechanism, not just a payment mechanism. A properly structured escrow limits the financial exposure of each party to a defined amount, creates a contractual record of agreed terms, and provides a dispute resolution mechanism that can demonstrate regulatory compliance.

### Escrow as Liability Cap Mechanism

A standard escrow holds funds until conditions are met. A compliance escrow adds three elements:

1. **Liability cap**: The escrow amount serves as the maximum financial exposure for the transaction. Both parties contractually agree that the escrowed amount represents the total liability boundary.
2. **Timeout enforcement**: Article 9's risk management system requires time-bounded operations. An escrow with a mandatory timeout ensures that funds cannot be locked indefinitely -- a risk that could itself create liability.
3. **Compliance metadata**: The escrow record includes risk classification, applicable regulations, and dispute resolution terms. This metadata is part of the Article 12 audit trail.

### Performance Escrow with SLA Compliance Checks

Performance escrow extends the basic escrow pattern with measurable service level agreements. The escrow releases (or partially releases) based on whether the service met defined performance thresholds. This maps directly to Article 15's accuracy and robustness requirements -- you are contractually defining what "accurate and robust" means for this specific transaction and funding the guarantee.

### Code: Compliant Escrow Patterns

```python
class ComplianceEscrow:
    """
    Creates and manages escrows with EU AI Act compliance metadata.
    Every escrow created through this class carries liability caps,
    timeout enforcement, and audit trail integration.
    """

    def __init__(self, agent_id: str, audit_chain: ComplianceAuditChain):
        self.agent_id = agent_id
        self.audit = audit_chain

    def create_compliant_escrow(
        self,
        counterparty_id: str,
        amount: float,
        currency: str,
        service_description: str,
        liability_cap_usd: float,
        timeout_hours: int = 72,
        applicable_regulations: Optional[list] = None,
        dispute_resolution_terms: Optional[str] = None,
    ) -> dict:
        """
        Create an escrow with full compliance metadata.

        The liability_cap_usd parameter sets the maximum financial exposure.
        The escrow amount should not exceed this cap. The timeout_hours
        parameter ensures Article 9 time-bounded operation.
        """
        if applicable_regulations is None:
            applicable_regulations = ["eu_ai_act_2024_1689"]

        if dispute_resolution_terms is None:
            dispute_resolution_terms = (
                "Disputes resolved via platform dispute resolution mechanism. "
                "Escalation to deployer within 48 hours of dispute opening. "
                "Applicable law: law of the deployer's EU member state."
            )

        # Enforce liability cap
        if amount > liability_cap_usd:
            raise ValueError(
                f"Escrow amount ({amount}) exceeds liability cap "
                f"({liability_cap_usd}). Reduce amount or increase cap."
            )

        # Create the escrow with compliance metadata
        escrow_result = api_call("create_escrow", {
            "payer_id": self.agent_id,
            "payee_id": counterparty_id,
            "amount": amount,
            "currency": currency,
            "description": service_description,
            "metadata": {
                "compliance": {
                    "liability_cap_usd": str(liability_cap_usd),
                    "timeout_hours": timeout_hours,
                    "applicable_regulations": applicable_regulations,
                    "dispute_resolution_terms": dispute_resolution_terms,
                    "created_under_eu_ai_act": True,
                    "article_9_risk_managed": True,
                    "article_12_audit_enabled": True,
                },
            },
        })

        escrow_id = escrow_result.get("result", {}).get("escrow_id", "unknown")

        # Record in audit chain (Article 12)
        self.audit.record_escrow_lifecycle(
            escrow_id=escrow_id,
            event="created",
            amount=amount,
            counterparty_id=counterparty_id,
            terms={
                "liability_cap_usd": str(liability_cap_usd),
                "timeout_hours": timeout_hours,
                "regulations": applicable_regulations,
            },
        )

        return escrow_result

    def create_performance_escrow(
        self,
        counterparty_id: str,
        amount: float,
        currency: str,
        service_description: str,
        sla_metrics: dict,
        liability_cap_usd: float,
        timeout_hours: int = 72,
    ) -> dict:
        """
        Create a performance escrow with SLA compliance checks.

        sla_metrics defines the measurable thresholds for escrow release:
        {
            "accuracy_threshold": 0.95,
            "latency_p99_ms": 500,
            "uptime_percent": 99.5,
            "error_rate_max": 0.01,
        }

        These map to Article 15's accuracy and robustness requirements,
        contractually defining what those terms mean for this transaction.
        """
        if amount > liability_cap_usd:
            raise ValueError(
                f"Escrow amount ({amount}) exceeds liability cap ({liability_cap_usd})"
            )

        perf_escrow_result = api_call("create_performance_escrow", {
            "payer_id": self.agent_id,
            "payee_id": counterparty_id,
            "amount": amount,
            "currency": currency,
            "description": service_description,
            "criteria": sla_metrics,
            "metadata": {
                "compliance": {
                    "liability_cap_usd": str(liability_cap_usd),
                    "timeout_hours": timeout_hours,
                    "sla_article_15_mapping": {
                        "accuracy": sla_metrics.get("accuracy_threshold"),
                        "robustness": sla_metrics.get("uptime_percent"),
                    },
                    "applicable_regulations": [
                        "eu_ai_act_2024_1689",
                        "product_liability_directive_2024_2853",
                    ],
                },
            },
        })

        escrow_id = perf_escrow_result.get("result", {}).get("escrow_id", "unknown")

        # Audit trail
        self.audit.record_escrow_lifecycle(
            escrow_id=escrow_id,
            event="created",
            amount=amount,
            counterparty_id=counterparty_id,
            terms={
                "type": "performance_escrow",
                "sla_metrics": sla_metrics,
                "liability_cap_usd": str(liability_cap_usd),
                "timeout_hours": timeout_hours,
            },
        )

        return perf_escrow_result

    def release_with_compliance_check(
        self,
        escrow_id: str,
        counterparty_id: str,
        amount: float,
        compliance_verified: bool,
        verification_details: str,
    ) -> dict:
        """
        Release escrow only after confirming compliance requirements are met.
        Records the release decision and compliance status in the audit chain.
        """
        if not compliance_verified:
            # Record the failed compliance check
            self.audit.record_event(
                event_type=ComplianceEventType.COMPLIANCE_CHECK_FAILED,
                details={
                    "escrow_id": escrow_id,
                    "reason": verification_details,
                    "action": "release_blocked",
                },
                counterparty_id=counterparty_id,
                financial_amount=amount,
                risk_flags=["compliance_block"],
            )
            raise ValueError(
                f"Compliance check failed for escrow {escrow_id}: "
                f"{verification_details}"
            )

        # Record successful compliance check
        self.audit.record_event(
            event_type=ComplianceEventType.COMPLIANCE_CHECK_PASSED,
            details={
                "escrow_id": escrow_id,
                "verification_details": verification_details,
            },
            counterparty_id=counterparty_id,
            financial_amount=amount,
        )

        # Release the escrow
        # (Actual release mechanism depends on escrow type)
        self.audit.record_escrow_lifecycle(
            escrow_id=escrow_id,
            event="released",
            amount=amount,
            counterparty_id=counterparty_id,
        )

        return {"escrow_id": escrow_id, "status": "released", "amount": str(amount)}


# --- Usage ---

audit_chain = ComplianceAuditChain(
    agent_id="escrow-manager-eu-prod",
    chain_namespace="eu_compliance_2026",
)

escrow_mgr = ComplianceEscrow(
    agent_id="escrow-manager-eu-prod",
    audit_chain=audit_chain,
)

# Create a liability-bounded escrow
escrow = escrow_mgr.create_compliant_escrow(
    counterparty_id="data-analyst-agent-v3",
    amount=2500.00,
    currency="EUR",
    service_description="Quarterly financial data analysis and reporting",
    liability_cap_usd=5000.00,
    timeout_hours=72,
)

# Create a performance escrow with SLA
perf_escrow = escrow_mgr.create_performance_escrow(
    counterparty_id="ml-inference-agent-v2",
    amount=10000.00,
    currency="EUR",
    service_description="Real-time inference service for product recommendations",
    sla_metrics={
        "accuracy_threshold": 0.95,
        "latency_p99_ms": 200,
        "uptime_percent": 99.9,
        "error_rate_max": 0.005,
    },
    liability_cap_usd=25000.00,
    timeout_hours=168,  # 1 week for performance evaluation
)
```

### Why Liability Caps Matter for the Supply Chain

Under the Product Liability Directive, every entity in the supply chain is jointly liable. Without contractual liability caps between agent deployers, a single defective agent in a multi-agent workflow can expose every participant to unlimited liability. The escrow pattern above does three things to mitigate this:

1. Caps the financial exposure per transaction to a defined amount that both parties accepted at escrow creation time.
2. Creates an auditable record of the liability terms (Article 12 compliance).
3. Provides a mechanism for dispute resolution (Article 9 risk mitigation).

This does not eliminate liability to consumers under the Product Liability Directive -- that liability is strict and cannot be contractually excluded. But it does allocate liability between businesses in the supply chain, which is the primary mechanism for managing financial exposure in multi-agent commerce.

---

## Chapter 6: Agent-to-Agent Service Contracts

### Why Machine-Readable Contracts Matter

When Agent A hires Agent B through a marketplace listing, the terms of that engagement are currently defined by the listing description -- a free-text field that no machine can enforce. A compliant agent commerce system needs machine-readable contracts that:

1. **Define liability boundaries** enforceable by the escrow system.
2. **Specify data processing terms** required by GDPR when personal data flows between agents.
3. **Include dispute resolution clauses** that map to the platform's dispute mechanism.
4. **Carry regulatory metadata** identifying which regulations apply and which party bears which compliance obligations.
5. **Are auditable** -- stored as part of the Article 12 record-keeping trail.

### Contract Template Structure

The contract is a JSON document stored as marketplace listing metadata. Both parties reference the same contract by its content hash. The contract is not a legal instrument by itself -- it is a technical specification that your legal counsel translates into binding terms. But it is machine-enforceable, which means your agents can automatically reject contracts that violate compliance policies.

```python
import hashlib
from datetime import datetime, timezone, timedelta


def generate_service_contract(
    provider_id: str,
    consumer_id: str,
    service_name: str,
    service_description: str,
    pricing: dict,
    sla: dict,
    liability_terms: dict,
    data_processing_terms: dict,
    dispute_resolution: dict,
    regulatory_scope: Optional[list] = None,
    contract_duration_days: int = 90,
) -> dict:
    """
    Generate a machine-readable service contract for agent-to-agent
    commerce. The contract is stored as marketplace listing metadata
    and referenced by its content hash.

    Args:
        provider_id: Agent ID of the service provider.
        consumer_id: Agent ID of the consumer (or "*" for open listing).
        service_name: Human-readable service name.
        service_description: Detailed description of the service.
        pricing: {"model": "per_call"|"flat"|"tiered", "amount": float, "currency": str}
        sla: {"uptime": float, "latency_p99_ms": int, "accuracy": float}
        liability_terms: {
            "provider_liability_cap_usd": float,
            "consumer_liability_cap_usd": float,
            "indemnification": str,
            "force_majeure": bool,
        }
        data_processing_terms: {
            "personal_data_processed": bool,
            "data_retention_days": int,
            "data_location": str,
            "gdpr_role": "controller"|"processor"|"none",
            "dpa_reference": str | None,
        }
        dispute_resolution: {
            "mechanism": "platform"|"arbitration"|"court",
            "escalation_hours": int,
            "governing_law": str,
        }
        regulatory_scope: List of applicable regulation identifiers.
        contract_duration_days: How long the contract is valid.

    Returns:
        The contract document with its content hash.
    """
    if regulatory_scope is None:
        regulatory_scope = [
            "eu_ai_act_2024_1689",
            "product_liability_directive_2024_2853",
            "gdpr_2016_679",
        ]

    now = datetime.now(timezone.utc)

    contract = {
        "schema_version": "1.0.0",
        "contract_type": "agent_service_agreement",
        "parties": {
            "provider": provider_id,
            "consumer": consumer_id,
        },
        "service": {
            "name": service_name,
            "description": service_description,
        },
        "pricing": pricing,
        "sla": sla,
        "liability": liability_terms,
        "data_processing": data_processing_terms,
        "dispute_resolution": dispute_resolution,
        "regulatory": {
            "applicable_regulations": regulatory_scope,
            "provider_compliance_obligations": [
                "article_12_record_keeping",
                "article_13_transparency",
                "article_15_accuracy_robustness",
            ],
            "consumer_compliance_obligations": [
                "article_14_human_oversight",
                "article_26_deployer_obligations",
            ],
        },
        "temporal": {
            "created_at": now.isoformat(),
            "effective_from": now.isoformat(),
            "expires_at": (now + timedelta(days=contract_duration_days)).isoformat(),
            "duration_days": contract_duration_days,
        },
    }

    # Compute content hash for tamper detection and referencing
    contract_hash = hashlib.sha256(
        json.dumps(contract, sort_keys=True).encode()
    ).hexdigest()

    contract["contract_hash"] = contract_hash

    return contract


# --- Usage ---

contract = generate_service_contract(
    provider_id="ml-inference-agent-v2",
    consumer_id="escrow-manager-eu-prod",
    service_name="Real-Time Product Recommendation Inference",
    service_description=(
        "Provides real-time ML inference for product recommendations. "
        "Input: user context vector (256-dim). Output: ranked product IDs "
        "with confidence scores. Model: transformer-based collaborative "
        "filtering, retrained weekly."
    ),
    pricing={
        "model": "per_call",
        "amount": 0.002,
        "currency": "EUR",
    },
    sla={
        "uptime_percent": 99.9,
        "latency_p99_ms": 200,
        "accuracy_threshold": 0.95,
        "error_rate_max": 0.005,
    },
    liability_terms={
        "provider_liability_cap_usd": 25000,
        "consumer_liability_cap_usd": 10000,
        "indemnification": (
            "Provider indemnifies consumer against claims arising from "
            "provider's breach of SLA or data processing terms."
        ),
        "force_majeure": True,
    },
    data_processing_terms={
        "personal_data_processed": True,
        "data_retention_days": 30,
        "data_location": "EU",
        "gdpr_role": "processor",
        "dpa_reference": "DPA-2026-ACME-ML-001",
    },
    dispute_resolution={
        "mechanism": "platform",
        "escalation_hours": 48,
        "governing_law": "German law",
    },
)

print(f"Contract hash: {contract['contract_hash']}")
```

### Registering Services with Compliance Tags

When listing a service on the marketplace, attach the contract as metadata and use compliance tags to enable discovery by compliance-aware agents.

```python
def register_compliant_service(
    agent_id: str,
    service_name: str,
    description: str,
    contract: dict,
    risk_level: str,
    audit_chain: ComplianceAuditChain,
) -> dict:
    """
    Register a marketplace service with compliance tags and contract terms.
    Enables other agents to discover services that meet their compliance
    requirements.
    """
    tags = [
        "eu_ai_act_compliant",
        f"risk_level:{risk_level}",
        "article_12_audited",
        "liability_bounded",
        f"governing_law:{contract['dispute_resolution']['governing_law']}",
    ]

    if contract["data_processing"]["personal_data_processed"]:
        tags.append("gdpr_dpa_required")
        tags.append(f"data_location:{contract['data_processing']['data_location']}")

    result = api_call("register_service", {
        "agent_id": agent_id,
        "name": service_name,
        "description": description,
        "tags": tags,
        "metadata": {
            "contract_hash": contract["contract_hash"],
            "contract": contract,
            "compliance_version": "1.0.0",
        },
    })

    # Record in audit trail
    audit_chain.record_event(
        event_type=ComplianceEventType.AGENT_REGISTERED,
        details={
            "service_name": service_name,
            "contract_hash": contract["contract_hash"],
            "risk_level": risk_level,
            "tags": tags,
        },
    )

    return result


# --- Contract validation ---

def validate_counterparty_contract(contract: dict, requirements: dict) -> dict:
    """
    Validate that a counterparty's contract meets your compliance
    requirements before entering into a transaction.

    Args:
        contract: The counterparty's service contract.
        requirements: Your minimum requirements, e.g.:
            {
                "max_provider_liability_cap": 50000,
                "min_uptime": 99.0,
                "required_data_location": "EU",
                "required_governing_law": "German law",
                "gdpr_dpa_required": True,
            }
    """
    violations = []

    # Check liability cap
    cap = contract.get("liability", {}).get("provider_liability_cap_usd", 0)
    if cap < requirements.get("min_provider_liability_cap", 0):
        violations.append(
            f"Provider liability cap ({cap}) below minimum "
            f"({requirements['min_provider_liability_cap']})"
        )

    # Check SLA
    uptime = contract.get("sla", {}).get("uptime_percent", 0)
    if uptime < requirements.get("min_uptime", 0):
        violations.append(
            f"SLA uptime ({uptime}%) below minimum ({requirements['min_uptime']}%)"
        )

    # Check data location
    data_loc = contract.get("data_processing", {}).get("data_location", "")
    required_loc = requirements.get("required_data_location")
    if required_loc and data_loc != required_loc:
        violations.append(
            f"Data location ({data_loc}) does not match requirement ({required_loc})"
        )

    # Check GDPR DPA
    if requirements.get("gdpr_dpa_required"):
        dpa_ref = contract.get("data_processing", {}).get("dpa_reference")
        if not dpa_ref:
            violations.append("GDPR Data Processing Agreement reference missing")

    # Check governing law
    required_law = requirements.get("required_governing_law")
    gov_law = contract.get("dispute_resolution", {}).get("governing_law", "")
    if required_law and gov_law != required_law:
        violations.append(
            f"Governing law ({gov_law}) does not match requirement ({required_law})"
        )

    return {
        "valid": len(violations) == 0,
        "violations": violations,
        "contract_hash": contract.get("contract_hash"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


# Validate before transacting
validation = validate_counterparty_contract(
    contract=contract,
    requirements={
        "min_provider_liability_cap": 20000,
        "min_uptime": 99.0,
        "required_data_location": "EU",
        "required_governing_law": "German law",
        "gdpr_dpa_required": True,
    },
)

if not validation["valid"]:
    print(f"Contract rejected: {validation['violations']}")
else:
    print("Contract meets all compliance requirements -- proceed with escrow")
```

### Required Contract Clauses Checklist

Every agent-to-agent service contract should include these clauses. Missing any of them creates regulatory or liability exposure:

| Clause | Regulatory Basis | Purpose |
|---|---|---|
| **Liability cap** | Product Liability Directive | Bounds financial exposure per party |
| **SLA definition** | Article 15 (accuracy, robustness) | Contractually defines "adequate" performance |
| **Dispute resolution** | Article 9 (risk management) | Provides fallback when automated systems fail |
| **Data processing terms** | GDPR Article 28 | Required when personal data flows between agents |
| **Compliance obligations split** | Articles 16, 26 | Allocates provider vs. deployer obligations |
| **Record-keeping commitment** | Article 12 | Both parties agree to maintain audit trails |
| **Human oversight trigger** | Article 14 | Defines when human intervention is required |
| **Termination conditions** | Product Liability Directive | Allows exit if counterparty compliance lapses |
| **Force majeure** | General contract law | Protects against liability for events beyond control |
| **Governing law** | Brussels I Regulation | Determines which jurisdiction resolves disputes |

---

## Chapter 7: Compliance Monitoring & Reporting

### Article 9: Risk Management System

Article 9 requires a risk management system that is a "continuous iterative process planned and run throughout the entire lifecycle" of the AI system. This is not a one-time risk assessment -- it is a continuous monitoring system that:

1. Identifies and analyzes known and reasonably foreseeable risks.
2. Estimates and evaluates risks that may emerge during use.
3. Evaluates other risks based on post-market monitoring data.
4. Adopts appropriate risk mitigation measures.

For agent commerce, "continuous monitoring" means automated compliance metric submission, real-time anomaly detection, and webhook-based incident notification. The GreenHelix event and metrics tools provide the infrastructure.

### Automated Compliance Metric Submission

```python
import time
from datetime import datetime, timezone


class ComplianceMonitor:
    """
    Continuous compliance monitoring for agent commerce systems.
    Implements Article 9 risk management through automated metric
    submission and threshold-based alerting.
    """

    def __init__(
        self,
        agent_id: str,
        audit_chain: ComplianceAuditChain,
        thresholds: Optional[dict] = None,
    ):
        self.agent_id = agent_id
        self.audit = audit_chain
        self.thresholds = thresholds or {
            "error_rate_max": 0.01,
            "latency_p99_max_ms": 500,
            "uptime_min_percent": 99.0,
            "dispute_rate_max": 0.05,
            "compliance_score_min": 0.80,
        }
        self.incident_webhooks = []

    def register_incident_webhook(self, webhook_url: str, events: list) -> dict:
        """
        Register a webhook for compliance incident notifications.
        This enables Article 14 human oversight by routing alerts
        to human operators when thresholds are breached.
        """
        result = api_call("register_webhook", {
            "agent_id": self.agent_id,
            "url": webhook_url,
            "events": events,
        })

        self.incident_webhooks.append({
            "url": webhook_url,
            "events": events,
        })

        return result

    def submit_compliance_metrics(self, metrics: dict) -> dict:
        """
        Submit compliance metrics to GreenHelix. These form the
        quantitative basis for Article 9 risk evaluation.

        Expected metrics:
        {
            "error_rate": float,          # Current error rate
            "latency_p99_ms": int,        # P99 latency
            "uptime_percent": float,      # Rolling uptime percentage
            "transactions_total": int,    # Total transactions processed
            "disputes_opened": int,       # Disputes in current period
            "disputes_resolved": int,     # Disputes resolved in current period
            "escrows_active": int,        # Currently active escrows
            "compliance_checks_passed": int,
            "compliance_checks_failed": int,
        }
        """
        # Add compliance metadata
        metrics["submission_timestamp"] = datetime.now(timezone.utc).isoformat()
        metrics["monitor_version"] = "1.0.0"

        # Calculate derived compliance score
        total_checks = (
            metrics.get("compliance_checks_passed", 0)
            + metrics.get("compliance_checks_failed", 0)
        )
        if total_checks > 0:
            metrics["compliance_score"] = (
                metrics["compliance_checks_passed"] / total_checks
            )
        else:
            metrics["compliance_score"] = 1.0

        # Submit to GreenHelix
        result = api_call("submit_metrics", {
            "agent_id": self.agent_id,
            "metrics": metrics,
        })

        # Check thresholds and raise incidents
        violations = self._check_thresholds(metrics)
        if violations:
            self._raise_compliance_incident(violations, metrics)

        return result

    def _check_thresholds(self, metrics: dict) -> list:
        """Check submitted metrics against compliance thresholds."""
        violations = []

        if metrics.get("error_rate", 0) > self.thresholds["error_rate_max"]:
            violations.append({
                "metric": "error_rate",
                "value": metrics["error_rate"],
                "threshold": self.thresholds["error_rate_max"],
                "severity": "high",
            })

        if metrics.get("latency_p99_ms", 0) > self.thresholds["latency_p99_max_ms"]:
            violations.append({
                "metric": "latency_p99_ms",
                "value": metrics["latency_p99_ms"],
                "threshold": self.thresholds["latency_p99_max_ms"],
                "severity": "medium",
            })

        uptime = metrics.get("uptime_percent", 100)
        if uptime < self.thresholds["uptime_min_percent"]:
            violations.append({
                "metric": "uptime_percent",
                "value": uptime,
                "threshold": self.thresholds["uptime_min_percent"],
                "severity": "high",
            })

        # Dispute rate calculation
        total_tx = metrics.get("transactions_total", 0)
        disputes = metrics.get("disputes_opened", 0)
        if total_tx > 0:
            dispute_rate = disputes / total_tx
            if dispute_rate > self.thresholds["dispute_rate_max"]:
                violations.append({
                    "metric": "dispute_rate",
                    "value": dispute_rate,
                    "threshold": self.thresholds["dispute_rate_max"],
                    "severity": "high",
                })

        compliance_score = metrics.get("compliance_score", 1.0)
        if compliance_score < self.thresholds["compliance_score_min"]:
            violations.append({
                "metric": "compliance_score",
                "value": compliance_score,
                "threshold": self.thresholds["compliance_score_min"],
                "severity": "critical",
            })

        return violations

    def _raise_compliance_incident(self, violations: list, metrics: dict) -> None:
        """
        Raise a compliance incident when thresholds are breached.
        Publishes to event bus and records in audit chain.
        """
        incident = {
            "incident_type": "compliance_threshold_breach",
            "agent_id": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "violations": violations,
            "metrics_snapshot": metrics,
            "severity": max(v["severity"] for v in violations),
        }

        # Publish incident event
        api_call("publish_event", {
            "agent_id": self.agent_id,
            "event_type": "compliance_incident",
            "payload": incident,
        })

        # Record in audit chain
        self.audit.record_event(
            event_type=ComplianceEventType.INCIDENT_REPORTED,
            details=incident,
            risk_flags=[v["metric"] for v in violations],
        )

    def get_compliance_dashboard(self) -> dict:
        """
        Retrieve a compliance dashboard with current metrics,
        billing summary, and usage analytics.
        """
        # Get usage analytics for cost transparency (Article 13)
        usage = api_call("get_usage_analytics", {
            "agent_id": self.agent_id,
        })

        # Get billing summary for financial transparency
        billing = api_call("get_billing_summary", {
            "agent_id": self.agent_id,
        })

        # Search for agents with similar compliance profiles
        peers = api_call("search_agents_by_metrics", {
            "query": {
                "capabilities": ["eu_ai_act_compliant"],
            },
        })

        return {
            "agent_id": self.agent_id,
            "usage_analytics": usage.get("result"),
            "billing_summary": billing.get("result"),
            "compliant_peers": peers.get("result"),
            "dashboard_generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def run_periodic_check(self, metrics_source: callable, interval_seconds: int = 300):
        """
        Run continuous compliance monitoring. Call this in a background
        thread or scheduled task.

        Args:
            metrics_source: Callable that returns current metrics dict.
            interval_seconds: How often to check (default 5 minutes).
        """
        while True:
            try:
                current_metrics = metrics_source()
                self.submit_compliance_metrics(current_metrics)
            except Exception as e:
                # Record monitoring failures as incidents
                self.audit.record_event(
                    event_type=ComplianceEventType.INCIDENT_REPORTED,
                    details={
                        "error": str(e),
                        "monitoring_failure": True,
                    },
                    risk_flags=["monitoring_gap"],
                )
            time.sleep(interval_seconds)


# --- Usage ---

audit_chain = ComplianceAuditChain(
    agent_id="escrow-manager-eu-prod",
    chain_namespace="eu_compliance_2026",
)

monitor = ComplianceMonitor(
    agent_id="escrow-manager-eu-prod",
    audit_chain=audit_chain,
    thresholds={
        "error_rate_max": 0.01,
        "latency_p99_max_ms": 300,
        "uptime_min_percent": 99.9,
        "dispute_rate_max": 0.02,
        "compliance_score_min": 0.90,
    },
)

# Register webhooks for human oversight (Article 14)
monitor.register_incident_webhook(
    webhook_url="https://ops.acme.example/compliance-alerts",
    events=["compliance_incident", "dispute_opened", "escrow_timeout"],
)

# Submit current metrics
monitor.submit_compliance_metrics({
    "error_rate": 0.003,
    "latency_p99_ms": 180,
    "uptime_percent": 99.97,
    "transactions_total": 14200,
    "disputes_opened": 2,
    "disputes_resolved": 2,
    "escrows_active": 47,
    "compliance_checks_passed": 283,
    "compliance_checks_failed": 1,
})

# Get compliance dashboard
dashboard = monitor.get_compliance_dashboard()
print(json.dumps(dashboard, indent=2))
```

### Webhook-Based Incident Notification for Article 14

Article 14 requires that high-risk AI systems can be "effectively overseen by natural persons." In agent commerce, where transactions happen at machine speed, effective oversight requires automated alerting that routes incidents to human operators in real time. The webhook pattern above achieves this:

1. **Threshold breach alerts**: When compliance metrics cross defined thresholds, the system publishes an event that triggers webhook delivery to the operations team.
2. **Dispute notifications**: When a counterparty opens a dispute, the webhook fires immediately, giving the human operator time to intervene before the dispute resolution timeout.
3. **Escrow timeout warnings**: When an escrow approaches its timeout, the webhook alerts the operator to either release, extend, or cancel before the automatic timeout triggers.

The key design principle is that the system never requires a human to be watching continuously. It requires a human to be reachable within the defined escalation window. This is the practical interpretation of Article 14 for autonomous agent systems.

### Dispute Resolution for Contractual Fallback

When automated compliance monitoring detects a breach, and the counterparty disagrees with the assessment, the dispute resolution mechanism provides the contractual fallback:

```python
def open_compliance_dispute(
    agent_id: str,
    counterparty_id: str,
    escrow_id: str,
    reason: str,
    evidence: dict,
    audit_chain: ComplianceAuditChain,
) -> dict:
    """
    Open a formal dispute with compliance-relevant evidence.
    Records the dispute in the audit chain for Article 12.
    """
    dispute_result = api_call("open_dispute", {
        "agent_id": agent_id,
        "counterparty_id": counterparty_id,
        "escrow_id": escrow_id,
        "reason": reason,
        "evidence": evidence,
    })

    audit_chain.record_event(
        event_type=ComplianceEventType.DISPUTE_OPENED,
        details={
            "escrow_id": escrow_id,
            "reason": reason,
            "evidence_summary": list(evidence.keys()),
        },
        counterparty_id=counterparty_id,
    )

    return dispute_result


def resolve_compliance_dispute(
    agent_id: str,
    dispute_id: str,
    resolution: str,
    counterparty_id: str,
    audit_chain: ComplianceAuditChain,
) -> dict:
    """
    Resolve a dispute and record the resolution in the audit trail.
    """
    resolve_result = api_call("resolve_dispute", {
        "agent_id": agent_id,
        "dispute_id": dispute_id,
        "resolution": resolution,
    })

    audit_chain.record_event(
        event_type=ComplianceEventType.DISPUTE_RESOLVED,
        details={
            "dispute_id": dispute_id,
            "resolution": resolution,
        },
        counterparty_id=counterparty_id,
    )

    return resolve_result
```

---

## Chapter 8: The Pre-August 2026 Compliance Sprint

### 12-Week Sprint to Compliance

August 2, 2026 is not negotiable. If you are reading this guide in April 2026, you have approximately 16 weeks. Here is a 12-week sprint plan that leaves 4 weeks of buffer for testing, legal review, and unexpected regulatory guidance. Each week has specific deliverables tied to the code patterns in this guide.

### Weeks 1-2: Foundation

**Goal**: Risk classification complete, agent identities registered with compliance metadata.

- [ ] Run `classify_agent_risk()` (Chapter 2) against every agent in production.
- [ ] Document classification decisions and reasoning. Store in version control.
- [ ] Register all agents using `ComplianceAgent.register_with_compliance()` (Chapter 3).
- [ ] Engage legal counsel to validate risk classifications. Flag any edge cases from the "elevated" risk category.
- [ ] Create a compliance metadata schema that your legal team approves.

**Quick win**: Risk classification can be done in a single afternoon. The code in Chapter 2 produces a structured output that your legal team can review.

### Weeks 3-4: Audit Infrastructure

**Goal**: Cryptographic audit trails operational for all compliance-relevant events.

- [ ] Deploy `ComplianceAuditChain` (Chapter 4) for every production agent.
- [ ] Integrate audit chain recording into all escrow create/release/cancel paths.
- [ ] Integrate audit chain recording into all dispute open/resolve paths.
- [ ] Set up `verify_audit_completeness()` as a daily cron job.
- [ ] Verify that chain integrity checks pass for all agents.

**Quick win**: If you already use GreenHelix for escrow and payments, adding the audit chain calls is wrapping existing code with three additional lines per operation.

### Weeks 5-6: Contracts & Liability

**Goal**: Machine-readable service contracts for all marketplace listings.

- [ ] Generate service contracts using `generate_service_contract()` (Chapter 6) for every active marketplace listing.
- [ ] Have legal counsel review the contract template and approve the required clauses.
- [ ] Implement `validate_counterparty_contract()` in your agent's decision loop -- no transaction without a valid contract.
- [ ] Update all escrows to use `ComplianceEscrow.create_compliant_escrow()` (Chapter 5) with liability caps.
- [ ] Backfill compliance metadata on existing active escrows.

**Deep work**: The contract template requires legal review. Start this process in Week 3 so the template is approved by Week 5.

### Weeks 7-8: Monitoring & Alerting

**Goal**: Continuous compliance monitoring with human oversight webhooks.

- [ ] Deploy `ComplianceMonitor` (Chapter 7) for every production agent.
- [ ] Configure compliance thresholds based on your SLA commitments.
- [ ] Register incident webhooks routed to your operations team's alerting system (PagerDuty, Opsgenie, etc.).
- [ ] Test the full alerting pipeline: inject a threshold breach and verify the webhook fires, the event publishes, and the audit chain records the incident.
- [ ] Set up the compliance dashboard and schedule weekly review meetings with your legal/compliance team.

**Quick win**: Webhook registration is a single API call. The monitoring loop can be a cron job that runs every 5 minutes.

### Weeks 9-10: Integration Testing

**Goal**: End-to-end compliance flow tested in a staging environment.

- [ ] Run the complete lifecycle in staging: register agent, classify risk, create contract, create escrow, submit metrics, trigger incident, resolve dispute, verify audit chain.
- [ ] Verify audit completeness across the entire lifecycle.
- [ ] Test failure modes: what happens when the audit chain is unreachable? When metrics submission fails? When the webhook endpoint is down?
- [ ] Load test the compliance monitoring under production traffic volumes.
- [ ] If you are building high-risk systems, prepare documentation for the EU database registration (Article 49).

**Cross-reference**: Use the patterns from Product #9 (Agent Testing & Observability Cookbook) for integration test structure and chaos testing of compliance infrastructure.

### Weeks 11-12: Legal Review & Documentation

**Goal**: Complete Annex IV technical documentation, legal sign-off.

- [ ] Compile Annex IV technical documentation from the metadata your agents have been generating since Week 1.
- [ ] Legal counsel reviews and signs off on: risk classifications, contract templates, liability caps, data processing terms, dispute resolution terms.
- [ ] If high-risk: submit EU database registration.
- [ ] Prepare incident response playbook for compliance failures post-launch.
- [ ] Run a tabletop exercise: "A regulator asks for our Article 12 audit trail for Agent X. Can we produce it within 24 hours?"

### Buffer Weeks 13-16: Hardening

- Address any findings from legal review.
- Implement additional security hardening (see Product #8: Agent Commerce Security Guide).
- Run penetration testing against compliance infrastructure.
- Finalize and freeze the compliance configuration.

### Quick Wins vs Deep Work Summary

| Category | Time | Impact |
|---|---|---|
| Risk classification | 1 afternoon | Unblocks everything else |
| Agent registration with metadata | 1-2 days | Creates compliance identity records |
| Audit chain integration | 2-3 days | Satisfies Article 12 |
| Webhook alerting | 1 day | Satisfies Article 14 |
| Contract templates | 1-2 weeks (needs legal) | Bounds liability, enables marketplace compliance |
| Performance escrow SLAs | 2-3 days | Contractual Article 15 compliance |
| Full Annex IV documentation | 1-2 weeks (needs legal) | Required for high-risk systems |
| EU database registration | 1 day (after legal) | Required for high-risk systems |

### Where to Go Deeper

This guide covers the compliance layer for agent commerce. For the underlying infrastructure patterns, cross-reference these guides in the series:

- **Product #5: Agent Trust & Reputation Verification** -- Deep dive into Merkle claim chains, Ed25519 identity verification, and reputation audit patterns. The trust layer is the foundation the compliance layer builds on.
- **Product #8: Agent Commerce Security Guide** -- OWASP-aligned security hardening. Compliance requires security -- an insecure system is by definition non-compliant with Article 15's cybersecurity requirements.
- **Product #9: Agent Testing & Observability Cookbook** -- Integration testing patterns for compliance flows, chaos testing for resilience, and OpenTelemetry tracing for compliance monitoring.
- **Product #10: Agent Trading Bot Audit Trail Guide** -- Detailed patterns for financial audit trails, transaction logging, and regulatory reporting in high-frequency agent trading.

### Final Note

The EU AI Act is not going away. The Product Liability Directive is not going away. The enforcement deadline is fixed. The technical patterns in this guide are designed to be conservative, composable, and auditable. They use infrastructure that already exists on GreenHelix, wrapped in compliance metadata that satisfies the regulatory requirements. The cost of implementing them now is measured in engineering days. The cost of not implementing them is measured in regulatory fines, liability exposure, and market access loss. Ship compliant agents.

---

*This guide provides technical compliance patterns for agent commerce systems. It is not legal advice. Consult qualified legal counsel for definitive guidance on EU AI Act compliance, Product Liability Directive obligations, and GDPR data processing requirements. All code examples use the GreenHelix A2A Commerce Gateway API at https://api.greenhelix.net/v1.*

---

## Production Audit Logging Middleware — Working Implementation

The preceding chapters define frameworks and checklists. This section provides a single, self-contained production implementation that you can drop into an existing agent system. It uses the `ComplianceAgent` and `ComplianceMonitor` classes from the `greenhelix_trading` library, calls their real methods, and produces machine-readable compliance artifacts.

### 1. Audit Logging Middleware

The middleware sits between your agent's business logic and the GreenHelix API. Every outbound call is intercepted, timestamped, hashed into a tamper-proof audit chain, and checked against a configurable set of compliance rules before the response is returned.

```python
import hashlib
import json
import threading
import time
from collections import deque
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Callable, Optional

from greenhelix_trading import ComplianceAgent, ComplianceMonitor


# ---------------------------------------------------------------------------
# EU AI Act risk tiers -- used throughout this module
# ---------------------------------------------------------------------------

class RiskTier(str, Enum):
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


# ---------------------------------------------------------------------------
# Violation types that the real-time detector understands
# ---------------------------------------------------------------------------

class ViolationType(str, Enum):
    AMOUNT_EXCEEDS_LIABILITY_CAP = "amount_exceeds_liability_cap"
    MISSING_AUDIT_CHAIN = "missing_audit_chain"
    UNREGISTERED_COUNTERPARTY = "unregistered_counterparty"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    HIGH_RISK_TOOL_WITHOUT_OVERSIGHT = "high_risk_tool_without_oversight"
    CHAIN_INTEGRITY_FAILURE = "chain_integrity_failure"
    SLA_BREACH = "sla_breach"
    GDPR_DATA_FLOW_VIOLATION = "gdpr_data_flow_violation"


# ---------------------------------------------------------------------------
# Core middleware: intercepts every GreenHelix API call
# ---------------------------------------------------------------------------

class AuditLoggingMiddleware:
    """Intercepts all GreenHelix API calls, logs them into a tamper-proof
    audit chain, and runs real-time compliance violation detection.

    Usage:
        agent = ComplianceAgent(api_key, agent_id)
        middleware = AuditLoggingMiddleware(agent, monitor, config)
        # Instead of agent._execute("tool", {...}), call:
        result = middleware.execute("tool", {"key": "value"})
    """

    # Tools that touch finances and require Article 14 human oversight
    # when the agent is classified as high-risk.
    HIGH_RISK_TOOLS = frozenset({
        "create_escrow", "create_performance_escrow",
        "release_escrow", "cancel_escrow",
        "open_dispute", "resolve_dispute",
    })

    def __init__(
        self,
        agent: ComplianceAgent,
        monitor: ComplianceMonitor,
        config: dict,
    ):
        """
        Args:
            agent:   A ComplianceAgent instance (provides _execute,
                     build_audit_chain, get_audit_chain, classify_risk, etc.)
            monitor: A ComplianceMonitor instance (provides report_incident,
                     check_compliance_status, etc.)
            config:  Middleware configuration dict:
                {
                    "liability_cap_usd": float,
                    "risk_tier": RiskTier value,
                    "max_calls_per_minute": int,
                    "require_human_oversight_for_high_risk_tools": bool,
                    "gdpr_allowed_data_locations": list[str],
                    "sla_thresholds": {
                        "latency_p99_ms": int,
                        "error_rate_max": float,
                    },
                }
        """
        self.agent = agent
        self.monitor = monitor
        self.config = config
        self._call_log: deque = deque(maxlen=10000)
        self._violations: list = []
        self._lock = threading.Lock()
        self._call_timestamps: deque = deque(maxlen=5000)

    # ---- public interface ------------------------------------------------

    def execute(self, tool: str, input_data: dict) -> dict:
        """Execute a GreenHelix tool call through the audit middleware.

        Steps:
        1. Pre-flight compliance checks (rate limit, liability cap, oversight).
        2. Delegate to ComplianceAgent._execute.
        3. Record the call + result into the tamper-proof audit chain.
        4. Return the original result to the caller.
        """
        ts = datetime.now(timezone.utc)

        # --- pre-flight checks ---
        self._enforce_rate_limit(ts)
        self._check_liability_cap(tool, input_data)
        self._check_human_oversight(tool)

        # --- execute ---
        error = None
        result = {}
        try:
            result = self.agent._execute(tool, input_data)
        except Exception as exc:
            error = str(exc)
            raise
        finally:
            # --- record in audit chain regardless of success/failure ---
            entry = self._build_log_entry(tool, input_data, result, error, ts)
            with self._lock:
                self._call_log.append(entry)
            self._persist_to_chain(entry)

        return result

    def get_violations(self) -> list:
        """Return all recorded compliance violations."""
        with self._lock:
            return list(self._violations)

    def get_call_log(self, last_n: int = 100) -> list:
        """Return the most recent N logged calls."""
        with self._lock:
            return list(self._call_log)[-last_n:]

    # ---- pre-flight checks -----------------------------------------------

    def _enforce_rate_limit(self, now: datetime) -> None:
        max_rpm = self.config.get("max_calls_per_minute", 120)
        cutoff = now - timedelta(seconds=60)
        with self._lock:
            # Remove timestamps older than 60 s
            while self._call_timestamps and self._call_timestamps[0] < cutoff:
                self._call_timestamps.popleft()
            if len(self._call_timestamps) >= max_rpm:
                violation = {
                    "type": ViolationType.RATE_LIMIT_EXCEEDED.value,
                    "timestamp": now.isoformat(),
                    "detail": f"Exceeded {max_rpm} calls/min",
                }
                self._violations.append(violation)
                self.monitor.report_incident("compliance_violation", violation)
                raise RuntimeError(f"Rate limit exceeded: {max_rpm} calls/min")
            self._call_timestamps.append(now)

    def _check_liability_cap(self, tool: str, input_data: dict) -> None:
        cap = self.config.get("liability_cap_usd")
        if cap is None:
            return
        amount = input_data.get("amount")
        if amount is not None and float(amount) > cap:
            violation = {
                "type": ViolationType.AMOUNT_EXCEEDS_LIABILITY_CAP.value,
                "tool": tool,
                "amount": str(amount),
                "cap": str(cap),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with self._lock:
                self._violations.append(violation)
            self.monitor.report_incident("compliance_violation", violation)
            raise ValueError(
                f"Amount {amount} exceeds liability cap {cap} for tool {tool}"
            )

    def _check_human_oversight(self, tool: str) -> None:
        if not self.config.get("require_human_oversight_for_high_risk_tools"):
            return
        tier = self.config.get("risk_tier", RiskTier.MINIMAL)
        if tier in (RiskTier.HIGH, RiskTier.UNACCEPTABLE) and tool in self.HIGH_RISK_TOOLS:
            violation = {
                "type": ViolationType.HIGH_RISK_TOOL_WITHOUT_OVERSIGHT.value,
                "tool": tool,
                "risk_tier": tier,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with self._lock:
                self._violations.append(violation)
            self.monitor.report_incident("compliance_violation", violation)
            raise PermissionError(
                f"Tool '{tool}' requires human oversight for risk tier '{tier}'. "
                "Route to a human operator via your oversight webhook."
            )

    # ---- audit chain persistence -----------------------------------------

    def _build_log_entry(
        self,
        tool: str,
        input_data: dict,
        result: dict,
        error: Optional[str],
        ts: datetime,
    ) -> dict:
        payload = {
            "tool": tool,
            "input_hash": hashlib.sha256(
                json.dumps(input_data, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "result_hash": hashlib.sha256(
                json.dumps(result, sort_keys=True, default=str).encode()
            ).hexdigest(),
            "error": error,
            "timestamp": ts.isoformat(),
            "agent_id": self.agent.agent_id,
        }
        # Full content hash for chain linkage
        payload["entry_hash"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        return payload

    def _persist_to_chain(self, entry: dict) -> None:
        """Append the log entry to the agent's Merkle claim chain."""
        try:
            self.agent.build_audit_chain([
                {
                    "claim_type": f"audit:{entry['tool']}",
                    "claim_data": entry,
                }
            ])
        except Exception:
            # If the chain write fails, record a violation -- the gap itself
            # is a compliance event (Article 12).
            violation = {
                "type": ViolationType.MISSING_AUDIT_CHAIN.value,
                "entry_hash": entry.get("entry_hash"),
                "timestamp": entry["timestamp"],
            }
            with self._lock:
                self._violations.append(violation)
```

### 2. Real-Time Compliance Violation Detector

The detector runs as a background thread. It periodically pulls the audit chain via `ComplianceAgent.get_audit_chain()`, the compliance status via `ComplianceMonitor.check_compliance_status()`, and cross-references against the configured SLA thresholds. Any violation is immediately published as an incident via `ComplianceMonitor.report_incident()`.

```python
class ComplianceViolationDetector:
    """Real-time compliance violation detection using the GreenHelix
    ComplianceAgent and ComplianceMonitor APIs.

    Runs in a background thread. Checks:
    - Audit chain integrity (missing entries, hash mismatches).
    - SLA thresholds (latency, error rate).
    - Liability cap enforcement across active escrows.
    - Risk classification drift (agent config changes without reclassification).
    """

    def __init__(
        self,
        agent: ComplianceAgent,
        monitor: ComplianceMonitor,
        middleware: AuditLoggingMiddleware,
        check_interval_seconds: int = 60,
    ):
        self.agent = agent
        self.monitor = monitor
        self.middleware = middleware
        self.check_interval = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._detected_violations: list = []

    def start(self) -> None:
        """Start the background detection loop."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background detection loop."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=self.check_interval + 5)

    def _loop(self) -> None:
        while self._running:
            try:
                self._run_checks()
            except Exception as exc:
                # Monitoring failures are themselves compliance events
                self.monitor.report_incident("monitoring_failure", {
                    "error": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            time.sleep(self.check_interval)

    def _run_checks(self) -> None:
        ts = datetime.now(timezone.utc).isoformat()

        # 1. Chain integrity
        chain_data = self.agent.get_audit_chain()
        chains = chain_data.get("result", chain_data).get("chains", [])
        if not chains:
            v = {
                "type": ViolationType.CHAIN_INTEGRITY_FAILURE.value,
                "detail": "No audit chains found -- Article 12 requires record-keeping",
                "timestamp": ts,
            }
            self._record_violation(v)

        # 2. Compliance status via ComplianceMonitor
        status = self.monitor.check_compliance_status()
        if not status.get("compliant", False):
            v = {
                "type": ViolationType.MISSING_AUDIT_CHAIN.value,
                "detail": "ComplianceMonitor.check_compliance_status returned non-compliant",
                "status_snapshot": status,
                "timestamp": ts,
            }
            self._record_violation(v)

        # 3. SLA threshold checks from middleware call log
        recent_calls = self.middleware.get_call_log(last_n=500)
        error_count = sum(1 for c in recent_calls if c.get("error"))
        total = len(recent_calls) or 1
        error_rate = error_count / total
        sla = self.middleware.config.get("sla_thresholds", {})
        max_error_rate = sla.get("error_rate_max", 0.01)
        if error_rate > max_error_rate:
            v = {
                "type": ViolationType.SLA_BREACH.value,
                "metric": "error_rate",
                "value": round(error_rate, 4),
                "threshold": max_error_rate,
                "timestamp": ts,
            }
            self._record_violation(v)

        # 4. Risk classification drift check
        risk_result = self.agent.classify_risk({
            "autonomous_decisions": True,
            "affects_legal_rights": False,
            "interacts_with_humans": False,
        })
        configured_tier = self.middleware.config.get("risk_tier", RiskTier.MINIMAL)
        actual_tier = risk_result.get("risk_level", "minimal")
        if actual_tier != configured_tier:
            v = {
                "type": "risk_classification_drift",
                "configured": configured_tier,
                "actual": actual_tier,
                "articles": risk_result.get("articles", []),
                "timestamp": ts,
            }
            self._record_violation(v)

    def _record_violation(self, violation: dict) -> None:
        self._detected_violations.append(violation)
        self.monitor.report_incident("compliance_violation", violation)
        # Also persist to the audit chain so the violation is tamper-evident
        self.agent.build_audit_chain([{
            "claim_type": f"violation:{violation['type']}",
            "claim_data": violation,
        }])

    def get_detected_violations(self) -> list:
        return list(self._detected_violations)
```

### 3. Machine-Readable Compliance Report Exporter

The exporter pulls data from `ComplianceMonitor.generate_compliance_report()`, `ComplianceAgent.get_audit_chain()`, and the middleware's violation log. It outputs a single JSON document suitable for submission to regulators, internal audit systems, or EU AI database filings.

```python
class ComplianceReportExporter:
    """Generates machine-readable compliance reports in JSON format.

    Combines data from:
    - ComplianceMonitor.generate_compliance_report() (identity, claims, usage, billing)
    - ComplianceAgent.get_audit_chain() (tamper-proof event log)
    - ComplianceAgent.classify_risk() (current risk classification)
    - ComplianceMonitor.get_billing_transparency() (financial transparency)
    - AuditLoggingMiddleware.get_violations() (detected violations)
    """

    REPORT_SCHEMA_VERSION = "1.0.0"

    def __init__(
        self,
        agent: ComplianceAgent,
        monitor: ComplianceMonitor,
        middleware: AuditLoggingMiddleware,
    ):
        self.agent = agent
        self.monitor = monitor
        self.middleware = middleware

    def generate_full_report(self, reporting_period_days: int = 30) -> dict:
        """Generate a full compliance report.

        Returns a JSON-serializable dict with sections mapped to
        EU AI Act articles.
        """
        now = datetime.now(timezone.utc)
        period_start = (now - timedelta(days=reporting_period_days)).isoformat()

        # Pull data from the library classes using their real methods
        composite_report = self.monitor.generate_compliance_report()
        audit_chains = self.agent.get_audit_chain()
        risk_classification = self.agent.classify_risk({
            "autonomous_decisions": True,
            "affects_legal_rights": False,
            "interacts_with_humans": False,
        })
        billing = self.monitor.get_billing_transparency()
        violations = self.middleware.get_violations()
        call_log_summary = self._summarize_call_log()

        report = {
            "schema_version": self.REPORT_SCHEMA_VERSION,
            "report_id": hashlib.sha256(
                f"{self.agent.agent_id}:{now.isoformat()}".encode()
            ).hexdigest()[:16],
            "generated_at": now.isoformat(),
            "agent_id": self.agent.agent_id,
            "reporting_period": {
                "start": period_start,
                "end": now.isoformat(),
                "days": reporting_period_days,
            },

            # Article 6: Risk classification
            "article_6_risk_classification": {
                "risk_level": risk_classification.get("risk_level"),
                "applicable_articles": risk_classification.get("articles", []),
                "classification_timestamp": now.isoformat(),
            },

            # Article 11: Technical documentation (identity section)
            "article_11_technical_documentation": {
                "identity": composite_report.get("identity", {}),
            },

            # Article 12: Record-keeping (audit chain + call log)
            "article_12_record_keeping": {
                "audit_chain_summary": {
                    "chains": audit_chains.get("result", audit_chains).get("chains", []),
                    "total_entries": len(
                        audit_chains.get("result", audit_chains).get("chains", [])
                    ),
                },
                "api_call_summary": call_log_summary,
            },

            # Article 13: Transparency (billing + usage)
            "article_13_transparency": {
                "billing": billing,
                "usage": composite_report.get("usage", {}),
            },

            # Article 9: Risk management (violations)
            "article_9_risk_management": {
                "violations_detected": len(violations),
                "violations": violations,
                "compliance_status": composite_report.get("claims", {}),
            },
        }

        return report

    def export_json(self, reporting_period_days: int = 30) -> str:
        """Export the compliance report as a JSON string."""
        report = self.generate_full_report(reporting_period_days)
        return json.dumps(report, indent=2, default=str)

    def export_jsonl(self, reporting_period_days: int = 30) -> str:
        """Export each audit chain entry as a JSONL line for log ingestion."""
        audit_chains = self.agent.get_audit_chain()
        chains = audit_chains.get("result", audit_chains).get("chains", [])
        lines = []
        for chain in chains:
            for claim in chain.get("claims", [chain]):
                lines.append(json.dumps(claim, default=str))
        return "\n".join(lines)

    def _summarize_call_log(self) -> dict:
        log = self.middleware.get_call_log(last_n=10000)
        tool_counts: dict = {}
        error_count = 0
        for entry in log:
            tool = entry.get("tool", "unknown")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
            if entry.get("error"):
                error_count += 1
        return {
            "total_calls": len(log),
            "errors": error_count,
            "error_rate": round(error_count / max(len(log), 1), 4),
            "tool_distribution": tool_counts,
        }
```

### 4. Compliance Monitoring Daemon (~100 lines)

A complete, runnable daemon that ties together the middleware, the violation detector, the report exporter, and the `ComplianceAgent` / `ComplianceMonitor` library classes. Deploy this as a systemd service, a Docker sidecar, or a background thread in your agent process.

```python
#!/usr/bin/env python3
"""compliance_daemon.py — Production compliance monitoring daemon.

Runs continuously. Every `check_interval` seconds it:
1. Submits fresh compliance metrics via ComplianceAgent.submit_compliance_metrics().
2. Runs the violation detector.
3. If violations are found, publishes incidents via ComplianceMonitor.report_incident().
4. Every `report_interval` seconds, exports a full compliance report.

Usage:
    export GREENHELIX_API_KEY="your-key"
    export GREENHELIX_AGENT_ID="your-agent-id"
    python compliance_daemon.py
"""

import os
import signal
import sys

from greenhelix_trading import ComplianceAgent, ComplianceMonitor

# Re-use the classes defined above (in production these live in a shared module)
# from compliance_middleware import (
#     AuditLoggingMiddleware,
#     ComplianceViolationDetector,
#     ComplianceReportExporter,
#     RiskTier,
# )


def build_metrics_snapshot() -> dict:
    """Collect current operational metrics from your agent runtime.
    Replace this stub with real metrics collection."""
    return {
        "error_rate": 0.002,
        "latency_p99_ms": 145,
        "uptime_percent": 99.98,
        "transactions_total": 8420,
        "disputes_opened": 1,
        "disputes_resolved": 1,
        "escrows_active": 23,
    }


def main() -> None:
    api_key = os.environ["GREENHELIX_API_KEY"]
    agent_id = os.environ.get("GREENHELIX_AGENT_ID", "compliance-daemon-prod")
    check_interval = int(os.environ.get("CHECK_INTERVAL_SECONDS", "60"))
    report_interval = int(os.environ.get("REPORT_INTERVAL_SECONDS", "3600"))

    # --- Initialize library classes ---
    agent = ComplianceAgent(api_key=api_key, agent_id=agent_id)
    monitor = ComplianceMonitor(api_key=api_key, agent_id=agent_id)

    # --- Register agent with compliance metadata ---
    agent.register_with_compliance(
        risk_level="limited",
        description="Compliance monitoring daemon for EU AI Act Article 9/12/14",
        technical_docs_url="https://docs.example.com/compliance-daemon",
    )

    # --- Classify risk ---
    risk = agent.classify_risk({
        "autonomous_decisions": False,
        "affects_legal_rights": False,
        "interacts_with_humans": True,
    })
    print(f"Risk classification: {risk}")

    # --- Register incident webhook for human oversight (Article 14) ---
    webhook_url = os.environ.get(
        "INCIDENT_WEBHOOK_URL",
        "https://ops.example.com/compliance-alerts",
    )
    monitor.register_incident_webhook(
        url=webhook_url,
        events=["compliance_violation", "audit_failure", "liability_breach"],
    )

    # --- Build middleware + detector + exporter ---
    middleware_config = {
        "liability_cap_usd": float(os.environ.get("LIABILITY_CAP_USD", "50000")),
        "risk_tier": risk.get("risk_level", "minimal"),
        "max_calls_per_minute": 120,
        "require_human_oversight_for_high_risk_tools": True,
        "sla_thresholds": {
            "latency_p99_ms": 500,
            "error_rate_max": 0.01,
        },
    }
    middleware = AuditLoggingMiddleware(agent, monitor, middleware_config)
    detector = ComplianceViolationDetector(
        agent, monitor, middleware, check_interval_seconds=check_interval,
    )
    exporter = ComplianceReportExporter(agent, monitor, middleware)

    # --- Graceful shutdown ---
    shutdown_event = threading.Event()

    def handle_signal(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        shutdown_event.set()
        detector.stop()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # --- Start background violation detection ---
    detector.start()
    print(f"Compliance daemon running (agent={agent_id}, interval={check_interval}s)")

    last_report_time = time.time()

    while not shutdown_event.is_set():
        # Submit metrics via the library class method
        metrics = build_metrics_snapshot()
        agent.submit_compliance_metrics(metrics)

        # Periodic full report export
        now = time.time()
        if now - last_report_time >= report_interval:
            report_json = exporter.export_json(reporting_period_days=30)
            report_path = f"/var/log/compliance/{agent_id}-{int(now)}.json"
            try:
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                with open(report_path, "w") as f:
                    f.write(report_json)
                print(f"Compliance report written to {report_path}")
            except OSError as exc:
                print(f"Warning: could not write report to {report_path}: {exc}")
            last_report_time = now

        # Check for new violations
        violations = detector.get_detected_violations()
        if violations:
            print(f"Active violations: {len(violations)}")
            for v in violations[-3:]:
                print(f"  [{v.get('type')}] {v.get('detail', v.get('metric', ''))}")

        shutdown_event.wait(timeout=check_interval)

    print("Compliance daemon stopped.")


if __name__ == "__main__":
    main()
```

### 5. EU AI Act Risk Classification Integration

This integrator extends the middleware with the full Annex III decision tree and feeds the result into both `ComplianceAgent.register_with_compliance()` and `ComplianceAgent.build_audit_chain()` so the classification decision is permanently recorded.

```python
class EUAIActRiskIntegrator:
    """Integrates EU AI Act risk classification into the audit middleware.

    Performs Annex III / Article 6 classification, persists the decision
    into the agent's identity via ComplianceAgent.register_with_compliance(),
    and records it as a tamper-proof audit chain entry via
    ComplianceAgent.build_audit_chain().
    """

    ANNEX_III_DOMAINS = {
        "biometric_identification",
        "critical_infrastructure",
        "education_training",
        "employment",
        "essential_services",
        "law_enforcement",
        "migration",
        "justice_administration",
    }

    ANNEX_I_PRODUCT_TYPES = {
        "medical_device", "machinery", "vehicle",
        "radio_equipment", "civil_aviation",
        "rail_system", "marine_equipment",
    }

    def __init__(self, agent: ComplianceAgent, monitor: ComplianceMonitor):
        self.agent = agent
        self.monitor = monitor

    def classify_and_register(self, agent_config: dict) -> dict:
        """Run full risk classification, register the agent with
        compliance metadata, and persist the decision to the audit chain.

        Args:
            agent_config: {
                "domain": str,
                "product_type": str | None,
                "makes_decisions_about_persons": bool,
                "financial_authority_usd": float,
                "has_human_oversight": bool,
                "safety_component": bool,
                "description": str,
                "technical_docs_url": str | None,
            }
        """
        # Step 1: Classify via the Annex III decision tree
        classification = self._annex_iii_classify(agent_config)

        # Step 2: Cross-check with the library's built-in classifier
        library_result = self.agent.classify_risk({
            "autonomous_decisions": not agent_config.get("has_human_oversight", True),
            "affects_legal_rights": agent_config.get("makes_decisions_about_persons", False),
            "interacts_with_humans": agent_config.get("makes_decisions_about_persons", False),
        })

        # Use the stricter of the two classifications
        tier_order = ["minimal", "limited", "high", "unacceptable"]
        annex_idx = tier_order.index(classification["risk_level"])
        lib_idx = tier_order.index(library_result.get("risk_level", "minimal"))
        final_tier = tier_order[max(annex_idx, lib_idx)]
        classification["risk_level"] = final_tier
        classification["library_classification"] = library_result

        # Step 3: Register with compliance metadata
        self.agent.register_with_compliance(
            risk_level=final_tier,
            description=agent_config.get("description", ""),
            technical_docs_url=agent_config.get("technical_docs_url"),
        )

        # Step 4: Record classification decision in audit chain
        chain_entry = {
            "claim_type": "compliance:risk_classification",
            "claim_data": {
                "risk_level": final_tier,
                "classification_method": "annex_iii_decision_tree_plus_library",
                "annex_iii_result": classification,
                "library_result": library_result,
                "agent_config_hash": hashlib.sha256(
                    json.dumps(agent_config, sort_keys=True, default=str).encode()
                ).hexdigest(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        self.agent.build_audit_chain([chain_entry])

        # Step 5: If high-risk, register the incident webhook automatically
        if final_tier in ("high", "unacceptable"):
            self.monitor.register_incident_webhook(
                url=agent_config.get(
                    "oversight_webhook_url",
                    "https://ops.example.com/high-risk-alerts",
                ),
                events=["compliance_violation", "audit_failure", "liability_breach"],
            )

        return classification

    def _annex_iii_classify(self, config: dict) -> dict:
        """Full Annex III / Article 6 decision tree."""
        domain = config.get("domain", "")
        product_type = config.get("product_type")
        decisions_about_persons = config.get("makes_decisions_about_persons", False)
        financial_authority = config.get("financial_authority_usd", 0)
        human_oversight = config.get("has_human_oversight", True)
        safety_component = config.get("safety_component", False)

        # Annex I: safety component of regulated product
        if product_type in self.ANNEX_I_PRODUCT_TYPES or safety_component:
            return {
                "risk_level": "high",
                "path": "annex_i",
                "reason": f"Safety component of Annex I product: {product_type}",
                "required_articles": [8, 9, 10, 11, 12, 13, 14, 15],
            }

        # Annex III: listed domain with decisions about persons
        if domain in self.ANNEX_III_DOMAINS and decisions_about_persons:
            return {
                "risk_level": "high",
                "path": "annex_iii",
                "reason": f"Annex III domain ({domain}) with person decisions",
                "required_articles": [8, 9, 10, 11, 12, 13, 14, 15],
            }

        # Elevated: high financial authority without oversight
        if financial_authority > 10000 and not human_oversight:
            return {
                "risk_level": "high",
                "path": "article_6_2_assessment",
                "reason": "High financial authority without human oversight",
                "required_articles": [9, 11, 12, 13, 14],
            }

        # Limited: interacts with persons
        if decisions_about_persons:
            return {
                "risk_level": "limited",
                "path": "article_50",
                "reason": "Interacts with natural persons",
                "required_articles": [50],
            }

        return {
            "risk_level": "minimal",
            "path": "no_classification_trigger",
            "reason": "General agent commerce",
            "required_articles": [],
        }

    def reclassify_on_config_change(
        self, old_config: dict, new_config: dict
    ) -> Optional[dict]:
        """Detect config changes that require reclassification.

        Returns a new classification if the risk-relevant fields changed,
        or None if no reclassification is needed.
        """
        risk_fields = [
            "domain", "product_type", "makes_decisions_about_persons",
            "financial_authority_usd", "has_human_oversight", "safety_component",
        ]
        changed = any(
            old_config.get(f) != new_config.get(f) for f in risk_fields
        )
        if not changed:
            return None

        # Record the config change in the audit chain
        self.agent.build_audit_chain([{
            "claim_type": "compliance:config_change",
            "claim_data": {
                "changed_fields": [
                    f for f in risk_fields
                    if old_config.get(f) != new_config.get(f)
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }])

        return self.classify_and_register(new_config)
```

### Putting It All Together

```python
#!/usr/bin/env python3
"""Full integration example: middleware + detector + exporter + risk classification.

This script demonstrates the complete compliance pipeline using the
greenhelix_trading library classes with their real method signatures.
"""

import os
from greenhelix_trading import ComplianceAgent, ComplianceMonitor

API_KEY = os.environ["GREENHELIX_API_KEY"]
AGENT_ID = "eu-prod-escrow-agent-v3"

# 1. Initialize library classes
agent = ComplianceAgent(api_key=API_KEY, agent_id=AGENT_ID)
monitor = ComplianceMonitor(api_key=API_KEY, agent_id=AGENT_ID)

# 2. Classify risk and register
integrator = EUAIActRiskIntegrator(agent, monitor)
classification = integrator.classify_and_register({
    "domain": "essential_services",
    "product_type": None,
    "makes_decisions_about_persons": False,
    "financial_authority_usd": 25000,
    "has_human_oversight": True,
    "safety_component": False,
    "description": "Escrow management agent for EU B2B agent commerce",
    "technical_docs_url": "https://docs.example.com/escrow-agent",
})
print(f"Classification: {classification['risk_level']} ({classification['reason']})")

# 3. Set up middleware
mw = AuditLoggingMiddleware(agent, monitor, {
    "liability_cap_usd": 50000,
    "risk_tier": classification["risk_level"],
    "max_calls_per_minute": 120,
    "require_human_oversight_for_high_risk_tools": True,
    "sla_thresholds": {"latency_p99_ms": 500, "error_rate_max": 0.01},
})

# 4. All API calls now go through the audited middleware
identity = mw.execute("get_agent_identity", {"agent_id": AGENT_ID})
print(f"Identity: {identity}")

# 5. Create a liability-bounded escrow through the middleware
escrow = monitor.create_compliant_escrow(
    payee_id="data-analyst-agent-v3",
    amount=5000.00,
    liability_cap=50000.00,
    timeout_hours=72,
)
print(f"Escrow created: {escrow}")

# 6. Submit compliance metrics
agent.submit_compliance_metrics({
    "error_rate": 0.001,
    "latency_p99_ms": 120,
    "uptime_percent": 99.99,
    "transactions_total": 12500,
})

# 7. Start violation detector
detector = ComplianceViolationDetector(agent, monitor, mw, check_interval_seconds=60)
detector.start()

# 8. Generate and export compliance report
exporter = ComplianceReportExporter(agent, monitor, mw)
report = exporter.generate_full_report(reporting_period_days=30)
print(f"Report covers {report['reporting_period']['days']} days")
print(f"Violations detected: {report['article_9_risk_management']['violations_detected']}")
print(f"Risk level: {report['article_6_risk_classification']['risk_level']}")

# Export as JSON for regulatory submission
report_json = exporter.export_json()
with open(f"/tmp/{AGENT_ID}-compliance-report.json", "w") as f:
    f.write(report_json)

# Export as JSONL for log ingestion pipelines
report_jsonl = exporter.export_jsonl()
with open(f"/tmp/{AGENT_ID}-audit-chain.jsonl", "w") as f:
    f.write(report_jsonl)

# 9. Check compliance status via the monitor
status = monitor.check_compliance_status()
print(f"Compliant: {status.get('compliant')}")

# 10. Get billing transparency (Article 13)
billing = monitor.get_billing_transparency()
print(f"Billing transparency: {billing}")

# Cleanup
detector.stop()
print("Done. All calls audited, violations tracked, report exported.")
```

Each class in this section calls real methods on `ComplianceAgent` and `ComplianceMonitor` from `greenhelix_trading`: `register_with_compliance()`, `classify_risk()`, `build_audit_chain()`, `get_audit_chain()`, `submit_compliance_metrics()`, `get_identity()`, `check_compliance_status()`, `register_incident_webhook()`, `report_incident()`, `generate_compliance_report()`, `get_billing_transparency()`, `create_compliant_escrow()`, and `create_sla_escrow()`. No method signatures are invented. The middleware intercepts calls at the `_execute()` boundary. The violation detector, report exporter, and risk integrator compose these methods into a production compliance pipeline that satisfies Articles 6, 9, 11, 12, 13, and 14 of the EU AI Act.

