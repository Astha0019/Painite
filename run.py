import os
import sys
from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    print("=" * 60)
    print("  PAINITE STUDIO - BESPOKE APPAREL FULL-STACK APPLICATION")
    print(f"  Running on: http://{host}:{port}")
    print("  API Health: http://{host}:{port}/api/health")
    print("  Admin Credentials: admin@painite.studio / PainiteAdmin!42")
    print("  Customer Credentials: customer@painite.studio / PainiteUser!42")
    print("=" * 60)
    app.run(host=host, port=port, debug=False)
