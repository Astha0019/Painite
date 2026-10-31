import unittest
import json
import os
import sys

from backend.app import create_app
from backend.database import get_db_connection
from backend.seeds import seed_database
class TestAdminSeparationAndCatalogModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database(force_refresh=True)

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_admin_vs_customer_separation(self):
        # 1. Login as customer
        res_cust = self.client.post('/api/auth/login', json={
            'email': 'customer@painite.studio',
            'password': 'PainiteUser!42'
        })
        self.assertEqual(res_cust.status_code, 200)
        data_cust = res_cust.get_json()
        self.assertEqual(data_cust['user']['role'], 'customer')
        cust_token = data_cust['token']

        # 2. Customer token must be forbidden from accessing admin API
        admin_orders_res = self.client.get('/api/admin/orders', headers={
            'Authorization': f'Bearer {cust_token}'
        })
        self.assertEqual(admin_orders_res.status_code, 403)

        admin_stats_res = self.client.get('/api/admin/stats', headers={
            'Authorization': f'Bearer {cust_token}'
        })
        self.assertEqual(admin_stats_res.status_code, 403)

        # 3. Unauthenticated requests must be unauthorized
        unauth_res = self.client.get('/api/admin/stats')
        self.assertEqual(unauth_res.status_code, 401)

        # 4. Login as admin
        res_admin = self.client.post('/api/auth/login', json={
            'email': 'admin@painite.studio',
            'password': 'PainiteAdmin!42'
        })
        self.assertEqual(res_admin.status_code, 200)
        data_admin = res_admin.get_json()
        self.assertEqual(data_admin['user']['role'], 'admin')
        admin_token = data_admin['token']

        # 5. Admin token can successfully access admin APIs
        admin_orders_ok = self.client.get('/api/admin/orders', headers={
            'Authorization': f'Bearer {admin_token}'
        })
        self.assertEqual(admin_orders_ok.status_code, 200)

        admin_stats_ok = self.client.get('/api/admin/stats', headers={
            'Authorization': f'Bearer {admin_token}'
        })
        self.assertEqual(admin_stats_ok.status_code, 200)

    def test_complete_catalog_models_and_unique_images(self):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM products ORDER BY id")
        products = c.fetchall()
        conn.close()

        # Total 48 products
        self.assertEqual(len(products), 48, f"Expected 48 products, found {len(products)}")

        seen_images = set()
        categories_count = {}

        for p in products:
            pid = p['id']
            name = p['name']
            cat = p['category']
            price = p['price']
            img = p['image']
            colors = json.loads(p['colors'])
            sizes = json.loads(p['sizes'])

            categories_count[cat] = categories_count.get(cat, 0) + 1

            # Assert valid fields
            self.assertTrue(len(name) > 3, f"Product {pid} name too short")
            self.assertTrue(len(colors) > 0, f"Product {pid} missing colors")
            self.assertTrue(len(sizes) > 0, f"Product {pid} missing sizes")

            # Assert price caps
            if cat == 'Jackets':
                self.assertLessEqual(price, 2000.00, f"Jacket {pid} price exceeds ₹2,000")
                self.assertGreaterEqual(price, 1500.00, f"Jacket {pid} price below ₹1,500")
            else:
                self.assertLessEqual(price, 1500.00, f"{cat} {pid} price exceeds ₹1,500")
                self.assertGreaterEqual(price, 800.00, f"{cat} {pid} price below ₹800")

            # Assert uniqueness of images
            self.assertNotIn(img, seen_images, f"Duplicate image detected: {img} on product {pid}")
            seen_images.add(img)

            # If local image, assert it exists on disk
            if img.startswith('/static/'):
                local_path = os.path.join(r"d:\panite", img.lstrip('/\\'))
                self.assertTrue(os.path.exists(local_path), f"Local image file not found: {local_path}")
                self.assertGreater(os.path.getsize(local_path), 5000, f"Image file suspiciously small: {local_path}")

        # Verify exact counts per category
        self.assertEqual(categories_count.get('Jackets'), 10)
        self.assertEqual(categories_count.get('Oversized T-Shirts'), 12)
        self.assertEqual(categories_count.get('Graphic T-Shirts'), 10)
        self.assertEqual(categories_count.get('Minimal & Core'), 8)
        self.assertEqual(categories_count.get('Shirts'), 4)
        self.assertEqual(categories_count.get('Sweatshirts'), 4)

        # 48 unique images
        self.assertEqual(len(seen_images), 48)

if __name__ == '__main__':
    unittest.main()
