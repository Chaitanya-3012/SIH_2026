from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from backend.models import Reading, DriftEvent
from backend.crud import create_health_snapshot  # Will need to add drift event creation


@dataclass
class DriftResult:
    parameter: str
    trend_value: float  # Slope per hour
    degradation_flag: bool
    severity: str  # "low" | "medium" | "high"


class DriftMonitor:
    """Rolling-window drift detection per sensor parameter."""
    
    # Drift thresholds (slope per hour)
    DRIFT_THRESHOLDS = {
        "temperature": 0.5,    # degC/hour
        "pressure": 0.3,       # hPa/hour
        "humidity": 1.0,       # %/hour
    }
    
    SEVERITY_BANDS = {
        "temperature": [0.5, 1.0, 2.0],
        "pressure": [0.3, 0.6, 1.2],
        "humidity": [1.0, 2.0, 4.0],
    }
    
    WINDOW_HOURS = 24
    MIN_SAMPLES = 20

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_drift(self, station_id: str) -> list[DriftResult]:
        """Check all parameters for drift, return drift events."""
        now = datetime.utcnow()
        window_start = now - timedelta(hours=self.WINDOW_HOURS)
        
        results = []
        for param in ["temperature", "pressure", "humidity"]:
            result = await self._check_parameter_drift(station_id, param, window_start, now)
            if result:
                results.append(result)
        
        return results

    async def _check_parameter_drift(
        self,
        station_id: str,
        parameter: str,
        start: datetime,
        end: datetime
    ) -> Optional[DriftResult]:
        """Check drift for a single parameter using linear regression slope."""
        col_map = {
            "temperature": Reading.temperature_c,
            "pressure": Reading.pressure_hpa,
            "humidity": Reading.humidity_pct,
        }
        col = col_map[parameter]
        
        stmt = select(Reading.ts, col).where(
            Reading.station_id == station_id,
            Reading.ts >= start,
            Reading.ts <= end,
            col.is_not(None)
        ).order_by(Reading.ts)
        
        result = await self.db.execute(stmt)
        rows = result.fetchall()
        
        if len(rows) < self.MIN_SAMPLES:
            return None
        
        # Convert to arrays for linear regression
        timestamps = [(r[0] - start).total_seconds() / 3600 for r in rows]  # hours from start
        values = [r[1] for r in rows]
        
        # Linear regression
        n = len(timestamps)
        x_mean = np.mean(timestamps)
        y_mean = np.mean(values)
        
        numerator = sum((timestamps[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((timestamps[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return None
        
        slope = numerator / denominator  # units per hour
        abs_slope = abs(slope)
        
        # Check against threshold
        threshold = self.DRIFT_THRESHOLDS[parameter]
        if abs_slope < threshold:
            return None
        
        # Determine severity
        bands = self.SEVERITY_BANDS[parameter]
        if abs_slope >= bands[2]:
            severity = "high"
        elif abs_slope >= bands[1]:
            severity = "medium"
        else:
            severity = "low"
        
        return DriftResult(
            parameter=parameter,
            trend_value=slope,
            degradation_flag=True,
            severity=severity,
        )

    async def save_drift_events(self, station_id: str, drift_results: list[DriftResult]) -> list[DriftEvent]:
        """Persist drift events to database."""
        events = []
        now = datetime.utcnow()
        
        for dr in drift_results:
            event = DriftEvent(
                station_id=station_id,
                ts=now,
                parameter=dr.parameter,
                trend_value=dr.trend_value,
                degradation_flag=dr.degradation_flag,
            )
            self.db.add(event)
            events.append(event)
        
        await self.db.flush()
        for e in events:
            await self.db.refresh(e)
        
        return events