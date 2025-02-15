from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from engineio.async_drivers import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app, resources={r"/*": {"origins": "*"}})

# Konfigurasi SocketIO untuk Vercel
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode=None,  # Biarkan SocketIO memilih mode yang sesuai
    ping_timeout=10000,
    ping_interval=25000,
    manage_session=False,
    logger=True,
    engineio_logger=True,
    path='/socket.io/',
    transports=['polling'],
    always_connect=True,
    max_http_buffer_size=1e8,
    cookie=False,
    cors_credentials=False,
    async_handlers=False,  # Disable async handlers di Vercel
    max_queue_size=10,
    # Tambahan untuk Vercel
    message_queue=None,
    channel='socketio',
    write_only=False
)

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('socketio')
logger.setLevel(logging.INFO)

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

@socketio.on_error_default
def default_error_handler(e):
    logger.error(f'SocketIO error occurred: {str(e)}')
    try:
        emit('error', {'message': 'An error occurred', 'details': str(e)})
    except Exception as emit_error:
        logger.error(f'Error sending error message: {str(emit_error)}')

@socketio.on('connect')
def handle_connect():
    try:
        print(f'Client connected: {request.sid}')
        session['sid'] = request.sid
        emit('connect_response', {'status': 'connected', 'sid': request.sid})
    except Exception as e:
        print(f'Error in handle_connect: {str(e)}')

@socketio.on('disconnect')
def handle_disconnect():
    try:
        print(f'Client disconnected: {request.sid}')
        if request.sid in global_users:
            username = global_users[request.sid]
            del global_users[request.sid]
            emit('global_message', {
                'username': 'System',
                'message': f'👋 {username} meninggalkan chat',
                'type': 'system'
            }, broadcast=True)
            emit('user_count', len(global_users), broadcast=True)
    except Exception as e:
        print(f'Error in handle_disconnect: {str(e)}')

@app.route('/global')
def global_chat():
    return render_template('global.html')

online_users = set()

@socketio.on('join_global')
def handle_global_join(data):
    try:
        username = data['username']
        session['username'] = username
        global_users[request.sid] = username
        
        emit('global_message', {
            'username': 'System',
            'message': f'👋 {username} bergabung ke chat',
            'type': 'system'
        }, broadcast=True)
        
        emit('user_count', len(global_users), broadcast=True)
    except Exception as e:
        print(f'Error in join_global: {str(e)}')
        emit('error', {'message': 'Failed to join chat'})

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

@socketio.on('ping')
def handle_ping():
    try:
        emit('pong')
    except Exception as e:
        logger.error(f'Error handling ping: {str(e)}')

if __name__ == '__main__':
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000,
        allow_unsafe_werkzeug=True
    )