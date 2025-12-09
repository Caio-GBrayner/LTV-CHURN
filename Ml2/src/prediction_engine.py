"""
Prediction Engine - Motor de predição para Churn e LTV.
"""

import numpy as np
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PredictionEngine:
    """
    Motor de predição que usa modelos carregados para fazer previsões.
    """
    
    def __init__(self, model_loader):
        self.model_loader = model_loader
        
    def predict_churn(self, features_dict):
        """
        Prediz probabilidade de churn para um usuário.
        
        Args:
            features_dict (dict): Dicionário com features do usuário
            
        Returns:
            dict: Resultado da predição com probabilidade, risk_level, etc.
        """
        try:
            logger.info("Predicting churn...")
            
            # Preparar features
            X = self._prepare_features(features_dict, 'churn')
            
            # Normalizar
            scaler = self.model_loader.get_scaler('churn')
            X_scaled = scaler.transform(X)
            
            # Predizer
            model = self.model_loader.get_model('churn')
            probability = float(model.predict_proba(X_scaled)[0, 1])
            prediction = int(model.predict(X_scaled)[0])
            
            # Determinar risk level
            if probability >= 0.7:
                risk_level = 'HIGH'
            elif probability >= 0.4:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            # Feature importance
            feature_importance = self._calculate_feature_importance(
                model, X, 'churn'
            )
            
            result = {
                'prediction': prediction,
                'probability': round(probability, 4),
                'risk_level': risk_level,
                'confidence_score': round(max(probability, 1 - probability), 4),
                'feature_importance': feature_importance,
                'model_version': self.model_loader.model_version,
                'predicted_at': datetime.now().isoformat()
            }
            
            logger.info(f"[OK] Churn prediction: {probability:.4f} ({risk_level})")
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Error predicting churn: {e}")
            raise
    
    def predict_ltv(self, features_dict):
        """
        Prediz LTV (Lifetime Value) de um usuário.
        
        Args:
            features_dict (dict): Dicionário com features do usuário
            
        Returns:
            dict: Resultado da predição com valor estimado, etc.
        """
        try:
            logger.info("Predicting LTV...")
            
            # Preparar features
            X = self._prepare_features(features_dict, 'ltv')
            
            # Normalizar
            scaler = self.model_loader.get_scaler('ltv')
            X_scaled = scaler.transform(X)
            
            # Predizer
            model = self.model_loader.get_model('ltv')
            ltv_value = float(model.predict(X_scaled)[0])
            ltv_value = max(ltv_value, 0)  # Garantir não-negativo
            
            # Categorizar LTV
            if ltv_value >= 500:
                ltv_category = 'HIGH'
            elif ltv_value >= 200:
                ltv_category = 'MEDIUM'
            elif ltv_value > 0:
                ltv_category = 'LOW'
            else:
                ltv_category = 'ZERO'
            
            # Feature importance
            feature_importance = self._calculate_feature_importance(
                model, X, 'ltv'
            )
            
            result = {
                'ltv_value': round(ltv_value, 2),
                'ltv_category': ltv_category,
                'feature_importance': feature_importance,
                'model_version': self.model_loader.model_version,
                'predicted_at': datetime.now().isoformat()
            }
            
            logger.info(f"[OK] LTV prediction: ${ltv_value:.2f} ({ltv_category})")
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Error predicting LTV: {e}")
            raise
    
    def predict_batch(self, users_features):
        """
        Prediz Churn e LTV para múltiplos usuários.
        
        Args:
            users_features (list): Lista de dicts com features de cada usuário
            
        Returns:
            list: Lista de resultados de predição
        """
        logger.info(f"Batch prediction for {len(users_features)} users...")
        
        results = []
        for user_features in users_features:
            try:
                churn_result = self.predict_churn(user_features)
                ltv_result = self.predict_ltv(user_features)
                
                results.append({
                    'user_id': user_features.get('user_id'),
                    'churn': churn_result,
                    'ltv': ltv_result
                })
            except Exception as e:
                logger.error(f"Error in batch prediction: {e}")
                results.append({
                    'user_id': user_features.get('user_id'),
                    'error': str(e)
                })
        
        logger.info(f"[OK] Batch prediction completed: {len(results)} results")
        return results
    
    def _prepare_features(self, features_dict, model_type):
        """Prepara features no formato correto para o modelo"""
        feature_names = self.model_loader.get_feature_names(model_type)
        
        # Criar DataFrame com features na ordem correta
        features_list = []
        for feature_name in feature_names:
            value = features_dict.get(feature_name, 0)
            features_list.append(value)
        
        X = pd.DataFrame([features_list], columns=feature_names)
        return X
    
    def _calculate_feature_importance(self, model, X, model_type, top_n=10):
        """
        Calcula importância das features para a predição.
        
        Returns:
            list: Lista com top N features mais importantes
        """
        if not hasattr(model, 'feature_importances_'):
            return []
        
        feature_names = self.model_loader.get_feature_names(model_type)
        importances = model.feature_importances_
        
        # Criar lista de features com importância
        feature_importance = []
        for i, (name, importance) in enumerate(zip(feature_names, importances)):
            feature_importance.append({
                'feature_name': name,
                'feature_value': float(X.iloc[0, i]),
                'importance_score': round(float(importance), 4),
                'rank': i + 1
            })
        
        # Ordenar por importância e pegar top N
        feature_importance.sort(key=lambda x: x['importance_score'], reverse=True)
        return feature_importance[:top_n]
