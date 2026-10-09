from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
            response = {"status": "healthy"}
        elif self.path == "/readyz":
            response = {"status": "ready"}
        elif self.path == "/metrics":
            response = "# HELP api_up API availability\napi_up 1\n"
        else:
            response = {"message": "Sample DevOps API v1.1"}
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain" if self.path == "/metrics"
            else "application/json"
        )
        self.end_headers()
        if isinstance(response, dict):
            self.wfile.write(json.dumps(response).encode())
        else:
            self.wfile.write(response.encode())
if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), APIHandler)
    print("Sample API listening on port 8080", flush=True)
    server.serve_forever()
