# 📋 Especificação Detalhada: Entidade de Predição (UserPrediction)

## 📌 Objetivo

Criar um sistema robusto de armazenamento e rastreamento de predições de **Churn** e **LTV** para cada usuário, permitindo auditoria completa, análise histórica e integração com o frontend do dashboard.

---

## 🗂️ Estrutura do Banco de Dados

### Tabela Principal: `user_predictions`

```sql
CREATE TABLE user_predictions (
  prediction_id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  prediction_type ENUM('CHURN', 'LTV') NOT NULL,
  probability DECIMAL(5,4) NOT NULL COMMENT 'Valor entre 0 e 1 (ex: 0.7823)',
  risk_level ENUM('LOW', 'MEDIUM', 'HIGH') NOT NULL,
  confidence_score DECIMAL(5,4) NOT NULL COMMENT 'Confiança da predição',
  model_version VARCHAR(50) NOT NULL COMMENT 'Versão do modelo (ex: v1.0.2)',
  is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Soft delete - 0 = deletado logicamente',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL COMMENT 'Data da exclusão lógica',
  
  PRIMARY KEY (prediction_id),
  KEY idx_user_id (user_id),
  KEY idx_prediction_type (prediction_type),
  KEY idx_risk_level (risk_level),
  KEY idx_is_active (is_active),
  KEY idx_created_at (created_at),
  KEY idx_user_type_active (user_id, prediction_type, is_active),
  
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### Tabela de Detalhes: `prediction_logs`

```sql
CREATE TABLE prediction_logs (
  log_id BIGINT NOT NULL AUTO_INCREMENT,
  prediction_id BIGINT NOT NULL,
  feature_name VARCHAR(100) NOT NULL COMMENT 'Nome da feature',
  feature_value DECIMAL(15,4) NOT NULL COMMENT 'Valor da feature',
  feature_type VARCHAR(50) COMMENT 'Tipo: NUMERIC, BOOLEAN, CATEGORICAL',
  importance_score DECIMAL(5,4) NOT NULL COMMENT 'Importância (0-1)',
  rank INT COMMENT 'Ranking de importância (1 é mais importante)',
  is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Soft delete',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  PRIMARY KEY (log_id),
  KEY idx_prediction_id (prediction_id),
  KEY idx_importance_score (importance_score),
  KEY idx_rank (rank),
  
  FOREIGN KEY (prediction_id) REFERENCES user_predictions(prediction_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### Tabela de Features Calculadas: `user_prediction_features`

```sql
CREATE TABLE user_prediction_features (
  feature_id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  
  -- Features de Engajamento
  running_sessions_count INT DEFAULT 0,
  runs_last_30_days INT DEFAULT 0,
  runs_last_90_days INT DEFAULT 0,
  distance_last_30_days_km DECIMAL(10,2) DEFAULT 0,
  distance_last_90_days_km DECIMAL(10,2) DEFAULT 0,
  days_since_last_run INT,
  avg_distance_per_run DECIMAL(8,2),
  
  -- Features de Tempo
  days_on_platform INT,
  days_since_last_login INT,
  
  -- Features de Saúde Física
  avg_heart_rate_last_30_days DECIMAL(5,2),
  peak_heart_rate_max SMALLINT,
  avg_elevation_gain DECIMAL(8,2),
  avg_pace_min_per_km DECIMAL(5,2),
  
  -- Features Comportamentais
  achievement_count INT DEFAULT 0,
  has_biometrics TINYINT(1) DEFAULT 0,
  membership_type_id SMALLINT,
  race_participation_count INT DEFAULT 0,
  
  -- Features Derived (Calculadas)
  engagement_score DECIMAL(10,4),
  days_inactive_ratio DECIMAL(10,4),
  consistency_score DECIMAL(10,4),
  monthly_activity_rate DECIMAL(10,4),
  
  -- Metadata
  is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Soft delete',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL,
  
  PRIMARY KEY (feature_id),
  UNIQUE KEY uk_user_id (user_id),
  KEY idx_engagement_score (engagement_score),
  KEY idx_is_active (is_active),
  
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (membership_type_id) REFERENCES membership_type(membership_type_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

### Tabela de Histórico de Modelos: `model_versions`

```sql
CREATE TABLE model_versions (
  model_version_id BIGINT NOT NULL AUTO_INCREMENT,
  model_type ENUM('CHURN', 'LTV') NOT NULL,
  version_name VARCHAR(50) NOT NULL COMMENT 'ex: v1.0.2',
  file_path VARCHAR(500) NOT NULL COMMENT 'Caminho para o arquivo .pkl ou .h5',
  accuracy DECIMAL(5,4),
  precision DECIMAL(5,4),
  recall DECIMAL(5,4),
  f1_score DECIMAL(5,4),
  rmse DECIMAL(10,4) COMMENT 'Para regressão (LTV)',
  mae DECIMAL(10,4) COMMENT 'Para regressão (LTV)',
  r2_score DECIMAL(5,4) COMMENT 'Para regressão (LTV)',
  is_active TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Versão ativa em produção',
  trained_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  
  PRIMARY KEY (model_version_id),
  UNIQUE KEY uk_model_version (model_type, version_name),
  KEY idx_model_type (model_type),
  KEY idx_is_active (is_active),
  KEY idx_trained_at (trained_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
```

---

## 🔗 Associações e Chaves Estrangeiras

### 1. **UserPrediction → User** (Many-to-One)
- **FK**: `user_id` referencia `users(user_id)`
- **Ação ON DELETE**: `CASCADE` - Se um usuário é deletado, todas suas predições são deletadas
- **Ação ON UPDATE**: `CASCADE` - Se user_id muda, atualiza em cascata
- **Relacionamento**: Um usuário pode ter múltiplas predições (uma por tipo de modelo ou múltiplas no histórico)

```java
@Entity
@Table(name = "user_predictions")
public class UserPrediction {
  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "user_id", nullable = false, foreignKey = @ForeignKey(name = "fk_user_predictions_user_id"))
  private User user;
}
```

### 2. **PredictionLog → UserPrediction** (Many-to-One)
- **FK**: `prediction_id` referencia `user_predictions(prediction_id)`
- **Ação ON DELETE**: `CASCADE` - Se predição é deletada, todos seus logs são deletados
- **Ação ON UPDATE**: `CASCADE` - Mantém integridade referencial
- **Relacionamento**: Uma predição pode ter múltiplos logs (um por feature importante)

```java
@Entity
@Table(name = "prediction_logs")
public class PredictionLog {
  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "prediction_id", nullable = false, foreignKey = @ForeignKey(name = "fk_prediction_logs_prediction_id"))
  private UserPrediction prediction;
}
```

### 3. **UserPredictionFeatures → User** (One-to-One)
- **FK**: `user_id` referencia `users(user_id)` com UNIQUE constraint
- **Ação ON DELETE**: `CASCADE` - Se usuário é deletado, features são deletadas
- **Ação ON UPDATE**: `CASCADE`
- **Relacionamento**: Um usuário tem exatamente um registro de features

```java
@Entity
@Table(name = "user_prediction_features")
public class UserPredictionFeatures {
  @OneToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "user_id", nullable = false, unique = true, foreignKey = @ForeignKey(name = "fk_features_user_id"))
  private User user;
}
```

### 4. **UserPredictionFeatures → MembershipType** (Many-to-One)
- **FK**: `membership_type_id` referencia `membership_type(membership_type_id)`
- **Ação ON DELETE**: `SET NULL` - Se tipo de membership é deletado, coluna vira null
- **Ação ON UPDATE**: `CASCADE`
- **Relacionamento**: Múltiplos usuários podem ter o mesmo tipo de membership

```java
@Entity
@Table(name = "user_prediction_features")
public class UserPredictionFeatures {
  @ManyToOne(fetch = FetchType.LAZY)
  @JoinColumn(name = "membership_type_id", nullable = true, foreignKey = @ForeignKey(name = "fk_features_membership_type_id"))
  private MembershipType membershipType;
}
```

---

## 🛡️ Estratégia de Deleção

### Soft Delete (Exclusão Lógica)

Todas as três entidades possuem soft delete para preservar histórico e auditoria:

```java
@Entity
@Table(name = "user_predictions")
@SQLDelete(sql = "UPDATE user_predictions SET is_active = 0, deleted_at = NOW() WHERE prediction_id = ?")
@Where(clause = "is_active = 1")
public class UserPrediction {
  @Column(name = "is_active", nullable = false, columnDefinition = "TINYINT(1) DEFAULT 1")
  private Boolean isActive = true;

  @Column(name = "deleted_at")
  private LocalDateTime deletedAt;
}
```

**Por que soft delete?**
- ✅ Preservar histórico completo de predições
- ✅ Auditoria: rastrear quando/por quem foi deletado
- ✅ Recuperação: poder restaurar dados se necessário
- ✅ Análise: comparar predições antigas vs novas
- ✅ Conformidade: LGPD/GDPR (registrar deleções)

---

## 📊 Entidades Java Completas

### 1. UserPrediction.java

```java
package com.rununit.prediction.entity;

import com.rununit.user.entity.User;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "user_predictions", indexes = {
    @Index(name = "idx_user_id", columnList = "user_id"),
    @Index(name = "idx_prediction_type", columnList = "prediction_type"),
    @Index(name = "idx_risk_level", columnList = "risk_level"),
    @Index(name = "idx_is_active", columnList = "is_active"),
    @Index(name = "idx_created_at", columnList = "created_at"),
    @Index(name = "idx_user_type_active", columnList = "user_id, prediction_type, is_active")
})
@SQLDelete(sql = "UPDATE user_predictions SET is_active = 0, deleted_at = NOW() WHERE prediction_id = ?")
@Where(clause = "is_active = 1")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserPrediction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "prediction_id")
    private Long predictionId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, foreignKey = @ForeignKey(name = "fk_user_predictions_user_id"))
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(name = "prediction_type", nullable = false)
    private PredictionType predictionType; // CHURN, LTV

    @Column(name = "probability", nullable = false, precision = 5, scale = 4)
    private BigDecimal probability; // 0.0000 a 1.0000

    @Enumerated(EnumType.STRING)
    @Column(name = "risk_level", nullable = false)
    private RiskLevel riskLevel; // LOW, MEDIUM, HIGH

    @Column(name = "confidence_score", nullable = false, precision = 5, scale = 4)
    private BigDecimal confidenceScore;

    @Column(name = "model_version", nullable = false, length = 50)
    private String modelVersion;

    @Column(name = "is_active", nullable = false, columnDefinition = "TINYINT(1) DEFAULT 1")
    private Boolean isActive = true;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @OneToMany(mappedBy = "prediction", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<PredictionLog> logs;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public enum PredictionType {
        CHURN, LTV
    }

    public enum RiskLevel {
        LOW, MEDIUM, HIGH
    }
}
```

### 2. PredictionLog.java

```java
package com.rununit.prediction.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "prediction_logs", indexes = {
    @Index(name = "idx_prediction_id", columnList = "prediction_id"),
    @Index(name = "idx_importance_score", columnList = "importance_score"),
    @Index(name = "idx_rank", columnList = "rank")
})
@SQLDelete(sql = "UPDATE prediction_logs SET is_active = 0 WHERE log_id = ?")
@Where(clause = "is_active = 1")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PredictionLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "log_id")
    private Long logId;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "prediction_id", nullable = false, foreignKey = @ForeignKey(name = "fk_prediction_logs_prediction_id"))
    private UserPrediction prediction;

    @Column(name = "feature_name", nullable = false, length = 100)
    private String featureName;

    @Column(name = "feature_value", nullable = false, precision = 15, scale = 4)
    private BigDecimal featureValue;

    @Column(name = "feature_type", length = 50)
    private String featureType; // NUMERIC, BOOLEAN, CATEGORICAL

    @Column(name = "importance_score", nullable = false, precision = 5, scale = 4)
    private BigDecimal importanceScore; // 0.0000 a 1.0000

    @Column(name = "rank")
    private Integer rank; // 1 = mais importante

    @Column(name = "is_active", nullable = false, columnDefinition = "TINYINT(1) DEFAULT 1")
    private Boolean isActive = true;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
```

### 3. UserPredictionFeatures.java

```java
package com.rununit.prediction.entity;

import com.rununit.membership.entity.MembershipType;
import com.rununit.user.entity.User;
import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.Where;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "user_prediction_features", indexes = {
    @Index(name = "idx_engagement_score", columnList = "engagement_score"),
    @Index(name = "idx_is_active", columnList = "is_active")
})
@SQLDelete(sql = "UPDATE user_prediction_features SET is_active = 0, deleted_at = NOW() WHERE feature_id = ?")
@Where(clause = "is_active = 1")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserPredictionFeatures {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "feature_id")
    private Long featureId;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true, foreignKey = @ForeignKey(name = "fk_features_user_id"))
    private User user;

    // ==================== Features de Engajamento ====================
    @Column(name = "running_sessions_count", columnDefinition = "INT DEFAULT 0")
    private Integer runningSessionsCount;

    @Column(name = "runs_last_30_days", columnDefinition = "INT DEFAULT 0")
    private Integer runsLast30Days;

    @Column(name = "runs_last_90_days", columnDefinition = "INT DEFAULT 0")
    private Integer runsLast90Days;

    @Column(name = "distance_last_30_days_km", precision = 10, scale = 2, columnDefinition = "DECIMAL(10,2) DEFAULT 0")
    private BigDecimal distanceLast30DaysKm;

    @Column(name = "distance_last_90_days_km", precision = 10, scale = 2, columnDefinition = "DECIMAL(10,2) DEFAULT 0")
    private BigDecimal distanceLast90DaysKm;

    @Column(name = "days_since_last_run")
    private Integer daysSinceLastRun;

    @Column(name = "avg_distance_per_run", precision = 8, scale = 2)
    private BigDecimal avgDistancePerRun;

    // ==================== Features de Tempo ====================
    @Column(name = "days_on_platform")
    private Integer daysOnPlatform;

    @Column(name = "days_since_last_login")
    private Integer daysSinceLastLogin;

    // ==================== Features de Saúde Física ====================
    @Column(name = "avg_heart_rate_last_30_days", precision = 5, scale = 2)
    private BigDecimal avgHeartRateLast30Days;

    @Column(name = "peak_heart_rate_max")
    private Short peakHeartRateMax;

    @Column(name = "avg_elevation_gain", precision = 8, scale = 2)
    private BigDecimal avgElevationGain;

    @Column(name = "avg_pace_min_per_km", precision = 5, scale = 2)
    private BigDecimal avgPaceMinPerKm;

    // ==================== Features Comportamentais ====================
    @Column(name = "achievement_count", columnDefinition = "INT DEFAULT 0")
    private Integer achievementCount;

    @Column(name = "has_biometrics", columnDefinition = "TINYINT(1) DEFAULT 0")
    private Boolean hasBiometrics;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "membership_type_id", foreignKey = @ForeignKey(name = "fk_features_membership_type_id"))
    private MembershipType membershipType;

    @Column(name = "race_participation_count", columnDefinition = "INT DEFAULT 0")
    private Integer raceParticipationCount;

    // ==================== Features Derived (Calculadas) ====================
    @Column(name = "engagement_score", precision = 10, scale = 4)
    private BigDecimal engagementScore;

    @Column(name = "days_inactive_ratio", precision = 10, scale = 4)
    private BigDecimal daysInactiveRatio;

    @Column(name = "consistency_score", precision = 10, scale = 4)
    private BigDecimal consistencyScore;

    @Column(name = "monthly_activity_rate", precision = 10, scale = 4)
    private BigDecimal monthlyActivityRate;

    // ==================== Metadata ====================
    @Column(name = "is_active", nullable = false, columnDefinition = "TINYINT(1) DEFAULT 1")
    private Boolean isActive = true;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

### 4. ModelVersion.java

```java
package com.rununit.prediction.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "model_versions", indexes = {
    @Index(name = "idx_model_type", columnList = "model_type"),
    @Index(name = "idx_is_active", columnList = "is_active"),
    @Index(name = "idx_trained_at", columnList = "trained_at")
}, uniqueConstraints = {
    @UniqueConstraint(name = "uk_model_version", columnNames = {"model_type", "version_name"})
})
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ModelVersion {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "model_version_id")
    private Long modelVersionId;

    @Enumerated(EnumType.STRING)
    @Column(name = "model_type", nullable = false)
    private UserPrediction.PredictionType modelType; // CHURN, LTV

    @Column(name = "version_name", nullable = false, length = 50)
    private String versionName;

    @Column(name = "file_path", nullable = false, length = 500)
    private String filePath; // Caminho do arquivo .pkl ou .h5

    // ==================== Métricas (Classificação - Churn) ====================
    @Column(name = "accuracy", precision = 5, scale = 4)
    private BigDecimal accuracy;

    @Column(name = "precision", precision = 5, scale = 4)
    private BigDecimal precision;

    @Column(name = "recall", precision = 5, scale = 4)
    private BigDecimal recall;

    @Column(name = "f1_score", precision = 5, scale = 4)
    private BigDecimal f1Score;

    // ==================== Métricas (Regressão - LTV) ====================
    @Column(name = "rmse", precision = 10, scale = 4)
    private BigDecimal rmse;

    @Column(name = "mae", precision = 10, scale = 4)
    private BigDecimal mae;

    @Column(name = "r2_score", precision = 5, scale = 4)
    private BigDecimal r2Score;

    @Column(name = "is_active", nullable = false, columnDefinition = "TINYINT(1) DEFAULT 0")
    private Boolean isActive = false; // Apenas uma versão ativa por tipo

    @Column(name = "trained_at", nullable = false)
    private LocalDateTime trainedAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```

---

## 📝 Enums

### PredictionType.java

```java
package com.rununit.prediction.enums;

public enum PredictionType {
    CHURN("Churn - Risco de Abandono"),
    LTV("LTV - Valor do Tempo de Vida");

    private final String description;

    PredictionType(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}
```

### RiskLevel.java

```java
package com.rununit.prediction.enums;

public enum RiskLevel {
    LOW("Baixo Risco", "🟢"),
    MEDIUM("Risco Médio", "🟡"),
    HIGH("Alto Risco", "🔴");

    private final String label;
    private final String emoji;

    RiskLevel(String label, String emoji) {
        this.label = label;
        this.emoji = emoji;
    }

    public String getLabel() {
        return label;
    }

    public String getEmoji() {
        return emoji;
    }
}
```

---

## 🗄️ Repositórios

### UserPredictionRepository.java

```java
package com.rununit.prediction.repository;

import com.rununit.prediction.entity.UserPrediction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface UserPredictionRepository extends JpaRepository<UserPrediction, Long> {

    // Encontrar predição mais recente de um usuário por tipo
    @Query("""
        SELECT up FROM UserPrediction up
        WHERE up.user.userId = :userId
          AND up.predictionType = :predictionType
          AND up.isActive = true
        ORDER BY up.createdAt DESC
        LIMIT 1
        """)
    Optional<UserPrediction> findLatestByUserAndType(
        @Param("userId") Long userId,
        @Param("predictionType") UserPrediction.PredictionType predictionType
    );

    // Listar todas as predições de um usuário
    @Query("""
        SELECT up FROM UserPrediction up
        WHERE up.user.userId = :userId
          AND up.isActive = true
        ORDER BY up.createdAt DESC
        """)
    Page<UserPrediction> findAllByUser(
        @Param("userId") Long userId,
        Pageable pageable
    );

    // Encontrar usuários com alto risco
    @Query("""
        SELECT up FROM UserPrediction up
        WHERE up.predictionType = :predictionType
          AND up.riskLevel = 'HIGH'
          AND up.isActive = true
        ORDER BY up.probability DESC
        """)
    Page<UserPrediction> findHighRiskUsers(
        @Param("predictionType") UserPrediction.PredictionType predictionType,
        Pageable pageable
    );

    // Contar predições por nível de risco
    @Query("""
        SELECT up.riskLevel, COUNT(up) FROM UserPrediction up
        WHERE up.predictionType = :predictionType
          AND up.isActive = true
        GROUP BY up.riskLevel
        """)
    List<Object[]> countByRiskLevel(
        @Param("predictionType") UserPrediction.PredictionType predictionType
    );

    // Encontrar predições criadas após data específica
    @Query("""
        SELECT up FROM UserPrediction up
        WHERE up.predictionType = :predictionType
          AND up.createdAt >= :startDate
          AND up.isActive = true
        ORDER BY up.createdAt DESC
        """)
    Page<UserPrediction> findByCreatedAtAfter(
        @Param("predictionType") UserPrediction.PredictionType predictionType,
        @Param("startDate") LocalDateTime startDate,
        Pageable pageable
    );
}
```

### UserPredictionFeaturesRepository.java

```java
package com.rununit.prediction.repository;

import com.rununit.prediction.entity.UserPredictionFeatures;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserPredictionFeaturesRepository extends JpaRepository<UserPredictionFeatures, Long> {

    // Encontrar features de um usuário
    Optional<UserPredictionFeatures> findByUserUserIdAndIsActiveTrue(@Param("userId") Long userId);

    // Verificar se usuário tem features
    boolean existsByUserUserIdAndIsActiveTrue(@Param("userId") Long userId);
}
```

### PredictionLogRepository.java

```java
package com.rununit.prediction.repository;

import com.rununit.prediction.entity.PredictionLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PredictionLogRepository extends JpaRepository<PredictionLog, Long> {

    // Encontrar logs de uma predição (ordenados por importância)
    @Query("""
        SELECT pl FROM PredictionLog pl
        WHERE pl.prediction.predictionId = :predictionId
          AND pl.isActive = true
        ORDER BY pl.rank ASC
        """)
    List<PredictionLog> findByPredictionOrderByRank(@Param("predictionId") Long predictionId);

    // Listar top N features por importância
    @Query("""
        SELECT pl FROM PredictionLog pl
        WHERE pl.prediction.predictionId = :predictionId
          AND pl.isActive = true
        ORDER BY pl.importanceScore DESC
        LIMIT :limit
        """)
    List<PredictionLog> findTopFeatures(
        @Param("predictionId") Long predictionId,
        @Param("limit") int limit
    );
}
```

### ModelVersionRepository.java

```java
package com.rununit.prediction.repository;

import com.rununit.prediction.entity.ModelVersion;
import com.rununit.prediction.entity.UserPrediction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ModelVersionRepository extends JpaRepository<ModelVersion, Long> {

    // Encontrar versão ativa de um modelo
    @Query("""
        SELECT mv FROM ModelVersion mv
        WHERE mv.modelType = :modelType
          AND mv.isActive = true
        """)
    Optional<ModelVersion> findActiveVersion(@Param("modelType") UserPrediction.PredictionType modelType);

    // Listar todas as versões de um modelo (ordenadas por data)
    @Query("""
        SELECT mv FROM ModelVersion mv
        WHERE mv.modelType = :modelType
        ORDER BY mv.trainedAt DESC
        """)
    List<ModelVersion> findByModelType(@Param("modelType") UserPrediction.PredictionType modelType);

    // Encontrar versão específica por nome
    Optional<ModelVersion> findByModelTypeAndVersionName(
        UserPrediction.PredictionType modelType,
        String versionName
    );
}
```

---

## 🔄 DTOs

### UserPredictionDTO.java

```java
package com.rununit.prediction.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@JsonInclude(JsonInclude.Include.NON_NULL)
public class UserPredictionDTO {
    
    private Long predictionId;
    private Long userId;
    private String userName;
    private String userEmail;
    private String predictionType; // CHURN, LTV
    private BigDecimal probability;
    private String riskLevel; // LOW, MEDIUM, HIGH
    private BigDecimal confidenceScore;
    private String modelVersion;
    private LocalDateTime predictedAt;
    
    private UserContextDTO userContext;
    private List<FeatureImportanceDTO> featureImportance;
    private String recommendation;
    private List<SimilarUserDTO> similarUsers;
}
```

### FeatureImportanceDTO.java

```java
package com.rununit.prediction.dto;

import lombok.*;

import java.math.BigDecimal;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class FeatureImportanceDTO {
    
    private String featureName;
    private BigDecimal featureValue;
    private BigDecimal normalizedValue;
    private BigDecimal importanceScore;
    private String direction; // increases_risk, decreases_risk
    private String explanation;
    private Integer rank;
}
```

### DashboardMetricsDTO.java

```java
package com.rununit.prediction.dto;

import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DashboardMetricsDTO {
    
    private Integer highRiskCount;
    private Integer mediumRiskCount;
    private Integer lowRiskCount;
    private BigDecimal averageProbability;
    private BigDecimal ltv;
    private BigDecimal retentionRate;
    private LocalDateTime lastUpdate;
}
```

---

## ✅ Checklist de Implementação

### Banco de Dados
- [ ] Criar tabela `user_predictions`
- [ ] Criar tabela `prediction_logs`
- [ ] Criar tabela `user_prediction_features`
- [ ] Criar tabela `model_versions`
- [ ] Adicionar índices para performance
- [ ] Testar foreign keys e cascatas

### Java/Spring Boot
- [ ] Criar entidade `UserPrediction`
- [ ] Criar entidade `PredictionLog`
- [ ] Criar entidade `UserPredictionFeatures`
- [ ] Criar entidade `ModelVersion`
- [ ] Criar enums (`PredictionType`, `RiskLevel`)
- [ ] Criar repositórios (JpaRepository)
- [ ] Criar DTOs
- [ ] Implementar serviços

### Testes
- [ ] Testes de entidades (JPA)
- [ ] Testes de repositórios
- [ ] Testes de serviços
- [ ] Testes de controllers

---

## 📝 Notas Importantes

1. **Soft Delete**: Use `@SQLDelete` e `@Where` para exclusão lógica
2. **Índices**: Adicione índices em colunas frequentemente consultadas
3. **Cascade**: Apenas CASCADE onde faz sentido (logs → predição)
4. **Lazy Loading**: Use LAZY para melhor performance
5. **Precision**: BigDecimal com `precision` e `scale` corretos
6. **Audit**: `createdAt` é imutável, `updatedAt` auto-atualiza
7. **Timestamps**: Use `LocalDateTime` (sem zona de tempo) ou `ZonedDateTime`
8. **Validação**: Adicione `@NotNull`, `@Min`, `@Max`, etc.

