import uuid
class SimulatedProvider:
    name = "simulated"
    def create_checkout(self, payment, return_url):
        return {"session_id": f"sim_{uuid.uuid4().hex}", "url": return_url}
