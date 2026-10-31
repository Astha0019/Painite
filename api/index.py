import os
import sys
import urllib.parse

# Ensure root workspace directory is added to sys.path so backend imports succeed
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app

flask_app = create_app()

class VercelWSGIMiddleware:
    """
    Normalizes Vercel Serverless Function WSGI environment so Flask routes
    correctly whether invoked via root rewrites, query captures, or direct Vercel preview.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Check if a route was captured via query parameter (__route__)
        query_string = environ.get("QUERY_STRING", "")
        params = urllib.parse.parse_qs(query_string)
        captured_route = params.get("__route__", [None])[0]

        # 2. Check if Vercel sent the original path in HTTP headers
        matched = environ.get("HTTP_X_MATCHED_PATH") or environ.get("HTTP_X_FORWARDED_URI")

        if captured_route:
            clean_route = "/" + captured_route.lstrip("/")
            if not clean_route.startswith("/api"):
                clean_route = "/api" + clean_route
            environ["PATH_INFO"] = clean_route
            # Clean __route__ from query string so endpoints receive undisturbed parameters
            filtered_params = {k: v for k, v in params.items() if k != "__route__"}
            environ["QUERY_STRING"] = urllib.parse.urlencode(filtered_params, doseq=True)
        elif matched:
            path_only = matched.split("?")[0]
            if path_only in ("/api/index", "/api/index.py", "/api"):
                environ["PATH_INFO"] = "/"
            else:
                environ["PATH_INFO"] = path_only
        elif environ.get("PATH_INFO") in ("/api/index", "/api/index.py", "/api"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)

app = VercelWSGIMiddleware(flask_app)
handler = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)
