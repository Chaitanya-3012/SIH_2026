from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import SensorHealth, Anomaly, Reading
from backend.crud.health import create_health_snapshot


@dataclass
class HealthComponents:
    anomaly_frequency: float
    drift_trend: float
    data_completeness: float
    reconstruction_error_trend: float
    variance_behavior: float


@dataclass
class HealthScore:
    composite_score: float
    label: str  # "healthy" | "degrading" | "faulty"
    components: HealthComponents


class HealthScorer:
    """Composite sensor health scoring based on 5 factors."""
    
    # Weights for composite score (sum = 1.0)
    WEIGHTS = {
        "anomaly_frequency": 0.25,
        "drift_trend": 0.25,
        "data_completeness": 0.15,
        "reconstruction_error_trend": 0.20,
        "variance_behavior": 0.15,
    }
    
    # Thresholds for label assignment
    HEALTHY_THRESHOLD = 0.3
    DEGRADING_THRESHOLD = 0.6
    
    # Time window for rolling calculations (hours)
    WINDOW_HOURS = 24

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_health(self, station_id: str) -> HealthScore:
        """Compute composite health score for a station."""
        now = datetime.utcnow()
        window_start = now - timedelta(hours=self.WINDOW_HOURS)
        
        components = await self._compute_components(station_id, window_start, now)
        composite = self._compute_composite(components)
        label = self._assign_label(composite)
        
        return HealthScore(
            composite_score=composite,
            label=label,
            components=components,
        )

    async def _compute_components(
        self,
        station_id: str,
        start: datetime,
        end: datetime
    ) -> HealthComponents:
        """Compute all 5 health components."""
        # 1. Anomaly frequency: anomalies per hour in window
        anomaly_freq = await self._anomaly_frequency(station_id, start, end)
        
        # 2. Drift trend: slope of drift events
        drift_trend = await self._drift_trend(station_id, start, end)
        
        # 3. Data completeness: % of expected readings present
        data_completeness = await self._data_completeness(station_id, start, end)
        
        # 4. Reconstruction error trend: LSTM AE error slope
        recon_trend = await self._reconstruction_error_trend(station_id, start, end)
        
        # 5. Variance behavior: coefficient of variation stability
        variance_behavior = await self._variance_behavior(station_id, start, end)
        
        return HealthComponents(
            anomaly_frequency=anomaly_freq,
            drift_trend=drift_trend,
            data_completeness=data_completeness,
            reconstruction_error_trend=recon_trend,
            variance_behavior=variance_behavior,
        )

    async def _anomaly_frequency(self, station_id: str, start: datetime, end: datetime) -> float:
        """Anomalies per hour, normalized (0 = no anomalies, 1 = high frequency)."""
        from backend.models import Anomaly
        stmt = select(func.count(Anomaly.anomaly_id)).where(
            Anomaly.station_id == station_id,
            Anomaly.ts >= start,
            Anomaly.ts <= end,
            Anomaly.status == "open"
        )
        result = await self.db.execute(stmt)
        count = result.scalar() or 0
        hours = (end - start).total_seconds() / 3600
        freq_per_hour = count / max(hours, 1)
        # Normalize: 10+ anomalies/hour = 1.0
        return min(freq_per_hour / 10.0, 1.0)

    async def _drift_trend(self, station_id: str, start: datetime, end: datetime) -> float:
        """Drift event trend (0 = stable, 1 = strong degradation)."""
        from backend.models import DriftEvent
        stmt = select(DriftEvent).where(
            DriftEvent.station_id == station_id,
            DriftEvent.ts >= start,
            DriftEvent.ts <= end,
            DriftEvent.degradation_flag == True
        ).order_by(DriftEvent.ts)
        result = await self.db.execute(stmt)
        events = list(result.scalars().all())
        
        if not events:
            return 0.0
        
        # Fraction of drift events with degradation flag
        degradation_count = sum(1 for e in events if e.degradation_flag)
        return min(degradation_count / max(len(events), 1), 1.0)

    async def _data_completeness(self, station_id: str, start: datetime, end: datetime) -> float:
        """% of expected readings present (assuming 1 reading/minute = 60/hour)."""
        stmt = select(func.count(Reading.reading_id)).where(
            Reading.station_id == station_id,
            Reading.ts >= start,
            Reading.ts <= end
        )
        result = await self.db.execute(stmt)
        actual = result.scalar() or 0
        
        expected = int((end - start).total_seconds() / 60)  # 1 per minute
        if expected == 0:
            return 1.0
        
        completeness = actual / expected
        # Invert: 0 = complete, 1 = missing data
        return min(1.0 - completeness, 1.0)

    async def _reconstruction_error_trend(self, station_id: str, start: datetime, end: datetime) -> float:
        """Trend of LSTM reconstruction error from anomalies' component_scores."""
        stmt = select(Anomaly.component_scores).where(
            Anomaly.station_id == station_id,
            Anomaly.ts >= start,
            Anomaly.ts <= end
        )
        result = await self.db.execute(stmt)
        scores = [row[0] for row in result.fetchall() if row[0] and "lstm_score" in row[0]]
        
        if len(scores) < 3:
            return 0.0
        
        # Simple slope of lstm_score over time
        lstm_scores = [s["lstm_score"] for s in scores]
        n = len(lstm_scores)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(lstm_scores) / n
        
        numerator = sum((x[i] - x_mean) * (lstm_scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        # Normalize slope: positive slope = increasing error = bad
        return min(max(slope * 10, 0.0), 1.0)

    async def _variance_behavior(self, station_id: str, start: datetime, end: datetime) -> float:
        """Coefficient of variation stability (0 = stable, 1 = erratic)."""
        stmt = select(Reading.temperature_c, Reading.pressure_hpa, Reading.humidity_pct).where(
            Reading.station_id == station_id,
            Reading.ts >= start,
            Reading.ts <= end,
            Reading.temperature_c.is_not(None),
            Reading.pressure_hpa.is_not(None),
            Reading.humidity_pct.is_not(None)
        )
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        
        if len(rows) < 10:
            return 0.0
        
        # Compute CV for each parameter
        import numpy as np
        temps = [r[0] for r in rows]
        pressures = [r[1] for r in rows]
        humids = [r[2] for r in rows]
        
        cvs = []
        for vals in [temps, pressures, humids]:
            mean = np.mean(vals)
            std = np.std(vals)
            if mean != 0:
                cvs.append(std / abs(mean))
        
        if not cvs:
            return 0.0
        
        avg_cv = np.mean(cvs)
        # Normalize: CV > 0.5 = erratic
        return min(avg_cv / 0.5, 1.0)

    def _compute_composite(self, components: HealthComponents) -> float:
        """Weighted composite score."""
        return (
            self.WEIGHTS["anomaly_frequency"] * components.anomaly_frequency +
            self.WEIGHTS["drift_trend"] * components.drift_trend +
            self.WEIGHTS["data_completeness"] * components.data_completeness +
            self.WEIGHTS["reconstruction_error_trend"] * components.reconstruction_error_trend +
            self.WEIGHTS["variance_behavior"] * components.variance_behavior
        )

    def _assign_label(self, composite: float) -> str:
        """Assign health label based on composite score."""
        if composite < self.HEALTHY_THRESHOLD:
            return "healthy"
        elif composite < self.DEGRADING_THRESHOLD:
            return "degrading"
        return "faulty"

    async def save_health_snapshot(self, station_id: str, health: HealthScore) -> SensorHealth:
        """Persist health snapshot to database."""
        return await create_health_snapshot(
            self.db,
            station_id=station_id,
            ts=datetime.utcnow(),
            composite_score=health.composite_score,
            label=health.label,
            anomaly_frequency=health.components.anomaly_frequency,
            drift_trend=health.components.drift_trend,
            data_completeness=health.components.data_completeness,
            reconstruction_error_trend=health.components.reconstruction_error_trend,
            variance_behavior=health.components.variance_behavior,
        )

    async def check_label_change(self, station_id: str, new_label: str) -> Optional[str]:
        """Check if health label changed from last snapshot."""
        last = await self.db.execute(
            select(SensorHealth.label)
            .where(SensorHealth.station_id == station_id)
            .order_by(desc(SensorHealth.ts))
            .limit(1)
        )
        prev_label = last.scalar_one_or_none()
        if prev_label and prev_label != new_label:
            return prev_label
        return None