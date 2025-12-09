#!/bin/bash

# Script de setup inicial para o projeto ML

echo "========================================"
echo "🚀 SETUP - MODELOS DE CHURN E LTV"
echo "========================================"
echo ""

# 1. Criar .env
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cp .env.example .env
    echo "✅ Arquivo .env criado. EDITE com suas configurações!"
    echo ""
else
    echo "✅ Arquivo .env já existe"
    echo ""
fi

# 2. Ativar venv
echo "🐍 Ativando ambiente virtual..."
source ../.venv/bin/activate
echo "✅ Ambiente ativado"
echo ""

# 3. Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt
echo "✅ Dependências instaladas"
echo ""

echo "========================================"
echo "✅ SETUP CONCLUÍDO!"
echo "========================================"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Configure o .env com os dados do banco:"
echo "   nano .env"
echo ""
echo "2. Extraia dados do banco:"
echo "   python extract_training_data.py"
echo ""
echo "3. Treine os modelos:"
echo "   python train_churn_model.py"
echo "   python train_ltv_model.py"
echo ""
echo "4. Inicie o serviço Flask:"
echo "   python app.py"
echo ""
echo "5. Teste a API:"
echo "   python test_api.py"
echo ""
