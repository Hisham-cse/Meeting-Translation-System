import os
from flask import Flask, render_template, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging
from datetime import datetime
from googletrans import Translator
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
socketio = SocketIO(app, cors_allowed_origins="*")

# Database configuration
database_url = os.environ.get("DATABASE_URL")
logger.info(f"Configuring database with URL type: {type(database_url)}")
if database_url is None:
    raise RuntimeError("DATABASE_URL environment variable is not set")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

from models import Translation, Room, Participant

def generate_room_id():
    """Generate a random 6-character room ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_translation(text, from_code, to_code):
    """
    Translate text using Google Translate
    """
    try:
        translator = Translator()
        result = translator.translate(text, src=from_code, dest=to_code)
        logger.info(f"Translation successful: {text} -> {result.text}")
        return result.text
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create-room', methods=['POST'])
def create_room():
    room_id = generate_room_id()
    room = Room(room_id=room_id)
    db.session.add(room)
    db.session.commit()
    return jsonify({'room_id': room_id})

@app.route('/join-room/<room_id>')
def join_room_page(room_id):
    room = Room.query.filter_by(room_id=room_id, active=True).first()
    if not room:
        return "Room not found", 404
    return render_template('room.html', room_id=room_id)

@socketio.on('join')
def on_join(data):
    room_id = data['room_id']
    name = data['name']
    language = data['language']

    participant = Participant(
        name=name,
        room_id=room_id,
        preferred_language=language
    )
    db.session.add(participant)
    db.session.commit()

    join_room(room_id)
    participants = Participant.query.filter_by(room_id=room_id).all()
    participant_list = [{'name': p.name, 'language': p.preferred_language} for p in participants]

    emit('user_joined', {
        'name': name,
        'language': language,
        'participants': participant_list
    }, room=room_id)

@socketio.on('leave')
def on_leave(data):
    room_id = data['room_id']
    name = data['name']

    Participant.query.filter_by(name=name, room_id=room_id).delete()
    db.session.commit()

    leave_room(room_id)
    emit('user_left', {'name': name}, room=room_id)

@socketio.on('speech')
def handle_speech(data):
    room_id = data['room_id']
    text = data['text']
    from_language = data['from_language']

    # Get all participants in the room
    participants = Participant.query.filter_by(room_id=room_id).all()

    # Translate and broadcast to each participant in their preferred language
    for participant in participants:
        if participant.preferred_language != from_language:
            translated_text = get_translation(text, from_language, participant.preferred_language)
            emit('translated_speech', {
                'original_text': text,
                'translated_text': translated_text,
                'from_language': from_language,
                'to_language': participant.preferred_language
            }, room=room_id)

@socketio.on('reaction')
def handle_reaction(data):
    room_id = data['room_id']
    name = data['name']
    emoji = data['emoji']

    emit('reaction_received', {
        'name': name,
        'emoji': emoji
    }, room=room_id)

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text', '')
    source_lang = data.get('sourceLang', 'en')
    target_lang = data.get('targetLang', 'kn')

    # Perform translation
    translated_text = get_translation(text, source_lang, target_lang)

    # Store translation in database
    translation = Translation(
        original_text=text,
        translated_text=translated_text,
        source_language=source_lang,
        target_language=target_lang,
        timestamp=datetime.utcnow()
    )
    db.session.add(translation)
    db.session.commit()

    return jsonify({
        'translation': translated_text,
        'source_lang': source_lang,
        'target_lang': target_lang
    })

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)