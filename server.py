from http.server import HTTPServer, BaseHTTPRequestHandler
import os, argparse, mimetypes, gzip, urllib.parse, hashlib, time

REDIRECTS = {
    "/blog/tar%C4%B1m-ciftlik-dijital-pazarlama.html": "/blog/tarim-ciftlik-dijital-pazarlama.html",
    "/blog/tarım-ciftlik-dijital-pazarlama.html": "/blog/tarim-ciftlik-dijital-pazarlama.html",
    "/blog/danismanlik-ko%C3%A7luk-dijital-pazarlama.html": "/blog/danismanlik-kocluk-dijital-pazarlama.html",
    "/blog/danismanlik-koçluk-dijital-pazarlama.html": "/blog/danismanlik-kocluk-dijital-pazarlama.html",
    "/ganz-dijital-FINAL.html": "/",
}

TRAILING_SLASH_EXEMPT = {"/"}

_file_cache = {}
_cache_max_age = 300

def _get_cached(file_path):
    now = time.time()
    entry = _file_cache.get(file_path)
    if entry and (now - entry["time"]) < _cache_max_age:
        return entry
    try:
        stat = os.stat(file_path)
        with open(file_path, "rb") as f:
            data = f.read()
        etag = hashlib.md5(data).hexdigest()
        compressed = gzip.compress(data, compresslevel=6)
        entry = {
            "data": data,
            "gzip": compressed,
            "etag": f'"{etag}"',
            "mtime": stat.st_mtime,
            "time": now,
        }
        _file_cache[file_path] = entry
        return entry
    except FileNotFoundError:
        return None


class GanzHandler(BaseHTTPRequestHandler):
    server_version = "GanzDigital/2.0"

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self._handle("GET")

    def do_HEAD(self):
        self._handle("HEAD")

    def _handle(self, method):
        raw_path = self.path.split("?")[0].split("#")[0]

        if raw_path in REDIRECTS:
            self._redirect(REDIRECTS[raw_path])
            return

        path = urllib.parse.unquote(raw_path)
        if path in REDIRECTS:
            self._redirect(REDIRECTS[path])
            return

        if path != "/" and path.endswith("/"):
            self._redirect(path.rstrip("/"), code=301)
            return

        if path in ("/", ""):
            self._serve("index.html", method=method)
            return

        file_path = path.lstrip("/")

        if os.path.isfile(file_path):
            self._serve(file_path, method=method)
            return
        if not file_path.endswith(".html") and os.path.isfile(file_path + ".html"):
            self._redirect("/" + file_path + ".html", code=301)
            return

        if os.path.isfile("404.html"):
            self._serve("404.html", status=404, method=method)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if method == "GET":
                self.wfile.write(b"<h1>404 Not Found</h1>")

    def _redirect(self, location, code=301):
        self.send_response(code)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.end_headers()

    def _serve(self, file_path, status=200, method="GET"):
        cached = _get_cached(file_path)
        if not cached:
            self.send_response(404)
            self.end_headers()
            return

        mime, _ = mimetypes.guess_type(file_path)
        if not mime:
            mime = "application/octet-stream"
        if file_path.endswith(".html"):
            mime = "text/html"
        elif file_path.endswith(".svg"):
            mime = "image/svg+xml"
        elif file_path.endswith(".json"):
            mime = "application/json"
        elif file_path.endswith(".xml"):
            mime = "application/xml"

        etag = cached["etag"]
        if_none_match = self.headers.get("If-None-Match", "")
        if etag and if_none_match == etag:
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", self._cache_control(file_path))
            self.end_headers()
            return

        is_text = "text" in mime or mime in ("application/json", "application/xml", "application/javascript", "image/svg+xml")
        accept_encoding = self.headers.get("Accept-Encoding", "")
        use_gzip = "gzip" in accept_encoding and is_text

        data = cached["gzip"] if use_gzip else cached["data"]

        self.send_response(status)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if is_text else ""))
        self.send_header("Cache-Control", self._cache_control(file_path))
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
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com https://pagead2.googlesyndication.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://www.google-analytics.com https://analytics.google.com; "
            "frame-ancestors 'none'"
        )
        self.send_header("X-DNS-Prefetch-Control", "on")

        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if method == "GET":
            self.wfile.write(data)

    def _cache_control(self, file_path):
        if file_path.endswith(".html"):
            return "public, max-age=3600, stale-while-revalidate=86400"
        elif file_path.endswith((".css", ".js")):
            return "public, max-age=2592000, immutable"
        elif file_path.endswith((".xml", ".txt", ".json")):
            return "public, max-age=3600, stale-while-revalidate=86400"
        elif file_path.endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico", ".gif")):
            return "public, max-age=31536000, immutable"
        return "public, max-age=86400"


def run(port=8000):
    server = HTTPServer(("", port), GanzHandler)
    print(f"Ganz Dijital serving on :{port}")
    server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args = parser.parse_args()
    run(port=args.port)
