"""
Script de treinamento do modelo de LTV (Lifetime Value).
Prediz o valor do tempo de vida de um usuário.
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error
)
import sys
sys.path.append(str(Path(__file__).parent))
from src.feature_engineering import FeatureEngineer

class LTVModelTrainer:
    """
    Classe responsável por treinar o modelo de predição de LTV.
    """
    
    def __init__(self, model_version='v1.0.0'):
        self.model_version = model_version
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.feature_names = []
        self.feature_importance = None
        
    def load_data(self, data_path='data/training_data.csv'):
        """Carrega dados de treinamento"""
        print(f"\n{'='*60}")
        print(f"[INFO] Carregando dados de: {data_path}")
        print(f"{'='*60}\n")
        
        df = pd.read_csv(data_path)
        print(f"[OK] {len(df)} registros carregados")
        print(f"[OK] {len(df.columns)} colunas")
        
        return df
    
    def prepare_data(self, df):
        """Prepara dados para treinamento"""
        print(f"\n{'='*60}")
        print("[INFO] PREPARANDO DADOS")
        print(f"{'='*60}\n")
        
        # Calcular features derivadas
        df_features = self.feature_engineer.calculate_all_features(df)
        
        # Preparar para treinamento
        X_train, X_test, y_train, y_test, feature_names = \
            self.feature_engineer.prepare_features_for_training(
                df_features, 
                target_col='lifetime_value',
                test_size=0.2
            )
        
        self.feature_names = feature_names
        
        # Normalizar features
        scaler_path = f'models/ltv_scaler_{self.model_version}.pkl'
        X_train_scaled, X_test_scaled = self.feature_engineer.scale_features(
            X_train, X_test, save_path=scaler_path
        )
        
        print(f"\n[INFO] Distribuição do Target (LTV):")
        print(f"   Treino - Média: ${y_train.mean():.2f} | Mediana: ${y_train.median():.2f}")
        print(f"   Teste  - Média: ${y_test.mean():.2f} | Mediana: ${y_test.median():.2f}")
        print(f"   Min: ${y_train.min():.2f} | Max: ${y_train.max():.2f}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_model(self, X_train, y_train, model_type='gradient_boosting'):
        """
        Treina o modelo de LTV.
        
        Args:
            X_train: Features de treino
            y_train: Target de treino
            model_type: Tipo de modelo ('gradient_boosting', 'random_forest', 'linear')
        """
        print(f"\n{'='*60}")
        print(f"[INFO] TREINANDO MODELO DE LTV ({model_type.upper()})")
        print(f"{'='*60}\n")
        
        if model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=20,
                min_samples_leaf=10,
                subsample=0.8,
                random_state=42,
                verbose=1
            )
        elif model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1,
                verbose=1
            )
        elif model_type == 'linear':
            self.model = LinearRegression()
        else:
            raise ValueError(f"Modelo {model_type} não suportado")
        
        # Treinar
        print("[INFO] Treinando modelo...")
        self.model.fit(X_train, y_train)
        print("[OK] Modelo treinado com sucesso!")
        
        # Feature importance (se disponível)
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print(f"\n[INFO] Top 10 Features Mais Importantes:")
            for idx, row in self.feature_importance.head(10).iterrows():
                print(f"   {row['feature']:30s} | {row['importance']:.4f}")
        
        return self.model
    
    def evaluate_model(self, X_test, y_test):
        """Avalia o modelo no conjunto de teste"""
        print(f"\n{'='*60}")
        print("[INFO] AVALIANDO MODELO")
        print(f"{'='*60}\n")
        
        # Predições
        y_pred = self.model.predict(X_test)
        
        # Garantir que predições sejam não-negativas
        y_pred = np.maximum(y_pred, 0)
        
        # Métricas
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # MAPE (apenas para valores > 0)
        mask = y_test > 0
        if mask.sum() > 0:
            mape = mean_absolute_percentage_error(y_test[mask], y_pred[mask])
        else:
            mape = 0
        
        print(f"[METRICS] MÉTRICAS DE PERFORMANCE:")
        print(f"   - RMSE (Root Mean Squared Error): ${rmse:.2f}")
        print(f"   - MAE (Mean Absolute Error): ${mae:.2f}")
        print(f"   - R² Score: {r2:.4f}")
        print(f"   - MAPE (Mean Absolute % Error): {mape*100:.2f}%")
        
        # Análise de erros
        errors = y_pred - y_test
        print(f"\n[INFO] Análise de Erros:")
        print(f"   - Erro Médio: ${errors.mean():.2f}")
        print(f"   - Erro Mediano: ${np.median(errors):.2f}")
        print(f"   - Desvio Padrão: ${errors.std():.2f}")
        
        # Salvar métricas
        metrics = {
            'rmse': float(rmse),
            'mae': float(mae),
            'r2_score': float(r2),
            'mape': float(mape)
        }
        
        return metrics, y_pred
    
    def save_model(self, metrics):
        """Salva o modelo treinado"""
        print(f"\n{'='*60}")
        print("[INFO] SALVANDO MODELO")
        print(f"{'='*60}\n")
        
        # Criar diretório
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        
        # Salvar modelo
        model_path = models_dir / f'ltv_model_{self.model_version}.pkl'
        joblib.dump(self.model, model_path)
        print(f"[OK] Modelo salvo: {model_path}")
        
        # Salvar feature names
        features_path = models_dir / f'ltv_features_{self.model_version}.pkl'
        joblib.dump(self.feature_names, features_path)
        print(f"[OK] Features salvas: {features_path}")
        
        # Salvar feature importance
        if self.feature_importance is not None:
            importance_path = models_dir / f'ltv_importance_{self.model_version}.csv'
            self.feature_importance.to_csv(importance_path, index=False)
            print(f"[OK] Feature importance salva: {importance_path}")
        
        # Salvar métricas
        metrics_path = models_dir / f'ltv_metrics_{self.model_version}.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"[OK] Métricas salvas: {metrics_path}")
        
        print(f"\n[OK] Modelo {self.model_version} salvo com sucesso!")
    
    def plot_results(self, y_test, y_pred):
        """Plota gráficos de avaliação"""
        print(f"\n[INFO] Gerando gráficos...")
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Predicted vs Actual
        axes[0].scatter(y_test, y_pred, alpha=0.5, s=30)
        axes[0].plot([y_test.min(), y_test.max()], 
                     [y_test.min(), y_test.max()], 
                     'r--', lw=2, label='Perfect Prediction')
        axes[0].set_xlabel('Actual LTV ($)')
        axes[0].set_ylabel('Predicted LTV ($)')
        axes[0].set_title('Predicted vs Actual LTV')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Residuals
        residuals = y_pred - y_test
        axes[1].scatter(y_pred, residuals, alpha=0.5, s=30)
        axes[1].axhline(y=0, color='r', linestyle='--', lw=2)
        axes[1].set_xlabel('Predicted LTV ($)')
        axes[1].set_ylabel('Residuals ($)')
        axes[1].set_title('Residual Plot')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Salvar
        plots_dir = Path('models')
        plot_path = plots_dir / f'ltv_evaluation_{self.model_version}.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"[OK] Gráficos salvos: {plot_path}")
        
        plt.close()
    
    def run_full_training_pipeline(self, data_path='data/training_data.csv'):
        """Executa pipeline completo de treinamento"""
        print(f"\n{'='*70}")
        print(f"[START] INICIANDO TREINAMENTO DO MODELO DE LTV")
        print(f"   Versão: {self.model_version}")
        print(f"   Data: {datetime.now()}")
        print(f"{'='*70}\n")
        
        try:
            # 1. Carregar dados
            df = self.load_data(data_path)
            
            # 2. Preparar dados
            X_train, X_test, y_train, y_test = self.prepare_data(df)
            
            # 3. Treinar modelo
            self.train_model(X_train, y_train, model_type='gradient_boosting')
            
            # 4. Avaliar modelo
            metrics, y_pred = self.evaluate_model(X_test, y_test)
            
            # 5. Salvar modelo
            self.save_model(metrics)
            
            # 6. Plotar resultados
            self.plot_results(y_test, y_pred)
            
            print(f"\n{'='*70}")
            print(f"[SUCCESS] TREINAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"{'='*70}\n")
            
            return metrics
            
        except Exception as e:
            print(f"\n[ERRO] ERRO NO TREINAMENTO: {e}")
            raise


# Script principal
if __name__ == "__main__":
    print("\n" + "="*70)
    print("LTV MODEL TRAINER")
    print("="*70 + "\n")
    
    # Configuração
    MODEL_VERSION = 'v1.0.0'
    DATA_PATH = 'data/training_data.csv'
    
    # Verificar se dados existem
    if not Path(DATA_PATH).exists():
        print(f"[ERRO] Dados não encontrados: {DATA_PATH}")
        print("[INFO] Execute primeiro: python extract_training_data.py")
        sys.exit(1)
    
    # Criar trainer
    trainer = LTVModelTrainer(model_version=MODEL_VERSION)
    
    # Executar treinamento
    metrics = trainer.run_full_training_pipeline(data_path=DATA_PATH)
    
    print(f"\n[SUMMARY] RESUMO FINAL:")
    print(f"   - RMSE: ${metrics['rmse']:.2f}")
    print(f"   - MAE: ${metrics['mae']:.2f}")
    print(f"   - R² Score: {metrics['r2_score']:.4f}")
    print(f"   - MAPE: {metrics['mape']*100:.2f}%")
    
    print(f"\n[OK] Modelo pronto para uso!")
    print(f"   Arquivo: models/ltv_model_{MODEL_VERSION}.pkl")
