---
name: tronscan-contract-analysis
description: |
  Analyze TRON contracts: deploy info, hot methods, top callers, open-source status,
  transaction count.
  Use when user asks "contract verification", "contract safety", "hot methods", "who is calling the contract", or provides a contract address.
  Do NOT use for token supply/holders (use tronscan-token-scanner); address balance (use tronscan-account-profiler).
metadata:
  author: tronscan-mcp
  version: "1.0"
  mcp-server: https://mcp.tronscan.org/mcp
---

# Contract Analysis

## Overview

| Tool | Function | Use Case |
|------|----------|----------|
| getContractDetail | Contract info | Balance, verification, call count, method map |
| getContractCallStatistic | Call stats | Call count, top callers, top methods |
| getContractCallers | Caller list | Callers and call count for a given day |
| getContractEvents | Events | Transfer events and method calls |
| getContractList | Contract list | Search by name/address, sort, paginate |
| getContractEnergyStatistic | Energy usage | Total and daily energy consumption |
| getContractTriggerTransactions | Trigger txs | Contract-triggered transactions in time range |
| getContractAnalysis | Daily analysis | Balance, transfers, energy, bandwidth, calls, fee |
| getCallerAddressStatistic | Caller address stats | Contract call count per period with max/min |
| getContractTriggerStatistic | Daily trigger stats | Daily call count for a contract in a time range |
| getHolderTokenBasicInfo | Holder token info | Token balance and holding duration for an account |

## Use Cases

1. **Deploy & Basic Info**: Use `getContractDetail` for balance, verification status, call count, method mapping.
2. **Hot Methods**: Use `getContractCallStatistic` for top called methods.
3. **Top Callers**: Use `getContractCallStatistic` or `getContractCallers` for top 5 or full caller list.
4. **Open-source / Verification**: Verification status is in `getContractDetail`.
5. **Transaction Count**: Use `getContractDetail` or `getContractTriggerTransactions` for call/tx volume.
6. **Malicious Clues**: Combine events (`getContractEvents`), energy (`getContractEnergyStatistic`), and call stats to spot unusual patterns.

## MCP Server

- **Prerequisite**: [TronScan MCP Guide](https://mcpdoc.tronscan.org)

## Tools

### getContractDetail

- **API**: `getContractDetail` — Get contract details (balance, verification status, call count, method map)
- **Use when**: User asks for "contract info", "contract address", or "is contract verified".
- **Input**: `contract` (contract address) — Note: parameter name is `contract`, not `address`.
- **Response**: Balance, verified flag, call count, method map.

### getContractCallStatistic

- **API**: `getContractCallStatistic` — Get contract call stats (call count, top callers, top methods)
- **Use when**: User asks for "hot methods", "top callers", or "who calls this contract".
- **Input**: Contract address (and optional time range).
- **Response**: Call counts, top callers, top methods.

### getContractCallers

- **API**: `getContractCallers` — Get all callers and call count for a given day
- **Use when**: User asks for "caller list" or "who called today".
- **Input**: Contract address, date.

### getContractEvents

- **API**: `getContractEvents` — Get contract events (transfer events and method calls)
- **Use when**: User asks for "contract events" or "transfers from contract".
- **Input**: Contract address, pagination.

### getContractList

- **API**: `getContractList` — Get contract list with search by name/address, sort, pagination
- **Use when**: User searches contracts by keyword or browses list.

### getContractEnergyStatistic

- **API**: `getContractEnergyStatistic` — Get contract energy consumption (total and daily)
- **Use when**: User asks for "contract energy" or "gas usage".

### getContractTriggerTransactions

- **API**: `getContractTriggerTransactions` — Get contract-triggered transactions in a time range
- **Use when**: User asks for "contract transactions" or "recent calls".

### getContractAnalysis

- **API**: `getContractAnalysis` — Get contract daily analysis (balance, transfers, energy, bandwidth, calls, fee)
- **Use when**: User asks for "contract activity over time".

### getCallerAddressStatistic

- **API**: `getCallerAddressStatistic` — Get contract call count per period (with max/min) on TRON
- **Use when**: User asks for "call volume over time" or "contract call statistics by period".
- **Input**: `startTimestamp`, `endTimestamp` (required); optional `limit`.

### getContractTriggerStatistic

- **API**: `getContractTriggerStatistic` — Get daily call count for a contract within a time range
- **Use when**: User asks for "daily call count", "contract trigger trend", or "how often is this contract called".
- **Input**: `address`, `startTimestamp`, `endTimestamp` (all required).
- **Response**: Daily call count and total call count.

### getHolderTokenBasicInfo

- **API**: `getHolderTokenBasicInfo` — Get token balance and holding duration for an account
- **Use when**: User asks for "how long has this address held this token" or "token holding details".
- **Input**: `accountAddress`, `tokenAddress` (both required).

## Troubleshooting

- **MCP connection failed**: If you see "Connection refused", verify TronScan MCP is connected in Settings > Extensions.
- **API rate limit / 429**: TronScan API has call count and frequency limits when no API key is used. If you encounter rate limiting or 429 errors, go to [TronScan Developer API](https://tronscan.org/#/developer/api) to apply for an API key, then add it to your MCP configuration and retry.

### Invalid contract address
Ensure the address is a valid TRON contract (not an EOA address). Use TRC20/721/1155 contract address for token contracts.

## Notes

- To assess malicious risk: check verification, top methods (unusual names), energy spike, and event patterns.
- Top 5 callers and top methods come from `getContractCallStatistic`.
- **Contract verification scope**: `getContractDetail` returns **contract-level** verification status (whether the contract source code has been open-sourced and verified on TronScan). This is a code-level check only — it does not indicate whether the token project itself has been officially endorsed or certified.
