"""
Script de extração de dados do banco MySQL para treinamento dos modelos.
"""

import pandas as pd
import mysql.connector
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class DataExtractor:
    def __init__(self, db_config=None):
        """
        Inicializa o extrator de dados.
        
        Args:
            db_config (dict): Configurações do banco de dados.
                Se None, usa variáveis de ambiente.
        """
        if db_config is None:
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'user': os.getenv('DB_USER', 'root'),
                'password': os.getenv('DB_PASSWORD', ''),
                'database': os.getenv('DB_NAME', 'runit')
            }
        else:
            self.db_config = db_config
        
    def connect(self):
        """Conectar ao banco MySQL"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            print(f"[OK] Conectado ao banco {self.db_config['database']} com sucesso!")
            return connection
        except mysql.connector.Error as err:
            print(f"[ERRO] Erro ao conectar ao banco: {err}")
            raise
    
    def extract_training_data(self, output_path='data/training_data.csv'):
        """
        Extrai dados para treinamento dos modelos.
        
        Args:
            output_path (str): Caminho para salvar os dados extraídos.
            
        Returns:
            pd.DataFrame: DataFrame com os dados extraídos.
        """
        print(f"\n{'='*60}")
        print(f"[INFO] Iniciando extração de dados em {datetime.now()}")
        print(f"{'='*60}\n")
        
        # Ler query SQL
        sql_path = Path(__file__).parent / 'sql' / 'extract_training_data.sql'
        with open(sql_path, 'r') as f:
            query = f.read()
        
        # Conectar e executar query
        connection = self.connect()
        
        try:
            print("[INFO] Executando query de extração...")
            df = pd.read_sql(query, connection)
            print(f"[OK] Query executada! {len(df)} registros extraídos.")
            
            # Criar diretório se não existir
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Salvar CSV
            df.to_csv(output_path, index=False)
            print(f"[OK] Dados salvos em: {output_path}")
            
            return df
            
        except Exception as e:
            print(f"[ERRO] Erro ao extrair dados: {e}")
            raise
        finally:
            connection.close()
            print("[INFO] Conexão fechada.")
    
    def get_data_summary(self, df):
        """Exibe resumo estatístico dos dados"""
        print(f"\n{'='*60}")
        print("[INFO] RESUMO DOS DADOS EXTRAÍDOS")
        print(f"{'='*60}\n")
        
        print(f"[INFO] Total de registros: {len(df)}")
        print(f"[INFO] Total de features: {len(df.columns)}")
        print(f"\n[INFO] Colunas:")
        for col in df.columns:
            print(f"   - {col}")
        
        print(f"\n[INFO] Estatísticas do Target CHURN:")
        churn_counts = df['churned'].value_counts()
        print(f"   - Não Churned (0): {churn_counts.get(0, 0)} ({churn_counts.get(0, 0)/len(df)*100:.2f}%)")
        print(f"   - Churned (1): {churn_counts.get(1, 0)} ({churn_counts.get(1, 0)/len(df)*100:.2f}%)")
        
        print(f"\n[INFO] Estatísticas do Target LTV:")
        print(f"   - Média: ${df['lifetime_value'].mean():.2f}")
        print(f"   - Mediana: ${df['lifetime_value'].median():.2f}")
        print(f"   - Min: ${df['lifetime_value'].min():.2f}")
        print(f"   - Max: ${df['lifetime_value'].max():.2f}")
        
        print(f"\n[INFO] Missing Values:")
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(missing[missing > 0])
        else:
            print("   [OK] Nenhum valor faltante!")
        
        print(f"\n{'='*60}\n")

# Uso
if __name__ == "__main__":
    # Configuração do banco (pode ser passada ou usar .env)
    # config = {
    #     'host': 'localhost',
    #     'port': 3306,
    #     'user': 'root',
    #     'password': 'sua_senha',
    #     'database': 'runit'
    # }
    
    extractor = DataExtractor()  # Usa .env
    df = extractor.extract_training_data()
    extractor.get_data_summary(df)
    
    print("[OK] Extração concluída! Dados prontos para treinamento.")
