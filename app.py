import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Database configuration with logging
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

from models import Translation

# Simple translation dictionaries for demo purposes
TRANSLATIONS = {
    'en': {
        'hi': {
            'hello': 'नमस्ते',
            'good morning': 'शुभ प्रभात',
            'thank you': 'धन्यवाद',
            'how are you': 'आप कैसे हैं',
            'welcome': 'स्वागत है',
            'meeting': 'बैठक',
            'started': 'शुरू हो गया',
            'finished': 'समाप्त',
            'please': 'कृपया',
            'yes': 'हाँ',
            'no': 'नहीं'
        },
        'kn': {
            'hello': 'ನಮಸ್ಕಾರ',
            'good morning': 'ಶುಭೋದಯ',
            'thank you': 'ಧನ್ಯವಾದಗಳು',
            'how are you': 'ಹೇಗಿದ್ದೀರಾ',
            'welcome': 'ಸ್ವಾಗತ',
            'meeting': 'ಸಭೆ',
            'started': 'ಪ್ರಾರಂಭವಾಗಿದೆ',
            'finished': 'ಮುಗಿದಿದೆ',
            'please': 'ದಯವಿಟ್ಟು',
            'yes': 'ಹೌದು',
            'no': 'ಇಲ್ಲ'
        }
    },
    'hi': {
        'en': {
            'नमस्ते': 'hello',
            'शुभ प्रभात': 'good morning',
            'धन्यवाद': 'thank you',
            'आप कैसे हैं': 'how are you',
            'स्वागत है': 'welcome',
            'बैठक': 'meeting',
            'शुरू हो गया': 'started',
            'समाप्त': 'finished',
            'कृपया': 'please',
            'हाँ': 'yes',
            'नहीं': 'no'
        },
        'kn': {
            'नमस्ते': 'ನಮಸ್ಕಾರ',
            'शुभ प्रभात': 'ಶುಭೋದಯ',
            'धन्यवाद': 'ಧನ್ಯವಾದಗಳು',
            'आप कैसे हैं': 'ಹೇಗಿದ್ದೀರಾ',
            'स्वागत है': 'ಸ್ವಾಗತ',
            'बैठक': 'ಸಭೆ',
            'शुरू हो गया': 'ಪ್ರಾರಂಭವಾಗಿದೆ',
            'समाप्त': 'ಮುಗಿದಿದೆ',
            'कृपया': 'ದಯವಿಟ್ಟು',
            'हाँ': 'ಹೌದು',
            'नहीं': 'ಇಲ್ಲ'
        }
    },
    'kn': {
        'en': {
            'ನಮಸ್ಕಾರ': 'hello',
            'ಶುಭೋದಯ': 'good morning',
            'ಧನ್ಯವಾದಗಳು': 'thank you',
            'ಹೇಗಿದ್ದೀರಾ': 'how are you',
            'ಸ್ವಾಗತ': 'welcome',
            'ಸಭೆ': 'meeting',
            'ಪ್ರಾರಂಭವಾಗಿದೆ': 'started',
            'ಮುಗಿದಿದೆ': 'finished',
            'ದಯವಿಟ್ಟು': 'please',
            'ಹೌದು': 'yes',
            'ಇಲ್ಲ': 'no'
        },
        'hi': {
            'ನಮಸ್ಕಾರ': 'नमस्ते',
            'ಶುಭೋದಯ': 'शुभ प्रभात',
            'ಧನ್ಯವಾದಗಳು': 'धन्यवाद',
            'ಹೇಗಿದ್ದೀರಾ': 'आप कैसे हैं',
            'ಸ್ವಾಗತ': 'स्वागत है',
            'ಸಭೆ': 'बैठक',
            'ಪ್ರಾರಂಭವಾಗಿದೆ': 'शुरू हो गया',
            'ಮುಗಿದಿದೆ': 'समाप्त',
            'ದಯವಿಟ್ಟು': 'कृपया',
            'ಹೌದು': 'हाँ',
            'ಇಲ್ಲ': 'नहीं'
        }
    }
}

def get_translation(text, from_code, to_code):
    """
    Simple dictionary-based translation for demo purposes
    """
    try:
        # Convert text to lowercase for matching
        text_lower = text.lower()

        # Check if we have a translation
        if from_code in TRANSLATIONS and to_code in TRANSLATIONS[from_code]:
            # Try to find the translation
            translation = TRANSLATIONS[from_code][to_code].get(text_lower, text)
            return translation
        else:
            logger.warning(f"Translation not available for {from_code} to {to_code}")
            return text

    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return text

@app.route('/')
def index():
    return render_template('index.html')

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