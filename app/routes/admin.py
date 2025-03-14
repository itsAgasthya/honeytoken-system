from flask import Blueprint, request, jsonify
from app.models.honeytoken import Honeytoken, TokenType, AlertConfig
from app import db

bp = Blueprint('admin', __name__)

@bp.route('/tokens', methods=['GET'])
def list_tokens():
    """List all honeytokens."""
    tokens = Honeytoken.query.all()
    return jsonify([{
        'id': token.id,
        'type': token.token_type.value,
        'description': token.description,
        'is_active': bool(token.is_active),
        'created_at': token.created_at.isoformat()
    } for token in tokens])

@bp.route('/tokens', methods=['POST'])
def create_token():
    """Create a new honeytoken."""
    data = request.get_json()
    
    try:
        token = Honeytoken(
            token_type=TokenType(data['type']),
            token_value=data['value'],
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )
        
        # Create associated alert config
        alert_config = AlertConfig(
            token_id=token.id,
            alert_threshold=data.get('alert_threshold', 1),
            alert_channels=data.get('alert_channels', ['email']),
            alert_message_template=data.get('alert_message', 'Honeytoken {token_id} accessed by {user_id}')
        )
        
        db.session.add(token)
        db.session.add(alert_config)
        db.session.commit()
        
        return jsonify({
            'id': token.id,
            'message': 'Honeytoken created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/tokens/<int:token_id>', methods=['DELETE'])
def delete_token(token_id):
    """Delete a honeytoken."""
    token = Honeytoken.query.get_or_404(token_id)
    
    try:
        db.session.delete(token)
        db.session.commit()
        return jsonify({'message': 'Honeytoken deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/tokens/<int:token_id>/toggle', methods=['POST'])
def toggle_token(token_id):
    """Toggle a honeytoken's active status."""
    token = Honeytoken.query.get_or_404(token_id)
    
    try:
        token.is_active = not token.is_active
        db.session.commit()
        return jsonify({
            'id': token.id,
            'is_active': bool(token.is_active)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 