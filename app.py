from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

@app.route('/')
def index():
    return render_template('coba.html')


@app.route('/save_message', methods=['POST'])
def save_message():
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'status': 'error', 'message': 'Pesan tidak boleh kosong.'}), 400
    return jsonify({'status': 'success', 'message': message})

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

@socketio.on_error()
def error_handler(e):
    print('An error has occurred: ' + str(e))

if __name__ == '__main__':
    socketio.run(app)
