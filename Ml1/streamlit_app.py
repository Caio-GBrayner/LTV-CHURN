import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os

# --- DEFINIÇÃO DE FEATURES (Deve ser EXATA à ordem de treino) ---

# Colunas esperadas pelo modelo CHURN (Regressão Logística)
CHURN_FEATURES = [
    'membership_type_id',
    'has_biometrics',
    'days_on_platform',
    'days_since_last_login',
    'days_since_last_run',
    'runs_last_90_days',
    'distance_last_90_days_km'
]

# Colunas esperadas pelo modelo LTV (Random Forest), incluindo o One-Hot Encoding
LTV_FEATURES = [
    'has_biometrics',
    'runs_last_90_days',
    'distance_last_90_days_km',
    'avg_pace_last_90_days',
    'achievement_count',
    'membership_type_id_1',
    'membership_type_id_2',
    'membership_type_id_3'
]

# --- 1. CARREGAMENTO DOS MODELOS ---

@st.cache_resource
def load_models():
    """Carrega os modelos CHURN e LTV a partir da pasta 'models/'."""
    
    # Caminhos esperados
    churn_path = 'models/churn_model.pkl'
    ltv_path = 'models/ltv_model.pkl'

    try:
        with open(churn_path, 'rb') as f:
            model_churn = pickle.load(f)
        
        with open(ltv_path, 'rb') as f:
            model_ltv = pickle.load(f)
            
        return model_churn, model_ltv
    
    except FileNotFoundError:
        st.error(f"Erro: Arquivos de modelo não encontrados. Verifique se os caminhos estão corretos e se os arquivos estão na pasta 'models/'.\nFaltando: {churn_path} ou {ltv_path}")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao carregar os modelos: {e}")
        st.stop()

# Carregar os modelos (executado apenas uma vez)
model_churn, model_ltv = load_models()


# --- 2. FUNÇÃO DE PRÉ-PROCESSAMENTO PARA PREDIÇÃO ---

def preprocess_input(user_input):
    """Converte o input do usuário para os DataFrames esperados pelos modelos."""

    data = {
        'membership_type_id': [user_input['membership_type_id']],
        'has_biometrics': [user_input['has_biometrics']],
        'runs_last_90_days': [user_input['runs_last_90_days']],
        'distance_last_90_days_km': [user_input['distance_last_90_days_km']],
        'days_since_last_login': [user_input['days_since_last_login']],
        'days_since_last_run': [user_input['days_since_last_run']],
        'days_on_platform': [user_input['days_on_platform']],
        'avg_pace_last_90_days': [user_input['avg_pace_last_90_days']],
        'achievement_count': [user_input['achievement_count']]
    }
    df = pd.DataFrame(data)
    
    # 1. Pré-processamento Comum
    df['has_biometrics'] = df['has_biometrics'].astype(int)

    # 2. DataFrame para CHURN (Reordenar colunas conforme CHURN_FEATURES)
    df_churn = df[CHURN_FEATURES].copy()

    # 3. DataFrame para LTV (Requer OHE e Reordenação)
    df_ltv = df[['membership_type_id', 'has_biometrics', 'runs_last_90_days', 'distance_last_90_days_km', 'avg_pace_last_90_days', 'achievement_count']].copy()
    
    # Aplicar One-Hot Encoding
    df_ltv = pd.get_dummies(df_ltv, columns=['membership_type_id'], drop_first=False)
    
    # Garantir que todas as 3 colunas de OHE existam (padrão de treinamento)
    for i in [1, 2, 3]:
        col_name = f'membership_type_id_{i}'
        if col_name not in df_ltv.columns:
            df_ltv[col_name] = 0
            
    # Reordenar colunas para corresponder ao treinamento LTV
    df_ltv = df_ltv[[col for col in LTV_FEATURES if col in df_ltv.columns]]

    return df_churn, df_ltv


# --- 3. INTERFACE STREAMLIT ---

st.set_page_config(layout="wide")

st.title("Sistema de Previsão ML para runit 🏃‍♀️")
st.subheader("Teste dos Modelos CHURN e LTV Carregados")

with st.sidebar:
    st.header("1. Features do Usuário")
    st.write("Defina as características de um usuário hipotético para a previsão.")
    
    membership_map = {1: "Básico", 2: "Premium", 3: "VIP"}
    member_type = st.selectbox("Plano de Assinatura (membership_type_id)", options=[1, 2, 3], format_func=lambda x: f"{x} ({membership_map[x]})")
    biometrics = st.checkbox("Utiliza Biometria (has_biometrics)", value=True)
    
    st.markdown("---")
    st.header("2. Atividade Recente (RFV)")
    runs = st.slider("Corridas (runs_last_90_days)", min_value=0, max_value=50, value=15, step=1)
    distance = st.number_input("Distância Total (km) em 90 dias", min_value=0, max_value=1000, value=150)
    
    st.markdown("---")
    st.header("3. Recência e Risco (CHURN)")
    login_recency = st.slider("Dias desde o Último Login (days_since_last_login)", min_value=1, max_value=180, value=10, step=1)
    run_recency = st.slider("Dias desde a Última Corrida (days_since_last_run)", min_value=1, max_value=180, value=10, step=1)
    account_age = st.slider("Idade da Conta (days_on_platform)", min_value=30, max_value=730, value=300, step=1)
    
    st.markdown("---")
    st.header("4. Performance (LTV)")
    pace = st.number_input("Ritmo Médio (min/km - avg_pace_last_90_days)", min_value=4.0, max_value=10.0, value=5.5)
    achievements = st.slider("Conquistas Acumuladas (achievement_count)", min_value=0, max_value=20, value=8, step=1)

user_input = {
    'membership_type_id': member_type,
    'has_biometrics': biometrics,
    'runs_last_90_days': runs,
    'distance_last_90_days_km': distance,
    'days_since_last_login': login_recency,
    'days_since_last_run': run_recency,
    'days_on_platform': account_age,
    'avg_pace_last_90_days': pace,
    'achievement_count': achievements
}

df_churn_input, df_ltv_input = preprocess_input(user_input)

churn_proba = model_churn.predict_proba(df_churn_input)[0][1]
ltv_proba = model_ltv.predict_proba(df_ltv_input)[0][1]
ltv_segment = "Alto Valor (High Value)" if ltv_proba > 0.5 else "Baixo/Médio Valor"

st.header("Análise Preditiva do Usuário")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📉 Modelo de Churn (Risco de Saída)")
    
    churn_score = int(churn_proba * 100)
    
    if churn_score > 75:
        st.error(f"RISCO EXTREMAMENTE ALTO: {churn_score}%")
        st.markdown("**Ação Recomendada:** Intervenção imediata (Suporte VIP ou Oferta de Retenção).")
    elif churn_score > 40:
        st.warning(f"RISCO ALTO: {churn_score}%")
        st.markdown("**Ação Recomendada:** Campanha de reengajamento segmentada.")
    else:
        st.success(f"RISCO BAIXO: {churn_score}%")
        st.markdown("**Ação Recomendada:** Monitoramento padrão.")

    st.progress(churn_proba, text=f"Probabilidade de Churn: **{churn_score}%**")
    st.markdown(f"*(Baseado em Recência e Frequência)*")

with col2:
    st.subheader("✨ Modelo de LTV (Potencial de Valor)")

    ltv_score = int(ltv_proba * 100)
    
    if ltv_segment == "Alto Valor (High Value)":
        st.balloons()
        st.metric(label="Segmento Previsto", value=ltv_segment, delta=f"Probabilidade: {ltv_score}%")
        st.markdown("**Ação Recomendada:** Priorizar em novos recursos, campanhas de *upsell* ou testes A/B.")
    else:
        st.metric(label="Segmento Previsto", value=ltv_segment, delta=f"Probabilidade (High Value): {ltv_score}%")
        st.markdown("**Ação Recomendada:** Foco em campanhas de motivação e aumento de volume de corridas.")

    st.progress(ltv_proba, text=f"Probabilidade de ser Alto Valor: **{ltv_score}%**")
    st.markdown(f"*(Baseado em Plano, Volume e Performance)*")

st.markdown("---")
st.caption("Os resultados refletem a lógica dos modelos 'model_churn.pkl' e 'model_ltv.pkl' carregados localmente.")