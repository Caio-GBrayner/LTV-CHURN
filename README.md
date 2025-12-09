# Prediction Service - Modelos de Churn e LTV

Serviço de Machine Learning para predição de Churn e Lifetime Value (LTV) de usuários.

## 📁 Estrutura do Projeto

```
Ml2/
├── app.py                          # Aplicação Flask (API REST)
├── extract_training_data.py        # Script para extrair dados do banco
├── train_churn_model.py            # Script para treinar modelo de Churn
├── train_ltv_model.py              # Script para treinar modelo de LTV
├── requirements.txt                # Dependências Python
├── Dockerfile                      # Container Docker
├── .env.example                    # Exemplo de variáveis de ambiente
│
├── src/                            # Código fonte
│   ├── __init__.py
│   ├── feature_engineering.py     # Engenharia de features
│   ├── model_loader.py            # Carregador de modelos
│   └── prediction_engine.py       # Motor de predição
│
├── models/                         # Modelos treinados (gerados após treinamento)
│   ├── churn_model_v1.0.0.pkl
│   ├── churn_scaler_v1.0.0.pkl
│   ├── churn_features_v1.0.0.pkl
│   ├── ltv_model_v1.0.0.pkl
│   ├── ltv_scaler_v1.0.0.pkl
│   └── ltv_features_v1.0.0.pkl
│
├── data/                           # Dados de treinamento
│   └── training_data.csv
│
├── sql/                            # Scripts SQL
│   └── extract_training_data.sql
│
└──
```

## 🚀 Quick Start

### 1. Configurar Ambiente

```bash
# Copiar exemplo de .env
cp .env.example .env

# Editar .env com suas configurações
nano .env
```

### 2. Instalar Dependências

```bash
# Usar venv existente na raiz do projeto
source ../.venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Extrair Dados do Banco

```bash
# Extrair dados para treinamento
python extract_training_data.py
```

### 4. Treinar Modelos

```bash
# Treinar modelo de Churn
python train_churn_model.py

# Treinar modelo de LTV
python train_ltv_model.py
```

### 5. Iniciar Serviço Flask

```bash
# Desenvolvimento
python app.py

# Produção (com gunicorn)
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

## 🐳 Docker

### Build

```bash
docker build -t prediction-service:latest .
```

### Run

```bash
docker run -d \
  --name prediction-service \
  -p 5000:5000 \
  -v $(pwd)/models:/app/models \
  -e MODEL_VERSION=v1.0.0 \
  prediction-service:latest
```

## 📡 API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Prediction Service",
  "version": "v1.0.0",
  "models_loaded": true
}
```

### Models Info

```bash
GET /models/info
```

**Response:**
```json
{
  "version": "v1.0.0",
  "models_loaded": ["churn", "ltv"],
  "churn_features_count": 25,
  "ltv_features_count": 25
}
```

### Predict Churn

```bash
POST /predict/churn
Content-Type: application/json

{
  "user_id": 123,
  "running_sessions_count": 50,
  "runs_last_30_days": 10,
  "runs_last_90_days": 35,
  "distance_last_30_days_km": 120,
  "distance_last_90_days_km": 400,
  "days_since_last_run": 5,
  "avg_distance_per_run": 8.5,
  "days_on_platform": 365,
  "days_since_last_login": 2,
  "avg_heart_rate_last_30_days": 145,
  "peak_heart_rate_max": 180,
  "avg_elevation_gain": 50,
  "avg_pace_min_per_km": 6.5,
  "achievement_count": 15,
  "has_biometrics": 1,
  "membership_type_id": 2,
  "race_participation_count": 5
}
```

**Response:**
```json
{
  "success": true,
  "user_id": 123,
  "prediction": {
    "prediction": 0,
    "probability": 0.1523,
    "risk_level": "LOW",
    "confidence_score": 0.8477,
    "feature_importance": [
      {
        "feature_name": "days_since_last_run",
        "feature_value": 5,
        "importance_score": 0.2534,
        "rank": 1
      }
    ],
    "model_version": "v1.0.0",
    "predicted_at": "2025-12-09T10:30:00"
  }
}
```

### Predict LTV

```bash
POST /predict/ltv
Content-Type: application/json

{
  "user_id": 123,
  ... (mesmas features)
}
```

**Response:**
```json
{
  "success": true,
  "user_id": 123,
  "prediction": {
    "ltv_value": 450.25,
    "ltv_category": "HIGH",
    "feature_importance": [...],
    "model_version": "v1.0.0",
    "predicted_at": "2025-12-09T10:30:00"
  }
}
```

### Predict All (Churn + LTV)

```bash
POST /predict/all
Content-Type: application/json

{
  "user_id": 123,
  ... (features)
}
```

### Batch Prediction

```bash
POST /predict/batch
Content-Type: application/json

{
  "users": [
    {"user_id": 1, ...},
    {"user_id": 2, ...}
  ]
}
```

## 📊 Features Utilizadas

### Features Base (do Banco de Dados)
- `running_sessions_count` - Total de sessões de corrida
- `runs_last_30_days` - Corridas nos últimos 30 dias
- `runs_last_90_days` - Corridas nos últimos 90 dias
- `distance_last_30_days_km` - Distância (30d)
- `distance_last_90_days_km` - Distância (90d)
- `days_since_last_run` - Dias desde última corrida
- `avg_distance_per_run` - Distância média por corrida
- `days_on_platform` - Dias na plataforma
- `days_since_last_login` - Dias desde último login
- `avg_heart_rate_last_30_days` - Frequência cardíaca média
- `peak_heart_rate_max` - Pico de frequência cardíaca
- `avg_elevation_gain` - Ganho de elevação médio
- `avg_pace_min_per_km` - Pace médio
- `achievement_count` - Conquistas desbloqueadas
- `has_biometrics` - Possui biometria (0/1)
- `membership_type_id` - Tipo de plano
- `race_participation_count` - Participação em corridas

### Features Derivadas (Calculadas Automaticamente)
- `engagement_score` - Score de engajamento (0-100)
- `days_inactive_ratio` - Razão de inatividade
- `consistency_score` - Consistência de corridas
- `monthly_activity_rate` - Taxa de atividade mensal
- `distance_trend` - Tendência de distância
- `is_premium` - Se é usuário premium
- `activity_level` - Nível de atividade (0-4)
- `pace_category` - Categoria de pace (0-4)

## 🔄 Retreinamento

Para retreinar os modelos com novos dados:

```bash
# 1. Extrair novos dados
python extract_training_data.py

# 2. Treinar novos modelos
python train_churn_model.py
python train_ltv_model.py

# 3. Reiniciar serviço Flask
# Os novos modelos serão carregados automaticamente
```

## 📈 Métricas dos Modelos

### Churn Model
- **Acurácia**: Meta > 85%
- **F1-Score**: Meta > 0.75
- **ROC-AUC**: Meta > 0.80

### LTV Model
- **RMSE**: Meta < $50
- **R² Score**: Meta > 0.65
- **MAE**: Meta < $35

## 🛠️ Troubleshooting

### Modelos não encontrados
```bash
# Verificar se modelos foram treinados
ls -la models/

# Se não existirem, treinar
python train_churn_model.py
python train_ltv_model.py
```

### Erro de conexão com banco
```bash
# Verificar .env
cat .env

# Testar conexão
python -c "import mysql.connector; print('OK')"
```

### Porta 5000 já em uso
```bash
# Mudar porta no .env
echo "FLASK_PORT=5001" >> .env

# Ou matar processo
lsof -ti:5000 | xargs kill -9
```

## 📝 Próximos Passos

1. ✅ Modelos criados e treinados
2. ✅ API Flask funcionando
3. ⏳ Integrar com backend Java (Spring Boot)
4. ⏳ Criar job de retreinamento automático
5. ⏳ Monitoramento de performance dos modelos
6. ⏳ Dashboard de analytics

## 📄 Licença

Propriedade de RunUnit
