from flask import request, Blueprint, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from ..services.speech_to_text_service import SpeechToTextService
from ..services.chatbot_service import ChatbotService
chatbot_bp = Blueprint('chatbot', __name__)
chatbot_service = ChatbotService()
speech_to_text_service = SpeechToTextService()
@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """API endpoint to process chat messages with optional TTS"""
    try:
        data = request.get_json()
        user_message = data.get('message')
        use_tts = data.get('tts', False)
        language = data.get('language', 'vi')  # Default to Vietnamese

        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'Message cannot be empty'
            }), 400

        # Get response from chatbot
        response = chatbot_service.get_response(user_message, use_tts)

        return jsonify({
            'status': 'success',
            'message': response["text"],
            'audio_url': response["audio_url"],
        })

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Đã có lỗi xảy ra: {str(e)}'
        }), 500


@chatbot_bp.route('/speak', methods=['GET'])
def speak():
    """Serve the generated speech file from static/audio/"""
    audio_folder = os.path.join(os.getcwd(), "static/audio")  # Absolute path
    filename = "response.mp3"

    # Ensure the file exists before serving
    if not os.path.exists(os.path.join(audio_folder, filename)):
        return jsonify({'status': 'error', 'message': 'Audio file not found'}), 404

    return send_from_directory(audio_folder, filename, mimetype="audio/mpeg")

@chatbot_bp.route('/train', methods=['POST'])
def train():
    """API endpoint to train new data"""
    try:
        data = request.get_json()
        documents = data.get('documents', [])
        
        if not documents:
            return jsonify({
                'status': 'error',
                'message': 'No data to train'
            }), 400
            
        success = chatbot_service.train_knowledge(documents)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Training successful'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'An error occurred during training'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
@chatbot_bp.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """API endpoint to convert speech to text"""
    try:
        if 'audio' not in request.files:
            return jsonify({'status': 'error', 'message': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        filename = secure_filename(audio_file.filename)
        audio_folder = os.path.join(os.getcwd(), "static/audio")  # Absolute path to the audio folder
        os.makedirs(audio_folder, exist_ok=True)  # Ensure the folder exists
        audio_path = os.path.join(audio_folder, filename)
        audio_file.save(audio_path)

        transcript = speech_to_text_service.transcribe_audio(audio_path)
        return jsonify({'status': 'success', 'transcript': transcript})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500