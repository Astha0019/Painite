import os
import sys

# Ensure root workspace directory is added to sys.path so backend imports succeed
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app

flask_app = create_app()

class VercelWSGIMiddleware:
    """
    Ensures standard WSGI environment matching for Vercel Serverless Functions.
    Resolves true PATH_INFO from proxy forwarding headers when available.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_VERCEL_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_ORIGINAL_URL")
        )
        if matched:
            path_only = matched.split("?")[0]
            environ["PATH_INFO"] = path_only

        return self.wsgi_app(environ, start_response)

app = VercelWSGIMiddleware(flask_app)
handler = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)
