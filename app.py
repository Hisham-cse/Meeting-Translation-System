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

# Initialize translator globally
translator = Translator()

# Language code mapping to ensure consistency
LANGUAGE_CODES = {
    'kannada': 'kn',
    'hindi': 'hi', 
    'english': 'en',
    'kn': 'kn',
    'hi': 'hi',
    'en': 'en'
}

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
        if 'translations' not in mongo.db.list_collection_names():
            mongo.db.create_collection('translations')
            logger.info("Created translations collection")

except Exception as e:
    logger.error(f"Database Connection Error: {str(e)}")
    raise

def normalize_language_code(lang_code):
    """Normalize language code to standard format"""
    if not lang_code:
        return 'en'  # Default to English
    
    lang_code = lang_code.lower().strip()
    return LANGUAGE_CODES.get(lang_code, lang_code)

def generate_room_id():
    """Generate a random 6-character room ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_translation(text, from_code, to_code):
    """Translate text using Google Translate with improved error handling"""
    if not text or not text.strip():
        return text
    
    # Normalize language codes
    from_code = normalize_language_code(from_code)
    to_code = normalize_language_code(to_code)
    
    # If source and target are the same, return original text
    if from_code == to_code:
        return text
    
    try:
        # Create a new translator instance for each request to avoid conflicts
        local_translator = Translator()
        
        # Detect language if from_code is 'auto' or not specified
        if from_code == 'auto' or not from_code:
            detection = local_translator.detect(text)
            from_code = detection.lang
            logger.info(f"Detected language: {from_code}")
        
        # Perform translation
        result = local_translator.translate(text, src=from_code, dest=to_code)
        logger.info(f"Translation successful: {text[:50]}... [{from_code} -> {to_code}] -> {result.text[:50]}...")
        return result.text
    except Exception as e:
        logger.error(f"Translation error: {str(e)} | Text: {text[:50]}... | {from_code} -> {to_code}")
        # Return original text if translation fails
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
    language = normalize_language_code(data['language'])

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
    from_language = normalize_language_code(data['from_language'])
    
    if not text or not text.strip():
        return

    participants = list(mongo.db.participants.find({'room_id': room_id}))
    
    # Send original speech to all participants first
    emit('speech_received', {
        'original_text': text,
        'from_language': from_language,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_id)
    
    # Then send translations for participants with different languages
    for participant in participants:
        participant_lang = normalize_language_code(participant['preferred_language'])
        if participant_lang != from_language:
            translated_text = get_translation(text, from_language, participant_lang)
            emit('translated_speech', {
                'original_text': text,
                'translated_text': translated_text,
                'from_language': from_language,
                'to_language': participant_lang,
                'participant_name': participant['name'],
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id)

@socketio.on('reaction')
def handle_reaction(data):
    room_id = data['room_id']
    name = data['name']
    emoji = data['emoji']
    emit('reaction_received', {
        'name': name,
        'emoji': emoji,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room_id)

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        text = data.get('text', '').strip()
        source_lang = normalize_language_code(data.get('sourceLang'))
        target_lang = normalize_language_code(data.get('targetLang'))
        room_id = data.get('roomId')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Perform translation
        translated_text = get_translation(text, source_lang, target_lang)
        
        # Store translation in database
        translation_record = {
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_lang,
            'target_language': target_lang,
            'timestamp': datetime.utcnow(),
            'room_id': room_id
        }
        mongo.db.translations.insert_one(translation_record)
        
        return jsonify({
            'translation': translated_text,
            'source_language': source_lang,
            'target_language': target_lang,
            'original_text': text
        })
        
    except Exception as e:
        logger.error(f"Translation API error: {str(e)}")
        return jsonify({'error': 'Translation failed'}), 500

@app.route('/languages', methods=['GET'])
def get_supported_languages():
    """Return supported languages for the frontend"""
    supported_languages = {
        'en': 'English',
        'hi': 'Hindi', 
        'kn': 'Kannada'
    }
    return jsonify(supported_languages)

@app.route('/room/<room_id>/translations', methods=['GET'])
def get_room_translations(room_id):
    """Get translation history for a room"""
    try:
        translations = list(mongo.db.translations.find(
            {'room_id': room_id},
            {'_id': 0}
        ).sort('timestamp', -1).limit(50))
        return jsonify(translations)
    except Exception as e:
        logger.error(f"Error fetching translations: {str(e)}")
        return jsonify({'error': 'Failed to fetch translations'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)