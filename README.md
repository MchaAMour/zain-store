# Zain Store

A Django payment demo. It uses PostgreSQL with Docker Compose, keeps all money in integer cents, and supports Stripe test Checkout or a deterministic local simulated provider.

## Run it

```bash
cp .env.example .env  # ignored by Git; edit for your local settings
# Legacy ../.env and ../.env-stripe are also loaded; .env takes precedence.
docker compose up --build
docker compose exec zain-store-web python manage.py seed_catalog
docker compose exec zain-store-web python manage.py createsuperuser
docker compose exec zain-store-web python manage.py create_demo_customer --password 'choose-a-temporary-demo-password'
```

The same tasks are available through `make`; for example, run `make up`, `make seed`, `make DEMO_PASSWORD='temporary-demo-password' demo-user`, and `make test`.

Open <http://localhost:8010>. Register a customer, add a product, and check out. With the supplied empty Stripe settings, checkout opens the simulator; it can approve, decline, or leave a payment pending. Failed or pending payments have a retry path.

Run the test suite inside the web container:

```bash
docker compose exec zain-store-web python manage.py test
```

## Stripe test mode (optional)

Put a Stripe test secret key in `.env`:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

Run the web app, then start forwarding in another interactive terminal:

```bash
stripe listen --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,checkout.session.expired --forward-to localhost:8010/payments/stripe/webhook/
```

Use the printed `whsec_...` value in the same environment file and restart the `zain-store-web` container. Use Stripe test card `4242 4242 4242 4242`, any future date and any CVC. The redirect itself does not mark an order paid: a verified, stored webhook does.

## Design highlights

- Product prices and order totals are calculated on the server and copied into immutable order lines.
- Each order has one durable payment with a stable idempotency key.
- A repeated browser checkout submit resumes the customer's existing pending order.
- Provider events are persisted and unique per provider/event ID, so replay is harmless.
- A late failure cannot overwrite a successful payment.
- Django admin exposes orders, payments, and the internal event timeline.

