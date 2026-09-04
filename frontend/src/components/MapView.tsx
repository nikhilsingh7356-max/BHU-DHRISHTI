"use client";

import React from "react";
import { MapContainer, TileLayer, GeoJSON, LayersControl } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { FeatureCollection } from "geojson";
import { Parcel } from "@/lib/types";

interface MapViewProps {
  parcels: Parcel[];
  height?: number | string;
  onParcelClick?: (parcel: Parcel) => void;
}

function parcelsToGeoJSON(parcels: Parcel[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: parcels
      .filter((p) => p.geometry)
      .map((p, i) => ({
        id: i,
        type: "Feature",
        properties: {
          id: p.id,
          survey_number: p.survey_number,
          khasra_number: p.khasra_number,
          area_sq_m: p.area_sq_m,
          status: p.current_status,
          name: p.survey_number || `Parcel ${p.id}`,
        },
        geometry: p.geometry as unknown as GeoJSON.Geometry,
      })),
  };
}

const styleByStatus = (status?: string) => {
  switch (status) {
    case "ACQUIRED":
      return { color: "#059669", weight: 2, fillColor: "#059669", fillOpacity: 0.3 };
    case "SURVEYED":
      return { color: "#2563eb", weight: 2, fillColor: "#2563eb", fillOpacity: 0.3 };
    case "COMPENSATION_PENDING":
    case "COMPENSATION_IN_PROGRESS":
      return { color: "#d97706", weight: 2, fillColor: "#d97706", fillOpacity: 0.3 };
    default:
      return { color: "#0f172a", weight: 1.5, fillColor: "#334155", fillOpacity: 0.2 };
  }
};

export default function MapView({ parcels, height = 500, onParcelClick }: MapViewProps) {
  const geoJson = parcelsToGeoJSON(parcels);

  const defaultCenter: [number, number] = [22.5, 79.5];
  const defaultZoom = 5;

  return (
    <div style={{ height: typeof height === "number" ? `${height}px` : height, width: "100%" }} className="rounded-xl overflow-hidden border border-slate-200 z-0">
      <MapContainer center={defaultCenter} zoom={defaultZoom} scrollWheelZoom className="h-full w-full">
        <LayersControl position="topright">
          <LayersControl.BaseLayer name="OpenStreetMap" checked>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite">
            <TileLayer
              attribution="ESRI"
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
          </LayersControl.BaseLayer>
          <LayersControl.Overlay name="Parcels" checked>
            <GeoJSON
              key={JSON.stringify(geoJson)}
              data={geoJson as never}
              style={(feature) => styleByStatus(String(feature?.properties?.status ?? "")) as never}
              onEachFeature={(feature, layer) => {
                layer.bindPopup(
                  `<strong>${feature.properties?.name || "Parcel"}</strong><br/>` +
                    `Khasra: ${feature.properties?.khasra_number || "-"}<br/>` +
                    `Area: ${feature.properties?.area_sq_m || 0} sq m<br/>` +
                    `Status: ${feature.properties?.status || "-"}`
                );
                layer.on("click", () => {
                  const parcel = parcels.find(
                    (p) => p.id === feature.properties?.id
                  );
                  if (parcel && onParcelClick) onParcelClick(parcel);
                });
              }}
            />
          </LayersControl.Overlay>
        </LayersControl>
      </MapContainer>
    </div>
  );
}
