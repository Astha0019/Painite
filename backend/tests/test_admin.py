import unittest
from backend.app import create_app

class TestAdmin(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        # Admin login
        login_res = self.client.post("/api/auth/login", json={
            "email": "admin@painite.studio",
            "password": "PainiteAdmin!42"
        })
        self.token = login_res.get_json()["token"]

    def test_get_stats(self):
        res = self.client.get("/api/admin/stats", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("revenue", data)
        self.assertIn("orders", data)
        self.assertIn("products", data)
        self.assertIn("customers", data)
        self.assertGreaterEqual(data["products"], 1)

    def test_get_admin_orders(self):
        res = self.client.get("/api/admin/orders", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(res.status_code, 200)
        orders = res.get_json()
        self.assertIsInstance(orders, list)
        self.assertGreaterEqual(len(orders), 1)

    def test_update_order_status(self):
        # Fetch first order
        orders_res = self.client.get("/api/admin/orders", headers={
            "Authorization": f"Bearer {self.token}"
        })
        first_order = orders_res.get_json()[0]

        patch_res = self.client.patch(f"/api/admin/orders/{first_order['id']}", json={
            "status": "In Production"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.get_json()
        self.assertEqual(updated["status"], "In Production")

    def test_create_and_delete_product(self):
        # 1. Price cap violation test (T-shirt > INR 1500 must fail with 400)
        invalid_tee = self.client.post("/api/admin/products", json={
            "name": "Overpriced Tee",
            "price": 1899.0,
            "category": "Graphic T-Shirts"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(invalid_tee.status_code, 400)
        self.assertIn("Price Violation", invalid_tee.get_json()["error"])

        # 2. Price cap violation test (Jacket > INR 2000 must fail with 400)
        invalid_jacket = self.client.post("/api/admin/products", json={
            "name": "Overpriced Jacket",
            "price": 2499.0,
            "category": "Jackets"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(invalid_jacket.status_code, 400)
        self.assertIn("Price Violation", invalid_jacket.get_json()["error"])

        # 3. Create Valid Product (T-shirt <= INR 1500)
        create_res = self.client.post("/api/admin/products", json={
            "name": "Bespoke Silk Screen Tee",
            "price": 1299.0,
            "category": "Graphic T-Shirts",
            "tag": "LIMITED",
            "image": "/static/images/noir-studio-tee.jpg",
            "description": "Hand-pulled ink on organic jersey",
            "colors": ["Black", "Charcoal"],
            "sizes": ["M", "L"],
            "styles": ["Oversized"]
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(create_res.status_code, 201)
        prod = create_res.get_json()
        prod_id = prod["id"]
        self.assertEqual(prod["name"], "Bespoke Silk Screen Tee")

        # Delete
        del_res = self.client.delete(f"/api/admin/products/{prod_id}", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(del_res.status_code, 200)

        # Confirm 404
        get_res = self.client.get(f"/api/products/{prod_id}")
        self.assertEqual(get_res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
