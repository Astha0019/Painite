import unittest
import json
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

        # Customer login
        cust_login_res = self.client.post("/api/auth/login", json={
            "email": "customer@painite.studio",
            "password": "PainiteUser!42"
        })
        self.cust_token = cust_login_res.get_json()["token"]

    def test_get_stats_and_analytics(self):
        # Stats
        res = self.client.get("/api/admin/stats", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("revenue", data)
        self.assertIn("orders", data)
        self.assertIn("products", data)
        self.assertIn("customers", data)
        self.assertIn("low_stock_count", data)
        self.assertIn("aov", data)

        # Analytics
        an_res = self.client.get("/api/admin/analytics", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(an_res.status_code, 200)
        an_data = an_res.get_json()
        self.assertIn("category_sales", an_data)
        self.assertIn("status_distribution", an_data)
        self.assertIn("daily_trend", an_data)
        self.assertIn("top_products", an_data)

    def test_get_admin_orders(self):
        res = self.client.get("/api/admin/orders", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(res.status_code, 200)
        orders = res.get_json()
        self.assertIsInstance(orders, list)
        self.assertGreaterEqual(len(orders), 1)

    def test_update_order_status_and_payment(self):
        orders_res = self.client.get("/api/admin/orders", headers={
            "Authorization": f"Bearer {self.token}"
        })
        first_order = orders_res.get_json()[0]
        order_id = first_order['id']

        # Status update
        patch_res = self.client.patch(f"/api/admin/orders/{order_id}", json={
            "status": "In Production"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.get_json()
        self.assertEqual(updated["status"], "In Production")

        # Payment status update
        pay_res = self.client.patch(f"/api/admin/orders/{order_id}/payment", json={
            "payment_status": "Paid"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(pay_res.status_code, 200)
        self.assertEqual(pay_res.get_json()["payment_status"], "Paid")

        # Tracking update
        track_res = self.client.patch(f"/api/admin/orders/{order_id}/tracking", json={
            "tracking_number": "BLUE-998877",
            "estimated_delivery_date": "5 Nov 2026"
        }, headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(track_res.status_code, 200)
        self.assertEqual(track_res.get_json()["tracking_number"], "BLUE-998877")

        # Full order update notification to customer
        notify_res = self.client.post(f"/api/admin/orders/{order_id}/notify", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(notify_res.status_code, 200)
        notify_data = notify_res.get_json()
        self.assertTrue(notify_data["success"])
        self.assertIn("wa_link", notify_data)
        self.assertTrue(notify_data["wa_link"].startswith("https://wa.me/"))

        # Broadcast order updates to multiple active customers
        broadcast_res = self.client.post("/api/admin/orders/notify-all", json={
            "order_ids": [order_id]
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(broadcast_res.status_code, 200)
        self.assertTrue(broadcast_res.get_json()["success"])
        self.assertEqual(broadcast_res.get_json()["total_notified"], 1)

    def test_create_update_stock_and_delete_product(self):
        # 1. Price cap violation (Tee > 1500)
        inv_tee = self.client.post("/api/admin/products", json={
            "name": "Overpriced Tee",
            "price": 1899.0,
            "category": "Graphic T-Shirts"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(inv_tee.status_code, 400)
        self.assertIn("Price Violation", inv_tee.get_json()["error"])

        # 2. Create valid product
        create_res = self.client.post("/api/admin/products", json={
            "name": "Bespoke Silk Screen Tee",
            "price": 1299.0,
            "original_price": 1999.0,
            "category": "Graphic T-Shirts",
            "tag": "LIMITED",
            "image": "/static/images/essential-tee.jpg",
            "description": "Hand-pulled ink on organic jersey",
            "stock_quantity": 40
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(create_res.status_code, 201)
        prod = create_res.get_json()
        prod_id = prod["id"]
        self.assertEqual(prod["stock_quantity"], 40)

        # 3. Quick stock adjustment
        stock_res = self.client.patch(f"/api/admin/products/{prod_id}/stock", json={
            "stock_quantity": 55,
            "in_stock": 1
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(stock_res.status_code, 200)
        self.assertEqual(stock_res.get_json()["stock_quantity"], 55)

        # 4. Full product update
        update_res = self.client.put(f"/api/admin/products/{prod_id}", json={
            "name": "Bespoke Silk Screen Tee (Edition 2)",
            "price": 1399.0,
            "stock_quantity": 50,
            "category": "Graphic T-Shirts"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.get_json()["name"], "Bespoke Silk Screen Tee (Edition 2)")

        # 5. Delete product
        del_res = self.client.delete(f"/api/admin/products/{prod_id}", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(del_res.status_code, 200)

    def test_categories_management(self):
        # 1. List categories
        res = self.client.get("/api/admin/categories", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(res.status_code, 200)
        cats = res.get_json()
        self.assertGreaterEqual(len(cats), 6)

        # 2. Add category
        add_res = self.client.post("/api/admin/categories", json={
            "name": "Limited Drop Test",
            "description": "Test collection description",
            "display_order": 99
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(add_res.status_code, 201)
        cat_id = add_res.get_json()["id"]

        # 3. Delete category
        del_res = self.client.delete(f"/api/admin/categories/{cat_id}", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(del_res.status_code, 200)

    def test_customers_management(self):
        res = self.client.get("/api/admin/customers", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(res.status_code, 200)
        customers = res.get_json()
        self.assertIsInstance(customers, list)
        self.assertGreaterEqual(len(customers), 1)
        self.assertIn("email", customers[0])
        self.assertIn("total_spent", customers[0])

    def test_coupons_management_and_apply(self):
        # 1. Create coupon
        res = self.client.post("/api/admin/coupons", json={
            "code": "UNITTEST30",
            "discount_type": "percentage",
            "discount_value": 30.0,
            "min_order_amount": 1000.0,
            "expires_at": "2026-12-31"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(res.status_code, 201)
        coupon_id = res.get_json()["id"]

        # 2. Public apply coupon (success)
        apply_res = self.client.post("/api/coupons/apply", json={
            "code": "UNITTEST30",
            "subtotal": 2000.0
        })
        self.assertEqual(apply_res.status_code, 200)
        apply_data = apply_res.get_json()
        self.assertEqual(apply_data["discount_amount"], 600.0)
        self.assertEqual(apply_data["new_total"], 1400.0)

        # 3. Public apply coupon below minimum order
        fail_res = self.client.post("/api/coupons/apply", json={
            "code": "UNITTEST30",
            "subtotal": 500.0
        })
        self.assertEqual(fail_res.status_code, 400)

        # 4. Toggle coupon
        toggle_res = self.client.patch(f"/api/admin/coupons/{coupon_id}/toggle", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(toggle_res.status_code, 200)
        self.assertFalse(toggle_res.get_json()["is_active"])

        # 5. Delete coupon
        del_res = self.client.delete(f"/api/admin/coupons/{coupon_id}", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(del_res.status_code, 200)

    def test_banners_management(self):
        # 1. Create banner
        res = self.client.post("/api/admin/banners", json={
            "title": "Winter Silk Drop",
            "subtitle": "280 GSM luxury combed cotton",
            "badge_text": "NEW IN ATELIER",
            "position": "hero"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(res.status_code, 201)
        banner_id = res.get_json()["id"]

        # 2. Public banners list
        pub_res = self.client.get("/api/banners")
        self.assertEqual(pub_res.status_code, 200)
        pub_banners = pub_res.get_json()
        self.assertTrue(any(b["id"] == banner_id for b in pub_banners))

        # 3. Delete banner
        del_res = self.client.delete(f"/api/admin/banners/{banner_id}", headers={
            "Authorization": f"Bearer {self.token}"
        })
        self.assertEqual(del_res.status_code, 200)

    def test_whatsapp_admin_system(self):
        # 1. Get WhatsApp system status
        res = self.client.get("/api/admin/whatsapp/status", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(res.status_code, 200)
        status_data = res.get_json()
        self.assertIn("business_number", status_data)
        self.assertIn("mode", status_data)

        # 2. Update WhatsApp settings
        settings_res = self.client.post("/api/admin/whatsapp/settings", json={
            "business_number": "919359615919",
            "api_version": "v21.0"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(settings_res.status_code, 200)

        # 3. Send test message
        test_res = self.client.post("/api/admin/whatsapp/test", json={
            "phone": "9845012345"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(test_res.status_code, 200)
        test_data = test_res.get_json()
        self.assertIn("wa_link", test_data)
        self.assertTrue(test_data["wa_link"].startswith("https://wa.me/"))

        # 4. Send custom message
        custom_res = self.client.post("/api/admin/whatsapp/send", json={
            "phone": "9845012345",
            "name": "Dev Test",
            "message": "Hello from Atelier WhatsApp system"
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(custom_res.status_code, 200)
        self.assertIn("wa_link", custom_res.get_json())

        # 5. Fetch WhatsApp logs
        logs_res = self.client.get("/api/admin/whatsapp/logs", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(logs_res.status_code, 200)
        logs = logs_res.get_json()
        self.assertIsInstance(logs, list)
        self.assertGreaterEqual(len(logs), 1)

    def test_customer_access_blocked(self):
        # Customer token cannot access any admin endpoint
        endpoints = [
            "/api/admin/stats",
            "/api/admin/analytics",
            "/api/admin/orders",
            "/api/admin/products",
            "/api/admin/categories",
            "/api/admin/customers",
            "/api/admin/coupons",
            "/api/admin/banners",
            "/api/admin/whatsapp/status",
            "/api/admin/whatsapp/logs"
        ]
        for ep in endpoints:
            res = self.client.get(ep, headers={"Authorization": f"Bearer {self.cust_token}"})
            self.assertEqual(res.status_code, 403, f"Endpoint {ep} should return 403 to customer")

if __name__ == "__main__":
    unittest.main()
