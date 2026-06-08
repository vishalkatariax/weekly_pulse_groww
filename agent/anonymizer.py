import re

# Regex patterns for matching various PII types
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
)

# Matches general phone numbers (e.g. +91 9999988888, 9876543210, 8877665544)
PHONE_REGEX = re.compile(
    r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
)

# Matches usernames / handles starting with @ (e.g. @groww_user, @myhandle)
HANDLE_REGEX = re.compile(
    r'@[a-zA-Z0-9_]+'
)

# Matches user ID patterns (e.g. User ID 992831, User ID: 110293, ID: 449231)
USER_ID_REGEX = re.compile(
    r'(?i)\b(?:user\s+)?id[:\s\-]+\d+\b|\b(?:user_id)[:\s\-]+\d+\b'
)

def anonymize_text(text: str) -> str:
    """
    Scrubs PII (Emails, Phone numbers, Handles, User IDs) from review text.
    """
    if not isinstance(text, str):
        return text

    # Anonymize User IDs first (more specific than general numeric strings)
    text = USER_ID_REGEX.sub("[REDACTED_ID]", text)

    # Anonymize Emails
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)

    # Anonymize Phone Numbers
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)

    # Anonymize Social Handles
    text = HANDLE_REGEX.sub("[REDACTED_USER]", text)

    return text
