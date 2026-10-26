from django.db import connection
from django.http import JsonResponse

def health(request):
    """A small dependency-aware endpoint for the demo deployment."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ok"})
