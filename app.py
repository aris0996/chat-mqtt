from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from engineio.async_drivers import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Tambahkan secret key
CORS(app, resources={r"/*": {"origins": "*"}})

# Update konfigurasi SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=5,
    ping_interval=25,
    logger=True,
    engineio_logger=True
)

logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

# Simpan data user global
global_users = {}

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

@app.route('/global')
def global_chat():
    return render_template('global.html')

online_users = set()

@socketio.on('join_global')
def handle_global_join(data):
    username = data['username']
    session['username'] = username
    global_users[request.sid] = username
    
    # Kirim pesan sistem untuk user baru
    emit('global_message', {
        'username': 'System',
        'message': f'👋 {username} bergabung ke chat',
        'type': 'system'
    }, broadcast=True)
    
    emit('user_count', len(global_users), broadcast=True)

@socketio.on('global_message')
def handle_global_message(data):
    username = global_users.get(request.sid, 'Anonymous')
    message_data = {
        'username': username,
        'message': data['message'],
        'type': data.get('type', 'text')
    }
    
    # Tambahkan informasi reply jika ada
    if 'replyTo' in data:
        message_data['replyTo'] = data['replyTo']
        message_data['replyToText'] = data.get('replyToText', '')
    
    emit('global_message', message_data, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in global_users:
        username = global_users[request.sid]
        del global_users[request.sid]
        emit('global_message', {
            'username': 'System',
            'message': f'👋 {username} meninggalkan chat',
            'type': 'system'
        }, broadcast=True)
        emit('user_count', len(global_users), broadcast=True)

if __name__ == '__main__':
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        allow_unsafe_werkzeug=True  # Hanya untuk development
    )