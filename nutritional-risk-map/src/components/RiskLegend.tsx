const buckets = [
  { label: 'Low', color: '#2D936C', range: '0 - 29' },
  { label: 'Moderate', color: '#F0C808', range: '30 - 49' },
  { label: 'Elevated', color: '#F49F0A', range: '50 - 69' },
  { label: 'Severe', color: '#D7263D', range: '70 - 100' },
];

export const RiskLegend = () => (
  <div className="risk-legend">
    <span className="legend-title">Nutrition Risk Score</span>
    <div className="legend-items">
      {buckets.map((bucket) => (
        <div className="legend-item" key={bucket.label}>
          <span className="legend-color" style={{ backgroundColor: bucket.color }} aria-hidden />
          <div>
            <strong>{bucket.label}</strong>
            <div>{bucket.range}</div>
          </div>
        </div>
      ))}
    </div>
  </div>
);
