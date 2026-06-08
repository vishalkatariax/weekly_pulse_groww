 Updated Problem Statement: App Review Weekly Pulse via MCP
## 1. Objective & Scope
The goal of this project is to build an automated pipeline that imports recent app reviews for a selected product (e.g., **Groww**), analyzes and groups them into high-level themes, and generates a scannable weekly pulse report. This report is then saved as a Google Doc and drafted as an email to stakeholders.
Instead of using traditional, complex API integrations for Google Docs and Gmail, this project mandates the use of **MCP (Model Context Protocol) servers** to handle all interactions with Google Workspace.
---
## 2. Target Audience
*   **Product & Growth Teams:** To quickly identify usability issues, bugs, and feature requests.
*   **Support Teams:** To stay aligned with user sentiments and acknowledge recurring feedback.
*   **Leadership:** To receive a clean, high-level weekly health pulse of the application.
---
## 3. Key Requirements
### A. Review Import & Analysis
*   **Data Source:** Import public review exports from the App Store and Google Play Store spanning the last **8–12 weeks** (fields: rating, title, text, date).
*   **Theme Grouping:** Categorize reviews into a maximum of **5 distinct themes** (e.g., onboarding, KYC, payments, statements, withdrawals).
*   **Privacy & Constraints:** Do NOT include any PII (Usernames, Emails, IDs) in any output artifacts.
### B. Weekly Pulse Report Generation (Google Docs via MCP)
Generate a structured, scannable weekly note (≤250 words) containing:
1.  **Top 3 Themes:** The most prevalent user feedback categories from the week.
2.  **3 Real User Quotes:** Verbatim quotes illustrating those themes (anonymized).
3.  **3 Action Ideas:** Clear, actionable steps the product/engineering team can take.
This report must be created and saved directly to Google Docs using a **Google Docs MCP Server**, avoiding direct OAuth flow and API client configuration in the code.
### C. Email Notification & Distribution (Gmail via MCP)
*   Draft a weekly email containing the generated pulse report.
*   The email should be drafted and sent to yourself or a designated alias.
*   This email creation must be performed via a **Gmail MCP Server** tool.
---
## 4. Key Constraints & Guidelines
*   **No Web Scraping Behind Logins:** Use only public exports or mock dataset files.
*   **Word Limit:** Keep the weekly note under **250 words** for readability and quick scanning.
*   **No Direct API Keys/SDKs:** Do not write boilerplate integration code or store secrets for Google Docs/Gmail APIs. Rely entirely on the configured MCP tool interface.

