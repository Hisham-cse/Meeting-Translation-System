from app import db
from datetime import datetime

class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_text = db.Column(db.Text, nullable=False)
    translated_text = db.Column(db.Text, nullable=False)
    source_language = db.Column(db.String(5), nullable=False)
    target_language = db.Column(db.String(5), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
