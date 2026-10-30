import unittest
from backend.app import create_app

class TestProducts(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_get_all_products(self):
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        self.assertGreaterEqual(len(products), 6)

    def test_filter_by_category(self):
        res = self.client.get("/api/products?category=Jackets")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        self.assertGreaterEqual(len(products), 1)
        self.assertTrue(all("jacket" in p["category"].lower() or "jacket" in p["name"].lower() for p in products))

    def test_search_products(self):
        res = self.client.get("/api/products?search=Bomber")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        self.assertTrue(any("Bomber" in p["name"] for p in products))

    def test_sort_price_asc(self):
        res = self.client.get("/api/products?sort=price-asc")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        prices = [p["price"] for p in products]
        self.assertEqual(prices, sorted(prices))

    def test_get_single_product(self):
        all_res = self.client.get("/api/products")
        self.assertEqual(all_res.status_code, 200)
        first_prod = all_res.get_json()[0]

        res = self.client.get(f"/api/products/{first_prod['id']}")
        self.assertEqual(res.status_code, 200)
        p = res.get_json()
        self.assertEqual(p["id"], first_prod["id"])
        self.assertIn("colors", p)
        self.assertIn("sizes", p)

    def test_price_caps_enforced_across_catalog(self):
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        for p in products:
            if "jacket" in p["category"].lower() or "jacket" in p["name"].lower():
                self.assertLessEqual(p["price"], 2000.0, f"Jacket {p['name']} exceeded INR 2,000 cap")
            else:
                self.assertLessEqual(p["price"], 1500.0, f"T-shirt {p['name']} exceeded INR 1,500 cap")

    def test_filter_by_price_and_size(self):
        # Test under-999
        res_under_999 = self.client.get("/api/products?price=under-999")
        self.assertEqual(res_under_999.status_code, 200)
        for p in res_under_999.get_json():
            self.assertLessEqual(p["price"], 999.0)

        # Test size
        res_size = self.client.get("/api/products?size=L")
        self.assertEqual(res_size.status_code, 200)
        self.assertGreaterEqual(len(res_size.get_json()), 1)

    def test_get_nonexistent_product(self):
        res = self.client.get("/api/products/non_existent_999")
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
