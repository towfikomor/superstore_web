# controller.py
import os
import http.server
import socketserver
import json
from urllib.parse import urlparse
from model import SuperstoreModel
from view import SuperstoreView

PORT = int(os.environ.get("PORT", 8000))

model = SuperstoreModel()
view = SuperstoreView()

class SuperstoreHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/" or parsed_path.path == "/index.html":
            content = view.render_template("index.html")
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
            
        elif parsed_path.path == "/api/products":
            self.send_json(model.get_all_products())
            
        elif parsed_path.path == "/api/customers":
            self.send_json(model.get_all_customers())
            
        elif parsed_path.path == "/api/sales":
            self.send_json(model.get_sales_report())
            
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8')) if post_data else {}
        except:
            body = {}

        if parsed_path.path == "/api/add_product":
            success, msg = model.add_product(
                body.get('name'), body.get('price'), body.get('stock'), body.get('category_id')
            )
            self.send_json({"status": "success" if success else "error", "message": msg}, status=200 if success else 400)
            
        elif parsed_path.path == "/api/add_customer":
            success, msg = model.add_customer(body.get('name'), body.get('email'))
            self.send_json({"status": "success" if success else "error", "message": msg}, status=200 if success else 400)
            
        elif parsed_path.path == "/api/place_order":
            success, msg = model.place_order(
                int(body.get('customer_id')), int(body.get('product_id')), int(body.get('quantity'))
            )
            self.send_json({"status": "success" if success else "error", "message": msg}, status=200 if success else 400)
        else:
            self.send_error(404, "Endpoint Not Found")

    def send_json(self, data, status=200):
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", len(response))
        self.end_headers()
        self.wfile.write(response)

if __name__ == "__main__":
    server_address = ("", PORT)
    httpd = socketserver.TCPServer(server_address, SuperstoreHandler)
    print(f"🚀 MVC Web Server running at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()