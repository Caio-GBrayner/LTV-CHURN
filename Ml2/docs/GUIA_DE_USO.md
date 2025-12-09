# 🎯 Guia Completo: Como Usar os Modelos de ML

## 📋 Visão Geral

Este projeto contém:
- ✅ Scripts de extração de dados do banco MySQL
- ✅ Feature Engineering automatizado
- ✅ Modelos de Churn e LTV (Gradient Boosting)
- ✅ API Flask REST para predições
- ✅ Docker para deploy
- ✅ Testes automatizados

---

## 🚀 Início Rápido (5 Passos)

### Passo 1: Configurar Ambiente

```bash
cd Ml2

# Executar setup automático
./setup.sh

# OU manualmente:
cp .env.example .env
source ../.venv/bin/activate
pip install -r requirements.txt
```

### Passo 2: Configurar Banco de Dados

Edite o arquivo `.env`:

```bash
nano .env
```

Configure as credenciais do MySQL:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=runit
```

### Passo 3: Extrair Dados do Banco

```bash
python extract_training_data.py
```

**Saída esperada:**
- ✅ Arquivo `data/training_data.csv` criado
- ✅ Resumo dos dados extraídos
- ✅ Estatísticas de Churn e LTV

**Requisitos mínimos:**
- Pelo menos 100 usuários com histórico de 30+ dias
- Taxa de churn entre 20-40% (ideal)

### Passo 4: Treinar Modelos

#### Modelo de Churn

```bash
python train_churn_model.py
```

**Tempo estimado:** 2-5 minutos

**Arquivos gerados:**
- `models/churn_model_v1.0.0.pkl` - Modelo treinado
- `models/churn_scaler_v1.0.0.pkl` - Normalizador
- `models/churn_features_v1.0.0.pkl` - Lista de features
- `models/churn_importance_v1.0.0.csv` - Feature importance
- `models/churn_metrics_v1.0.0.pkl` - Métricas
- `models/churn_evaluation_v1.0.0.png` - Gráficos

**Métricas esperadas:**
- Acurácia: > 85%
- F1-Score: > 0.75
- ROC-AUC: > 0.80

#### Modelo de LTV

```bash
python train_ltv_model.py
```

**Tempo estimado:** 2-5 minutos

**Arquivos gerados:**
- `models/ltv_model_v1.0.0.pkl` - Modelo treinado
- `models/ltv_scaler_v1.0.0.pkl` - Normalizador
- `models/ltv_features_v1.0.0.pkl` - Lista de features
- `models/ltv_importance_v1.0.0.csv` - Feature importance
- `models/ltv_metrics_v1.0.0.pkl` - Métricas
- `models/ltv_evaluation_v1.0.0.png` - Gráficos

**Métricas esperadas:**
- RMSE: < $50
- R² Score: > 0.65
- MAE: < $35

### Passo 5: Iniciar API Flask

```bash
python app.py
```

**Saída esperada:**
```
🚀 Initializing Prediction Service...
   Model Version: v1.0.0
   Models Path: ./models
✅ Churn model loaded
✅ LTV model loaded
✅ Prediction Service initialized successfully
🚀 Starting Flask server on port 5000
```

API disponível em: `http://localhost:5000`

---

## 🧪 Testar API

Em outro terminal:

```bash
cd Ml2
source ../.venv/bin/activate
python test_api.py
```

**Testes executados:**
1. ✅ Health Check
2. ✅ Models Info
3. ✅ Predict Churn
4. ✅ Predict LTV
5. ✅ Predict All

---

## 📡 Usando a API

### 1. Health Check

```bash
curl http://localhost:5000/health
```

### 2. Informações dos Modelos

```bash
curl http://localhost:5000/models/info
```

### 3. Predizer Churn

```bash
curl -X POST http://localhost:5000/predict/churn \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### 4. Predizer LTV

```bash
curl -X POST http://localhost:5000/predict/ltv \
  -H "Content-Type: application/json" \
  -d '{ ... }' # mesmas features
```

### 5. Predizer Ambos (Churn + LTV)

```bash
curl -X POST http://localhost:5000/predict/all \
  -H "Content-Type: application/json" \
  -d '{ ... }' # mesmas features
```

---

## 🔄 Retreinamento dos Modelos

Recomendado: **Mensal** ou quando houver mudanças significativas nos dados.

```bash
# 1. Extrair novos dados
python extract_training_data.py

# 2. Verificar qualidade dos dados
# - Revisar data/training_data.csv
# - Verificar distribuição de churn
# - Verificar range de LTV

# 3. Retreinar modelos
python train_churn_model.py
python train_ltv_model.py

# 4. Revisar métricas
# - Comparar com versão anterior
# - Verificar se não houve degradação

# 5. Atualizar versão (se necessário)
# - Editar MODEL_VERSION no .env
# - Reiniciar Flask

# 6. Reiniciar serviço Flask
# Ctrl+C no terminal do Flask
python app.py
```

---

## 🐳 Deploy com Docker

### Build

```bash
docker build -t prediction-service:v1.0.0 .
```

### Run

```bash
docker run -d \
  --name prediction-service \
  -p 5000:5000 \
  -v $(pwd)/models:/app/models \
  -e MODEL_VERSION=v1.0.0 \
  -e DB_HOST=host.docker.internal \
  -e DB_USER=root \
  -e DB_PASSWORD=senha \
  -e DB_NAME=runit \
  --restart unless-stopped \
  prediction-service:v1.0.0
```

### Verificar logs

```bash
docker logs -f prediction-service
```

### Parar/Iniciar

```bash
docker stop prediction-service
docker start prediction-service
docker restart prediction-service
```

---

## 🔧 Troubleshooting

### Problema: Dados não encontrados

```bash
❌ Dados não encontrados: data/training_data.csv
```

**Solução:**
```bash
python extract_training_data.py
```

---

### Problema: Erro ao conectar ao banco

```bash
❌ Erro ao conectar ao banco: Access denied
```

**Solução:**
1. Verificar credenciais no `.env`
2. Testar conexão:
```bash
mysql -h localhost -u root -p
```

---

### Problema: Modelos não carregados

```bash
❌ Failed to load models: Model not found
```

**Solução:**
```bash
# Verificar se modelos existem
ls -la models/

# Se não, treinar
python train_churn_model.py
python train_ltv_model.py
```

---

### Problema: Porta 5000 já em uso

```bash
OSError: [Errno 98] Address already in use
```

**Solução 1:** Mudar porta no `.env`
```bash
echo "FLASK_PORT=5001" >> .env
```

**Solução 2:** Matar processo
```bash
lsof -ti:5000 | xargs kill -9
```

---

### Problema: Métricas baixas

**Churn com acurácia < 70%:**
- Verificar balanceamento de classes
- Aumentar dados de treinamento
- Ajustar hiperparâmetros

**LTV com R² < 0.5:**
- Verificar outliers
- Revisar features
- Considerar transformação log

---

## 📊 Monitoramento

### Verificar Performance

```bash
# Health check
curl http://localhost:5000/health

# Informações dos modelos
curl http://localhost:5000/models/info
```

### Logs

```bash
# Se rodando diretamente
tail -f logs/flask.log

# Se rodando com Docker
docker logs -f prediction-service
```

---

## 🎯 Integração com Backend Java

### Configuração no Spring Boot

```properties
# application.properties
prediction.service.url=http://localhost:5000
prediction.service.timeout=30000
```

### Exemplo de Chamada

```java
RestTemplate restTemplate = new RestTemplate();

Map<String, Object> features = calculateUserFeatures(userId);

ResponseEntity<PredictionResponse> response = restTemplate.postForEntity(
    "http://localhost:5000/predict/all",
    features,
    PredictionResponse.class
);

PredictionResponse prediction = response.getBody();
```

---

## 📝 Checklist de Deploy

- [ ] Dados extraídos e validados
- [ ] Modelos treinados com métricas adequadas
- [ ] API Flask funcionando localmente
- [ ] Testes automatizados passando
- [ ] Docker build bem-sucedido
- [ ] Variáveis de ambiente configuradas
- [ ] Health check respondendo
- [ ] Integração com backend testada
- [ ] Logs configurados
- [ ] Monitoramento ativo

---

## 🆘 Suporte

Se encontrar problemas:

1. Verificar logs
2. Revisar `.env`
3. Testar com `test_api.py`
4. Verificar versões das dependências
5. Consultar README.md

---

**Última atualização:** 2025-12-09
**Versão dos Modelos:** v1.0.0
