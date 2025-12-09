"""
Model Loader - Carrega modelos treinados para uso em produção.
"""

import joblib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    """Carrega e gerencia modelos treinados"""
    
    def __init__(self, models_dir='models', model_version='v1.0.0'):
        self.models_dir = Path(models_dir)
        self.model_version = model_version
        self.models = {}
        self.scalers = {}
        self.feature_names = {}
        
    def load_all_models(self):
        """Carrega todos os modelos (Churn e LTV)"""
        logger.info(f"Loading models version {self.model_version}")
        
        try:
            # Churn Model
            self.models['churn'] = self._load_model('churn_model')
            self.scalers['churn'] = self._load_model('churn_scaler')
            self.feature_names['churn'] = self._load_model('churn_features')
            logger.info("[OK] Churn model loaded")
            
            # LTV Model
            self.models['ltv'] = self._load_model('ltv_model')
            self.scalers['ltv'] = self._load_model('ltv_scaler')
            self.feature_names['ltv'] = self._load_model('ltv_features')
            logger.info("[OK] LTV model loaded")
            
            logger.info("[OK] All models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error loading models: {e}")
            return False
    
    def _load_model(self, model_name):
        """Carrega um modelo específico"""
        model_path = self.models_dir / f'{model_name}_{self.model_version}.pkl'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        return joblib.load(model_path)
    
    def get_model(self, model_type):
        """Retorna modelo carregado"""
        return self.models.get(model_type)
    
    def get_scaler(self, model_type):
        """Retorna scaler carregado"""
        return self.scalers.get(model_type)
    
    def get_feature_names(self, model_type):
        """Retorna nomes das features"""
        return self.feature_names.get(model_type)
    
    def get_model_info(self):
        """Retorna informações sobre modelos carregados"""
        return {
            'version': self.model_version,
            'models_loaded': list(self.models.keys()),
            'churn_features_count': len(self.feature_names.get('churn', [])),
            'ltv_features_count': len(self.feature_names.get('ltv', []))
        }
