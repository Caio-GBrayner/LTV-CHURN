"""
Script de teste para verificar se a API Flask está funcionando.
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_health():
    """Testa endpoint de health"""
    print("\n" + "="*60)
    print("[TEST] Testando /health")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_models_info():
    """Testa endpoint de models info"""
    print("\n" + "="*60)
    print("[TEST] Testando /models/info")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/models/info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_predict_churn():
    """Testa predição de churn"""
    print("\n" + "="*60)
    print("[TEST] Testando /predict/churn")
    print("="*60)
    
    # Features de exemplo
    features = {
        "user_id": 999,
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
    
    response = requests.post(
        f"{BASE_URL}/predict/churn",
        json=features
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_predict_ltv():
    """Testa predição de LTV"""
    print("\n" + "="*60)
    print("[TEST] Testando /predict/ltv")
    print("="*60)
    
    # Features de exemplo
    features = {
        "user_id": 999,
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
    
    response = requests.post(
        f"{BASE_URL}/predict/ltv",
        json=features
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_predict_all():
    """Testa predição completa (Churn + LTV)"""
    print("\n" + "="*60)
    print("[TEST] Testando /predict/all")
    print("="*60)
    
    # Features de exemplo
    features = {
        "user_id": 999,
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
    
    response = requests.post(
        f"{BASE_URL}/predict/all",
        json=features
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("\n" + "="*70)
    print("[START] TESTANDO API DE PREDIÇÃO")
    print("="*70)
    
    print(f"\n[INFO] Base URL: {BASE_URL}")
    print("[INFO] Certifique-se de que o servidor Flask está rodando!")
    print("   Comando: python app.py")
    
    try:
        # Testes
        results = {
            "Health Check": test_health(),
            "Models Info": test_models_info(),
            "Predict Churn": test_predict_churn(),
            "Predict LTV": test_predict_ltv(),
            "Predict All": test_predict_all()
        }
        
        # Resumo
        print("\n" + "="*70)
        print("[SUMMARY] RESUMO DOS TESTES")
        print("="*70)
        
        for test_name, passed in results.items():
            status = "[PASS] PASSOU" if passed else "[FAIL] FALHOU"
            print(f"{test_name:20s} - {status}")
        
        all_passed = all(results.values())
        
        print("\n" + "="*70)
        if all_passed:
            print("[SUCCESS] TODOS OS TESTES PASSARAM!")
        else:
            print("[FAIL] ALGUNS TESTES FALHARAM")
        print("="*70 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] ERRO: Não foi possível conectar ao servidor Flask")
        print("[INFO] Execute: python app.py")
        print()
