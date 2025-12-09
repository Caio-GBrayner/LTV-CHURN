"""
Feature Engineering para modelos de Churn e LTV.
Calcula features derivadas a partir dos dados brutos.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

class FeatureEngineer:
    """
    Classe responsável por calcular features derivadas e preparar dados para ML.
    """
    
    def __init__(self):
        self.feature_names = []
        self.scaler = StandardScaler()
    
    def calculate_all_features(self, df):
        """
        Calcula todas as features derivadas.
        
        Args:
            df (pd.DataFrame): DataFrame com features básicas
            
        Returns:
            pd.DataFrame: DataFrame com features derivadas adicionadas
        """
        print("\n[INFO] Calculando features derivadas...")
        
        df_features = df.copy()
        
        # ==================== ENGAGEMENT SCORE ====================
        # Score de 0-100 baseado em atividade
        df_features['engagement_score'] = self._calculate_engagement_score(df_features)
        
        # ==================== DAYS INACTIVE RATIO ====================
        # Proporção de dias inativos vs dias na plataforma
        df_features['days_inactive_ratio'] = (
            df_features['days_since_last_run'] / 
            df_features['days_on_platform'].replace(0, 1)
        ).clip(0, 1)
        
        # ==================== CONSISTENCY SCORE ====================
        # Consistência das corridas (quão regular é o usuário)
        df_features['consistency_score'] = self._calculate_consistency_score(
            df_features['runs_last_30_days'], 
            df_features['runs_last_90_days']
        )
        
        # ==================== MONTHLY ACTIVITY RATE ====================
        # Taxa de atividade mensal
        df_features['monthly_activity_rate'] = (
            df_features['running_sessions_count'] / 
            (df_features['days_on_platform'] / 30).replace(0, 1)
        ).clip(0, 50)  # Máximo 50 corridas por mês
        
        # ==================== DISTANCE TREND ====================
        # Tendência de distância (30d vs 90d)
        avg_30d = df_features['distance_last_30_days_km']
        avg_90d = df_features['distance_last_90_days_km'] / 3  # Normalizar para 30d
        df_features['distance_trend'] = np.where(
            avg_90d > 0,
            (avg_30d - avg_90d) / avg_90d,
            0
        ).clip(-1, 1)
        
        # ==================== IS PREMIUM ====================
        # Flag se é usuário premium
        df_features['is_premium'] = (df_features['membership_type_id'] > 1).astype(int)
        
        # ==================== ACTIVITY LEVEL ====================
        # Categorização de nível de atividade
        df_features['activity_level'] = pd.cut(
            df_features['running_sessions_count'],
            bins=[-1, 0, 5, 20, 50, float('inf')],
            labels=[0, 1, 2, 3, 4]  # 0=Inativo, 1=Baixo, 2=Médio, 3=Alto, 4=Muito Alto
        ).astype(int)
        
        # ==================== PACE CATEGORY ====================
        # Categorização de pace (velocidade)
        df_features['pace_category'] = pd.cut(
            df_features['avg_pace_min_per_km'],
            bins=[0, 5, 6, 7, 8, float('inf')],
            labels=[4, 3, 2, 1, 0]  # 4=Muito Rápido, 0=Lento
        ).astype(int)
        
        print(f"[OK] {len(df_features.columns) - len(df.columns)} features derivadas criadas!")
        
        return df_features
    
    def _calculate_engagement_score(self, df):
        """
        Calcula score de engajamento (0-100).
        
        Leva em consideração:
        - Frequência de corridas
        - Distância percorrida
        - Conquistas
        - Biometria
        - Participação em corridas
        """
        # Normalizar componentes (0-1)
        runs_norm = np.clip(df['runs_last_90_days'] / 30, 0, 1)  # 30+ corridas = 1
        distance_norm = np.clip(df['distance_last_90_days_km'] / 500, 0, 1)  # 500km = 1
        achievements_norm = np.clip(df['achievement_count'] / 20, 0, 1)  # 20+ conquistas = 1
        biometrics_norm = df['has_biometrics']
        races_norm = np.clip(df['race_participation_count'] / 10, 0, 1)  # 10+ corridas = 1
        
        # Pesos
        weights = {
            'runs': 0.35,
            'distance': 0.25,
            'achievements': 0.20,
            'biometrics': 0.10,
            'races': 0.10
        }
        
        # Score ponderado
        score = (
            runs_norm * weights['runs'] +
            distance_norm * weights['distance'] +
            achievements_norm * weights['achievements'] +
            biometrics_norm * weights['biometrics'] +
            races_norm * weights['races']
        ) * 100
        
        return score.round(2)
    
    def _calculate_consistency_score(self, runs_30d, runs_90d):
        """
        Calcula consistência das corridas.
        
        Se o usuário mantém o mesmo ritmo nos últimos 30 vs 90 dias,
        tem alta consistência.
        """
        # Normalizar para 30 dias
        avg_30d = runs_30d
        avg_90d = runs_90d / 3
        
        # Calcular diferença relativa
        consistency = np.where(
            avg_90d > 0,
            1 - np.abs(avg_30d - avg_90d) / avg_90d,
            0
        )
        
        return np.clip(consistency, 0, 1).round(4)
    
    def prepare_features_for_training(self, df, target_col, test_size=0.2):
        """
        Prepara features para treinamento (separa X, y, treino/teste).
        
        Args:
            df (pd.DataFrame): DataFrame com todas as features
            target_col (str): Nome da coluna target ('churned' ou 'lifetime_value')
            test_size (float): Proporção do conjunto de teste
            
        Returns:
            tuple: (X_train, X_test, y_train, y_test, feature_names)
        """
        from sklearn.model_selection import train_test_split
        
        print(f"\n[INFO] Preparando dados para treinamento (target: {target_col})...")
        
        # Colunas a remover
        cols_to_drop = [
            'user_id', 'name', 'user_created_at',  # Identificação
            'churned', 'lifetime_value'  # Targets
        ]
        
        # Features
        feature_cols = [col for col in df.columns if col not in cols_to_drop]
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        
        # Tratar valores infinitos e NaN
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        # Split treino/teste
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=test_size, 
            random_state=42,
            stratify=y if target_col == 'churned' else None  # Stratify apenas para classificação
        )
        
        print(f"[OK] Dados preparados:")
        print(f"   - Features: {X_train.shape[1]}")
        print(f"   - Treino: {X_train.shape[0]} amostras")
        print(f"   - Teste: {X_test.shape[0]} amostras")
        
        self.feature_names = feature_cols
        
        return X_train, X_test, y_train, y_test, feature_cols
    
    def scale_features(self, X_train, X_test=None, save_path=None):
        """
        Normaliza features usando StandardScaler.
        
        Args:
            X_train: Features de treino
            X_test: Features de teste (opcional)
            save_path: Caminho para salvar o scaler (opcional)
            
        Returns:
            tuple: (X_train_scaled, X_test_scaled) ou apenas X_train_scaled
        """
        print("\n[INFO] Normalizando features...")
        
        # Fit no treino
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Transform no teste (se fornecido)
        X_test_scaled = None
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
        
        # Salvar scaler
        if save_path:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.scaler, save_path)
            print(f"[OK] Scaler salvo em: {save_path}")
        
        print("[OK] Normalização concluída!")
        
        if X_test is not None:
            return X_train_scaled, X_test_scaled
        return X_train_scaled
    
    def load_scaler(self, scaler_path):
        """Carrega scaler salvo"""
        self.scaler = joblib.load(scaler_path)
        print(f"[OK] Scaler carregado de: {scaler_path}")
        return self.scaler


if __name__ == "__main__":
    # Teste básico
    print("[TEST] Testando Feature Engineering...")
    
    # Criar dados de exemplo
    sample_data = pd.DataFrame({
        'user_id': [1, 2, 3],
        'name': ['User1', 'User2', 'User3'],
        'running_sessions_count': [50, 10, 2],
        'runs_last_30_days': [15, 3, 0],
        'runs_last_90_days': [45, 9, 2],
        'distance_last_30_days_km': [150, 30, 0],
        'distance_last_90_days_km': [450, 90, 20],
        'days_since_last_run': [1, 30, 90],
        'avg_distance_per_run': [10, 10, 10],
        'days_on_platform': [365, 180, 90],
        'days_since_last_login': [1, 15, 60],
        'avg_heart_rate_last_30_days': [145, 150, 0],
        'peak_heart_rate_max': [180, 185, 0],
        'avg_elevation_gain': [50, 30, 0],
        'avg_pace_min_per_km': [6.0, 7.0, 0],
        'achievement_count': [15, 5, 0],
        'has_biometrics': [1, 1, 0],
        'membership_type_id': [2, 1, 1],
        'race_participation_count': [5, 2, 0],
        'churned': [0, 0, 1],
        'lifetime_value': [299.0, 0, 0],
        'user_created_at': pd.to_datetime(['2024-01-01', '2024-06-01', '2024-09-01'])
    })
    
    # Calcular features
    engineer = FeatureEngineer()
    df_with_features = engineer.calculate_all_features(sample_data)
    
    print("\n[INFO] Features calculadas:")
    for col in df_with_features.columns:
        if col not in sample_data.columns:
            print(f"   - {col}")
    
    print("\n[OK] Feature Engineering funcionando corretamente!")
