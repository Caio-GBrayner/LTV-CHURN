"""
Script de treinamento do modelo de Churn.
Prediz se um usuário tem risco de abandonar a plataforma.
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    roc_auc_score, 
    roc_curve,
    precision_recall_curve,
    accuracy_score,
    f1_score
)
import sys
sys.path.append(str(Path(__file__).parent))
from src.feature_engineering import FeatureEngineer

class ChurnModelTrainer:
    """
    Classe responsável por treinar o modelo de predição de Churn.
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
                target_col='churned',
                test_size=0.2
            )
        
        self.feature_names = feature_names
        
        # Normalizar features
        scaler_path = f'models/churn_scaler_{self.model_version}.pkl'
        X_train_scaled, X_test_scaled = self.feature_engineer.scale_features(
            X_train, X_test, save_path=scaler_path
        )
        
        print(f"\n[INFO] Distribuição do Target:")
        print(f"   Treino - Churn: {y_train.sum()} ({y_train.mean()*100:.2f}%)")
        print(f"   Teste  - Churn: {y_test.sum()} ({y_test.mean()*100:.2f}%)")
        
        return X_train_scaled, X_test_scaled, y_train, y_test
    
    def train_model(self, X_train, y_train, model_type='gradient_boosting'):
        """
        Treina o modelo de Churn.
        
        Args:
            X_train: Features de treino
            y_train: Target de treino
            model_type: Tipo de modelo ('gradient_boosting', 'random_forest', 'logistic')
        """
        print(f"\n{'='*60}")
        print(f"[INFO] TREINANDO MODELO DE CHURN ({model_type.upper()})")
        print(f"{'='*60}\n")
        
        if model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
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
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1,
                verbose=1
            )
        elif model_type == 'logistic':
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                solver='liblinear'
            )
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
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Métricas
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        print(f"[METRICS] MÉTRICAS DE PERFORMANCE:")
        print(f"   - Acurácia: {accuracy:.4f}")
        print(f"   - F1-Score: {f1:.4f}")
        print(f"   - ROC-AUC: {roc_auc:.4f}")
        
        print(f"\n[INFO] Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Não Churn', 'Churn']))
        
        print(f"\n[INFO] Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        print(f"\n   TN: {cm[0,0]} | FP: {cm[0,1]}")
        print(f"   FN: {cm[1,0]} | TP: {cm[1,1]}")
        
        # Salvar métricas
        metrics = {
            'accuracy': float(accuracy),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'confusion_matrix': cm.tolist()
        }
        
        return metrics, y_pred, y_pred_proba
    
    def save_model(self, metrics):
        """Salva o modelo treinado"""
        print(f"\n{'='*60}")
        print("[INFO] SALVANDO MODELO")
        print(f"{'='*60}\n")
        
        # Criar diretório
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        
        # Salvar modelo
        model_path = models_dir / f'churn_model_{self.model_version}.pkl'
        joblib.dump(self.model, model_path)
        print(f"[OK] Modelo salvo: {model_path}")
        
        # Salvar feature names
        features_path = models_dir / f'churn_features_{self.model_version}.pkl'
        joblib.dump(self.feature_names, features_path)
        print(f"[OK] Features salvas: {features_path}")
        
        # Salvar feature importance
        if self.feature_importance is not None:
            importance_path = models_dir / f'churn_importance_{self.model_version}.csv'
            self.feature_importance.to_csv(importance_path, index=False)
            print(f"[OK] Feature importance salva: {importance_path}")
        
        # Salvar métricas
        metrics_path = models_dir / f'churn_metrics_{self.model_version}.pkl'
        joblib.dump(metrics, metrics_path)
        print(f"[OK] Métricas salvas: {metrics_path}")
        
        print(f"\n[OK] Modelo {self.model_version} salvo com sucesso!")
    
    def plot_results(self, y_test, y_pred_proba):
        """Plota gráficos de avaliação"""
        print(f"\n[INFO] Gerando gráficos...")
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # ROC Curve
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        axes[0].plot(fpr, tpr, label=f'ROC Curve (AUC = {roc_auc:.4f})')
        axes[0].plot([0, 1], [0, 1], 'k--', label='Random')
        axes[0].set_xlabel('False Positive Rate')
        axes[0].set_ylabel('True Positive Rate')
        axes[0].set_title('ROC Curve - Churn Model')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Precision-Recall Curve
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        
        axes[1].plot(recall, precision)
        axes[1].set_xlabel('Recall')
        axes[1].set_ylabel('Precision')
        axes[1].set_title('Precision-Recall Curve')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Salvar
        plots_dir = Path('models')
        plot_path = plots_dir / f'churn_evaluation_{self.model_version}.png'
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"[OK] Gráficos salvos: {plot_path}")
        
        plt.close()
    
    def run_full_training_pipeline(self, data_path='data/training_data.csv'):
        """Executa pipeline completo de treinamento"""
        print(f"\n{'='*70}")
        print(f"[START] INICIANDO TREINAMENTO DO MODELO DE CHURN")
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
            metrics, y_pred, y_pred_proba = self.evaluate_model(X_test, y_test)
            
            # 5. Salvar modelo
            self.save_model(metrics)
            
            # 6. Plotar resultados
            self.plot_results(y_test, y_pred_proba)
            
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
    print("CHURN MODEL TRAINER")
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
    trainer = ChurnModelTrainer(model_version=MODEL_VERSION)
    
    # Executar treinamento
    metrics = trainer.run_full_training_pipeline(data_path=DATA_PATH)
    
    print(f"\n[SUMMARY] RESUMO FINAL:")
    print(f"   - Acurácia: {metrics['accuracy']:.4f}")
    print(f"   - F1-Score: {metrics['f1_score']:.4f}")
    print(f"   - ROC-AUC: {metrics['roc_auc']:.4f}")
    
    print(f"\n[OK] Modelo pronto para uso!")
    print(f"   Arquivo: models/churn_model_{MODEL_VERSION}.pkl")
