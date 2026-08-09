# Developer Documentation Dataset - Acme Commerce API

## API Overview & Authentication

The Acme Commerce API is a RESTful interface for managing users, products, orders, and webhooks.

Base URL:
```text
https://api.acmecommerce.dev/v1
```

Authentication is handled via OAuth 2.0 Bearer Tokens. All requests must include the header:
```http
Authorization: Bearer <your_access_token>
```
Access tokens expire after 3600 seconds (1 hour). Use the refresh token endpoint to obtain a new access token without re-authenticating the user.

---

## Users API Endpoint (`POST /v1/users`)

Creates a new user account in the system.

### Request Body Parameters:
- `email` (string, required): Primary user email address. Must be unique.
- `full_name` (string, required): User's legal first and last name.
- `role` (string, optional): Account permission role. Allowed values: `customer`, `admin`, `support`. Default is `customer`.

### Response (HTTP 201 Created):
```json
{
  "user_id": "usr_99812",
  "email": "dev@acmecommerce.dev",
  "role": "customer",
  "created_at": "2026-08-09T10:00:00Z"
}
```

---

## Orders API Endpoint (`POST /v1/orders`)

Places a new order for items in the customer's cart.

### Request Parameters:
- `user_id` (string, required): Unique identifier of the purchasing user (e.g. `usr_99812`).
- `items` (array of objects, required): List of item objects containing `product_id` and `quantity`.
- `payment_method_id` (string, required): Stripe or PayPal payment method ID.

### Response (HTTP 201 Created):
```json
{
  "order_id": "ord_77102",
  "status": "processing",
  "total_amount": 149.99,
  "currency": "USD"
}
```

---

## Webhooks & Event Notifications

Acme Commerce sends real-time HTTP POST webhooks for critical events.

### Webhook Event Types:
- `order.created`: Triggered when an order is successfully placed.
- `order.shipped`: Triggered when shipping tracking is attached.
- `payment.failed`: Triggered when payment processing fails.

### HMAC Signature Security:
Every webhook request includes an `X-Acme-Signature` header computed using HMAC-SHA256 with your endpoint secret. Always verify this signature before processing webhook payloads to prevent spoofing.

---

## Rate Limits & Security Policy

To protect system availability, Acme Commerce enforces rate limits per API key:
- **Standard Tier:** 100 requests per minute per IP address.
- **Enterprise Tier:** 5,000 requests per minute.

Exceeding the rate limit returns an HTTP 429 Too Many Requests response with a `Retry-After` header indicating the required wait time in seconds.

---

## Customer Refund & Return Policy

Merchants using Acme Commerce must adhere to the standard return framework:
- Returns are accepted within **30 days** of delivery for unopened items.
- Full refunds are issued to the original payment method within 5 business days of item inspection.
- Digital software downloads and gift cards are non-refundable.
