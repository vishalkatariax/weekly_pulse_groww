# Implementation Plan: Groww Weekly Review AI Agent (MCP-Based)

This implementation plan outlines the steps required to build and deploy the Groww Weekly Review AI Agent. Focus is placed on establishing solid testing gates and clear code modules to ensure robustness.

---

## Phase 0: Foundation & Environment Setup

Establish the project directory, dependency management system, and run basic sanity tests for the Model Context Protocol (MCP) servers.

### 0.1 Setup Steps
- Initialize the directory structure to isolate logs, inputs, tests, prompts, and agent code.
- Create a Python virtual environment (`.venv`) to isolate dependencies.
- Install primary core dependencies: `langchain` / `langchain-core` for orchestration, the Groq SDK or equivalent Groq client integration for model calls, `pandas` for review ingestion, and `python-dotenv` for configuration management.
- Create a `.env.example` file listing configurations such as `LLM_API_KEY`, `DOCS_MCP_SERVER_URL`, and `GMAIL_MCP_SERVER_URL`.
- Download and configure Google Docs and Gmail MCP servers locally. Set up a simple client test script to perform a health check on both server instances.

### 0.2 Verification & Exit Gates
- Ensure dependencies install cleanly with no version conflicts.
- Confirm both MCP servers respond with a successful "ping" payload.

---

## Phase 1: Data Ingestion & Anonymization

Build the review data ingestion pipeline, including date parsing, filtering, and a robust PII (Personally Identifiable Information) scrubber.

### 1.1 Ingestion Steps
- Design a loader module (`ingestion.py`) that reads raw CSV and JSON exports containing app store ratings, review dates, titles, and body texts.
- Standardize all input timestamps to UTC ISO formats. Implement a date filter function that isolates reviews from the last 8–12 weeks based on the run date.
- Build the anonymizer module (`anonymizer.py`). It applies a pipeline of regular expressions to search for and redact:
  - Email addresses (`[REDACTED_EMAIL]`)
  - Phone numbers (`[REDACTED_PHONE]`)
  - Social media/forum handles and usernames starting with `@` (`[REDACTED_USER]`)
  - Numeric patterns resembling IDs (`[REDACTED_ID]`)
- Synthesize a local test dataset of mock reviews representing realistic Groww app feedback, complete with deliberate PII injects to verify scrubber functionality.

### 1.2 Verification & Exit Gates
- Verify data loader parses dates and handles missing columns correctly without throwing exceptions.
- Confirm anonymizer successfully redacts all injected PII markers in the test dataset while preserving the semantic meaning of the reviews.

---

## Phase 2: Thematic Analysis (LLM: `llama-3.3-70b-versatile`)

Integrate the `llama-3.3-70b-versatile` model pipeline to categorize reviews, select representative quotes, and generate actionable recommendations. Because this model enforces hard request and token quotas, the implementation must include deterministic preprocessing, sampling, batching, and token accounting to avoid rate-limit and daily-cap breaches.

### 2.1 Analysis Steps
- Draft LLM prompt templates in dedicated text files within the `/prompts` folder:
  - **Theme Classifier Prompt:** Categorizes individual reviews into five defined categories (Onboarding, KYC, Payments, Statements, Withdrawals).
  - **Ranking and Quote Prompt:** Directs the LLM to identify the top 3 themes by review density and extract exactly 3 representative, anonymized user quotes.
  - **Action Generator Prompt:** Prompts the LLM to draft 3 highly specific action ideas for the engineering/product team.
- Implement the analyzer orchestrator (`analyzer.py`) to chunk and send reviews to the LLM. Add error-handling wrapper functions for API rate-limiting, token exhaustions, and temporary network timeouts.
  - Implement a rate-limited request wrapper that enforces:
    - **30 requests per minute** max
    - **1,000 requests per day** max
    - **12,000 tokens per minute** and **100,000 tokens per day** tracking
  - Add a token-estimation helper to compute approximate tokens per payload (quotes + metadata) and cap batch sizes accordingly.
- Implement a post-processing utility (`assembler.py`) that formats the LLM outputs into a structured JSON payload containing the week number, top themes, quotes, and action items.
- Write a constraint validator that measures output word counts, failing the run if the report length exceeds 250 words.

### Phase 2 Operational Details (rate limits, sampling, batching)

- **Sampling target:** Reduce input set to **~1,000 reviews** per run (configurable). Prioritize reviews with negative ratings (1–2), high word counts, and high keyword signal, then fill remaining quota with representative positive/neutral reviews to preserve balance.
- **Preprocessing:** Perform deterministic theme tagging and sentiment bucketing locally. From each theme, pick top 2–3 representative, anonymized quotes. Aggregate counts and produce a compact payload: theme name, counts (neg/neu/pos), top words, and selected quotes.
- **Batching strategy:** Send multiple small structured requests to the model rather than one large request. Example flow:
  1. Create theme-level payloads (one per theme or per theme-chunk) and estimate tokens.
 2. Group theme payloads into batches that keep estimated tokens < per-minute budget and requests < 30/min.
 3. Call the model for each batch, collecting theme summaries and recommendations.
 4. Merge results in `assembler.py` into the final pulse.
- **Token budgeting:** Implement an accounting system that decrements available tokens per minute/day and enforces backoff when thresholds are reached.
- **Retries & backoff:** On transient failures or rate-limit responses, use exponential backoff and requeue the batch within daily quota boundaries.
- **Dry-run & testing:** Provide `--dry-run` mode that exercises the preprocessing, batching, and assembler logic without calling the remote LLM (use local mock responses for validation).

### Phase 2 Verification & Exit Gates (updated)

- Confirm that the request wrapper enforces 30 R/M and tracks daily request counters.
- Validate token-estimation logic against several payload shapes and ensure per-minute token usage stays below 12K in tests.
- Verify the sampling logic yields representative sets and that the final assembled pulse remains ≤250 words.
- In dry-run mode, produce a sample JSON matching the schema and a text pulse for manual review.

### 2.2 Verification & Exit Gates
- Ensure the theme classifier matches mock reviews to correct categories with at least 80% accuracy in local test runs.
- Confirm report word counts strictly respect the 250-word budget.
- Verify the generated JSON matches the required schema structure.

---

## Phase 3: Google Docs Integration (MCP)

Publish the generated pulse report directly to a Google Doc using the Docs MCP server.

### 3.1 Integration Steps
- Create `gdocs_client.py` to interface with the Google Docs MCP server.
- Define layout mapping rules that translate the structured JSON pulse report into standard Google Doc elements (headings, bold text, bullet points).
- Implement a document creator routine. This makes an MCP call to create a blank document named with the current week (e.g., `Groww Weekly Pulse - 2026-W23`), writes the structured sections, and formats the font hierarchy.
- Incorporate a folder path resolver to ensure documents are organized within a dedicated folder on the user's Google Drive.
- Add try-except error catching to catch connection limits or permission issues reported by the Docs MCP server.

### 3.2 Verification & Exit Gates
- Confirm the client script successfully creates a formatted Google Doc.
- Verify that the layout and typography in the generated doc are clean, readable, and match the target output content.

---

## Phase 4: Email Distribution Integration (Gmail MCP)

Build the email distribution layer to draft and queue the summary report using the Gmail MCP server.

### 4.1 Integration Steps
- Write an email formatter that renders an HTML template containing the text summary and a direct hyperlink to the generated Google Doc.
- Create `gmail_client.py` containing tools to hook into the Gmail MCP server.
- Write a routine to compile the email subject and body, calling the Gmail MCP draft tool to create a draft in the user's Gmail box.
- Configure recipient mailing lists and CC lists via the core configuration file.
- Provide a fallback text-only version of the email body to ensure support for basic email clients.

### 4.2 Verification & Exit Gates
- Confirm the script successfully creates a draft in Gmail.
- Check that the draft subject, body text, formatting, and the Google Doc URL link are correct.

---

## Phase 5: End-to-End Orchestration & Hardening

Unify all modules under a single orchestrator command-line tool.

### 5.1 Orchestration Steps
- Write `orchestrator.py` as the main system runner. It sequentially calls the ingestion, anonymization, analysis, document creation, and email drafting routines.
- Set up a standard configuration file (`config.yaml`) defining file paths, threshold limits, recipient parameters, and MCP URLs.
- Implement a CLI interface supporting flags:
  - `--dry-run`: Runs ingestion and analysis, saving final outputs to a local file, completely bypassing the external MCP servers.
  - `--config <path>`: Allows specifying a custom configuration file.
- Configure python's `logging` library to write timestamped log statements capturing failures, API call latencies, and tool execution status to `logs/agent.log`.

### 5.2 Verification & Exit Gates
- Run the full pipeline in `--dry-run` mode to verify it saves local JSON reports without throwing errors.
- Confirm the complete end-to-end run completes successfully (raw reviews to Google Doc and Gmail draft).

---

## Phase 6: Productionization & Automation (Future)

Automate the weekly execution flow.

### 6.1 Automation Steps
- Write a `Dockerfile` packaging the Python environment, source files, and configuration.
- Write configuration templates for container deployment.
- Configure a automated runner workflow (such as a GitHub Actions schedule or Cron job) to execute the container weekly.
- Build a failure monitoring routine that sends alerts (e.g., Slack Webhooks or raw emails) if any stage of the execution fails.

### 6.2 Verification & Exit Gates
- Verify the containerized agent runs locally inside Docker.
- Confirm scheduler triggers execution and failure alerts are dispatched when simulated errors are encountered.
