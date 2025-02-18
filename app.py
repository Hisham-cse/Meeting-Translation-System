import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging
from datetime import datetime
from googletrans import Translator

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

def get_translation(text, from_code, to_code):
    """
    Translate text using Google Translate
    """
    try:
        translator = Translator()
        # Translate the text
        result = translator.translate(text, src=from_code, dest=to_code)
        logger.info(f"Translation successful: {text} -> {result.text}")
        return result.text
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