from http.server import HTTPServer, BaseHTTPRequestHandler
import os, argparse, mimetypes, gzip, urllib.parse, hashlib

REDIRECTS = {
    "/blog/tar%C4%B1m-ciftlik-dijital-pazarlama.html": "/blog/tarim-ciftlik-dijital-pazarlama.html",
    "/blog/tarım-ciftlik-dijital-pazarlama.html": "/blog/tarim-ciftlik-dijital-pazarlama.html",
    "/blog/danismanlik-ko%C3%A7luk-dijital-pazarlama.html": "/blog/danismanlik-kocluk-dijital-pazarlama.html",
    "/blog/danismanlik-koçluk-dijital-pazarlama.html": "/blog/danismanlik-kocluk-dijital-pazarlama.html",
    "/og-image.jpg": "/og-image.svg",
}

class GanzHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _handle_request(self, head_only=False):
        raw_path = self.path.split("?")[0].split("#")[0]

        if raw_path in REDIRECTS:
            self.send_response(301)
            self.send_header("Location", REDIRECTS[raw_path])
            self.send_header("Cache-Control", "public, max-age=31536000")
            self.end_headers()
            return

        path = urllib.parse.unquote(raw_path)
        if path in REDIRECTS:
            self.send_response(301)
            self.send_header("Location", REDIRECTS[path])
            self.send_header("Cache-Control", "public, max-age=31536000")
            self.end_headers()
            return

        if path.endswith("/") and path != "/":
            canonical = path.rstrip("/")
            if os.path.isfile(canonical.lstrip("/")) or os.path.isfile(canonical.lstrip("/") + ".html"):
                self.send_response(301)
                self.send_header("Location", canonical)
                self.send_header("Cache-Control", "public, max-age=31536000")
                self.end_headers()
                return

        if path in ("/", ""):
            self.serve_file("index.html", head_only=head_only)
            return
        file_path = path.lstrip("/")
        if os.path.isfile(file_path):
            self.serve_file(file_path, head_only=head_only)
            return
        if os.path.isfile(file_path + ".html"):
            self.serve_file(file_path + ".html", head_only=head_only)
            return

        if os.path.isfile("404.html"):
            self.serve_file("404.html", status=404, head_only=head_only)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if not head_only:
                self.wfile.write(b"<h1>404 Not Found</h1>")

    def do_GET(self):
        self._handle_request(head_only=False)

    def do_HEAD(self):
        self._handle_request(head_only=True)

    def serve_file(self, file_path, status=200, head_only=False):
        mime, _ = mimetypes.guess_type(file_path)
        if not mime:
            mime = "text/html"
        with open(file_path, "rb") as f:
            data = f.read()

        etag = '"' + hashlib.md5(data).hexdigest() + '"'
        if_none = self.headers.get("If-None-Match", "")
        if if_none == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", self._cache_header(file_path))
            self.end_headers()
            return

        accept_encoding = self.headers.get("Accept-Encoding", "")
        use_gzip = "gzip" in accept_encoding and ("text" in mime or mime in (
            "application/json", "application/xml", "image/svg+xml",
            "application/javascript"
        ))

        self.send_response(status)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if "text" in mime or mime == "application/json" else ""))
        self.send_header("Cache-Control", self._cache_header(file_path))
        self.send_header("ETag", etag)
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://www.google-analytics.com; "
            "frame-ancestors 'none'"
        )
        self.send_header("X-DNS-Prefetch-Control", "on")

        if use_gzip:
            data = gzip.compress(data, compresslevel=6)
            self.send_header("Content-Encoding", "gzip")

        self.send_header("Content-Length", str(len(data)))
        self.end_headers()

        if not head_only:
            self.wfile.write(data)

    def _cache_header(self, file_path):
        if file_path.endswith(".html"):
            return "public, max-age=3600, stale-while-revalidate=86400"
        elif file_path.endswith((".css", ".js")):
            return "public, max-age=604800, immutable"
        elif file_path.endswith((".xml", ".txt", ".json")):
            return "public, max-age=3600"
        elif file_path.endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico")):
            return "public, max-age=2592000, immutable"
        return "public, max-age=3600"

def run(port=8000):
    server = HTTPServer(("", port), GanzHandler)
    print(f"Ganz Dijital serving on :{port}")
    server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args = parser.parse_args()
    run(port=args.port)
