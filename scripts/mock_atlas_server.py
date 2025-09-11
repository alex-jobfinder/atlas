from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


PNG_PATH = Path('chart.png')  # existing small PNG in repo


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/graph':
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.end_headers()
            with PNG_PATH.open('rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress console logging
        return


def main():
    server = HTTPServer(('localhost', 5000), Handler)
    print('Mock Atlas server running on http://localhost:5000')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
