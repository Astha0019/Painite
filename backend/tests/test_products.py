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
        res = self.client.get("/api/products?category=Core")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        self.assertTrue(all(p["category"].lower() == "core" for p in products))

    def test_search_products(self):
        res = self.client.get("/api/products?search=Essential")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        self.assertTrue(any("Essential" in p["name"] for p in products))

    def test_sort_price_asc(self):
        res = self.client.get("/api/products?sort=price-asc")
        self.assertEqual(res.status_code, 200)
        products = res.get_json()
        prices = [p["price"] for p in products]
        self.assertEqual(prices, sorted(prices))

    def test_get_single_product(self):
        res = self.client.get("/api/products/p1")
        self.assertEqual(res.status_code, 200)
        p = res.get_json()
        self.assertEqual(p["id"], "p1")
        self.assertIn("colors", p)
        self.assertIn("sizes", p)
        self.assertIn("styles", p)

    def test_get_nonexistent_product(self):
        res = self.client.get("/api/products/non_existent_999")
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
