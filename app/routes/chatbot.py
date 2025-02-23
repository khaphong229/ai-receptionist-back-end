from flask import Blueprint, request, jsonify, send_from_directory
import os
from ..services.chatbot_service import ChatbotService
from flask import send_file

chatbot_bp = Blueprint('chatbot', __name__)
chatbot_service = ChatbotService()


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """API endpoint to process chat messages with optional TTS"""
    try:
        data = request.get_json()
        user_message = data.get('message')
        use_tts = data.get('tts', False)  # Check if TTS is requested

        if not user_message:
            return jsonify({'status': 'error', 'message': 'Message cannot be empty'}), 400
        response = chatbot_service.get_response(user_message, use_tts)
        return jsonify({
            'status': 'success',
            'message': response["text"],
            'audio_url': response["audio_url"], # If TTS is enabled, returns "/speak"
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500




@chatbot_bp.route('/speak', methods=['GET'])
def speak():
    try:
        # Lấy đường dẫn tuyệt đối đến thư mục gốc của project
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        audio_path = os.path.join(base_dir, 'static', 'audio', 'response.mp3')
        
        print(f"Base directory: {base_dir}")
        print(f"Looking for audio file at: {audio_path}")
        
        if not os.path.exists(audio_path):
            print(f"Audio file not found at {audio_path}")
            return 'Audio file not found', 404
            
        file_size = os.path.getsize(audio_path)
        print(f"Audio file size: {file_size} bytes")
        
        if file_size == 0:
            print("Audio file is empty")
            return 'Audio file is empty', 404

        try:
            return send_file(
                audio_path,
                mimetype='audio/mpeg',
                as_attachment=False,
                download_name='response.mp3'
            )
        except Exception as send_error:
            print(f"Error sending file: {send_error}")
            print(f"Current working directory: {os.getcwd()}")
            raise send_error
            
    except Exception as e:
        print(f"Error in /speak route: {str(e)}")
        return str(e), 500

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
