from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import uuid
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_aplikasi'  # Ganti dengan kunci rahasia yang aman
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

# Setup Database
DATABASE_URL = "postgresql://postgres.isadrgmnkdggmoqinxiq:arisdevdatabase@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Model Database
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    device_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    content = Column(Text)
    message_type = Column(String(20))  # 'text' atau 'image'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(engine)

@app.route('/')
def index():
    return render_template('global.html')

@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    device_id = data.get('device_id')
    
    db = SessionLocal()
    try:
        # Cek apakah device_id sudah terdaftar
        existing_device = db.query(User).filter_by(device_id=device_id).first()
        if existing_device:
            if existing_device.username != username:
                return jsonify({
                    'status': 'error',
                    'message': f'Perangkat ini sudah terdaftar dengan username {existing_device.username}'
                }), 400
            return jsonify({
                'status': 'success',
                'username': existing_device.username
            })

        # Cek apakah username sudah digunakan
        if db.query(User).filter_by(username=username).first():
            return jsonify({
                'status': 'error',
                'message': 'Username sudah digunakan'
            }), 400

        # Daftarkan user baru
        new_user = User(username=username, device_id=device_id)
        db.add(new_user)
        db.commit()
        
        return jsonify({
            'status': 'success',
            'username': username
        })
    finally:
        db.close()

@socketio.on('send_message')
def handle_message(data):
    username = data.get('username')
    message = data.get('message')
    message_type = data.get('type', 'text')
    
    db = SessionLocal()
    try:
        new_message = Message(
            username=username,
            content=message,
            message_type=message_type
        )
        db.add(new_message)
        db.commit()
        
        emit('new_message', {
            'username': username,
            'message': message,
            'type': message_type,
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
        }, broadcast=True)
    finally:
        db.close()

@app.route('/get_messages', methods=['GET'])
def get_messages():
    db = SessionLocal()
    try:
        messages = db.query(Message).order_by(Message.created_at.desc()).limit(50).all()
        return jsonify([{
            'username': msg.username,
            'message': msg.content,
            'type': msg.message_type,
            'timestamp': msg.created_at.strftime('%H:%M:%S')
        } for msg in messages[::-1]])
    finally:
        db.close()

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
