# Real-Time Meeting Translation System

A Flask-based web application that enables real-time multilingual communication in virtual meetings by providing instant speech translation across different languages.

## Features

- **Real-time Translation**: Instantly translates speech between multiple languages
- **Virtual Meeting Rooms**: Create and join private meeting rooms
- **User Management**: Track participants and their preferred languages
- **Speech Recognition**: Convert spoken words to text
- **Emoji Reactions**: Express reactions during meetings
- **Cross-browser Support**: Works on all modern web browsers

## Technology Stack

- **Backend**: Python/Flask
- **Database**: MongoDB Atlas
- **Real-time Communication**: Flask-SocketIO
- **Translation Service**: Google Translate API
- **Frontend**: HTML, CSS, JavaScript
- **WebSocket**: For real-time updates

## Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account
- Internet connection for translation services

## Installation

# 1. Clone the repository:
```bash
git clone https://github.com/Hisham-cse/Meeting-Translation-System.git

cd Meeting-Translation-System
```

# 2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```
# 3. Install dependencies:
```bash
pip install -r requirements.txt
```
# 4. Set up environment variables in `.env`:
```bash
SESSION_SECRET=your_secret_key
MONGO_URI=your_mongodb_connection_string
```
#5. Run the application:
```bash
python main.py
```

## The application will be available at `http://localhost:5000`

## Usage

1. **Create a Meeting**:
   - Click "Create Room" on the homepage
   - Share the generated room ID with participants

2. **Join a Meeting**:
   - Enter the room ID
   - Select your preferred language
   - Enter your name
   - Click "Join"

3. **During the Meeting**:
   - Speak in your preferred language
   - View real-time translations
   - Use emoji reactions
   - See participant list

## Project Structure
```
Meeting-Translation-System/
├── app.py # Main application file
├── models.py # Database schemas
├── templates/ # HTML templates
│ ├── index.html # Homepage
│ └── room.html # Meeting room page
├── static/ # Static files (CSS, JS)
├── requirements.txt # Project dependencies
└── .env # Environment variables
```

## Features in Detail

- **Speech Recognition**: Converts spoken words to text in real-time
- **Language Translation**: Supports multiple languages using Google Translate
- **Real-time Updates**: Instant message delivery using WebSocket
- **Participant Management**: Tracks users and their language preferences
- **Room Management**: Creates and maintains virtual meeting rooms
- **Error Handling**: Robust error management for various scenarios
- **Logging**: Comprehensive logging for debugging

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask-SocketIO for real-time communication
- Google Translate API for translation services
- MongoDB Atlas for database services

## Contact

Muhammad Hisham - muhammadhisham305@gmail.com

Project Link: [https://github.com/Hisham-cse/Meeting-Translation-System](https://github.com/Hisham-cse/Meeting-Translation-System)
