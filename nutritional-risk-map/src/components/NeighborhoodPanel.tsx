import type { NeighborhoodWithScore } from '../types';

interface Props {
  neighborhood?: NeighborhoodWithScore | null;
}

const prettyPercent = (value: number) => `${Math.round(value * 100)}`;

export const NeighborhoodPanel = ({ neighborhood }: Props) => {
  if (!neighborhood) {
    return (
      <div className="panel empty-panel">
        <p>Select a neighborhood on the map to see nutrition risk details.</p>
      </div>
    );
  }

  return (
    <div className="panel neighborhood-panel">
      <header>
        <div>
          <p className="eyebrow">Neighborhood</p>
          <h2>{neighborhood.name}</h2>
        </div>
        <div className={`risk-pill ${neighborhood.riskLevel}`}>{neighborhood.riskLevel}</div>
      </header>

      <section>
        <p className="eyebrow">Risk score</p>
        <div className="score-value">{prettyPercent(neighborhood.riskScore)}</div>
        <p className="score-subtitle">0 (low risk) — 100 (severe risk)</p>
      </section>

      <section>
        <p className="eyebrow">Key drivers</p>
        <p>{neighborhood.driverSummary}</p>
      </section>

      <section>
        <p className="eyebrow">Recommended intervention</p>
        <p>{neighborhood.recommendation}</p>
      </section>

      <section className="metrics-grid">
        <Metric label="Median income" value={`$${neighborhood.income.toLocaleString()}`} />
        <Metric
          label="Transit access index"
          value={neighborhood.transportAccess.toFixed(2)}
        />
        <Metric label="Miles to grocery" value={neighborhood.distanceToGrocery.toFixed(1)} />
        <Metric label="Store density" value={`${neighborhood.storeDensity.toFixed(1)} / sq mi`} />
        <Metric
          label="Chronic disease prevalence"
          value={`${prettyPercent(neighborhood.chronicDiseasePrevalence)}%`}
        />
        {neighborhood.population && (
          <Metric label="Population" value={neighborhood.population.toLocaleString()} />
        )}
      </section>
    </div>
  );
};

const Metric = ({ label, value }: { label: string; value: string }) => (
  <div className="metric-card">
    <p className="eyebrow">{label}</p>
    <strong>{value}</strong>
  </div>
);
