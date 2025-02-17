from flask import Blueprint, request, jsonify
from ..services.chatbot_service import ChatbotService

chatbot_bp = Blueprint('chatbot', __name__)
chatbot_service = ChatbotService()

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    """API endpoint to process chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message')
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'Message is not empty'
            }), 400
            
        response = chatbot_service.get_response(user_message)
        
        return jsonify({
            'status': 'success',
            'message': response
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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
