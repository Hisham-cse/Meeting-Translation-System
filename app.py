import os
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request, session
import logging
from datetime import datetime
from googletrans import Translator
from flask_socketio import SocketIO, emit, join_room, leave_room
import random
import string
from flask_pymongo import PyMongo

# Load environment variables from .ENV file
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
socketio = SocketIO(app, cors_allowed_origins="*")

try:
    # Configure MongoDB
    mongo_uri = os.environ.get('MONGO_URI')
    if not mongo_uri:
        raise RuntimeError("MONGO_URI environment variable is not set")

    app.config['MONGO_URI'] = mongo_uri
    app.config['MONGO_TLS'] = True
    app.config['MONGO_TLS_ALLOW_INVALID_CERTIFICATES'] = True
    app.config['MONGO_AUTH_SOURCE'] = 'admin'
    app.config['MONGO_CONNECT'] = True
    
    mongo = PyMongo(app)
    
    # Test MongoDB connection
    with app.app_context():
        mongo.db.command('ping')
        logger.info("MongoDB connection successful")
        
        # Create MongoDB collections if they don't exist
        if 'participants' not in mongo.db.list_collection_names():
            mongo.db.create_collection('participants')
            logger.info("Created participants collection")
        if 'rooms' not in mongo.db.list_collection_names():
            mongo.db.create_collection('rooms')
            logger.info("Created rooms collection")

except Exception as e:
    logger.error(f"Database Connection Error: {str(e)}")
    raise

def generate_room_id():
    """Generate a random 6-character room ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_translation(text, from_code, to_code):
    """Translate text using Google Translate"""
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
    try:
        room_id = generate_room_id()
        
        # Store in MongoDB
        mongo.db.rooms.insert_one({
            'room_id': room_id,
            'created_at': datetime.utcnow(),
            'active': True
        })
        
        return jsonify({'room_id': room_id})
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        return jsonify({'error': 'Failed to create room'}), 500

@app.route('/join-room/<room_id>')
def join_room_page(room_id):
    room = mongo.db.rooms.find_one({'room_id': room_id, 'active': True})
    if not room:
        return "Room not found", 404
    return render_template('room.html', room_id=room_id)

@socketio.on('join')
def on_join(data):
    room_id = data['room_id']
    name = data['name']
    language = data['language']

    participant = {
        'name': name,
        'room_id': room_id,
        'preferred_language': language,
        'joined_at': datetime.utcnow()
    }
    
    # Insert into MongoDB
    mongo.db.participants.insert_one(participant)

    join_room(room_id)
    participants = list(mongo.db.participants.find({'room_id': room_id}, {'_id': 0}))
    participant_list = [{'name': p['name'], 'language': p['preferred_language']} for p in participants]

    emit('user_joined', {
        'name': name,
        'language': language,
        'participants': participant_list
    }, room=room_id)

@socketio.on('leave')
def on_leave(data):
    room_id = data['room_id']
    name = data['name']
    mongo.db.participants.delete_one({'name': name, 'room_id': room_id})
    leave_room(room_id)
    emit('user_left', {'name': name}, room=room_id)

@socketio.on('speech')
def handle_speech(data):
    room_id = data['room_id']
    text = data['text']
    from_language = data['from_language']

    participants = list(mongo.db.participants.find({'room_id': room_id}))
    for participant in participants:
        if participant['preferred_language'] != from_language:
            translated_text = get_translation(text, from_language, participant['preferred_language'])
            emit('translated_speech', {
                'original_text': text,
                'translated_text': translated_text,
                'from_language': from_language,
                'to_language': participant['preferred_language']
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
    data = request.json
    text = data.get('text')
    source_lang = data.get('sourceLang')
    target_lang = data.get('targetLang')
    room_id = data.get('roomId')

    translated = translator.translate(text, src=source_lang, dest=target_lang)

    translation = {
        'original_text': text,
        'translated_text': translated.text,
        'source_language': source_lang,
        'target_language': target_lang,
        'timestamp': datetime.utcnow(),
        'room_id': room_id
    }
    mongo.db.translations.insert_one(translation)

    return jsonify({'translation': translated.text})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)