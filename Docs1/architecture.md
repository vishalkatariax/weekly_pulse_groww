# Architecture: Groww Weekly Review AI Agent (MCP-Based)

## 1. Overview

This document describes the high-level architecture of the **Groww App Review Weekly Pulse** system. The system is designed as an autonomous, LLM-powered AI agent that ingests public app review exports (such as App Store and Play Store reviews), categorizes them into common application themes, synthesizes a concise "weekly pulse" report, and publishes the report to Google Docs and Gmail drafts using **Model Context Protocol (MCP)** servers.

Model selection for Phase 2: `llama-3.3-70b-versatile` with constrained request/ token quotas. Phase 2 is therefore implemented with a preprocessing + aggregation layer that minimizes per-call token usage and number of requests (see Section 3.3 and the implementation plan).

---

## 2. Architectural Principles

- **MCP-First Integration:** Rather than implementing direct, hardcoded OAuth flows and REST API clients for Google Docs and Gmail, the system communicates entirely through MCP servers. The core agent remains clean and service-agnostic, simply calling standardized tools exposed by the MCP host.
- **Separation of Concerns:** Ingestion, PII scrubbing, analysis, formatting, and publishing are isolated. Each layer exposes clear interfaces, allowing unit and integration testing in isolation.
- **Privacy by Design:** To prevent leakage of customer-identifiable information (PII) to LLMs and final reports, anonymization is applied at the ingestion boundary.
- **Stateless Agent Core:** Execution runs on a batch cadence (typically weekly) with no database storage dependencies. The filesystem is utilized strictly for caching raw reviews and logging run statistics.

---

## 3. System Components & Detailed Design

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Orchestrator / Agent Core                             │
│       - Coordinates execution steps (Ingestion -> Analysis -> Publishing)      │
│       - Manages config files, logging, execution dry-run status, & exceptions   │
└─────────┬──────────────────────────┬──────────────────────────┬─────────────────┘
          │                          │                          │
          ▼                          ▼                          ▼
┌───────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│ Ingestion Layer   │      │ Analysis Layer    │      │ Publishing Layer  │
│                   │      │                   │      │                   │
│ - CSV/JSON Loaders│      │ - Theme Classifier│      │ - Doc Generator   │
│ - Date-Filter     │      │ - Theme Ranker    │      │ - Email Formatter │
│ - PII Scrubbing   │      │ - Quote Selection │      │                   │
└─────────┬─────────┘      └─────────┬─────────┘      └─────────┬─────────┘
          │                          │                          │
          └──────────────────────────┼──────────────────────────┘
                                     │
                                     ▼
                       ┌──────────────────────────┐
                       │     MCP Client SDK       │
                       └─────────────┬────────────┘
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
        ┌──────────────────┐                  ┌──────────────────┐
        │ Google Docs MCP  │                  │    Gmail MCP     │
        │ Server           │                  │    Server        │
        └─────────┬────────┘                  └─────────┬────────┘
                  │                                     │
                  ▼                                     ▼
        ┌──────────────────┐                  ┌──────────────────┐
        │   Google Docs    │                  │  Gmail Drafts    │
        │ (Pulse Document)  │                  │  (Email Draft)   │
        └──────────────────┘                  └──────────────────┘
```

### 3.1 Orchestrator / Agent Core
The Orchestrator governs the lifecycle of a single weekly pulse generation run. 
*   **Workflow Coordination:** It reads the configuration, invokes the Ingestion Layer, passes the anonymized dataset to the Analysis Layer, receives the structured JSON analysis, formats it, and calls the Google Docs and Gmail MCP clients.
*   **Configuration Management:** A configuration file (`config.yaml`) sets critical variables including date ranges (defaulting to the last 8-12 weeks), file paths, target email recipients, and defined theme categories.
*   **Error Boundaries:** The orchestrator handles downstream failures. For example, if the Google Docs MCP server is unreachable, the orchestrator logs the incident and continues to run the Gmail MCP server (or caches the output locally) instead of crashing the process.

### 3.2 Data Ingestion & Anonymization Layer
This layer handles the reading and sanitization of raw review exports.
*   **Schema Enforcement:** Normalizes incoming records from both iOS App Store and Google Play Store into a unified schema: `id`, `rating`, `title`, `text`, `date`, and `source`.
*   **Date Window Filtering:** Extracts only reviews matching the designated week range (e.g., between $T-8$ weeks and $T-12$ weeks).
*   **PII Scrubbing Pipeline:** Raw reviews are run through an anonymizer that strips username handles (e.g., `@name`), email addresses, phone numbers, and potential user IDs using robust regex rules. This ensures only sanitized text reaches the LLM.

### 3.3 Thematic Analysis Layer (LLM: `llama-3.3-70b-versatile`)
The analysis layer uses `llama-3.3-70b-versatile` to process pre-aggregated review summaries rather than raw review text. Because the model has strict rate and token limits, a lightweight deterministic preprocessing stage organizes the data and reduces token use sent to the model.

*   **Step 1: Deterministic Theme Tagging:** The ingestion/preprocessing layer tags reviews to up to 5 product themes (Onboarding, KYC, Payments, Statements, Withdrawals) using keyword maps and simple classifiers. This produces theme buckets and counts.
*   **Step 2: Aggregation & Sampling:** From each theme, select representative, high-signal quotes (2–3 per theme) and aggregate counts by sentiment bucket (negative/neutral/positive). Limit the total review sample to ~1,000 reviews (configurable) to stay well within daily request and token budgets.
*   **Step 3: Batched Model Calls & Token Budgeting:** Create small structured payloads (theme summary, counts, 2–3 quotes) and call the model in batches sized to respect the model limits (see Model Constraints below). Each batch returns theme-level summaries and recommendations.
*   **Step 4: Synthesis & Recommendation Merge:** The assembler combines batched outputs into a single 250-word pulse and a structured JSON of themes, quotes, and 3 prioritized recommendations.

Model Constraints & Operational Guidance:

- **Model:** `llama-3.3-70b-versatile`
- **Request / minute:** 30
- **Requests / day:** 1,000
- **Tokens / minute:** 12,000
- **Tokens / day:** 100,000

To avoid hitting these limits the pipeline will:

- Pre-aggregate reviews and send structured payloads rather than raw text.
- Cap the analysis input to ~1,000 sampled reviews per run (configurable) and prioritize negative, high-signal reviews first.
- Use batching with a strict token budget per call (calculate estimated tokens per quote + metadata and keep batches small). Typical batch size targets will be in the range of 5–20 theme payloads per minute depending on token weight.
- Implement a rate-limiter that enforces 30 requests/minute and tracking for daily request and token usage with graceful backoff when approaching limits.
- Prefer multiple smaller calls that each return concise theme summaries, then merge client-side to produce the final 250-word pulse.

This design keeps the model work focused on summarization and recommendation generation from compact, high-signal inputs and preserves tokens for higher-quality outputs.

### 3.4 MCP Server Layer (Workspace Integration)
Rather than dealing with local OAuth configuration or web tokens, the agent client loads MCP-compliant configurations that map to local or remote Google Workspace MCP servers.
*   **Google Docs MCP Wrapper:** Converts the structured JSON summary into a formatted outline and sends request payloads to the Docs MCP server to generate a new document under a specified folder structure.
*   **Gmail MCP Wrapper:** Injects the document URL and plain-text pulse summary into an HTML template, calling the Gmail MCP server to create a draft email ready for stakeholder review.

---

## 4. Security, Credentials, and Isolation

- **Zero API Keys in Core Agent:** All authentication tokens and API keys are stored in the respective MCP server runtime configurations. The agent core remains completely credential-free.
- **Data Privacy Loop:** The Pre-LLM PII Anonymizer ensures user personal data is stripped locally before it leaves the environment.
- **Dry-Run Environment:** By executing with a `--dry-run` flag, the agent bypasses external MCP writing entirely, writing JSON reports to a local `outputs/` folder for local evaluation.
