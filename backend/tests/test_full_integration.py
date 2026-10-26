import unittest
import io
from PIL import Image
from backend.app import create_app

class TestFullIntegration(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_complete_end_to_end_flow(self):
        # 1. Health check
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["status"], "healthy")

        # 2. Fetch products
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        self.assertGreaterEqual(len(products), 6)
        first_prod = products[0]

        # 3. Customer login
        login_res = self.client.post("/api/auth/login", json={
            "email": "customer@painite.studio",
            "password": "PainiteUser!42"
        })
        self.assertEqual(login_res.status_code, 200)
        cust_token = login_res.get_json()["token"]

        # 4. Artwork upload (simulate file upload with Pillow)
        img_byte_arr = io.BytesIO()
        img = Image.new('RGB', (120, 120), color='red')
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        upload_res = self.client.post("/api/upload", data={
            "file": (img_byte_arr, "custom_emblem.png")
        }, content_type="multipart/form-data")
        self.assertEqual(upload_res.status_code, 201)
        artwork_url = upload_res.get_json()["url"]
        self.assertTrue(artwork_url.startswith("/static/uploads/"))

        # 5. Place customizer order
        order_res = self.client.post("/api/orders", json={
            "items": [{
                "id": first_prod["id"],
                "name": f"{first_prod['name']} (Bespoke)",
                "price": first_prod["price"],
                "quantity": 1,
                "color": "Black",
                "size": "L",
                "style": "Oversized",
                "text": "PAINITE 2026",
                "artwork_url": artwork_url
            }],
            "total": first_prod["price"],
            "address": "12th Main, Indiranagar, Bengaluru, Karnataka - 560038",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": "560038",
            "phone": "9845012345",
            "payment_method": "cod"
        }, headers={"Authorization": f"Bearer {cust_token}"})
        self.assertEqual(order_res.status_code, 201)
        placed_order = order_res.get_json()
        order_id = placed_order["id"]
        self.assertEqual(placed_order["status"], "Pending")

        # 6. Customer checks order history
        me_orders = self.client.get("/api/me/orders", headers={"Authorization": f"Bearer {cust_token}"})
        self.assertEqual(me_orders.status_code, 200)
        history_ids = [o["id"] for o in me_orders.get_json()]
        self.assertIn(order_id, history_ids)

        # 7. Admin login
        admin_login = self.client.post("/api/auth/login", json={
            "email": "admin@painite.studio",
            "password": "PainiteAdmin!42"
        })
        self.assertEqual(admin_login.status_code, 200)
        admin_token = admin_login.get_json()["token"]

        # 8. Admin updates order status
        patch_res = self.client.patch(f"/api/admin/orders/{order_id}", json={
            "status": "In Production"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.get_json()["status"], "In Production")

        # 9. Verify SPA routes serve index.html
        for route in ["/", "/shop", "/customize", "/orders", "/admin"]:
            spa_res = self.client.get(route)
            self.assertEqual(spa_res.status_code, 200)
            self.assertIn(b"PAINITE STUDIO", spa_res.data)

if __name__ == "__main__":
    unittest.main()
