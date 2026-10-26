import unittest
from backend.app import create_app

class TestOrders(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_create_order_empty_cart(self):
        res = self.client.post("/api/orders", json={
            "items": [],
            "address": "123 Main St"
        })
        self.assertEqual(res.status_code, 400)

    def test_create_order_missing_address(self):
        res = self.client.post("/api/orders", json={
            "items": [{"id": "p1", "name": "The Essential Tee", "price": 42.0, "quantity": 1}],
            "address": ""
        })
        self.assertEqual(res.status_code, 400)

    def test_create_order_and_retrieve_history(self):
        # 1. Login customer
        login_res = self.client.post("/api/auth/login", json={
            "email": "customer@painite.studio",
            "password": "PainiteUser!42"
        })
        token = login_res.get_json()["token"]

        # 2. Place order with customizer specs
        order_payload = {
            "items": [
                {
                    "id": "p1",
                    "name": "The Essential Heavyweight Tee",
                    "price": 1299.0,
                    "quantity": 2,
                    "color": "Onyx Black",
                    "size": "L",
                    "style": "Oversized",
                    "text": "PAINITE CUSTOM",
                    "artwork_url": ""
                }
            ],
            "total": 2598.0,
            "address": "Flat 402, Signature Towers, Indiranagar",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560038",
            "phone": "9845012345",
            "payment_method": "cod"
        }

        res = self.client.post("/api/orders", json=order_payload, headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(res.status_code, 201)
        created_order = res.get_json()
        self.assertEqual(created_order["total"], 2598.0)
        self.assertEqual(created_order["currency"], "INR")
        self.assertEqual(created_order["status"], "Pending")
        self.assertEqual(len(created_order["items"]), 1)
        self.assertEqual(created_order["items"][0]["custom_text"], "PAINITE CUSTOM")

        # 3. Verify in order history
        hist_res = self.client.get("/api/me/orders", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(hist_res.status_code, 200)
        orders = hist_res.get_json()
        order_ids = [o["id"] for o in orders]
        self.assertIn(created_order["id"], order_ids)

if __name__ == "__main__":
    unittest.main()
