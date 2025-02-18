import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///translations.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

from models import Translation

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    text = data.get('text', '')
    source_lang = data.get('sourceLang', 'en')
    target_lang = data.get('targetLang', 'es')
    
    # Store translation in database
    translation = Translation(
        original_text=text,
        translated_text=text,  # In a real implementation, this would be the translated text
        source_language=source_lang,
        target_language=target_lang,
        timestamp=datetime.now()
    )
    db.session.add(translation)
    db.session.commit()
    
    # For demo purposes, we're just returning the same text
    # In production, you would integrate with libre-translate here
    return jsonify({
        'translation': text,
        'source_lang': source_lang,
        'target_lang': target_lang
    })

with app.app_context():
    db.create_all()
