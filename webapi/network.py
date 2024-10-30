
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


def parse_dhcpcd_config():
    """Parse the /etc/dhcpcd.conf file to get current network settings."""
    config = {
        "dhcp": True,
        "ip": "",
        "cider": "",
        "gateway": "",
        "dns": ""
    }

    with open(DHCPCD_CONFIG_PATH, 'r') as file:
        lines = file.readlines()
        
        # Check for DHCP by seeing if interface configuration is commented
        dhcp_enabled = all(line.startswith('#') for line in lines if 'interface eth0' in line)
        print(dhcp_enabled)
        config['dhcp'] = dhcp_enabled
        
        if not dhcp_enabled:
            for line in lines:
                if line.startswith('static ip_address'):
                    ip_cidr = line.split('=')[1].strip()
                    ip, cidr = ip_cidr.split('/')
                    config['ip'] = ip
                    config['cider'] = int(cidr)
                elif line.startswith('static routers'):
                    config['gateway'] = line.split('=')[1].strip()
                elif line.startswith('static domain_name_servers'):
                    config['dns'] = line.split('=')[1].strip()
    
    return config


def write_dhcpcd_config(config):
    """Write network configuration to /etc/dhcpcd.conf based on input."""
    lines = []
    with open(DHCPCD_CONFIG_PATH, 'r') as file:
        lines = file.readlines()

    with open(DHCPCD_CONFIG_PATH, 'w') as file:
        dhcp_enabled = config['dhcp']
        inside_static_section = False

        for line in lines:
            if 'interface eth0' in line:
                inside_static_section = True
                if dhcp_enabled:
                    # Only add a comment if the line isn't already commented
                    if not line.strip().startswith('#'):
                        file.write(f"# {line}")
                    else:
                        file.write(line)  # Keep the line as is if it's already commented
                else:
                    # Uncomment the line if DHCP is disabled
                    file.write(line.lstrip('#').strip() + '\n')  # Remove # and any trailing spaces
                    
            elif inside_static_section and 'static' in line:
                if dhcp_enabled:
                    # Only comment out static lines if they're not already commented
                    if not line.strip().startswith('#'):
                        file.write(f"# {line}")
                    else:
                        file.write(line)  # Keep the line as is if it's already commented
                else:
                    key = line.split('=')[0].strip('#').strip()
                    if key == 'static ip_address':
                        file.write(f"static ip_address={config['ip']}/{config['cider']}\n")
                    elif key == 'static routers':
                        file.write(f"static routers={config['gateway']}\n")
                    elif key == 'static domain_name_servers':
                        file.write(f"static domain_name_servers={config['dns']}\n")
            else:
                file.write(line)

        if not dhcp_enabled:
            # Add the interface section if not present
            if not any('interface eth0' in line for line in lines):
                file.write("interface eth0\n")
                file.write(f"static ip_address={config['ip']}/{config['cider']}\n")
                file.write(f"static routers={config['gateway']}\n")
                file.write(f"static domain_name_servers={config['dns']}\n")


def register_network_routes(app):


    
    @app.route('/network/set-config', methods=['POST', 'OPTIONS'])
    def handle_network_config(request):
        # authendification check
        session_id = request.headers.get('Authorization')
        if not (session_id and is_session_valid(session_id)):
            response = Response({}, 403)
            return add_cors_headers(response)

        if request.method == 'OPTIONS':
            # Handle the preflight OPTIONS request with CORS headers
            response = Response()
            return add_cors_headers(response)

        data = request.json
        print('/network/config')

        if 'dhcp' in data and 'ip' in data and 'cider' in data and 'gateway' in data and 'dns' in data:
            if data['dhcp']:
                config = {
                    "dhcp": True,
                    "ip": "",
                    "cider": "",
                    "gateway": "",
                    "dns": ""
                }
            else:
                config = {
                    "dhcp": False,
                    "ip": data['ip'],
                    "cider": data['cider'],
                    "gateway": data['gateway'],
                    "dns": data['dns']
                }
            write_dhcpcd_config(config)
            response = Response({"message": "Configuration updated successfully"}, 200)
            return add_cors_headers(response)
        else:
            response = Response({"error": "Invalid request data"}, 400)
            return add_cors_headers(response)


    @app.route('/network/get-config', methods=['GET'])
    def get_network_config(request):
        # authendification check
        session_id = request.headers.get('Authorization')
        if not (session_id and is_session_valid(session_id)):
            response = Response({}, 403)
            return add_cors_headers(response)

        config = parse_dhcpcd_config()

        response = Response(config, 200)
        return add_cors_headers(response)

