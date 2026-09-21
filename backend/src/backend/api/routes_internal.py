from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from backend.database import get_db
from backend.schemas.internal import IngestReading, IngestBatchResponse, DetectionResultSummary
from backend.crud.reading import bulk_create_readings
from backend.crud.anomaly import bulk_create_anomalies
from backend.services.detection import DetectionService

router = APIRouter(prefix="/internal", tags=["internal"])

detection_service = DetectionService()


@router.post("/ingest", response_model=IngestBatchResponse)
async def ingest_readings(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Ingest NDJSON stream of readings, run batch detection, persist results."""
    # Parse NDJSON from request body
    readings: List[IngestReading] = []
    
    async for line in request.stream():
        line = line.strip()
        if not line:
            continue
        try:
            reading = IngestReading.model_validate_json(line)
            readings.append(reading)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid NDJSON line: {e}")
    
    if not readings:
        raise HTTPException(status_code=400, detail="No valid readings in request")
    
    # Run batch detection
    detection_results = detection_service.process_batch(readings)
    
    # Convert to summaries for response
    summaries = detection_service.to_summary(detection_results)
    
    # Prepare readings for bulk insert
    reading_creates = []
    for r in readings:
        reading_creates.append(type('obj', (object,), {
            'station_id': r.station_id,
            'ts': r.ts,
            'temperature_c': r.temperature_c,
            'pressure_hpa': r.pressure_hpa,
            'humidity_pct': r.humidity_pct,
            'source': 'simulator',
        })())
    
    # Bulk insert readings
    saved_readings = await bulk_create_readings(db, reading_creates)
    
    # Prepare anomalies for bulk insert
    anomaly_creates = []
    for i, result in enumerate(detection_results):
        if result.is_anomaly and i < len(saved_readings):
            anomaly_creates.append(type('obj', (object,), {
                'reading_id': saved_readings[i].reading_id,
                'station_id': result.station_id,
                'ts': result.ts,
                'anomaly_type': result.root_cause_tag or 'unknown',
                'confidence_score': result.confidence_score,
                'severity': result.severity or 'low',
                'root_cause_tag': result.root_cause_tag,
                'shap_values': result.component_scores,
                'component_scores': result.component_scores,
            })())
    
    # Bulk insert anomalies
    if anomaly_creates:
        await bulk_create_anomalies(db, anomaly_creates)
    
    anomalies_detected = len(anomaly_creates)
    
    return IngestBatchResponse(
        processed=len(readings),
        anomalies_detected=anomalies_detected,
        results=summaries
    )