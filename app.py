from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
import logging
import pusher
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app, resources={r"/*": {"origins": "chat.arisdev.my.id"}})

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Konfigurasi Pusher
pusher_client = pusher.Pusher(
    app_id = "1889242",
    key = "45e0fb5846ec69139f37",   
    secret = "47b3e72aba0b27741aab",
    cluster = "ap1",
    ssl=True
)

# Simpan data user global
global_users = {}
online_users = set()

@app.route('/')
def index():
    return render_template('coba.html')

@app.route('/global')
def global_chat():
    return render_template('global.html')

@app.route('/join', methods=['POST'])
def join_chat():
    try:
        data = request.json
        username = data.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        user_id = str(time.time())
        global_users[user_id] = username
        online_users.add(username)

        # Broadcast join message
        pusher_client.trigger('chat-channel', 'join-event', {
            'username': username,
            'message': f'👋 {username} bergabung ke chat',
            'type': 'system',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

        # Update user count
        pusher_client.trigger('chat-channel', 'user-count', {
            'count': len(online_users)
        })

        return jsonify({
            'status': 'success',
            'user_id': user_id,
            'username': username
        })
    except Exception as e:
        logger.error(f'Error in join_chat: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/leave', methods=['POST'])
def leave_chat():
    try:
        data = request.json
        user_id = data.get('user_id')
        if user_id not in global_users:
            return jsonify({'error': 'User not found'}), 404

        username = global_users[user_id]
        del global_users[user_id]
        online_users.remove(username)

        # Broadcast leave message
        pusher_client.trigger('chat-channel', 'leave-event', {
            'username': username,
            'message': f'👋 {username} meninggalkan chat',
            'type': 'system',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })

        # Update user count
        pusher_client.trigger('chat-channel', 'user-count', {
            'count': len(online_users)
        })

        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f'Error in leave_chat: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/message', methods=['POST'])
def send_message():
    try:
        data = request.json
        user_id = data.get('user_id')
        message = data.get('message')
        reply_to = data.get('replyTo')
        reply_to_text = data.get('replyToText')

        if not message:
            return jsonify({'error': 'Message is required'}), 400
        if user_id not in global_users:
            return jsonify({'error': 'User not found'}), 404

        username = global_users[user_id]
        message_data = {
            'username': username,
            'message': message,
            'type': 'text',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }

        if reply_to:
            message_data['replyTo'] = reply_to
            message_data['replyToText'] = reply_to_text

        # Broadcast message
        pusher_client.trigger('chat-channel', 'message-event', message_data)

        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f'Error in send_message: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )