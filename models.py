from datetime import datetime

# MongoDB schema reference (not actual code, just for documentation)
translation_schema = {
    "original_text": str,
    "translated_text": str,
    "source_language": str,
    "target_language": str,
    "timestamp": datetime,
    "room_id": str
}

room_schema = {
    "room_id": str,
    "created_at": datetime,
    "active": bool
}

participant_schema = {
    "name": str,
    "room_id": str,
    "preferred_language": str,
    "joined_at": datetime
}