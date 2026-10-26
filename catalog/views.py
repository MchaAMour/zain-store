from django.shortcuts import get_object_or_404, render
from .models import Product

def product_list(request):
    return render(request, "catalog/product_list.html", {"products": Product.objects.filter(active=True)})

def product_detail(request, slug):
    return render(request, "catalog/product_detail.html", {"product": get_object_or_404(Product, slug=slug, active=True)})
