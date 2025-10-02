
from microdot import Response
from .authendification import is_session_valid

Response.default_content_type = 'application/json'

DHCPCD_CONFIG_PATH = '/etc/dhcpcd.conf'

def add_cors_headers(response):
    # Allow requests from http://localhost:8080
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response




def register_device_controller_routes(app, device_controller):
    @app.route('/mobile/get-info', methods=['POST'])
    def handle_post(request):
        # authendification check
        session_id = request.headers.get('Authorization')
        if not (session_id and is_session_valid(session_id)):
            response = Response({}, 403)
            return add_cors_headers(response)
        
        R_OBJECT = {}

        (state, connection) = device_controller.get_status()
        R_OBJECT['state'] = state
        R_OBJECT['connection'] = connection
        
        R_OBJECT['apn'] = device_controller.get_apn()

        (rssi, ber) = device_controller.get_signal_quality()
        R_OBJECT['rssi'] = rssi
        R_OBJECT['ber'] = ber

        # get mobile info

        response = Response(R_OBJECT, 200)
        return add_cors_headers(response)

    
    @app.route('/mobile/set-info', methods=['POST'])
    def handle_post(request):
        #try:
        # authendification check
        session_id = request.headers.get('Authorization')
        if not (session_id and is_session_valid(session_id)):
            response = Response({}, 403)
            return add_cors_headers(response)
        
        data = request.json
        print(data)
        apn = data['apn']
        device_controller.set_apn(apn)

        # get mobile info

        response = Response({}, 200)
        '''
            return add_cors_headers(response)
        except Exception as e:
            print(e)
            response = Response(str(e), 500)
            return add_cors_headers(response)
        '''