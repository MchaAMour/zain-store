# Payment workflow

```mermaid
flowchart LR
  Browser --> Django
  Django --> PostgreSQL
  Django -->|test key present| Stripe[Stripe Checkout]
  Django -->|otherwise| Simulator
  Stripe -->|verified webhook| Django
  Simulator -->|stored event| Django
```

The browser never supplies money values. Checkout creates an order and immutable line-item snapshots first, then attaches a single payment. A successful verified provider event transitions the payment and its order in one database transaction. Provider event IDs have a database uniqueness constraint, making webhook delivery idempotent.
