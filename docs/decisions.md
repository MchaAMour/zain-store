# Engineering decisions

This document records the choices intentionally made for the demo.

## ADR-001: Django monolith with PostgreSQL

**Decision:** Use Django templates, Django authentication/admin, and PostgreSQL in Docker Compose.

**Why:** The scope is a single-store payment workflow. A monolith keeps the core payment invariants visible in one codebase and lets the built-in admin demonstrate operational visibility without a separate back-office frontend.

**Deferred:** API gateway, separate frontend, asynchronous workers, caching, and horizontal scaling.

## ADR-002: Stripe-hosted Checkout with a simulated fallback

**Decision:** Use Stripe-hosted Checkout when `STRIPE_SECRET_KEY` is configured; otherwise use a deterministic local simulator.

**Why:** Stripe hosts card entry, so this application does not handle card numbers or CVCs. The simulator makes the demo flow dependable and demonstrates failure, pending, and retry behaviour even without external connectivity.

**Deferred:** Additional payment methods, subscriptions, Stripe Connect, and multi-provider routing.

## ADR-003: Server-side pricing and immutable order items

**Decision:** The session cart stores only product identifiers and quantities. The server recalculates totals from database products and copies them to `OrderItem` snapshots at checkout.

**Why:** Browser-supplied totals are untrusted and catalogue prices may later change. Order records must preserve what the customer was asked to pay.

## ADR-004: A payment is durable and provider events are idempotent

**Decision:** Each order has one payment with a stable provider idempotency key. Provider events have a unique `(provider, external_event_id)` constraint.

**Why:** Double-clicks, network retries, and duplicate webhooks are normal. The database, rather than process-local memory, prevents repeated business effects.

For browser checkout submits, the customer session retains the reference of the pending order. A repeated submit resumes that order instead of creating a second one; a cart change clears that reference.

The payment service also enforces a small explicit state-transition matrix. Invalid and late transitions are retained as audit entries but do not overwrite terminal payment states.

**Deferred:** Request-hash idempotency for an external JSON API, outbox processing, and reconciliation jobs.

## ADR-005: Webhooks, not redirects, confirm success

**Decision:** The Stripe success redirect is informational. A signature-verified Stripe webhook records the final success or failure transition.

**Why:** Redirects can be skipped, forged, or arrive before provider processing completes. The saved provider event and payment state are the source of truth.

## ADR-006: Test-mode, explicit refund action

**Decision:** A Django-admin action issues a full refund only for a successful payment. The simulator completes immediately; Stripe calls its test-mode Refund API.

**Why:** This is enough to show an auditable refund lifecycle. It is not a customer-facing refund policy or a settlement system.

## ADR-007: Demo deployment stays separate from local development

**Decision:** Use an HTTPS demo subdomain with a separate PostgreSQL volume and server-side environment variables. Keep secrets in `../.env` locally and outside Git.

**Why:** The demo environment should be polished and recoverable without exposing credentials or local development data.
