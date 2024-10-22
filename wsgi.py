from app import app, socketio

app = socketio.asgi_app(app)
