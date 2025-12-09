-- Script: extract_training_data.sql
-- Propósito: Extrair todos os dados necessários para treinamento dos modelos
-- Executar: Mensalmente ou quando houver dados suficientes

SELECT 
    -- ============ IDENTIFICAÇÃO ============
    u.user_id,
    u.name,
    u.created_at as user_created_at,
    
    -- ============ FEATURES DE ENGAJAMENTO ============
    COUNT(DISTINCT rs.running_session_id) as running_sessions_count,
    
    -- Corridas nos últimos períodos
    COUNT(DISTINCT CASE 
        WHEN rs.started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
        THEN rs.running_session_id 
    END) as runs_last_30_days,
    
    COUNT(DISTINCT CASE 
        WHEN rs.started_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) 
        THEN rs.running_session_id 
    END) as runs_last_90_days,
    
    -- Distância nos últimos períodos (convertendo metros para km)
    COALESCE(SUM(CASE 
        WHEN rs.started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
        THEN rs.distance_meters / 1000.0
        ELSE 0 
    END), 0) as distance_last_30_days_km,
    
    COALESCE(SUM(CASE 
        WHEN rs.started_at >= DATE_SUB(NOW(), INTERVAL 90 DAY) 
        THEN rs.distance_meters / 1000.0
        ELSE 0 
    END), 0) as distance_last_90_days_km,
    
    -- Dias desde última corrida
    COALESCE(DATEDIFF(NOW(), MAX(rs.started_at)), 999) as days_since_last_run,
    
    -- Média de distância por corrida
    COALESCE(AVG(rs.distance_meters / 1000.0), 0) as avg_distance_per_run,
    
    -- ============ FEATURES DE TEMPO ============
    DATEDIFF(NOW(), u.created_at) as days_on_platform,
    COALESCE(DATEDIFF(NOW(), MAX(l.last_login_at)), 999) as days_since_last_login,
    
    -- ============ FEATURES DE SAÚDE FÍSICA ============
    COALESCE(AVG(CASE 
        WHEN rs.started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
        THEN rs.avg_heart_rate 
    END), 0) as avg_heart_rate_last_30_days,
    
    COALESCE(MAX(rs.peak_heart_rate), 0) as peak_heart_rate_max,
    
    COALESCE(AVG(rs.elevation_gain_meters), 0) as avg_elevation_gain,
    
    -- Pace médio (minutos por km)
    COALESCE(AVG(
        CASE 
            WHEN rs.distance_meters > 0 
            THEN (rs.elapsed_seconds / 60.0) / (rs.distance_meters / 1000.0)
        END
    ), 0) as avg_pace_min_per_km,
    
    -- ============ FEATURES COMPORTAMENTAIS ============
    COUNT(DISTINCT ua.achievement_id) as achievement_count,
    
    CASE 
        WHEN u.has_biometrics = 1 THEN 1 
        ELSE 0 
    END as has_biometrics,
    
    COALESCE(u.membership_type_id, 1) as membership_type_id,
    
    COUNT(DISTINCT ur.race_id) as race_participation_count,
    
    -- ============ TARGET: CHURN ============
    -- Usuário é considerado "churned" se não tem atividade há mais de 60 dias
    CASE 
        WHEN COALESCE(DATEDIFF(NOW(), MAX(rs.started_at)), 999) > 60 THEN 1
        WHEN COALESCE(DATEDIFF(NOW(), MAX(l.last_login_at)), 999) > 60 THEN 1
        ELSE 0 
    END as churned,
    
    -- ============ TARGET: LTV ============
    -- Para simplificar, vamos estimar LTV baseado em:
    -- 1. Tipo de membership (Free=0, Premium=29.90, etc)
    -- 2. Tempo de atividade
    -- 3. Engajamento
    CASE 
        WHEN u.membership_type_id = 1 THEN 0  -- Free
        WHEN u.membership_type_id = 2 THEN 
            (DATEDIFF(NOW(), u.created_at) / 30.0) * 29.90  -- Premium
        WHEN u.membership_type_id = 3 THEN 
            (DATEDIFF(NOW(), u.created_at) / 30.0) * 49.90  -- Plus
        ELSE 0 
    END as lifetime_value

FROM users u
LEFT JOIN running_sessions rs ON u.user_id = rs.user_id
LEFT JOIN logins l ON u.user_id = l.user_id
LEFT JOIN user_biometrics ub ON u.user_id = ub.user_id
LEFT JOIN user_achievements ua ON u.user_id = ua.user_id
LEFT JOIN user_races ur ON u.user_id = ur.user_id

WHERE 
    -- Apenas usuários com pelo menos 30 dias de histórico
    u.created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
    -- Apenas usuários ativos (não deletados)
    AND u.active = 1

GROUP BY 
    u.user_id, u.name, u.created_at, 
    u.has_biometrics, u.membership_type_id

ORDER BY u.user_id;
