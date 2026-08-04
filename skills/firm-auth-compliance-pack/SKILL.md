---
name: firm-auth-compliance-pack
version: 1.0.0
description: >
  Authentication and compliance audit pack.
  OAuth 2.1/OIDC Discovery, token scope enforcement, tool deprecation lifecycle,
  circuit breaker, GDPR residency, DID identity, model routing, and resource links.
  8 compliance tools.
author: romainsantoli-web
license: MIT
metadata:
  openclaw:
    registry: ClawHub
    requires:
      - mcp-openclaw-extensions >= 3.0.0
tags:
  - auth
  - compliance
  - oauth
  - gdpr
  - did
---

# firm-auth-compliance-pack

> ⚠️ Contenu généré par IA — validation humaine requise avant utilisation.

## Purpose

Comprehensive authentication and compliance auditing: OAuth 2.1 / OIDC Discovery
compliance (PKCE, RFC 9728, RFC 8707), token scope enforcement, tool deprecation
lifecycle, circuit breaker patterns, GDPR data residency, W3C DID identity,
multi-model routing, and resource links validation.

## Tools (8)

| Tool | Description | Severity |
|------|-------------|----------|
| `openclaw_oauth_oidc_audit` | OAuth 2.1 / OIDC Discovery compliance | HIGH |
| `openclaw_token_scope_check` | Token scope enforcement | HIGH |
| `openclaw_tool_deprecation_audit` | Tool deprecation lifecycle audit | MEDIUM |
| `openclaw_circuit_breaker_audit` | Circuit breaker pattern validation | MEDIUM |
| `openclaw_gdpr_residency_audit` | GDPR data residency compliance | MEDIUM |
| `openclaw_agent_identity_audit` | W3C DID agent identity validation | MEDIUM |
| `openclaw_model_routing_audit` | Multi-model routing configuration | MEDIUM |
| `openclaw_resource_links_audit` | Resource links validation | MEDIUM |

## Usage

```yaml
skills:
  - firm-auth-compliance-pack

# Run compliance audit:
openclaw_oauth_oidc_audit config_path=/path/to/config.json
openclaw_gdpr_residency_audit config_path=/path/to/config.json
openclaw_agent_identity_audit config_path=/path/to/config.json
```

## Requirements

- `mcp-openclaw-extensions >= 3.0.0`
