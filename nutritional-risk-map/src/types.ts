import type { Polygon, MultiPolygon } from 'geojson';

export interface NeighborhoodMetrics {
  id: string;
  name: string;
  income: number; // median household income in USD
  transportAccess: number; // 0-1 index, higher is better access
  distanceToGrocery: number; // miles to nearest full-service grocery
  storeDensity: number; // healthy food stores per square mile
  chronicDiseasePrevalence: number; // 0-1 share of adults with nutrition-related chronic disease
  population?: number;
  geometry: Polygon | MultiPolygon;
}

export interface CityDataset {
  city: string;
  description?: string;
  neighborhoods: NeighborhoodMetrics[];
}

export interface CityOption {
  id: string;
  name: string;
  dataUrl: string;
  center: [number, number];
  zoom: number;
}

export interface NeighborhoodWithScore extends NeighborhoodMetrics {
  riskScore: number; // normalized 0-1
  riskLevel: 'low' | 'moderate' | 'elevated' | 'severe';
  driverSummary: string;
  recommendation: string;
}
