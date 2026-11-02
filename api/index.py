import os
import sys
from urllib.parse import parse_qs, urlencode, unquote

# Ensure root workspace directory is added to sys.path so backend imports succeed
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app

flask_app = create_app()

class VercelWSGIMiddleware:
    """
    Ensures standard WSGI environment matching for Vercel Serverless Functions.
    Accurately restores original client PATH_INFO and QUERY_STRING across
    Vercel reverse proxy rewrites and query-based routing.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get("QUERY_STRING", "")

        # 1. Primary: check if Vercel rewrite injected explicit __route__
        if "__route__" in query_string:
            params = parse_qs(query_string, keep_blank_values=True)
            if "__route__" in params:
                route_val = params.pop("__route__")[0]
                route_clean = unquote(route_val).lstrip("/")
                environ["PATH_INFO"] = f"/api/{route_clean}" if route_clean else "/api"

                # Reconstruct remaining original query parameters
                flat_params = []
                for k, vals in params.items():
                    for v in vals:
                        flat_params.append((k, v))
                environ["QUERY_STRING"] = urlencode(flat_params)
                return self.wsgi_app(environ, start_response)

        current_path = environ.get("PATH_INFO", "")

        # 2. If PATH_INFO is already a specific API route (e.g. /api/products), keep it
        if current_path.startswith("/api/") and current_path not in ("/api/index", "/api/index.py"):
            return self.wsgi_app(environ, start_response)

        # 3. Check raw client request headers forwarded by reverse proxies
        raw_uri = (
            environ.get("REQUEST_URI")
            or environ.get("RAW_URI")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_ORIGINAL_URL")
        )
        if raw_uri:
            parts = raw_uri.split("?", 1)
            uri_path = parts[0]
            if uri_path.startswith("/api/") and uri_path not in ("/api/index", "/api/index.py"):
                environ["PATH_INFO"] = uri_path
                if len(parts) > 1 and not environ.get("QUERY_STRING"):
                    environ["QUERY_STRING"] = parts[1]
                return self.wsgi_app(environ, start_response)

        return self.wsgi_app(environ, start_response)

app = VercelWSGIMiddleware(flask_app)
handler = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)
