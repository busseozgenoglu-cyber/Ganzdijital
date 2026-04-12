from http.server import HTTPServer, BaseHTTPRequestHandler
import os, argparse, mimetypes

class GanzHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress logs

    def do_GET(self):
        path = self.path.split('?')[0]

        # Root → index.html
        if path == '/' or path == '':
            path = '/index.html'

        # Remove leading slash
        file_path = path.lstrip('/')

        # Try exact file
        if os.path.isfile(file_path):
            self.serve_file(file_path)
            return

        # Try with .html extension
        if os.path.isfile(file_path + '.html'):
            self.serve_file(file_path + '.html')
            return

        # 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'404 Not Found')

    def serve_file(self, file_path):
        mime, _ = mimetypes.guess_type(file_path)
        if not mime:
            mime = 'text/html'
        with open(file_path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8' if 'text' in mime else mime)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

def run(port=8000):
    server = HTTPServer(('', port), GanzHandler)
    print(f'Ganz Dijital serving on port {port}')
    server.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8000)))
    args = parser.parse_args()
    run(port=args.port)
