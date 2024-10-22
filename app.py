from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import uuid
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

UPLOAD_FOLDER = 'temp_audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('coba.html')

@app.route('/save_message', methods=['POST'])
def save_message():
    data = request.json
    message = data.get('message')
    return jsonify({'status': 'success', 'message': message})

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    filename = str(uuid.uuid4()) + '.wav'
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(filepath)

    return jsonify({'success': True, 'url': f'/audio/{filename}'})

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'{username} telah bergabung ke ruangan.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f'{username} telah meninggalkan ruangan.'}, room=room)

@socketio.on('offer')
def on_offer(data):
    emit('offer', data, room=data['target'])

@socketio.on('answer')
def on_answer(data):
    emit('answer', data, room=data['target'])

@socketio.on('ice_candidate')
def on_ice_candidate(data):
    emit('ice_candidate', data, room=data['target'])

@socketio.on('call_request')
def on_call_request(data):
    emit('incoming_call', {'caller': request.sid}, room=data['target'])

@socketio.on('call_accepted')
def on_call_accepted(data):
    emit('call_accepted', room=data['target'])

@socketio.on('call_rejected')
def on_call_rejected(data):
    emit('call_rejected', room=data['target'])

@socketio.on_error()
def error_handler(e):
    print('An error has occurred: ' + str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
