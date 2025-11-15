import type { NeighborhoodMetrics, NeighborhoodWithScore } from '../types';

const clamp = (value: number, min = 0, max = 1) => Math.max(min, Math.min(max, value));

const inverseScale = (value: number, low: number, high: number) =>
  clamp((high - value) / (high - low));

const scale = (value: number, low: number, high: number) => clamp((value - low) / (high - low));

export const calculateRiskScore = (metrics: NeighborhoodMetrics): number => {
  const incomeScore = inverseScale(metrics.income, 30000, 90000);
  const transportScore = inverseScale(metrics.transportAccess, 0.4, 0.95);
  const distanceScore = scale(metrics.distanceToGrocery, 0.25, 2.75);
  const densityScore = inverseScale(metrics.storeDensity, 0.8, 4.0);
  const chronicScore = scale(metrics.chronicDiseasePrevalence, 0.08, 0.32);

  const weighted =
    incomeScore * 0.25 +
    transportScore * 0.2 +
    distanceScore * 0.2 +
    densityScore * 0.15 +
    chronicScore * 0.2;

  return Number(clamp(weighted, 0, 1).toFixed(3));
};

export const classifyRiskLevel = (riskScore: number): NeighborhoodWithScore['riskLevel'] => {
  if (riskScore < 0.3) return 'low';
  if (riskScore < 0.5) return 'moderate';
  if (riskScore < 0.7) return 'elevated';
  return 'severe';
};

export const describeDrivers = (metrics: NeighborhoodMetrics): string => {
  const driverScores = [
    { key: 'income', value: inverseScale(metrics.income, 30000, 90000), label: 'lower incomes' },
    {
      key: 'transport',
      value: inverseScale(metrics.transportAccess, 0.4, 0.95),
      label: 'limited transportation access',
    },
    {
      key: 'distance',
      value: scale(metrics.distanceToGrocery, 0.25, 2.75),
      label: 'long distances to full-service groceries',
    },
    {
      key: 'density',
      value: inverseScale(metrics.storeDensity, 0.8, 4.0),
      label: 'low healthy food store density',
    },
    {
      key: 'health',
      value: scale(metrics.chronicDiseasePrevalence, 0.08, 0.32),
      label: 'high chronic disease prevalence',
    },
  ]
    .sort((a, b) => b.value - a.value)
    .slice(0, 2)
    .filter((entry) => entry.value > 0.35);

  if (!driverScores.length) {
    return 'Balanced access and health indicators keep overall risk low.';
  }

  if (driverScores.length === 1) {
    return `Risk is primarily driven by ${driverScores[0].label}.`;
  }

  return `Risk is driven by ${driverScores[0].label} and ${driverScores[1].label}.`;
};

export const recommendIntervention = (metrics: NeighborhoodMetrics): string => {
  if (metrics.distanceToGrocery > 2.2) {
    return 'Pilot a mobile produce market that rotates through apartment complexes and schools twice per week.';
  }
  if (metrics.storeDensity < 1.2) {
    return 'Offer corner store refrigeration grants plus SNAP healthy incentive marketing to expand fresh produce nearby.';
  }
  if (metrics.transportAccess < 0.55) {
    return 'Partner with the transit agency on dedicated shuttles or micro-transit credits for grocery trips.';
  }
  if (metrics.chronicDiseasePrevalence > 0.25) {
    return 'Embed peer-led nutrition and chronic disease management classes at trusted community centers.';
  }
  return 'Support community-run produce co-ops and pop-up farmers markets using underutilized public plazas.';
};
