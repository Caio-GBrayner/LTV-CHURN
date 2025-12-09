"""
Flask API para predições de Churn e LTV.
Serviço REST que expõe os modelos treinados.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from src.model_loader import ModelLoader
from src.prediction_engine import PredictionEngine

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS

# Variáveis globais
model_loader = None
prediction_engine = None

# Configurações
MODEL_VERSION = os.getenv('MODEL_VERSION', 'v1.0.0')
MODELS_PATH = os.getenv('MODELS_PATH', './models')

@app.before_first_request
def initialize():
    """Inicializa modelos na primeira requisição"""
    global model_loader, prediction_engine
    
    logger.info("[START] Initializing Prediction Service...")
    logger.info(f"   Model Version: {MODEL_VERSION}")
    logger.info(f"   Models Path: {MODELS_PATH}")
    
    try:
        # Carregar modelos
        model_loader = ModelLoader(
            models_dir=MODELS_PATH,
            model_version=MODEL_VERSION
        )
        success = model_loader.load_all_models()
        
        if not success:
            raise Exception("Failed to load models")
        
        # Criar prediction engine
        prediction_engine = PredictionEngine(model_loader)
        
        logger.info("[OK] Prediction Service initialized successfully")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize: {e}")
        raise


# ============================================================================
# ENDPOINTS DE SAÚDE E INFORMAÇÃO
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    Retorna status do serviço.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Prediction Service',
        'version': MODEL_VERSION,
        'models_loaded': model_loader is not None and prediction_engine is not None
    }), 200


@app.route('/models/info', methods=['GET'])
def models_info():
    """
    Retorna informações sobre os modelos carregados.
    """
    if model_loader is None:
        return jsonify({'error': 'Models not loaded'}), 503
    
    info = model_loader.get_model_info()
    return jsonify(info), 200


# ============================================================================
# ENDPOINTS DE PREDIÇÃO
# ============================================================================

@app.route('/predict/churn', methods=['POST'])
def predict_churn():
    """
    Prediz probabilidade de churn para um usuário.
    
    Request Body:
    {
        "user_id": 123,
        "running_sessions_count": 50,
        "runs_last_30_days": 10,
        ...
    }
    
    Response:
    {
        "success": true,
        "prediction": {
            "probability": 0.7823,
            "risk_level": "HIGH",
            "confidence_score": 0.92,
            ...
        }
    }
    """
    try:
        if prediction_engine is None:
            return jsonify({'error': 'Service not initialized'}), 503
        
        # Validar request
        if not request.json:
            return jsonify({'error': 'No data provided'}), 400
        
        features = request.json
        
        # Validar user_id
        if 'user_id' not in features:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Predizer
        result = prediction_engine.predict_churn(features)
        
        return jsonify({
            'success': True,
            'user_id': features['user_id'],
            'prediction': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in /predict/churn: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/predict/ltv', methods=['POST'])
def predict_ltv():
    """
    Prediz LTV (Lifetime Value) para um usuário.
    
    Request Body:
    {
        "user_id": 123,
        "running_sessions_count": 50,
        ...
    }
    
    Response:
    {
        "success": true,
        "prediction": {
            "ltv_value": 450.00,
            "ltv_category": "HIGH",
            ...
        }
    }
    """
    try:
        if prediction_engine is None:
            return jsonify({'error': 'Service not initialized'}), 503
        
        # Validar request
        if not request.json:
            return jsonify({'error': 'No data provided'}), 400
        
        features = request.json
        
        # Validar user_id
        if 'user_id' not in features:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Predizer
        result = prediction_engine.predict_ltv(features)
        
        return jsonify({
            'success': True,
            'user_id': features['user_id'],
            'prediction': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in /predict/ltv: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/predict/all', methods=['POST'])
def predict_all():
    """
    Prediz Churn e LTV para um usuário.
    
    Request Body:
    {
        "user_id": 123,
        "running_sessions_count": 50,
        ...
    }
    
    Response:
    {
        "success": true,
        "churn": {...},
        "ltv": {...}
    }
    """
    try:
        if prediction_engine is None:
            return jsonify({'error': 'Service not initialized'}), 503
        
        # Validar request
        if not request.json:
            return jsonify({'error': 'No data provided'}), 400
        
        features = request.json
        
        # Validar user_id
        if 'user_id' not in features:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Predizer ambos
        churn_result = prediction_engine.predict_churn(features)
        ltv_result = prediction_engine.predict_ltv(features)
        
        return jsonify({
            'success': True,
            'user_id': features['user_id'],
            'churn': churn_result,
            'ltv': ltv_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in /predict/all: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    """
    Prediz Churn e LTV para múltiplos usuários.
    
    Request Body:
    {
        "users": [
            {"user_id": 1, "running_sessions_count": 50, ...},
            {"user_id": 2, "running_sessions_count": 10, ...}
        ]
    }
    
    Response:
    {
        "success": true,
        "count": 2,
        "predictions": [...]
    }
    """
    try:
        if prediction_engine is None:
            return jsonify({'error': 'Service not initialized'}), 503
        
        # Validar request
        if not request.json or 'users' not in request.json:
            return jsonify({'error': 'No users data provided'}), 400
        
        users_features = request.json['users']
        
        if not isinstance(users_features, list):
            return jsonify({'error': 'users must be a list'}), 400
        
        # Predizer batch
        results = prediction_engine.predict_batch(users_features)
        
        return jsonify({
            'success': True,
            'count': len(results),
            'predictions': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in /predict/batch: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handler para 404"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para 500"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting Flask server on port {port}")
    logger.info(f"   Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
