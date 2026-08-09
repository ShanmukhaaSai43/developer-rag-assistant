# Acme Commerce API Reference Manual

## Authentication & OAuth2

The Acme Commerce API uses OAuth 2.0 Bearer Tokens for authentication.

Base URL:
```text
https://api.acmecommerce.dev/v1
```

All API requests must include the Authorization header:
```http
Authorization: Bearer <access_token>
```
Access tokens expire after 3600 seconds (1 hour). Use the `/v1/oauth/token` refresh endpoint to issue a new token without requiring the user to re-enter credentials.

---

## Users API Endpoint (`POST /v1/users`)

Creates a new customer or admin user profile.

### Request Body Parameters:
- `email` (string, required): Unique primary email address.
- `full_name` (string, required): Legal first and last name.
- `role` (string, optional): Account role (`customer`, `admin`, `support`). Default is `customer`.

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

Places an order for items in a customer's cart.

### Request Parameters:
- `user_id` (string, required): Unique user ID (e.g. `usr_99812`).
- `items` (array of objects, required): Objects with `product_id` and `quantity`.
- `payment_method_id` (string, required): Valid Stripe or PayPal payment token.

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

## Webhook Subscriptions & HMAC Signatures

Acme Commerce emits real-time HTTP POST webhooks for asynchronous events.

### Supported Events:
- `order.created`: Fired upon successful order placement.
- `order.shipped`: Fired when shipment tracking is attached.
- `payment.failed`: Fired when payment authorization fails.

### HMAC Signature Verification:
Every webhook includes an `X-Acme-Signature` header computed using HMAC-SHA256. Always verify this signature against your webhook secret key to prevent forged requests.
