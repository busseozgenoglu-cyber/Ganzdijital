from http.server import HTTPServer, BaseHTTPRequestHandler
import os, argparse, mimetypes, gzip

class GanzHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]
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
        # SEO: 404 page
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"""<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>404 | Ganz Dijital</title>
<meta name="robots" content="noindex,follow">
<style>body{background:#020408;color:#e8f4ff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;flex-direction:column;gap:20px;text-align:center}
h1{font-size:80px;margin:0;color:#00f5ff}a{color:#00f5ff;border:1px solid #00f5ff;padding:12px 28px;text-decoration:none}</style>
</head><body><h1>404</h1><p>Sayfa bulunamadi</p><a href="/">Ana Sayfaya Don</a></body></html>""")

    def serve_file(self, file_path):
        mime, _ = mimetypes.guess_type(file_path)
        if not mime:
            mime = "text/html"
        with open(file_path, "rb") as f:
            data = f.read()
        accept_encoding = self.headers.get("Accept-Encoding", "")
        use_gzip = "gzip" in accept_encoding and "text" in mime
        self.send_response(200)
        self.send_header("Content-Type", mime + ("; charset=utf-8" if "text" in mime else ""))
        # Cache — HTML kısa, statik uzun
        if file_path.endswith(".html"):
            self.send_header("Cache-Control", "public, max-age=3600, stale-while-revalidate=86400")
        elif file_path.endswith((".css", ".js")):
            self.send_header("Cache-Control", "public, max-age=604800")
        elif file_path.endswith((".xml", ".txt")):
            self.send_header("Cache-Control", "public, max-age=3600")
        elif file_path.endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".ico")):
            self.send_header("Cache-Control", "public, max-age=2592000")
        # Güvenlik + SEO headers
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-XSS-Protection", "1; mode=block")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # Gzip
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
