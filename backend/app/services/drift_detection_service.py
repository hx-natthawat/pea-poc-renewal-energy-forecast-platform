"""
Drift Detection and Model Retraining Service.

Implements automated drift detection, retraining triggers, and model lifecycle management.
Part of v1.1.0 Model Retraining Pipeline feature.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


class DriftType(str, Enum):
    """Types of drift that can be detected."""
    DATA_DRIFT = "data_drift"  # Input feature distribution shift
    CONCEPT_DRIFT = "concept_drift"  # Relationship between features and target changed
    PREDICTION_DRIFT = "prediction_drift"  # Model output distribution shift
    PERFORMANCE_DRIFT = "performance_drift"  # Model accuracy degradation


class DriftSeverity(str, Enum):
    """Severity levels for detected drift."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftResult:
    """Result of drift detection analysis."""
    drift_type: DriftType
    feature_name: str
    drift_score: float
    threshold: float
    drift_detected: bool
    severity: DriftSeverity
    baseline_stats: dict
    current_stats: dict
    p_value: Optional[float] = None
    recommendation: str = ""


@dataclass
class RetrainingTrigger:
    """Configuration for automatic retraining triggers."""
    # Performance thresholds
    mape_threshold: float = 12.0  # Trigger if MAPE exceeds this (TOR target: 10%)
    mae_threshold_voltage: float = 2.5  # Trigger if MAE exceeds this (TOR target: 2V)

    # Drift thresholds
    drift_score_threshold: float = 2.0  # Z-score threshold for drift
    min_samples_for_detection: int = 100

    # Time-based triggers
    max_days_without_retrain: int = 30
    min_days_between_retrains: int = 7

    # Confidence settings
    confidence_level: float = 0.95
    consecutive_violations: int = 3  # Require N consecutive violations


@dataclass
class ModelCandidate:
    """A candidate model for A/B testing or replacement."""
    model_id: str
    model_type: str
    version: str
    metrics: dict
    trained_at: datetime
    traffic_percentage: float = 0.0
    is_champion: bool = False
    is_challenger: bool = False


@dataclass
class RetrainingDecision:
    """Decision result from the retraining evaluation."""
    should_retrain: bool
    model_type: str
    reasons: list = field(default_factory=list)
    drift_results: list = field(default_factory=list)
    performance_metrics: dict = field(default_factory=dict)
    urgency: DriftSeverity = DriftSeverity.NONE
    estimated_improvement: Optional[float] = None


class DriftDetectionService:
    """
    Service for detecting data drift and triggering model retraining.

    Implements multiple drift detection methods:
    - Kolmogorov-Smirnov test for distribution comparison
    - Population Stability Index (PSI)
    - Performance degradation monitoring
    """

    def __init__(self, config: Optional[RetrainingTrigger] = None):
        """Initialize drift detection service."""
        self.config = config or RetrainingTrigger()
        self._violation_counts: dict[str, int] = {}
        self._last_retrain_times: dict[str, datetime] = {}

    def detect_data_drift(
        self,
        baseline_data: np.ndarray,
        current_data: np.ndarray,
        feature_name: str,
    ) -> DriftResult:
        """
        Detect data drift using Kolmogorov-Smirnov test.

        Args:
            baseline_data: Historical baseline feature values
            current_data: Current feature values
            feature_name: Name of the feature being analyzed

        Returns:
            DriftResult with detection results
        """
        if len(baseline_data) < self.config.min_samples_for_detection:
            return DriftResult(
                drift_type=DriftType.DATA_DRIFT,
                feature_name=feature_name,
                drift_score=0.0,
                threshold=self.config.drift_score_threshold,
                drift_detected=False,
                severity=DriftSeverity.NONE,
                baseline_stats={"count": len(baseline_data)},
                current_stats={"count": len(current_data)},
                recommendation="Insufficient baseline data for drift detection",
            )

        # Calculate statistics
        baseline_mean = float(np.mean(baseline_data))
        baseline_std = float(np.std(baseline_data))
        current_mean = float(np.mean(current_data))
        current_std = float(np.std(current_data))

        # Kolmogorov-Smirnov test
        ks_statistic, p_value = stats.ks_2samp(baseline_data, current_data)

        # Calculate drift score (z-score of mean shift)
        drift_score = abs((current_mean - baseline_mean) / baseline_std) if baseline_std > 0 else 0.0

        # Calculate PSI (Population Stability Index)
        psi = self._calculate_psi(baseline_data, current_data)

        # Determine severity
        drift_detected = drift_score > self.config.drift_score_threshold or p_value < (1 - self.config.confidence_level)
        severity = self._determine_severity(drift_score, psi)

        recommendation = self._generate_recommendation(drift_detected, severity, feature_name)

        return DriftResult(
            drift_type=DriftType.DATA_DRIFT,
            feature_name=feature_name,
            drift_score=round(drift_score, 4),
            threshold=self.config.drift_score_threshold,
            drift_detected=drift_detected,
            severity=severity,
            baseline_stats={
                "mean": round(baseline_mean, 4),
                "std": round(baseline_std, 4),
                "count": len(baseline_data),
            },
            current_stats={
                "mean": round(current_mean, 4),
                "std": round(current_std, 4),
                "count": len(current_data),
                "psi": round(psi, 4),
            },
            p_value=round(p_value, 6),
            recommendation=recommendation,
        )

    def detect_performance_drift(
        self,
        model_type: str,
        baseline_mape: float,
        current_mape: float,
        baseline_mae: Optional[float] = None,
        current_mae: Optional[float] = None,
    ) -> DriftResult:
        """
        Detect performance degradation in model predictions.

        Args:
            model_type: Type of model (solar/voltage)
            baseline_mape: Historical MAPE value
            current_mape: Current MAPE value
            baseline_mae: Historical MAE value (for voltage)
            current_mae: Current MAE value (for voltage)

        Returns:
            DriftResult with performance drift analysis
        """
        # Choose appropriate threshold based on model type
        if model_type == "solar":
            threshold = self.config.mape_threshold
            metric_name = "MAPE"
            baseline_value = baseline_mape
            current_value = current_mape
        else:
            threshold = self.config.mae_threshold_voltage
            metric_name = "MAE"
            baseline_value = baseline_mae or baseline_mape
            current_value = current_mae or current_mape

        # Calculate degradation
        degradation_pct = ((current_value - baseline_value) / baseline_value * 100) if baseline_value > 0 else 0
        drift_score = current_value / threshold if threshold > 0 else 0

        drift_detected = current_value > threshold
        severity = self._determine_performance_severity(current_value, threshold, model_type)

        # Track consecutive violations
        violation_key = f"{model_type}_performance"
        if drift_detected:
            self._violation_counts[violation_key] = self._violation_counts.get(violation_key, 0) + 1
        else:
            self._violation_counts[violation_key] = 0

        return DriftResult(
            drift_type=DriftType.PERFORMANCE_DRIFT,
            feature_name=metric_name,
            drift_score=round(drift_score, 4),
            threshold=threshold,
            drift_detected=drift_detected,
            severity=severity,
            baseline_stats={
                "value": round(baseline_value, 4),
                "metric": metric_name,
            },
            current_stats={
                "value": round(current_value, 4),
                "degradation_pct": round(degradation_pct, 2),
                "consecutive_violations": self._violation_counts.get(violation_key, 0),
            },
            recommendation=self._generate_performance_recommendation(
                drift_detected, severity, model_type, current_value, threshold
            ),
        )

    def evaluate_retraining_need(
        self,
        model_type: str,
        drift_results: list[DriftResult],
        current_metrics: dict[str, float],
        last_retrain_date: Optional[datetime] = None,
    ) -> RetrainingDecision:
        """
        Evaluate whether model retraining is needed.

        Args:
            model_type: Type of model to evaluate
            drift_results: List of drift detection results
            current_metrics: Current model performance metrics
            last_retrain_date: Date of last model retraining

        Returns:
            RetrainingDecision with recommendation
        """
        reasons = []
        urgency = DriftSeverity.NONE

        # Check drift results
        critical_drifts = [r for r in drift_results if r.severity == DriftSeverity.CRITICAL]
        high_drifts = [r for r in drift_results if r.severity == DriftSeverity.HIGH]

        if critical_drifts:
            reasons.append(f"Critical drift detected in {len(critical_drifts)} feature(s)")
            urgency = DriftSeverity.CRITICAL
        elif high_drifts:
            reasons.append(f"High drift detected in {len(high_drifts)} feature(s)")
            urgency = DriftSeverity.HIGH

        # Check performance thresholds
        current_mape = current_metrics.get("mape", 0)
        current_mae = current_metrics.get("mae", 0)

        if model_type == "solar" and current_mape > self.config.mape_threshold:
            reasons.append(f"MAPE ({current_mape:.2f}%) exceeds threshold ({self.config.mape_threshold}%)")
            urgency = max(urgency, DriftSeverity.HIGH, key=lambda x: list(DriftSeverity).index(x))

        if model_type == "voltage" and current_mae > self.config.mae_threshold_voltage:
            reasons.append(f"MAE ({current_mae:.3f}V) exceeds threshold ({self.config.mae_threshold_voltage}V)")
            urgency = max(urgency, DriftSeverity.HIGH, key=lambda x: list(DriftSeverity).index(x))

        # Check time-based triggers
        if last_retrain_date:
            days_since_retrain = (datetime.now() - last_retrain_date).days
            if days_since_retrain > self.config.max_days_without_retrain:
                reasons.append(f"Model has not been retrained in {days_since_retrain} days")
                urgency = max(urgency, DriftSeverity.MEDIUM, key=lambda x: list(DriftSeverity).index(x))

            # Prevent too frequent retraining
            if days_since_retrain < self.config.min_days_between_retrains:
                return RetrainingDecision(
                    should_retrain=False,
                    model_type=model_type,
                    reasons=[f"Minimum {self.config.min_days_between_retrains} days required between retrains"],
                    drift_results=drift_results,
                    performance_metrics=current_metrics,
                    urgency=DriftSeverity.NONE,
                )

        # Check consecutive violations
        violation_key = f"{model_type}_performance"
        if self._violation_counts.get(violation_key, 0) >= self.config.consecutive_violations:
            reasons.append(f"Performance threshold violated {self._violation_counts[violation_key]} consecutive times")

        should_retrain = len(reasons) > 0 and urgency in [DriftSeverity.HIGH, DriftSeverity.CRITICAL]

        return RetrainingDecision(
            should_retrain=should_retrain,
            model_type=model_type,
            reasons=reasons,
            drift_results=drift_results,
            performance_metrics=current_metrics,
            urgency=urgency,
        )

    def _calculate_psi(self, baseline: np.ndarray, current: np.ndarray, buckets: int = 10) -> float:
        """Calculate Population Stability Index."""
        # Create bins from baseline
        _, bin_edges = np.histogram(baseline, bins=buckets)

        # Calculate proportions
        baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
        current_counts, _ = np.histogram(current, bins=bin_edges)

        # Avoid division by zero
        baseline_props = (baseline_counts + 1) / (len(baseline) + buckets)
        current_props = (current_counts + 1) / (len(current) + buckets)

        # Calculate PSI
        psi = np.sum((current_props - baseline_props) * np.log(current_props / baseline_props))
        return float(psi)

    def _determine_severity(self, drift_score: float, psi: float) -> DriftSeverity:
        """Determine drift severity based on scores."""
        # PSI thresholds: <0.1 = no drift, 0.1-0.25 = moderate, >0.25 = significant
        if drift_score > 4.0 or psi > 0.25:
            return DriftSeverity.CRITICAL
        elif drift_score > 3.0 or psi > 0.2:
            return DriftSeverity.HIGH
        elif drift_score > 2.0 or psi > 0.1:
            return DriftSeverity.MEDIUM
        elif drift_score > 1.0 or psi > 0.05:
            return DriftSeverity.LOW
        return DriftSeverity.NONE

    def _determine_performance_severity(
        self, current_value: float, threshold: float, model_type: str
    ) -> DriftSeverity:
        """Determine severity based on performance degradation."""
        ratio = current_value / threshold if threshold > 0 else 0

        if ratio > 1.5:
            return DriftSeverity.CRITICAL
        elif ratio > 1.2:
            return DriftSeverity.HIGH
        elif ratio > 1.0:
            return DriftSeverity.MEDIUM
        elif ratio > 0.8:
            return DriftSeverity.LOW
        return DriftSeverity.NONE

    def _generate_recommendation(
        self, drift_detected: bool, severity: DriftSeverity, feature_name: str
    ) -> str:
        """Generate recommendation based on drift detection."""
        if not drift_detected:
            return "No action required - feature distribution is stable"

        recommendations = {
            DriftSeverity.LOW: f"Monitor {feature_name} - minor distribution shift detected",
            DriftSeverity.MEDIUM: f"Schedule data review for {feature_name} - moderate drift detected",
            DriftSeverity.HIGH: f"Consider retraining - significant drift in {feature_name}",
            DriftSeverity.CRITICAL: f"Immediate action required - critical drift in {feature_name}",
        }
        return recommendations.get(severity, "Review feature distribution")

    def _generate_performance_recommendation(
        self,
        drift_detected: bool,
        severity: DriftSeverity,
        model_type: str,
        current_value: float,
        threshold: float,
    ) -> str:
        """Generate recommendation based on performance drift."""
        if not drift_detected:
            return f"Model performance within acceptable limits ({current_value:.2f} < {threshold:.2f})"

        recommendations = {
            DriftSeverity.MEDIUM: "Schedule model review and prepare retraining data",
            DriftSeverity.HIGH: "Initiate model retraining pipeline",
            DriftSeverity.CRITICAL: "Urgent: Consider rolling back to previous model version",
        }
        return recommendations.get(severity, "Review model performance")


class ModelRegistryService:
    """
    Service for managing model versions and A/B testing.

    Handles model lifecycle: registration, promotion, rollback, and traffic splitting.
    """

    def __init__(self):
        """Initialize model registry service."""
        self._models: dict[str, list[ModelCandidate]] = {}
        self._traffic_config: dict[str, dict[str, float]] = {}

    def register_model(
        self,
        model_type: str,
        version: str,
        metrics: dict,
        model_id: Optional[str] = None,
    ) -> ModelCandidate:
        """
        Register a new model version.

        Args:
            model_type: Type of model (solar/voltage)
            version: Version string
            metrics: Training/validation metrics
            model_id: Optional custom ID

        Returns:
            Registered ModelCandidate
        """
        if model_type not in self._models:
            self._models[model_type] = []

        candidate = ModelCandidate(
            model_id=model_id or f"{model_type}-{version}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            model_type=model_type,
            version=version,
            metrics=metrics,
            trained_at=datetime.now(),
            traffic_percentage=0.0,
            is_champion=len(self._models[model_type]) == 0,  # First model is champion
            is_challenger=len(self._models[model_type]) > 0,
        )

        self._models[model_type].append(candidate)
        logger.info(f"Registered model: {candidate.model_id}")

        return candidate

    def setup_ab_test(
        self,
        model_type: str,
        champion_id: str,
        challenger_id: str,
        challenger_traffic_pct: float = 10.0,
    ) -> dict:
        """
        Set up A/B test between champion and challenger models.

        Args:
            model_type: Type of model
            champion_id: ID of current production model
            challenger_id: ID of new model to test
            challenger_traffic_pct: Percentage of traffic to route to challenger

        Returns:
            A/B test configuration
        """
        self._traffic_config[model_type] = {
            "champion_id": champion_id,
            "challenger_id": challenger_id,
            "champion_traffic": 100.0 - challenger_traffic_pct,
            "challenger_traffic": challenger_traffic_pct,
            "started_at": datetime.now().isoformat(),
        }

        logger.info(f"A/B test started for {model_type}: {challenger_traffic_pct}% to challenger")

        return self._traffic_config[model_type]

    def get_model_for_prediction(self, model_type: str) -> str:
        """
        Get model ID to use for prediction (supports A/B routing).

        Args:
            model_type: Type of model

        Returns:
            Model ID to use
        """
        if model_type not in self._traffic_config:
            # No A/B test, return champion
            models = self._models.get(model_type, [])
            champion = next((m for m in models if m.is_champion), None)
            return champion.model_id if champion else None

        config = self._traffic_config[model_type]

        # Simple random routing based on traffic percentage
        if np.random.random() * 100 < config["challenger_traffic"]:
            return config["challenger_id"]
        return config["champion_id"]

    def promote_challenger(self, model_type: str) -> Optional[ModelCandidate]:
        """
        Promote challenger to champion after successful A/B test.

        Args:
            model_type: Type of model

        Returns:
            Promoted model or None
        """
        if model_type not in self._traffic_config:
            return None

        config = self._traffic_config[model_type]
        challenger_id = config["challenger_id"]

        models = self._models.get(model_type, [])

        # Demote current champion
        for model in models:
            if model.is_champion:
                model.is_champion = False
                model.traffic_percentage = 0.0

        # Promote challenger
        challenger = next((m for m in models if m.model_id == challenger_id), None)
        if challenger:
            challenger.is_champion = True
            challenger.is_challenger = False
            challenger.traffic_percentage = 100.0

            # Clear A/B test config
            del self._traffic_config[model_type]

            logger.info(f"Promoted challenger {challenger_id} to champion")
            return challenger

        return None

    def rollback(self, model_type: str, target_version: Optional[str] = None) -> Optional[ModelCandidate]:
        """
        Rollback to a previous model version.

        Args:
            model_type: Type of model
            target_version: Specific version to rollback to (or previous if None)

        Returns:
            Rolled back model or None
        """
        models = self._models.get(model_type, [])
        if len(models) < 2:
            logger.warning(f"Cannot rollback {model_type}: insufficient model history")
            return None

        # Clear any A/B test
        if model_type in self._traffic_config:
            del self._traffic_config[model_type]

        # Find target model
        if target_version:
            target = next((m for m in models if m.version == target_version), None)
        else:
            # Get second most recent model
            sorted_models = sorted(models, key=lambda m: m.trained_at, reverse=True)
            target = sorted_models[1] if len(sorted_models) > 1 else None

        if target:
            # Demote current champion
            for model in models:
                model.is_champion = False
                model.traffic_percentage = 0.0

            # Promote target
            target.is_champion = True
            target.traffic_percentage = 100.0

            logger.info(f"Rolled back {model_type} to version {target.version}")
            return target

        return None

    def get_model_history(self, model_type: str) -> list[dict]:
        """Get history of all model versions."""
        models = self._models.get(model_type, [])
        return [
            {
                "model_id": m.model_id,
                "version": m.version,
                "metrics": m.metrics,
                "trained_at": m.trained_at.isoformat(),
                "is_champion": m.is_champion,
                "is_challenger": m.is_challenger,
                "traffic_percentage": m.traffic_percentage,
            }
            for m in sorted(models, key=lambda x: x.trained_at, reverse=True)
        ]


# Singleton instances
_drift_service: Optional[DriftDetectionService] = None
_registry_service: Optional[ModelRegistryService] = None


def get_drift_detection_service() -> DriftDetectionService:
    """Get or create drift detection service instance."""
    global _drift_service
    if _drift_service is None:
        _drift_service = DriftDetectionService()
    return _drift_service


def get_model_registry_service() -> ModelRegistryService:
    """Get or create model registry service instance."""
    global _registry_service
    if _registry_service is None:
        _registry_service = ModelRegistryService()
    return _registry_service
