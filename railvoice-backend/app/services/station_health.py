from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.location import Station
from app.models.issue import Issue
from app.schemas.analytics_schemas import (
    StationHeatmapResponse,
    StationGeoFeature,
    StationGeoFeatureGeometry,
    StationGeoFeatureProperties,
)

class StationHealthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_station_heatmap_geojson(self) -> StationHeatmapResponse:
        # Get all active stations
        res = await self.db.execute(select(Station).where(Station.is_active == True))
        stations = res.scalars().all()

        features = []
        for station in stations:
            # Default lat/lng for demo if missing
            lat = station.latitude if station.latitude is not None else 18.9322
            lng = station.longitude if station.longitude is not None else 72.8264

            # Fetch open issues for this station
            issue_res = await self.db.execute(
                select(Issue).where(
                    Issue.station_id == station.id,
                    Issue.status.in_(["OPEN", "IN_PROGRESS"])
                )
            )
            issues = issue_res.scalars().all()

            active_count = len(issues)
            critical_count = sum(1 for i in issues if (i.severity or 1) >= 4)

            # Compute health score
            health_score = 100.0 - (active_count * 10.0) - (critical_count * 15.0)
            if health_score < 0:
                health_score = 0.0

            status_summary = {
                "OPEN": sum(1 for i in issues if i.status == "OPEN"),
                "IN_PROGRESS": sum(1 for i in issues if i.status == "IN_PROGRESS"),
            }

            feature = StationGeoFeature(
                type="Feature",
                geometry=StationGeoFeatureGeometry(
                    type="Point",
                    coordinates=[float(lng), float(lat)]
                ),
                properties=StationGeoFeatureProperties(
                    station_id=str(station.id),
                    code=station.code,
                    name=station.name,
                    health_score=float(health_score),
                    active_issues_count=active_count,
                    critical_issues_count=critical_count,
                    status_summary=status_summary
                )
            )
            features.append(feature)

        return StationHeatmapResponse(type="FeatureCollection", features=features)
