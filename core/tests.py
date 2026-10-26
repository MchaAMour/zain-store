from django.test import TestCase

class HealthEndpointTests(TestCase):
    def test_health_endpoint_reports_ok(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
