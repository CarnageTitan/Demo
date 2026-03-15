import { useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson';
import type { LatLngExpression, Layer, LeafletMouseEvent, StyleFunction } from 'leaflet';
import type { NeighborhoodWithScore } from '../types';

type NeighborhoodFeature = Feature<Polygon | MultiPolygon, NeighborhoodWithScore>;

interface Props {
  neighborhoods: NeighborhoodWithScore[];
  center: LatLngExpression;
  zoom: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const getRiskColor = (score: number) => {
  if (score < 0.3) return '#2D936C';
  if (score < 0.5) return '#F0C808';
  if (score < 0.7) return '#F49F0A';
  return '#D7263D';
};

export const RiskMap = ({ neighborhoods, center, zoom, selectedId, onSelect }: Props) => {
  const featureCollection = useMemo<FeatureCollection<Polygon | MultiPolygon, NeighborhoodWithScore>>(
    () => ({
      type: 'FeatureCollection',
      features: neighborhoods.map((neighborhood) => ({
        type: 'Feature',
        id: neighborhood.id,
        properties: neighborhood,
        geometry: neighborhood.geometry,
      })),
    }),
    [neighborhoods],
  );

  const styleFeature: StyleFunction = (feature) => {
    const props = feature?.properties as NeighborhoodWithScore | undefined;
    const isSelected = props?.id === selectedId;
    return {
      color: isSelected ? '#111' : '#444',
      weight: isSelected ? 3 : 1,
      fillOpacity: 0.75,
      fillColor: getRiskColor(props?.riskScore ?? 0),
    };
  };

  return (
    <MapContainer center={center} zoom={zoom} className="risk-map" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <GeoJSON
        key={selectedId ?? 'all'}
        data={featureCollection}
        style={styleFeature}
        onEachFeature={(feature: NeighborhoodFeature, layer: Layer) => {
          layer.on({
            click: () => {
              const props = feature?.properties;
              if (props) {
                onSelect(props.id);
              }
            },
            mouseover: (event: LeafletMouseEvent) => {
              event.target.setStyle({ ...styleFeature(feature), weight: 3 });
            },
            mouseout: (event: LeafletMouseEvent) => {
              event.target.setStyle(styleFeature(feature));
            },
          });
          const props = feature?.properties;
          if (props) {
            layer.bindTooltip(
              `${props.name}: ${Math.round(props.riskScore * 100)} risk score`,
              { sticky: true },
            );
          }
        }}
      />
    </MapContainer>
  );
};
