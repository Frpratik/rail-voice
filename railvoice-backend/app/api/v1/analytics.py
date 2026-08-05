from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.station_health import StationHealthService
from app.schemas.analytics_schemas import StationHeatmapResponse

router = APIRouter()

@router.get("/station-heatmap", response_model=StationHeatmapResponse)
async def get_station_heatmap(db: AsyncSession = Depends(get_db)):
    service = StationHealthService(db)
    return await service.get_station_heatmap_geojson()
