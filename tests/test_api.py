import json
import threading
import unittest
from http.server import HTTPServer
from urllib.request import urlopen
from app.server import APIHandler
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), APIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
    def test_healthz(self):
        with urlopen(f"{self.base_url}/healthz") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read()), {"status": "healthy"})
    def test_readyz(self):
        with urlopen(f"{self.base_url}/readyz") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read()), {"status": "ready"})
    def test_metrics(self):
        with urlopen(f"{self.base_url}/metrics") as response:
            self.assertIn("api_up 1", response.read().decode())
if __name__ == "__main__":
    unittest.main()

