# Problem Statement: Weekly Review Automation for Groww (via MCP)

## 1. Context & Background
In a fast-paced fintech environment like **Groww**, cross-functional alignment and timely progress tracking are critical. Currently, compiling the **Weekly Review** requires manually gathering performance metrics, product updates, and operational milestones from various stakeholders and data sources. 

To automate this, we will import recent app reviews for our product, analyze and group them into high-level themes, and generate a scannable weekly pulse report.

Rather than implementing direct, hardcoded API integrations (which require managing OAuth2 flows, credential files, token lifecycles, and complex Google SDK payloads), we will use **MCP (Model Context Protocol) servers** to handle all Google Docs and Gmail integration.

---

## 2. Target Audience
*   **Product / Growth Teams:** To quickly identify usability issues, KYC/payment bugs, and feature requests.
*   **Support Teams:** To stay aligned with user sentiments and acknowledge recurring feedback.
*   **Leadership:** To receive a clean, high-level weekly health pulse of the application.

---

## 3. Key Requirements & Features

### A. Review Import & Analysis
*   **Import Reviews:** Import public review exports from the App Store and Play Store spanning the last **8–12 weeks** (rating, title, text, date).
*   **Theme Grouping:** Categorize reviews into a maximum of **5 themes** (e.g., onboarding, KYC, payments, statements, withdrawals).
*   **Anonymization:** Do NOT include any PII (Usernames, Emails, IDs) in any output or generated artifacts.

### B. Weekly Pulse Report Generation (Google Docs via MCP)
Generate a structured, scannable weekly note (≤250 words) containing:
1.  **Top 3 Themes:** The most prevalent user feedback categories from the week.
2.  **3 Real User Quotes:** Verbatim quotes illustrating those themes (anonymized).
3.  **3 Action Ideas:** Clear, actionable steps the product/engineering team can take.

This report must be created and styled as a Google Doc using a **Google Docs MCP Server**, avoiding direct OAuth configuration or Google client library dependencies in the code.

### C. Email Notification & Distribution (Gmail via MCP)
*   Draft a weekly email containing the generated pulse report.
*   The email should be drafted and sent to yourself or a designated alias.
*   This email draft must be created via a **Gmail MCP Server** tool.

---

## 4. Key Constraints & Guidelines
*   **Use Public Exports Only:** No scraping behind logins.
*   **Max 5 Themes:** Group reviews concisely.
*   **Keep Notes Scannable:** Ensure the summary is ≤250 words.
*   **No Direct APIs:** Rely entirely on the configured MCP tool interface to communicate with Google Workspace.
