from app import db
from datetime import datetime

class Translation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_text = db.Column(db.Text, nullable=False)
    translated_text = db.Column(db.Text, nullable=False)
    source_language = db.Column(db.String(5), nullable=False)
    target_language = db.Column(db.String(5), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    room_id = db.Column(db.String(10), nullable=False)
    preferred_language = db.Column(db.String(5), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)