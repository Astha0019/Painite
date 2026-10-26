import unittest
import json
from backend.app import create_app

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_login_success_admin(self):
        res = self.client.post("/api/auth/login", json={
            "email": "admin@painite.studio",
            "password": "PainiteAdmin!42"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "admin")
        self.assertEqual(data["user"]["email"], "admin@painite.studio")

    def test_login_success_customer(self):
        res = self.client.post("/api/auth/login", json={
            "email": "customer@painite.studio",
            "password": "PainiteUser!42"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "customer")

    def test_login_invalid_password(self):
        res = self.client.post("/api/auth/login", json={
            "email": "customer@painite.studio",
            "password": "WrongPassword123"
        })
        self.assertEqual(res.status_code, 401)
        self.assertIn("detail", res.get_json())

    def test_register_and_get_me(self):
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:10]}@studio.com"
        res = self.client.post("/api/auth/register", json={
            "name": "Test Patron",
            "email": unique_email,
            "password": "SecurePassword123"
        })
        self.assertEqual(res.status_code, 201)
        token = res.get_json()["token"]

        # Call /api/auth/me with bearer token
        me_res = self.client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(me_res.status_code, 200)
        user = me_res.get_json()
        self.assertEqual(user["email"], unique_email)
        self.assertEqual(user["name"], "Test Patron")

    def test_register_duplicate_email(self):
        res = self.client.post("/api/auth/register", json={
            "name": "Duplicate User",
            "email": "customer@painite.studio",
            "password": "SecurePassword123"
        })
        self.assertEqual(res.status_code, 409)

if __name__ == "__main__":
    unittest.main()
