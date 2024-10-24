from microdot import Microdot, send_file, Response
import os

app = Microdot()
Response.default_content_type = 'text/html'

# Path to the static files directory
STATIC_FOLDER = 'client'

@app.route('/')
async def index(request):
    return send_file('./client/index.html')

@app.route('/client/<path:path>')
def serve_static(request, path):
    print(path)
    file_path = os.path.join(STATIC_FOLDER, path)
    if os.path.isfile(file_path):
        return Response(open(file_path, 'rb').read())
    else:
        return Response('File not found')



@app.post('/get-data')
def handle_post(request):
    data = request.json

    
    # Process the data here
    return 'Data received', 200

@app.post('/save-data')
def handle_post(request):
    data = request.json
    # Process the data here
    return 'Data received', 200


app.run(port=5002)