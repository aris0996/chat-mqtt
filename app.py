from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import uuid
from flask_cors import CORS
import logging
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db, AudioMessage
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

UPLOAD_FOLDER = 'temp_audio'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Fungsi untuk menghapus pesan audio yang kedaluwarsa
def delete_expired_messages():
    db = next(get_db())
    try:
        now = datetime.utcnow()
        expired_messages = db.query(AudioMessage).filter(AudioMessage.expiration_time <= now).all()
        for message in expired_messages:
            db.delete(message)
        db.commit()
    finally:
        db.close()

# Inisialisasi scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(delete_expired_messages, 'interval', minutes=1)
scheduler.start()

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
    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400

    if audio_file:
        filename = secure_filename(audio_file.filename)
        audio_data = audio_file.read()

        db = next(get_db())
        try:
            new_audio = AudioMessage(filename=filename, data=audio_data)
            db.add(new_audio)
            db.commit()
            db.refresh(new_audio)

            return jsonify({
                'success': True,
                'url': f'/get_audio/{new_audio.id}',
                'message': 'Audio uploaded successfully'
            }), 200
        finally:
            db.close()

    return jsonify({'success': False, 'error': 'Failed to upload audio'}), 500

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

@app.route('/get_audio/<int:audio_id>', methods=['GET'])
def get_audio(audio_id):
    db = next(get_db())
    try:
        audio = db.query(AudioMessage).filter(AudioMessage.id == audio_id).first()
        if audio:
            return audio.data, 200, {'Content-Type': 'audio/wav'}
        else:
            return jsonify({'success': False, 'error': 'Audio not found'}), 404
    finally:
        db.close()

if __name__ == '__main__':
    socketio.run(app)
