from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import uuid
from flask_cors import CORS
import logging
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy.orm import Session
from database import get_db, AudioMessage
from apscheduler.schedulers.background import BackgroundScheduler
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

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

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    return jsonify({'success': False, 'error': 'Audio upload function removed'}), 400

@app.route('/get_audio/<int:audio_id>', methods=['GET'])
def get_audio(audio_id):
    return jsonify({'success': False, 'error': 'Audio retrieval function removed'}), 400

if __name__ == '__main__':
    socketio.run(app)
