from http.server import BaseHTTPRequestHandler, HTTPServer

class S(BaseHTTPRequestHandler):
    def __init__(self):
        self.get_routes = []
        self.post_routes = []
        
        pass
    
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
    def _send_response(self, status, response):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.send_response(response)
        self.end_headers()
    
    def do_GET(self):
        self._set_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        
        # decode current data object of post request   
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        found_route = False
        for r in self.post_routes:
            # find matching route
            if r[0] == self.path:
                found_route = True
                
                # call handler
                (status, response) = r[1](post_data)
                self._send_response(status, response)
                break
                    
        if not found_route:
            # send response if no route is defined
            self._set_headers()
        
        
        print(post_data)

    def add_post(self, path, handler):
        
        # add current route to handler
        self.post_routes.append([path, handler])
        
        
    
def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    def set_config(data):
        print(data)
        return (200, )
    
    httpd.add_post('/set-config')
    print('Starting httpd... {}'.format(port))
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()