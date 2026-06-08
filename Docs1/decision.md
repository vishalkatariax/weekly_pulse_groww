# Decision Log

This document records the major technical, logical, and architectural decisions made while designing and building the Groww App Review Weekly Pulse AI Agent.

---

## 1. Google Workspace Integration via Model Context Protocol (MCP)

*   **Status:** Approved
*   **Context:** The agent needs to write reports to Google Docs and create draft emails in Gmail. Setting up OAuth2 flows, generating client credential files, managing refresh token expirations, and writing direct API integrations requires significant boilerplate code and security considerations.
*   **Decision:** We decided to use standard Model Context Protocol (MCP) servers (Google Docs MCP and Gmail MCP) rather than direct REST APIs or Google SDKs.
*   **Impact:** 
    *   Keeps the agent codebase clean and decoupled from specific authentication protocols.
    *   Delegates token management and Google API handshakes to the MCP runtime.
    *   Enables rapid replacement or updates of workspace integrations without code modifications in the core agent.

---

## 2. Ingestion-Level PII Scrubbing (Prior to LLM Analysis)

*   **Status:** Approved
*   **Context:** Public reviews often contain personal names, phone numbers, customer support tickets, email addresses, and account numbers. Sending this information to third-party LLMs presents severe compliance, security, and privacy risks.
*   **Decision:** Implement a robust PII sanitization pipeline (using regular expressions and patterns) immediately during the data ingestion phase, before reviews are saved in-memory or dispatched to the LLM analyzer.
*   **Impact:**
    *   Guarantees that sensitive data is stripped at the boundaries.
    *   No PII is ever logged, cached, or written to downstream reports.
    *   Reviews retain semantic meaning for categorization while maintaining full anonymity.

---

## 3. Five Predefined Themes with Top-3 Summary

*   **Status:** Approved
*   **Context:** App review feedback can be scattered and disorganized. Summarizing dozens of disparate topics makes report digests noisy and difficult for teams to act upon.
*   **Decision:** Restrict classification to 5 predefined themes (Onboarding, KYC, Payments, Statements, Withdrawals), and summarize only the top 3 themes based on frequency and sentiment in the output.
*   **Impact:**
    *   Filters out background noise to focus stakeholder attention on high-impact customer pain points.
    *   Stabilizes prompt categorization, leading to predictable LLM behavior.

---

## 4. Stateless Pipeline with Local Cache Logging

*   **Status:** Approved
*   **Context:** We need a way to debug runs, trace theme classifications, and review generated summaries without the operational overhead of a relational or document database.
*   **Decision:** Build the agent as a stateless pipeline. It reads reviews from flat files (CSV/JSON), processes them in memory, and writes output metrics and audit logs locally.
*   **Impact:**
    *   Simplifies deployment and local testing.
    *   Eliminates database connection pooling and credential configuration.
    *   Provides complete run transparency via local text logs and dry-run cached outputs.

---

## 5. Structured JSON Output with Strict Word Count Budget (250 Words)

*   **Status:** Approved
*   **Context:** LLMs are prone to verbosity. Stakeholders require brief, highly readable summaries, and excess text reduces the utility of the reports.
*   **Decision:** The thematic analysis must compile output into a strict JSON payload, and the text report length is capped at a strict limit of 250 words.
*   **Impact:**
    *   Ensures consistent parsing of themes, quotes, and action items.
    *   Enforces conciseness through programmatic validation before pushing output to Google Docs or Gmail.
