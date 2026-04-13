from http.server import HTTPServer, BaseHTTPRequestHandler
import os, argparse, mimetypes, gzip, urllib.parse

# Redirect map: old Turkish-char URLs → new ASCII-safe URLs
REDIRECTS = {
    "/blog/tar%C4%B1m-ciftlik-dijital-pazarlama.html": "/blog/tarim-ciftlik-dijital-pazarlama.html",
    "/blog/tarım-ciftlik-dijital-pazarlama.html": "/blog/tarim-ciftlik-dijital-pazarlama.html",
    "/blog/danismanlik-ko%C3%A7luk-dijital-pazarlama.html": "/blog/danismanlik-kocluk-dijital-pazarlama.html",
    "/blog/danismanlik-koçluk-dijital-pazarlama.html": "/blog/danismanlik-kocluk-dijital-pazarlama.html",
}

class GanzHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        raw_path = self.path.split("?")[0].split("#")[0]

        # Check permanent redirects first
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

        if path in ("/", ""):
            self.serve_file("index.html")
            return
        file_path = path.lstrip("/")
        if os.path.isfile(file_path):
            self.serve_file(file_path)
            return
        if os.path.isfile(file_path + ".html"):
            self.serve_file(file_path + ".html")
            return
        # 404
        if os.path.isfile("404.html"):
            self.serve_file_with_status("404.html", 404)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>404 Not Found</h1>")

    def serve_file(self, file_path, status=200):
        self.serve_file_with_status(file_path, status)

    def serve_file_with_status(self, file_path, status=200):
        mime, _ = mimetypes.guess_type(file_path)
        if not mime:
            mime = "text/html"
        with open(file_path, "rb") as f:
            data = f.read()
        accept_encoding = self.headers.get("Accept-Encoding", "")
        use_gzip = "gzip" in accept_encoding and "text" in mime
        self.send_response(status)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if "text" in mime else ""))
        if file_path.endswith(".html"):
            self.send_header("Cache-Control", "public, max-age=3600, stale-while-revalidate=86400")
        elif file_path.endswith((".css", ".js")):
            self.send_header("Cache-Control", "public, max-age=604800")
        elif file_path.endswith((".xml", ".txt", ".json")):
            self.send_header("Cache-Control", "public, max-age=3600")
        elif file_path.endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico")):
            self.send_header("Cache-Control", "public, max-age=2592000")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-XSS-Protection", "1; mode=block")
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
            data = gzip.compress(data, compresslevel=9)
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self):
        self.do_GET()

def run(port=8000):
    server = HTTPServer(("", port), GanzHandler)
    print(f"Ganz Dijital serving on :{port}")
    server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)))
    args = parser.parse_args()
    run(port=args.port)
