from flask import Blueprint, request, jsonify
from app.services.recommendations_service import get_recommendations

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/recommend', methods=['POST'])
def recommend():
    user_query = request.json.get('query')
    recommendations = get_recommendations(user_query)
    return jsonify(recommendations)
