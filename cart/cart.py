from catalog.models import Product

class Cart:
    key = "zain_store_cart"
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(self.key, {})
    def save(self):
        self.session[self.key] = self.data
        self.session.modified = True
    def add(self, product, quantity=1):
        # A changed cart represents a new checkout intent.
        self.session.pop("pending_checkout_order", None)
        key = str(product.id)
        self.data[key] = self.data.get(key, 0) + quantity
        self.save()
    def remove(self, product_id):
        self.session.pop("pending_checkout_order", None)
        self.data.pop(str(product_id), None)
        self.save()
    def clear(self):
        self.session.pop(self.key, None)
        self.session.modified = True
    def items(self):
        products = Product.objects.filter(id__in=self.data.keys(), active=True)
        output = []
        for product in products:
            quantity = self.data[str(product.id)]
            output.append({"product": product, "quantity": quantity, "line_total_cents": product.price_cents * quantity})
        return output
    def total_cents(self):
        return sum(item["line_total_cents"] for item in self.items())
    def __len__(self):
        return sum(self.data.values())
