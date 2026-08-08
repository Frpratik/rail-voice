"use client";

import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { StationGeoFeature } from "@/lib/types";

interface MapProps {
  features: StationGeoFeature[];
}

function SetViewOnLoad({ features }: { features: StationGeoFeature[] }) {
  const map = useMap();
  useEffect(() => {
    if (features.length > 0) {
      const first = features[0].geometry.coordinates;
      map.setView([first[1], first[0]], 11);
    }
  }, [features, map]);
  return null;
}

export default function StationHeatmapMap({ features }: MapProps) {
  // Center near Mumbai (Western Railway line default: 19.0760, 72.8777)
  const defaultCenter: [number, number] = [19.0760, 72.8777];

  const getColor = (score: number) => {
    if (score >= 80) return "#10b981"; // Green
    if (score >= 50) return "#f59e0b"; // Amber
    return "#ef4444"; // Red
  };

  return (
    <div className="h-[600px] w-full rounded-2xl overflow-hidden border border-border shadow-xl relative z-10">
      <MapContainer
        center={defaultCenter}
        zoom={10}
        scrollWheelZoom={true}
        className="h-full w-full bg-slate-950"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <SetViewOnLoad features={features} />
        {features.map((feat) => {
          const [lng, lat] = feat.geometry.coordinates;
          const { name, code, health_score, active_issues_count, critical_issues_count } = feat.properties;
          const color = getColor(health_score);

          return (
            <CircleMarker
              key={feat.properties.station_id}
              center={[lat, lng]}
              radius={health_score < 50 ? 16 : 12}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: 2,
              }}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-2 min-w-[200px] text-slate-900">
                  <div className="flex items-center justify-between border-b pb-1 mb-2">
                    <h4 className="font-bold text-sm">{name}</h4>
                    <span className="text-xs font-mono font-semibold px-1.5 py-0.5 rounded bg-slate-100">
                      {code}
                    </span>
                  </div>
                  <div className="space-y-1 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Health Index:</span>
                      <span className="font-bold font-mono" style={{ color: color }}>
                        {Number(health_score || 0).toFixed(1)} / 100
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Active Issues:</span>
                      <span className="font-semibold">{active_issues_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Critical Issues:</span>
                      <span className="font-semibold text-rose-600">{critical_issues_count}</span>
                    </div>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
