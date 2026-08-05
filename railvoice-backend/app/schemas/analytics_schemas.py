from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class StationGeoFeatureGeometry(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]

class StationGeoFeatureProperties(BaseModel):
    station_id: str
    code: str
    name: str
    health_score: float
    active_issues_count: int
    critical_issues_count: int
    status_summary: Dict[str, int]

class StationGeoFeature(BaseModel):
    type: str = "Feature"
    geometry: StationGeoFeatureGeometry
    properties: StationGeoFeatureProperties

class StationHeatmapResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[StationGeoFeature]
