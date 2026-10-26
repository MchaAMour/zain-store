from django.core.management.base import BaseCommand
from catalog.models import Product

PRODUCTS = [
    {"name": "Orbit Mechanical Keyboard", "slug": "orbit-mechanical-keyboard", "description": "Compact wireless mechanical keyboard with tactile switches.", "price_cents": 12990, "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=900&q=80"},
    {"name": "Focus Pro Webcam", "slug": "focus-pro-webcam", "description": "Sharp 1080p webcam for meetings, calls, and streaming.", "price_cents": 7990, "image_url": "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&w=900&q=80"},
    {"name": "Pulse Noise-Cancelling Headphones", "slug": "pulse-headphones", "description": "Comfortable over-ear headphones built for deep work.", "price_cents": 15990, "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80"},
]
class Command(BaseCommand):
    help = "Create or update Zain Store demo products"
    def handle(self, *args, **options):
        for product in PRODUCTS:
            Product.objects.update_or_create(slug=product["slug"], defaults=product)
        self.stdout.write(self.style.SUCCESS("Seeded 3 Zain Store products."))
