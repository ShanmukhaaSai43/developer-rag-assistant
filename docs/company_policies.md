# Acme Commerce Security & Corporate Policies

## API Rate Limits & Throttling Rules

To preserve infrastructure availability and protect against Denial of Service (DoS) attacks, Acme Commerce enforces rate limits per API key:
- **Standard Tier:** Maximum 100 requests per minute per IP address.
- **Enterprise Tier:** Maximum 5,000 requests per minute per IP address.

If an application exceeds these limits, the API returns an **HTTP 429 Too Many Requests** error with a `Retry-After` header indicating the required cool-down period in seconds.

---

## Customer Refund & Return Policy

Merchants using the Acme Commerce platform must comply with our uniform consumer protection framework:
- Returns are accepted within **30 calendar days** of order delivery for unopened items in original packaging.
- Full refunds are processed to the original payment method within 5 business days after warehouse inspection.
- Digital downloads, software licenses, and customized items are non-refundable.

---

## Data Privacy & Encryption Standards

Acme Commerce adheres to strict security compliance protocols:
- All data in transit is encrypted using TLS 1.3.
- All database fields storing sensitive PII are encrypted at rest using AES-256.
- API secret keys (`client_secret`) must always be stored in environment variables (`.env`) and never exposed in client-side code or public code repositories.
