from microdot import Response
from crypt import crypt
import uuid
import time
import subprocess


# In-memory session store
sessions = {}

def create_session():
    session_id = str(uuid.uuid4())

    expiration_time = time.time() + 3600  # 1-hour expiration from now
    sessions[session_id] = expiration_time

    return session_id

def is_session_valid(session_id):
    current_time = time.time()
    expiration_time = sessions.get(session_id)
    
    # Check if session exists and if it is still valid
    if expiration_time and current_time < expiration_time:
        return True
    else:
        # If session has expired, remove it
        if session_id in sessions:
            del sessions[session_id]
        return False



def read_shadow():
    try:
        # Run the cat command on /etc/shadow with sudo
        result = subprocess.run(
            ['sudo', 'cat', '/etc/shadow'],
            capture_output=True,
            text=True,
            check=True
        )
        # Print the output
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error reading /etc/shadow: {e.stderr}")


# Helper function to get the hashed password from /etc/shadow for a user
def get_user_hash(username):

    shadow_file = read_shadow()
    for line in shadow_file.split('\n'):
        fields = line.strip().split(":")
        if fields[0] == username:
            return fields[1]
        

    return None

# Verify user credentials
def verify_login(username, password):
    stored_hash = get_user_hash(username)
    if not stored_hash:
        return False
    
    # check if this is yeacrypt
    if stored_hash.startswith('$y'):
        return crypt(password, stored_hash) == stored_hash


    # Extract salt from the stored hash
    salt = "$".join(stored_hash.split("$")[:3])
    # Hash the provided password with the salt
    hashed_password = crypt(password, salt)
    
    return hashed_password == stored_hash

def register_login_routes(app):
    # Web route for login page
    @app.route('/login', methods=['POST'])
    def login(request):
        data = request.json

        username = data['username'] if 'username' in data else False
        password = data['password'] if 'password' in data else False
        

        if username and password and verify_login(username, password):
            return Response({ "session_id": create_session() }, 200)
        else:
            return Response({ "error": "Login Failed" }, 401)
        
