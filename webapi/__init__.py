from microdot import Microdot, send_file, Response, Request
import os
import json
from .network import register_network_routes
from .authendification import register_login_routes, is_session_valid
from .devicecontroller import register_device_controller_routes


app = Microdot()
Response.default_content_type = 'text/html'

Request.max_content_length = 1024 * 1024 * 1024
Request.max_body_length = 16 * 1024 * 1024

CONFIG_PATH = '/home/pi/Documents/IotAdapter/config.json'


# Path to the static files directory
STATIC_FOLDER = '/home/pi/Documents/IotAdapter/webapi/client'


PORT = os.getenv('WEB_PORT', 0)



def main(CONFIG_OBJECT, device_controller):

    def add_cors_headers(response):
        # Allow requests from http://localhost:8080
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    @app.before_request
    def handle_options(request):
        
        if request.method == 'OPTIONS':
            response = Response()  # Create an empty response for OPTIONS
            return add_cors_headers(response)  # Return CORS headers

    @app.after_request
    def apply_cors_headers(request, response):
        """Apply CORS headers to all responses."""
        return add_cors_headers(response)

    @app.route('/')
    async def index(request):
        response = send_file(f'{STATIC_FOLDER}/index.html')
        return add_cors_headers(response)

    @app.post('/get-config')
    def handle_post(request):
        # authendification check
        session_id = request.headers.get('Authorization')
        if not (session_id and is_session_valid(session_id)):
            response = Response({}, 403)
            return add_cors_headers(response)


        data = request.json

        response = Response(CONFIG_OBJECT, 200)
        return add_cors_headers(response)


    # Handle preflight requests for CORS
    @app.route('/set-config', methods=['POST'])
    def handle_post(request):
        # authendification check
        session_id = request.headers.get('Authorization')
        if not (session_id and is_session_valid(session_id)):
            response = Response({}, 403)
            return add_cors_headers(response)

        data = request.json

        if not 'config' in data:
            response = Response({}, 500)
            return add_cors_headers(response)
        
        config = data['config']
        print( config['data'] )

        # exchange config by reference
        CONFIG_OBJECT['data'] = config['data']

        
        try:
            # save new config file
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"Configuration saved as JSON to {CONFIG_PATH}")

        except:
            response = Response({}, 500)
            return add_cors_headers(response)

        response = Response({}, 200)
        return add_cors_headers(response)
    
   

    register_network_routes(app)
    register_login_routes(app)
    register_device_controller_routes(app, device_controller)


    @app.route('/img/<path:path>')
    def serve_img(request, path):
        file_path = os.path.join(STATIC_FOLDER, 'img', path)
        if os.path.exists(file_path):
            return send_file(file_path, content_type='image/svg+xml' if path.endswith('.svg') else None)

        return Response('File not found', status=404)

    # 
    @app.route('/<path:path>')
    def serve_static(request, path):
        # Check if the requested file exists
        file_path = os.path.join(STATIC_FOLDER, path)
        if os.path.exists(file_path):
            return send_file(file_path)

        # Serve nindex.html for unmatched paths (for Vue Router)
        return send_file(os.path.join(STATIC_FOLDER, 'index.html'))

   

    if PORT:
        app.run(debug=True, port=PORT)


#asyncio.run(main())