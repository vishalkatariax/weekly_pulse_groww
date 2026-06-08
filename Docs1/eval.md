# Evaluation Criteria: Phase-by-Phase Exit Gates

## Purpose

This document defines **testing requirements and exit criteria** for each phase of the Groww Weekly Review AI Agent. A phase must satisfy all exit criteria before work on the next phase begins.

---

## Phase 0: Foundation & Environment Setup

### Tests
| Test | Method | Expected Result |
|------|--------|-----------------|
| Python environment installs cleanly | `pip install -r requirements.txt` | No errors |
| MCP server health check — Google Docs | `mcp.ping("gdocs")` | `{"status": "ok"}` |
| MCP server health check — Gmail | `mcp.ping("gmail")` | `{"status": "ok"}` |
| Project directory structure exists | `ls` / tree check | All required folders present |

### Exit Criteria
- [ ] All dependencies install without conflicts
- [ ] Both MCP servers (Google Docs, Gmail) respond to a test tool invocation
- [ ] `README.md` is present and a fresh developer can set up the environment following it
- [ ] No secrets or credentials committed to the repository

---

## Phase 1: Data Ingestion & Anonymization

### Tests

#### Unit Tests (`tests/test_ingestion.py`)
| Test | Input | Expected Output |
|------|-------|-----------------|
| Load valid CSV | `mock_reviews.csv` | DataFrame with correct schema |
| Load valid JSON | `mock_reviews.json` | DataFrame with correct schema |
| Date range filter — 8 weeks | Full dataset | Only reviews from last 8 weeks |
| Date range filter — 12 weeks | Full dataset | Only reviews from last 12 weeks |
| Reject reviews with missing fields | Row missing `text` | Row excluded or flagged |

#### Anonymizer Tests (`tests/test_anonymizer.py`)
| Test | Input | Expected Output |
|------|-------|-----------------|
| Strip email addresses | `"Contact me at john@example.com"` | `"Contact me at [REDACTED]"` |
| Strip phone numbers | `"Call 9876543210"` | `"Call [REDACTED]"` |
| Strip username patterns | `"User @groww_user123"` | `"User [REDACTED]"` |
| Clean review has no PII | Full mock dataset | Zero PII patterns detected post-anonymization |
| Non-PII text is unchanged | `"The app crashes on login"` | Identical output |

### Exit Criteria
- [ ] All unit tests pass with 100% success rate
- [ ] PII detection has **zero false negatives** on the mock dataset (verified manually for a 20-row sample)
- [ ] Date range filter is accurate to ±0 days
- [ ] Mock dataset (`mock_reviews.csv`) covers all 5 themes with ≥10 reviews per theme

---

## Phase 2: Thematic Analysis (LLM Integration)

### Tests

#### Theme Classification (`tests/test_analyzer.py`)
| Test | Input | Expected Output |
|------|-------|-----------------|
| Single review classification | Review about KYC delay | Theme: `"KYC"` |
| All 5 themes represented | 50-review mock dataset | Each theme has ≥1 review assigned |
| No review assigned to unknown theme | Full mock dataset | All themes in `["Onboarding", "KYC", "Payments", "Statements", "Withdrawals"]` |
| Top 3 themes are ranked correctly | Mock dataset with known distribution | Correct top 3 by count |

#### Output Quality Tests
| Test | Criteria | Pass Condition |
|------|----------|----------------|
| Word count enforcement | Generated pulse report | ≤ 250 words |
| Quote anonymization | 3 selected quotes | Zero PII in quotes |
| Action relevance | 3 action ideas | Each action maps to one of the top 3 themes |
| Pulse JSON schema | Output object | Contains `week`, `top_themes`, `quotes`, `actions` |

#### Manual Evaluation (Spot Check)
- Run analysis on mock dataset and have a human reviewer score:
  - Theme accuracy: ≥ 80% correct classification
  - Action quality: All 3 actions are specific and actionable (not generic)
  - Quote representativeness: Quotes clearly illustrate their theme

### Exit Criteria
- [ ] All automated tests pass
- [ ] Manual spot check score ≥ 80% on theme accuracy
- [ ] Pulse object schema validation passes on 5 consecutive runs
- [ ] Word count is ≤ 250 on every test run
- [ ] LLM retry logic handles a simulated API timeout gracefully

---

## Phase 3: Google Docs Report Generation (MCP)

### Tests

#### MCP Integration Tests (`tests/test_gdocs_mcp.py`)
| Test | Method | Expected Result |
|------|--------|-----------------|
| Create doc with mock pulse | `create_weekly_doc(mock_pulse)` | Returns valid Google Doc URL |
| Doc title contains week identifier | Inspect created doc | Title includes `"Week YYYY-WNN"` |
| Doc has correct headings | Inspect created doc | H1: "Weekly Pulse", H2 per section |
| Doc word count within limit | Count words in created doc | ≤ 250 words in body |
| Duplicate run does not overwrite | Run twice in same week | Second run creates new doc or version, not overwrite |
| Error handling: MCP unavailable | Kill MCP server, run agent | Graceful error message logged, no crash |

#### Manual Verification
- Open the created Google Doc and confirm:
  - [ ] Formatting is clean and readable
  - [ ] Top 3 themes are listed clearly
  - [ ] 3 quotes are present, clearly labeled
  - [ ] 3 action ideas are listed
  - [ ] No PII visible anywhere in the doc

### Exit Criteria
- [ ] All automated integration tests pass
- [ ] Google Doc is created successfully in the target Drive folder on first attempt
- [ ] Doc content matches the pulse object (verified field-by-field)
- [ ] Manual formatting review passes
- [ ] Error handling test passes (no unhandled exceptions)

---

## Phase 4: Email Distribution (Gmail MCP)

### Tests

#### MCP Integration Tests (`tests/test_gmail_mcp.py`)
| Test | Method | Expected Result |
|------|--------|-----------------|
| Create email draft | `draft_email(mock_pulse, recipients)` | Draft appears in Gmail Drafts |
| Subject line is correct | Inspect draft | Subject: `"Groww Weekly Pulse — Week YYYY-WNN"` |
| Email body includes report | Inspect draft body | Top themes, quotes, actions present |
| Google Doc link in email | Inspect draft body | Contains valid Google Doc URL |
| Plain-text fallback exists | Inspect draft | `text/plain` MIME part present |
| Error handling: invalid recipient | Pass malformed email | Error logged, draft not created, no crash |

#### Manual Verification
- Open Gmail Drafts and confirm:
  - [ ] Email is readable and professional
  - [ ] Report content is correctly formatted
  - [ ] Google Doc link is clickable and opens the correct doc
  - [ ] No PII in the email body

### Exit Criteria
- [ ] All automated integration tests pass
- [ ] Email draft is visible in Gmail Drafts on first attempt
- [ ] Manual readability review passes
- [ ] Plain-text fallback is present and readable
- [ ] Error handling test passes (no unhandled exceptions)

---

## Phase 5: End-to-End Orchestration & Hardening

### Tests

#### Full Pipeline Test (`tests/test_e2e.py`)
| Test | Scenario | Expected Result |
|------|----------|-----------------|
| Full pipeline — live mode | Real mock data, MCP servers up | Google Doc created + Email draft created |
| Full pipeline — dry-run mode | `--dry-run` flag | No MCP write calls; output saved to `outputs/` folder |
| Pipeline handles MCP server failure | Kill Docs MCP mid-run | Logs error, skips email step, exits cleanly |
| Config file overrides work | Modify `config.yaml` date range | Pipeline uses new date range |
| Structured logs are emitted | Run full pipeline | JSON log file written to `logs/` with all steps |

#### Security Audit Checklist
- [ ] No API keys or credentials in any `.py`, `.yaml`, or `.env` file in the repo
- [ ] `git log` shows no secrets ever committed
- [ ] PII check: run the anonymizer on all pipeline outputs and confirm zero PII
- [ ] MCP server endpoints are not hardcoded (read from config)

### Exit Criteria
- [ ] Full pipeline runs end-to-end without errors on the mock dataset
- [ ] Dry-run mode produces correct local output files
- [ ] All security checklist items are confirmed
- [ ] A second developer can run the pipeline from scratch using only the `README.md`
- [ ] Structured logs capture each step with timestamps and status

---

## Phase 6: Scheduling & Productionization

### Tests

#### Scheduling Tests
| Test | Method | Expected Result |
|------|--------|-----------------|
| Docker build succeeds | `docker build .` | Image builds without errors |
| Container runs pipeline | `docker run` with env vars | Full pipeline completes successfully |
| Cron trigger fires correctly | Simulate cron (or manual trigger) | Pipeline runs at scheduled time |
| Alert fires on failure | Force a pipeline error | Alert (email/Slack) received within 5 minutes |

### Exit Criteria
- [ ] Docker image builds and pipeline runs inside container
- [ ] Weekly cron trigger is active and verified with a test run
- [ ] Failure alerting is tested and confirmed working
- [ ] Operational runbook is written and reviewed
- [ ] System runs two consecutive weekly cycles without manual intervention
